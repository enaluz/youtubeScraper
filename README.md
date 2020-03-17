# Youtube Scraper

## Table of Contents
[Purpose](#purpose)  
[Installation](#installation)  
[Usage](#usage)  
[Limitations](#limitations)  
[Example Output](#example-output)  
[TODO](#TODO)

## Purpose
A Youtube Scraper for video query results and video page metadata.

## Installation
1. Run `pip3 install bs4 selenium`
2. Install [Chromedriver](https://sites.google.com/a/chromium.org/chromedriver/downloads) for the version of 
Chrome you have installed in your computer. 


Ensure it's installed in your os' default path. On a Mac, this is usually `~/usr/local/bin`. Else, supply a custom path to `customPath` in `index.py`. To make this easy, you could just place the Chromedriver executable in this directory, and paste the absolute path in `customPath`.

[How do I find out which version of Chrome I'm using?](https://help.zenplanner.com/hc/en-us/articles/204253654-How-to-Find-Your-Internet-Browser-Version-Number-Google-Chrome)
## Usage
1. Get a [Youtube API key](https://developers.google.com/youtube/v3/getting-started). 

2. Rename `secrets.template.py` to `secrets.py` and add your key to that file. 

3. Populate `queries` in `index.py` with whatever strings you'd like to search for. Run `python3 index.py`. Make sure the browser instance is visible while script runs. This will take approximately `len(queries)` * 140 seconds to run.

4. *Optional:
  - Edit `maxComments` to set the (rough) estimate for the max comments to scrape.
    - Default: 50
  - Edit `videoBreadth` to set the number of videos to scrape. 
    - Max: ~20
    - Default: 25

## Limitations
1. `maxComments` setting is only an estimate. May return slightly more or less comments.
2. Rarely `countComments` doesn't return a result. Sometimes this is because comments are disabled, sometimes there's a race condition.
3. The browser must be in visual focus in order to scrape `countComments` and probably `comments` too.

## Example Output

```
{
  "query": "friends",
  "timestamp": "2020-03-08 09:17:29.174640",
  "videoId": "lvjc2Z48qR8",
  "videoUrl": "https://youtube.com/watch?v=lvjc2Z48qR8",
  "channel": {
    "channelPublishedAt": "2006-11-21T04:53:43.000Z",
    "channelDescription": "For 17 incredible, eventful and sometimes life-changing seasons, Ellen has been making audiences laugh all over the world with her signature brand of humor and her powerful message of kindness. There's nobody better at making you laugh and brightening your day. You never know what funny can do!",
    "channelSubscriberCount": 36900000,
    "channelViewCount": 19223023647,
    "channelCommentCount": 0,
    "channelVideoCount": 11572,
    "channelUrl": "https://youtube.com/user/TheEllenShow"
  },
  "comments": {
    "totalComments": 661,
    "length": 289,
    "comments": ["I love friends!", ...]
  }
}
```


## TODO
- Scrape comments
- Remove `truncatedDescription`
