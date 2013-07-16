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

from apiclient.discovery import build
import PyRSS2Gen

VERBOSE_MODE = 0
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def usage():
  sys.stderr.write(
"""  Usage: %s [ -h ] [ -v ] -k APIKey -c ChannelName

    -h, --help      Show this usage message and exit.
    -v, --verbose   Verbose Output to StdErr
    -k, --apikey    YouTube API Key
    -c, --channel   YouTube Channel / Username
""" % sys.argv[0])

## Get the video list from a YouTube Channel, and convert into an RSS Feed.
#
# Print an RSS XML File to STDOUT.
# @param apikey YouTube Developer API Key
# @param channel YouTube Channel Name to convert to RSS.
# @return 0 on success, non-zero on any errors.

def YtChannelToRss(apikey, channel):
  if (VERBOSE_MODE): sys.stderr.write("ApiKey:  " + apikey + "\n")
  if (VERBOSE_MODE): sys.stderr.write("Channel: " + channel + "\n")

  # Build the Google API Client
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=apikey)

  # Get the Channel ID String from the Channel Name
  channelResponse = youtube.channels().list(
    part="id,snippet",
    forUsername=channel,
  ).execute()
  
  channelIds = channelResponse.get("items", [])
  if len(channelIds) != 1:
    sys.stderr.write("Didn't find exactly one channel ID: found " + str(len(channelIds)) + " channel Ids\n")
    sys.exit(1)

  channelIdString = channelIds[0]['id']
  if (VERBOSE_MODE): sys.stderr.write("Channel ID: " + channelIdString + "\n")

  # Get List of Videos
  searchRequest = youtube.search().list(
    channelId=channelIdString,
    part="id,snippet",
    maxResults=20
  )
  searchResponse = searchRequest.execute()

  videos = []
  channels = []
  playlists = []

  while (searchResponse):
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
      elif searchResult["id"]["kind"] == "youtube#channel":
        channels.append("%s (%s)" % (searchResult["snippet"]["title"],
                                     searchResult["id"]["channelId"]))
      elif searchResult["id"]["kind"] == "youtube#playlist":
        playlists.append("%s (%s)" % (searchResult["snippet"]["title"],
                                      searchResult["id"]["playlistId"]))
    # get next page of results
    searchRequest = youtube.search().list_next(previous_request=searchRequest , previous_response=searchResponse)
    if searchRequest:
      searchResponse = searchRequest.execute()
    else:
      searchResponse = None

  # Sort Videos
  videos = sorted(videos, key=lambda video:video['published'], reverse=True)

  if (VERBOSE_MODE): sys.stderr.write("Found " + str(len(videos)) + " Videos\n")
  if (VERBOSE_MODE): sys.stderr.write("Found " + str(len(channels)) + " Channels\n")
  if (VERBOSE_MODE): sys.stderr.write("Found " + str(len(playlists)) + " Playlists\n")

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

  if (VERBOSE_MODE): sys.stderr.write("Building RSS with " + str(len(rssItems)) + " Items\n")

  rss = PyRSS2Gen.RSS2(
    title = "YtChannelRss: " + channel,
    link = "",
    description = "RSS Feed Auto-Generated by YtChannelRss for Youtube Channels",
    lastBuildDate = datetime.datetime.now(),
    items = rssItems
  )

  # Print RSS to STDOUT
  xmlOutput = rss.to_xml()
  print xmlOutput
  return 0


def main(argv):

  apikey = ""
  channelname = ""

  # Get Opts
  try:
    opts, args = getopt.getopt(argv, "hvk:c:", ["help", "verbose", "apikey=", "channel="]) 
  except getopt.GetoptError:
    usage()
    sys.exit(2)

  # Process Opts
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      usage()
      sys.exit()
    elif opt in ("-v", "--verbose"):
      global VERBOSE_MODE
      VERBOSE_MODE = 1
    elif opt in ("-k", "--apikey"): 
      apikey = arg
    elif opt in ("-c", "--channel"):
      channelname = arg

  # Required Arguments
  if (channelname == "" or apikey == ""):
    usage()
    sys.exit(1)

  # Run
  sys.exit( YtChannelToRss(apikey, channelname) )

if __name__ == "__main__":
    main(sys.argv[1:])
