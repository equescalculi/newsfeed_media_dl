# newsfeed_media_dl

A Python script that parses a list of news feeds, checks for new entries and
downloads the corresponding media files via wget, aria2c or youtube-dl

## Dependencies

 * Python (tested with versions 2.7.13 and 3.6.0)
 * feedparser (tested with version 5.2.1)
 * At least one of:
   * aria2c
   * wget
   * youtube-dl

## Configuration

The script relies on a JSON configuration file with the following keys:

 * directory: path to the download directory
 * maxage: maximum age in days for entries to be considered for download
 * feeds: list of the RSS feeds with entries with the following keys:
   * url: URL of the RSS feed
   * regex: only entries matching this regular expression are considered
   * downloader: download command

See settings.json.example for an example configuration.

## License

This project is licensed under the MIT License, see LICENSE for details.
