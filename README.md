YtChannelRss
============

YtChannelRss downloads a list of videos from a YouTube channel, and creates an RSS feed containing all videos in that feed. This XML file will contain all videos in the channel, in contrast to many feeds that provide only the most recent items. 

    Usage: YtChannelRss.py [ -h ] [ -v ] [ --v2 ] -k APIKey -c ChannelName
    -h, --help      Show this usage message and exit.
    -v, --verbose   Verbose Output to StdErr
    -k, --apikey    YouTube API Key
    -c, --channel   YouTube Channel / Username
    --v2            Use the YouTube v2 API (default is v3)


The XML document is output to STDOUT. Errors and Verbose logging are sent to STDERR. Typical usage may be:

    python YtChannelRss.py -k "Google API Key" -c RoosterTeeth > /path/to/webfiles/RoosterTeeth.xml

Note that this completely rebuilds the RSS Feed on every run, downloading the entire video list - it is not incremental. When placing this in a cron, keep in mind the available quota on your API Key if building from large channels.

### Required Modules

This script requires: 

* Google APIs Client Library for Python and a Google API Key
** For using v3 - (https://developers.google.com/api-client-library/python/start/installation)
** For using v2 - (http://code.google.com/p/gdata-python-client/downloads/list)
* PyRSS2Gen (https://pypi.python.org/pypi/PyRSS2Gen/1.1)

### Notes and Known Issues

On channels with a large number of videos (in my case, RoosterTeeth), the v3 
API does not return a complete list of videos. For example, the v3 function 
reports "WARNING: Search Result Reported 4595 but only retrieved 983" (533 
after adding the De-Duplication). Of these, many were duplicates. The v2 API 
seems much closer to this, returning 4461 videos at this time. As far as I 
can tell, this is an issue with the v3 API. Hence the option to use the v2 
API that I have added. 

Also note, my implementation of the v2 API is messy at best, so I invite 
anyone familiar with this API to clean this up a bit. If not needed, I would 
recommend avoiding using th v2 API and sticking with the v3 API implementation.

### License

The MIT License (MIT)

Copyright (c) 2013 tonyborries

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

