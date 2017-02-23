#!/usr/bin/env python
"""Download media files from news feeds"""
# Licensed under the MIT License, see LICENSE for details

from datetime import datetime, timedelta
import json
import logging
import os
import re
from subprocess import CalledProcessError, check_call
import sys
import time
import feedparser


SUPPORTED_DOWNLOADERS = ["aria2c", "wget", "youtube-dl"]


class InvalidInputDataException(Exception):
    """Exception to raise in case of an invalid settings file"""

    pass


def get_entry_datetime(entry):
    """
    Convert the published attribute or, if the former is lacking, the
    updated attribute of a feed entry to a datetime object

    Parameters
    ----------
    entry : feedparser.FeedParserDict
        a feed entry

    Returns
    -------
    etime : datetime.datetime
        timestamp of the entry
    """

    try:
        etime = datetime.fromtimestamp(time.mktime(entry.published_parsed))
    except AttributeError:
        etime = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
    return etime


def extract_items(url, regex, newer_than):
    """
    Return all entries of url that have a title matching regex and are
    newer than newer_than

    Parameters
    ----------
    url : str
        feed URL
    regex : str
        regular expression that an entry's title has to match for the
        entry in order to be downloaded
    newer_than : datetime.datetime
        entries have to be newer than this time in order to be
        downloaded

    Returns
    -------
    vurls : list
        list of the strings of the extracted URLs
    newest : datetime.datetime
        time of the newest feed entry
    """

    content = feedparser.parse(url)
    vurls = [e.link for e in content.entries if
             get_entry_datetime(e) > newer_than and re.match(regex, e.title)]
    newest = max(get_entry_datetime(e) for e in content.entries)

    return (vurls, newest)


def download(vurl, downloader):
    """
    Download urls via downloader

    Parameters
    ----------
    vurl : str
        URL to be passed to the downloader
    downloader : str
        command to invoke the downloader
    """

    try:
        check_call([downloader, vurl])
    except CalledProcessError:
        logging.error("Download failed: %s", vurl)


def download_new(settings_file):
    """
    Check all feeds in settings_file for new entries and download them

    Parameters
    ----------
    settings_file : str
        path to the settings file, for its format see README.md
    """

    logging.debug("Starting download_new... ")

    json_file = open(settings_file, "r")
    settings = json_file.read()
    json_file.close()
    settings = json.loads(settings)

    # Parse settings file
    try:
        directory = settings["directory"]
    except KeyError:
        raise InvalidInputDataException("No directory given in settings file")
    try:
        os.chdir(directory)
    except OSError:
        raise InvalidInputDataException(
            "Directory given in settings file does not exist")
    try:
        maxage = int(settings["maxage"])
        start_time = datetime.now().replace(hour=0, minute=0, second=0,
                                            microsecond=0) - timedelta(
                                                days=maxage)
    except KeyError:
        raise InvalidInputDataException(
            "No time frame given in settings file")
    except TypeError:
        raise InvalidInputDataException(
            "Invalid time frame given in settings file")
    try:
        feeds = settings["feeds"]
    except KeyError:
        raise InvalidInputDataException("No feeds given in settings file")

    # Check for .newsfeed_media_dl.json containing the latest timestamps
    # from the previous run
    try:
        json_file = open(".newsfeed_media_dl.json", "r")
        last_run = json_file.read()
        json_file.close()
    except IOError:
        last_run = "{}"
    try:
        last_run = json.loads(last_run)
    except json.JSONDecodeError:
        logging.warning(
            "Ignoring .newsfeed_media_dl.json due to parsing error")
        last_run = {}

    # Check each feed for downloadable content and download it
    for feed in feeds:
        try:
            url = feed["url"]
            regex = re.compile(feed["regex"])
            downloader = feed["downloader"]
        except (KeyError, TypeError):
            raise InvalidInputDataException("Invalid feeds list")
        logging.debug("Parsing feed: %s", url)
        if downloader not in SUPPORTED_DOWNLOADERS:
            raise InvalidInputDataException(
                "Unsupported downloader: %s" % downloader)
        try:
            newer_than = max(start_time,
                             datetime.strptime(last_run[url],
                                               "%Y-%m-%dT%H:%M:%S"))
        except KeyError:
            newer_than = start_time

        # Extract all new media links from the feed and determine the
        # timestamp of the newest feed entry
        vurls, newest = extract_items(url, regex, newer_than)

        # Download all new media files found in the feed
        for vurl in vurls:
            logging.debug("Found url: %s", vurl)
            download(vurl, downloader)

        # Write the timestamp of the newest feed entry to
        # .newsfeed_media_dl.json
        last_run[url] = newest.isoformat()
        json_file = open(".newsfeed_media_dl.json", "w")
        json_file.write(json.dumps(last_run))
        json_file.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    if len(sys.argv) < 2:
        logging.error("No settings file specified")
    else:
        try:
            download_new(sys.argv[1])
        except InvalidInputDataException as err:
            logging.error("Invalid input: %s", err)
