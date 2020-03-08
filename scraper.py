import os
import sys

root = os.getcwd()
sys.path.append("{root}/python".format(root=root))

import pprint as prettyPrint
import csv
import json
import xml.etree.ElementTree as ET
import urllib

from datetime import datetime
from retrying import retry
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from secrets import SECRETS
from apiclient.discovery import build

from decorators import classDecorator, exceptionHandler

@classDecorator(exceptionHandler)
class YoutubeScraper():
  def __init__(self, executablePath = "", maxComments = 50):
    self.baseUrl = "https://youtube.com"
    self.driver = None
    self.youtube = None
    self.maxComments = maxComments
    self.executablePath = executablePath

  def __del__(self):
    print("Exiting...")
    if self.driver: self.driver.quit()

  def pprint(self, prefix='', data=''):
    pp = prettyPrint.PrettyPrinter(indent=2)
    if prefix: pp.pprint("{0}: {1}".format(prefix, data))
    else: pp.pprint(data)

  # Files
  def assertCorrectFileType(self, filepath, fileType):
    assert filepath[-4:] == fileType, '"{0}" is not a "{1}" file'.format(filepath, fileType)

  def saveToJSON(self, filename, data = {}):
    filepath = '{0}.json'.format(filename)
    with open(filepath, 'w+', encoding='utf-8') as file:
      json.dump(data, file, ensure_ascii=False, indent=2)
    file.close()

  def addToCSV(self, filepath, data = [], keys = []):
    self.assertCorrectFileType(filepath=filepath, fileType=".csv")
    with open(filepath, 'a', newline='\n') as file:
      if self.isCSVEmpty(filepath):
        writer = csv.writer(file)
        writer.writerow(keys)
      writer = csv.DictWriter(file, fieldnames=keys)
      for review in data:
        writer.writerow(review)
      file.close()

  def isCSVEmpty(self, filepath):
    self.assertCorrectFileType(filepath=filepath, fileType=".csv")
    with open(filepath, 'r') as file:
      reader = csv.reader(file)
      for index, _ in enumerate(reader):
        if index: return False
      return True

  def getCSVData(self, filepath, dictKeys = []):
    self.assertCorrectFileType(filepath = filepath, fileType = ".csv")
    file = open(filepath, "r")
    reader = list(csv.DictReader(file, delimiter = ","))
    data = []
    file.seek(1)
    if dictKeys:
      for line in reader:
        record = {}
        for key in dictKeys:
          record[key] = line[key]
        data.append(record)
    else: data = list(reader)
    file.close()
    return data

  # Text Processing
  def processText(self, text):
    # Remove emojis, extra spaces, and newline characters
    return ' '.join(text.split()).replace('\n', '').encode('ascii', 'ignore').decode('ascii')

  def extractChannelInfoFromUrl(self, channelUrl):
    if "user/" in channelUrl:
      cleansedUrl = channelUrl.replace("user/", "").replace(self.baseUrl, "").replace("/", "")
      return ("user", cleansedUrl)
    elif "channel/" in channelUrl:
      cleansedUrl = channelUrl.replace("channel/", "").replace(self.baseUrl, "").replace("/", "")
      return ("channel", cleansedUrl)
    else: return (None, channelUrl)

  # Browser Manipulation
  def initBrowser(self):
    if not self.driver:
      chromeOptions = webdriver.ChromeOptions()
      chromeOptions.add_argument("--mute-audio")
      if self.executablePath == '': self.driver = webdriver.Chrome(options=chromeOptions)
      else: self.driver = webdriver.Chrome(options=chromeOptions, executable_path=self.executablePath)

  def navigate(self, url):
    self.driver.get(url)

  def setupPage(self):
    if not self.driver: self.initBrowser()
    self.scrollDown()

  def wait(self, seconds): 
    if self.driver: sleep(seconds)

  def scrollDown(self): 
    html = self.driver.find_element_by_tag_name('html')
    [html.send_keys(Keys.PAGE_DOWN) for i in range(3)]

  def scrollUpSlightly(self): 
    html = self.driver.find_element_by_tag_name('html')
    html.send_keys(Keys.PAGE_UP)

  def infiniteScrollDown(self, totalComments):
    # ~ Each scroll reveals 4-5 more comments
    countScrolls = totalComments if totalComments < self.maxComments else self.maxComments
    for i in range(countScrolls):
      self.scrollDown()

  @retry(stop_max_attempt_number = 10)
  def clickRetry(self, element):
    element.click()

  # Page Scraping
  def getPageSoup(self):
    html = self.driver.find_element_by_tag_name('html').get_attribute("innerHTML")
    soup = BeautifulSoup(html, 'html.parser')
    return soup

  def selectOne(self, elementSoup, selector):
    elements = elementSoup.select(selector)
    if len(elements) == 0: return None
    return elements[0]

  def scrapeResults(self, query):
    self.initBrowser()
    self.setupPage()
    self.navigate("{0}/results?search_query={1}".format(self.baseUrl, query))
    queryResultsSoup = self.getPageSoup()
    videos = queryResultsSoup.select("ytd-video-renderer")
    return [self.scrapeSingleResult(video, query) for video in videos]

  def scrapeSingleResult(self, videoSoup, query):
    channelNameParentList = videoSoup.select("yt-formatted-string.style-scope.ytd-channel-name.complex-string")
    channelNameElement = channelNameParentList[0]
    channelName = channelNameElement.select("a")[0].get("href", "")
    channelUrl = "{0}{1}".format(self.baseUrl, channelName) if channelName else ""
    titleElement = self.selectOne(videoSoup, "#thumbnail")
    videoId = titleElement.get("href", "").strip("/watch?v=")
    return { "videoId": videoId, "query": query, "channelUrl": channelUrl, "timestamp": str(datetime.now()) }

  def scrapeSingleVideoComments(self, videoId, maxComments = 50):
    assert isinstance(videoId, str), "videoId {0} is not a string".format(videoId)
    self.initBrowser()
    self.setupPage()
    self.navigate("{0}{1}{2}".format(self.baseUrl, "/watch?v=", videoId))

    pageSoup = self.getPageSoup()
    self.wait(2)
    self.scrollDown()
    self.wait(2)
    try: commentsFilter = self.driver.find_element_by_id("icon-label")
    except NoSuchElementException: 
      print("Got NoSuchElementException for {0}. Skipping...".format(videoId))
      return (None, None)

    # Get recent comments, not just top comments
    self.clickRetry(commentsFilter)
    self.wait(1)
    newestFirstButton = self.driver.find_element_by_xpath('//*[@id="menu"]/a[2]')
    self.clickRetry(newestFirstButton)
    self.wait(1)
    self.scrollUpSlightly()
    self.clickRetry(newestFirstButton)
    self.wait(1)

    pageSoup = self.getPageSoup()

    commentsSectionElement = self.selectOne(pageSoup, "#comments")
    totalCommentsElement = self.selectOne(commentsSectionElement, "yt-formatted-string.count-text.style-scope.ytd-comments-header-renderer")
    totalComments = int(totalCommentsElement.text.split(" ")[0].replace("," , "")) if totalCommentsElement else None
    if totalComments:
      self.infiniteScrollDown(totalComments)
      pageSoup = self.getPageSoup()
      comments = [self.processText(comment.text) for comment in pageSoup.select("#content-text")]
      return (totalComments, comments)

  # Youtube API
  def initYoutubeAPI(self):
    if not self.youtube:
      DEVELOPER_KEY = SECRETS["DEVELOPER_KEY"]
      YOUTUBE_API_SERVICE_NAME = "youtube"
      YOUTUBE_API_VERSION = "v3"
      self.youtube = build(
        YOUTUBE_API_SERVICE_NAME, 
        YOUTUBE_API_VERSION,
        developerKey=DEVELOPER_KEY
      )

  def fetchChannelId(self, username):
    self.initYoutubeAPI()
    channelData = self.youtube.channels().list(part = "id", forUsername = username).execute()
    channelData = channelData.get("items", [])
    if not len(channelData):
      print('Could not find channelId for username "{0}"'.format(username))
      return
    return channelData[0].get("id", "")

  def fetchChannelMetadata(self, channelId):
    self.initYoutubeAPI()
    channelDetails = self.youtube.channels().list(id = channelId, part = "snippet,statistics").execute()
    channelData = {}
    for channel in channelDetails.get("items",[]):
      try:
        channelData['channelPublishedAt'] = channel['snippet'].get('publishedAt', '')
        channelData['channelDescription'] = channel['snippet'].get('description', '')
        channelData['channelSubscriberCount'] = int(channel['statistics'].get('subscriberCount', 0))
        channelData['channelViewCount'] = int(channel['statistics'].get('viewCount', 0))
        channelData['channelCommentCount'] = int(channel['statistics'].get("commentCount", 0))
        channelData['channelVideoCount'] = int(channel['statistics'].get('videoCount', 0))
      except KeyError as e:
        print("An KeyError error %s occurred:\n%s" % (e.resp.status, e.content))
    return channelData

  def fetchVideoMetadata(self, videoId):
    self.initYoutubeAPI()
    captions = youtube.captions().list(videoId = videoId, part = "snippet").execute()
    videoData = {}
    for capts in captions.get("items", []):
      if capts["snippet"]["language"] == 'en':
        videoData['captid'] = capts["id"]
        videoData['trackKind'] = capts["snippet"]["trackKind"]
        videoData['isCC'] = capts["snippet"]["isCC"]
        videoData['language'] = capts["snippet"]["language"]
        videoData['isAutoSynced'] = capts["snippet"]["isAutoSynced"]
        videoData['audioTrackType'] = capts["snippet"]["audioTrackType"]
        videoData['captsLastUpdated'] = capts["snippet"]["lastUpdated"]

    url = "http://video.google.com/timedtext?lang=en&v={0}".format(videoId)
    subtitle = []
    subtitle_retrieve = urllib.urlopen(url).read()

    if len(subtitle_retrieve) != 0:
      tree = ET.fromstring(subtitle_retrieve)
      subtitle_extract = ET.tostring(tree, encoding = 'utf-8', method = 'text')
      subtitle.extend([subtitle_extract.decode('utf-8', 'ignore').encode('utf-8')])
    videoData['subtitle'] = subtitle
    return videoData4