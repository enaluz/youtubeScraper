from scraper import YoutubeScraper
import os
from datetime import datetime

queries = ["the common cold"]

customPath = ""
maxComments = 50
videoBreadth = 20

for query in queries:
  storageDirectoryPath = "./data/{0}".format(query.replace(" ", "-"))
  if not os.path.exists(storageDirectoryPath): os.makedirs(storageDirectoryPath)
  Scraper = YoutubeScraper(executablePath = customPath, maxComments = maxComments)
  videosData = Scraper.scrapeResults(query)
  videosDataPath = "{0}/videosData.csv".format(storageDirectoryPath)
  Scraper.addToCSV(filepath=videosDataPath, data = videosData, keys = videosData[0].keys())
  videoData = Scraper.getCSVData(filepath = videosDataPath, dictKeys = ["channelUrl", "videoId", "timestamp"])
  for index, record in enumerate(videoData):
    if index < videoBreadth or 25:
      channelUrl = record["channelUrl"]
      videoId = record["videoId"]
      timestamp = record["timestamp"]
      urlType, cleansedUrl = Scraper.extractChannelInfoFromUrl(channelUrl)
      if urlType == "user": channelId = Scraper.fetchChannelId(cleansedUrl)
      elif urlType == "channel": channelId = cleansedUrl
      else: pass
      channelMetadata = Scraper.fetchChannelMetadata(channelId)
      totalComments, comments = Scraper.scrapeSingleVideoComments(videoId)
      data = {
        "query": query,
        "timestamp": timestamp,
        "videoId": videoId,
        "videoUrl": "{0}/watch?v={1}".format(Scraper.baseUrl, videoId),
        "channel": {
          **channelMetadata,
          "channelUrl": channelUrl
        },
        "comments": {
          "totalComments": totalComments,
          "length": len(comments) if comments else None,
          "comments": comments
        }
      }
      if comments:
        print("Saving data to JSON file")
        Scraper.saveToJSON('{0}/{1}'.format(storageDirectoryPath, videoId), data)