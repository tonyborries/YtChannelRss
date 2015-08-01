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
import time

import PyRSS2Gen

def usage():
  sys.stderr.write(
"""  Usage: %s [ -h ] [ -v ] -k <APIKey> -c <ChannelName> -r <num_most_recent>

    -h, --help        Show this usage message and exit.
    -v, --verbose     Verbose Output to StdErr
    -k, --apikey      YouTube API Key
    -c, --channel     YouTube Channel Name / Username
    -i, --channel_id  YouTube Channel ID
    -r, --recent      Retrieve only the num_most_recent uploads (Experimental)
""" % sys.argv[0])

## De-duplicate the video list. 
#
# I've seen some issues with the v3 API returning duplicate videos, so 
# clean up any dupes here. 
# @param videos The input Video List
# [{'id', 'title', 'url', 'published', 'description'}]
# @return The de-duplicated video list, in the same format.

def DeDuplicateVideos(videos, verbose=False):

  if (verbose): sys.stderr.write("Begin Dedup:  " + str(len(videos)) + " Videos\n")

  # sort by URL
  videos = sorted(videos, key=lambda video:video['url'], reverse=True)

  # if Duplicate URLs, remove from list
  x=0
  while (x<(len(videos)-1)):
    if videos[x]["url"] == videos[x+1]["url"]:
      videos.pop(x)
    else:
      x+=1

  if (verbose): sys.stderr.write("End Dedup:  " + str(len(videos)) + " Videos\n")

  return videos


## Get the Channel ID from Channel Name
#
# @param apikey YouTube Developer API Key
# @param channel_name YouTube Channel Name
# @param verbose Enable Verbose Printing to STDERR.
# @return YouTube Channel ID as String

def GetChannelIdFromName(apikey, channel_name, verbose):
  from apiclient.discovery import build
  from googleapiclient.errors import HttpError

  if (verbose): sys.stderr.write("Retrieving ID for Channel: " + channel_name + "\n")

  YOUTUBE_API_SERVICE_NAME = "youtube"
  YOUTUBE_API_VERSION = "v3"

  # Build the Google API Client
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=apikey)

  # Get the Channel ID String from the Channel Name
  channelResponse = youtube.channels().list(
    part="id,snippet,contentDetails",
    forUsername=channel_name,
  ).execute()
  
  channels = channelResponse.get("items", [])
  if len(channels) != 1:
    sys.stderr.write("Didn't find exactly one channel ID: found " + str(len(channels)) + " channel Ids\n")
    sys.exit(1)
  channel = channels[0]

  channelIdString = channel['id']
  if (verbose): sys.stderr.write("Found Channel ID: " + channelIdString + "\n")

  return channelIdString


## Get the video list from a YouTube Channel, using the v3 API.
#
# @param apikey YouTube Developer API Key
# @param channel_id YouTube Channel ID to convert to RSS.
# @param verbose Enable Verbose Printing to STDERR.
# @param num_most_recent Retrieve only the num_most_recent uploads for the Channel (<= 0 disables)
# @return None on error / no videos found. Otherwise, return a list of dictionary objects as 
# [{'id', 'title', 'url', 'published', 'description'}]

def GetVideosV3(apikey, channel_id, verbose, num_most_recent):
  from apiclient.discovery import build
  from googleapiclient.errors import HttpError

  if (verbose): sys.stderr.write("Channel ID: " + channel_id + "\n")

  YOUTUBE_API_SERVICE_NAME = "youtube"
  YOUTUBE_API_VERSION = "v3"

  # Build the Google API Client
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=apikey)

  if (verbose): sys.stderr.write("Retrieving Channel ID: " + channel_id + "\n")

  ###
  # Get the Channel Object

  channelResponse = youtube.channels().list(
    part="id,snippet,contentDetails",
    id=channel_id,
  ).execute()
  
  channels = channelResponse.get("items", [])
  if len(channels) != 1:
    sys.stderr.write("Didn't find exactly one channel ID: found " + str(len(channels)) + " channel Ids\n")
    sys.exit(1)
  channel = channels[0]

  ### 
  # Get the Channel Upload List

  uploads_list_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

  playlist_request = youtube.playlistItems().list(
    playlistId=uploads_list_id,
    part="id,snippet,contentDetails",
    maxResults=50,
  )

  reportedNumVideos = 0
  videos = []


  while (playlist_request):
    retries = 5
    while (retries):
      try:
        playlist_response = playlist_request.execute()
        retries = 0
      except HttpError, err:
        retries = retries - 1
        if retries <= 0:
          raise
        if err.resp.status in [500, 503]:
          if (verbose): sys.stderr.write("Received API Error - Sleeping for retry\n\t" + repr(err) + "\n")
          time.sleep(10)
        else:
          raise

    if reportedNumVideos == 0:
      reportedNumVideos = playlist_response['pageInfo']['totalResults']

    for playlist_result in playlist_response.get("items", []):
      video = {}
      video['id'] = playlist_result['contentDetails']['videoId']
      video['title'] = playlist_result['snippet']['title']
      video['url'] = "http://www.youtube.com/watch?v=" + video['id']
      dateString = playlist_result['snippet']['publishedAt'][0:19] # 2013-05-18T01:43:21.000Z -> 2013-05-18T01:43:21
      video['published'] = datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S")
      video['description'] = playlist_result['snippet']['description']
      videos.append(video)

    # get next page of results
    playlist_request = youtube.playlistItems().list_next(previous_request=playlist_request , previous_response=playlist_response)

    # if limit the number of most recent... 
    if (num_most_recent > 0):
      if (len(videos) > num_most_recent):
        playlist_request = None


  ###
  # Get List of Videos based on Search
#  ytSearch = youtube.search()
#
#  searchRequest = ytSearch.list(
#    channelId=channelIdString,
#    part="id,snippet",
#    maxResults=50,
#    type='video'
#  )
#
#  reportedNumVideos = 0
#  videos = []
#
#  while (searchRequest):
#    searchResponse = searchRequest.execute()
#
#    if reportedNumVideos == 0:
#      reportedNumVideos = searchResponse['pageInfo']['totalResults']
#
#    for searchResult in searchResponse.get("items", []):
#      if searchResult["id"]["kind"] == "youtube#video":
#        video = {}
#        video['id'] = searchResult['id']['videoId']
#        video['title'] = searchResult['snippet']['title']
#        video['url'] = "http://www.youtube.com/watch?v=" + video['id']
#        dateString = searchResult['snippet']['publishedAt'][0:19] # 2013-05-18T01:43:21.000Z -> 2013-05-18T01:43:21
#        video['published'] = datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S")
#        video['description'] = searchResult['snippet']['description']
#        videos.append(video)
#      else:
#        sys.stderr.write("Unknown media type: " + searchResult["id"]["kind"] + "\n")
#
#    # get next page of results
#    searchRequest = youtube.search().list_next(previous_request=searchRequest , previous_response=searchResponse)

  videos = DeDuplicateVideos(videos, verbose)

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
  channelId = ""
  VERBOSE_MODE = 0
  num_most_recent = 0

  # Get Opts
  try:
    opts, args = getopt.getopt(argv, "hvk:c:i:r:", ["help", "verbose", "apikey=", "channel=", "channel_id=", "recent="]) 
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
    elif opt in ("-i", "--channel_id"):
      channelId = arg
    elif opt in ("-r", "--recent"):
      num_most_recent = int(arg)

  # Required Arguments
  if (apikey == ""):
    sys.stderr.write("Missing API Key\n")
    usage()
    sys.exit(1)

  if (channelId == ""):
    if (channelName == ""):
      sys.stderr.write("Missing Channel Id/Name\n")
      usage()
      sys.exit(1)
    else:
      channelId = GetChannelIdFromName(apikey, channelName, VERBOSE_MODE)

  # get Video list
  videos = GetVideosV3(apikey, channelId, VERBOSE_MODE, num_most_recent)

  if not videos:
    return 1

  # Sort Videos
  videos = sorted(videos, key=lambda video:video['published'], reverse=True)

  if (num_most_recent > 0):
    if (len(videos) > num_most_recent): 
      videos = videos[0:num_most_recent]

  if (VERBOSE_MODE): sys.stderr.write("Found " + str(len(videos)) + " Videos\n")

  # make RSS
  sys.exit( WriteRss(videos, channelName, VERBOSE_MODE) )


if __name__ == "__main__":
    main(sys.argv[1:])

