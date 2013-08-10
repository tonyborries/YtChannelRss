#!/usr/bin/env python

"""YtChannelRss.py: Generate an RSS XML file from all videos of a YouTube Channel.

https://github.com/tonyborries/YtChannelRss
"""

__author__ = "tonyborries"
__copyright__ = "Copyright 2013, tonyborries"
__credits__ = ["tonyborries"]
__license__ = "MIT"
__maintainer__ = "tonyborries"
__email__ = "hiretonyb@gmail.com"

import sys
import getopt
import datetime

import PyRSS2Gen

def usage():
  sys.stderr.write(
"""  Usage: %s [ -h ] [ -v ] -k APIKey -c ChannelName

    -h, --help      Show this usage message and exit.
    -v, --verbose   Verbose Output to StdErr
    -k, --apikey    YouTube API Key
    -c, --channel   YouTube Channel / Username
    --v2            Use the YouTube v2 API (default is V3)
""" % sys.argv[0])

## De-duplicate the video list. 
#
# I've seen some issues with the v3 API returning duplicate videos, so 
# clean up any dupes here. 
# @param videos The input Video List
# [{'id', 'title', 'url', 'published', 'description'}]
# @return The de-duplicated video list, in the same format.

def DeDuplicateVideos(videos):
  # sort by URL
  videos = sorted(videos, key=lambda video:video['url'], reverse=True)

  # if Duplicate URLs, remove from list
  x=0
  while (x<(len(videos)-1)):
    if videos[x]["url"] == videos[x+1]["url"]:
      videos.pop(x)
    else:
      x+=1

  return videos

## Get the video list from a YouTube Channel, using the v2 API.
#
# @param apikey YouTube Developer API Key
# @param channel YouTube Channel Name to convert to RSS.
# @param verbose Enable Verbose Printing to STDERR.
# @return None on error / no videos found. Otherwise, return a list of dictionary objects as 
# [{'id', 'title', 'url', 'published', 'description'}]

def GetVideosV2(apikey, channelName, verbose):
  if (verbose): sys.stderr.write("Running v2 API\n")
  if (verbose): sys.stderr.write("ApiKey:  " + apikey + "\n")
  if (verbose): sys.stderr.write("Channel: " + channelName + "\n")

  from gdata.youtube import service as myService
  ytService = myService.YouTubeService(developer_key=apikey)
  searchResults = ytService.GetYouTubeUserFeed(username=channelName)

  videos = []
  reportedNumVideos = 0

  while (searchResults):
    if reportedNumVideos == 0:
      reportedNumVideos = int(searchResults.total_results.text)
  
    for entry in searchResults.entry:
  
      video = {}
  
      # parse Id string to get Video Id
      # id is in the format 'Id:http://gdata.youtube.com/feeds/api/videos/A3e48TnUFBE'
      video['id'] = entry.id.text.split('/')[-1]

      video['title'] = entry.title.text
      video['url'] = "http://www.youtube.com/watch?v=" + video['id']
      dateString = entry.published.text[0:19] # 2013-05-18T01:43:21.000Z -> 2013-05-18T01:43:21
      video['published'] = datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S")
      video['description'] = entry.media.description.text
      videos.append(video)
  
    searchResults = ytService.GetNext(searchResults)

  videos = DeDuplicateVideos(videos)

  if len(videos) != reportedNumVideos:
    sys.stderr.write("WARNING: Search Result Reported " + str(reportedNumVideos) + " but only retrieved " + str(len(videos)) + "\n")

  return videos


## Get the video list from a YouTube Channel, using the v3 API.
#
# @param apikey YouTube Developer API Key
# @param channel YouTube Channel Name to convert to RSS.
# @param verbose Enable Verbose Printing to STDERR.
# @return None on error / no videos found. Otherwise, return a list of dictionary objects as 
# [{'id', 'title', 'url', 'published', 'description'}]

def GetVideosV3(apikey, channelName, verbose):
  from apiclient.discovery import build

  if (verbose): sys.stderr.write("ApiKey:  " + apikey + "\n")
  if (verbose): sys.stderr.write("Channel: " + channelName + "\n")

  YOUTUBE_API_SERVICE_NAME = "youtube"
  YOUTUBE_API_VERSION = "v3"

  # Build the Google API Client
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=apikey)

  # Get the Channel ID String from the Channel Name
  channelResponse = youtube.channels().list(
    part="id,snippet",
    forUsername=channelName,
  ).execute()
  
  channelIds = channelResponse.get("items", [])
  if len(channelIds) != 1:
    sys.stderr.write("Didn't find exactly one channel ID: found " + str(len(channelIds)) + " channel Ids\n")
    sys.exit(1)

  channelIdString = channelIds[0]['id']
  if (verbose): sys.stderr.write("Channel ID: " + channelIdString + "\n")

  ###
  # Get List of Videos
  ytSearch = youtube.search()

  searchRequest = ytSearch.list(
    channelId=channelIdString,
    part="id,snippet",
    maxResults=50,
    type='video'
  )

  reportedNumVideos = 0
  videos = []

  while (searchRequest):
    searchResponse = searchRequest.execute()

    if reportedNumVideos == 0:
      reportedNumVideos = searchResponse['pageInfo']['totalResults']

    for searchResult in searchResponse.get("items", []):
      if searchResult["id"]["kind"] == "youtube#video":
        video = {}
        video['id'] = searchResult['id']['videoId']
        video['title'] = searchResult['snippet']['title']
        video['url'] = "http://www.youtube.com/watch?v=" + video['id']
        dateString = searchResult['snippet']['publishedAt'][0:19] # 2013-05-18T01:43:21.000Z -> 2013-05-18T01:43:21
        video['published'] = datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S")
        video['description'] = searchResult['snippet']['description']
        videos.append(video)
      else:
        sys.stderr.write("Unknown media type: " + searchResult["id"]["kind"] + "\n")

    # get next page of results
    searchRequest = youtube.search().list_next(previous_request=searchRequest , previous_response=searchResponse)

  videos = DeDuplicateVideos(videos)

  if len(videos) != reportedNumVideos:
    sys.stderr.write("WARNING: Search Result Reported " + str(reportedNumVideos) + " but only retrieved " + str(len(videos)) + "\n")

  return videos

## Output an RSS Feed
#
# @param videos A List of Dictionary objects describing the videos to place in the feed
# [{'id', 'title', 'url', 'published', 'description'}]
# @param channel YouTube Channel Name to convert to RSS.
# @param verbose Enable Verbose Printing to STDERR.
# @return None on error / no videos found. Otherwise, return a list of dictionary objects as 

def WriteRss(videos, channelName, verbose):
  # Build RSS
  rssItems = []
  for video in videos:
    rssItem = PyRSS2Gen.RSSItem(
      title = video['title'],
      link  = video['url'],
      description = video['description'], 
      guid = PyRSS2Gen.Guid(video['url']),
      pubDate = video['published']
    )
    rssItems.append(rssItem)

  if (verbose): sys.stderr.write("Building RSS with " + str(len(rssItems)) + " Items\n")

  rss = PyRSS2Gen.RSS2(
    title = channelName + " by YtChannelRss", 
    link = "",
    description = "RSS Feed Generated by YtChannelRss for Youtube Channels",
    lastBuildDate = datetime.datetime.now(),
    items = rssItems
  )

  # Print RSS to STDOUT
  xmlOutput = rss.to_xml()
  print xmlOutput
  return 0


def main(argv):

  apikey = ""
  channelName = ""
  VERBOSE_MODE = 0
  USE_V2 = 0

  # Get Opts
  try:
    opts, args = getopt.getopt(argv, "hvk:c:", ["help", "verbose", "apikey=", "channel=", "v2"]) 
  except getopt.GetoptError:
    usage()
    sys.exit(2)

  # Process Opts
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      usage()
      sys.exit()
    elif opt in ("-v", "--verbose"):
      VERBOSE_MODE = 1
    elif opt in ("-k", "--apikey"): 
      apikey = arg
    elif opt in ("-c", "--channel"):
      channelName = arg
    elif opt in ("--v2"):
      USE_V2 = 1

  # Required Arguments
  if (channelName == "" or apikey == ""):
    usage()
    sys.exit(1)

  # get Video list
  if USE_V2 > 0:
    videos = GetVideosV2(apikey, channelName, VERBOSE_MODE)
  else:
    videos = GetVideosV3(apikey, channelName, VERBOSE_MODE)

  if not videos:
    return 1

  # Sort Videos
  videos = sorted(videos, key=lambda video:video['published'], reverse=True)

  if (VERBOSE_MODE): sys.stderr.write("Found " + str(len(videos)) + " Videos\n")

  # make RSS
  sys.exit( WriteRss(videos, channelName, VERBOSE_MODE) )


if __name__ == "__main__":
    main(sys.argv[1:])

