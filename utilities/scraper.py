from requests_html import HTMLSession
import re
import json
from pprint import pprint
import shutil
from pytube import YouTube
import ffmpeg
import os
# Currently only supports downloading the first video from a search query

class SongInfo():
    #region properties
    @property
    def title(self):
        return self._title
    
    @property
    def url(self):
        return self._url

    @property
    def cleaned_title(self):
        return self._cleaned_title
    #endregion

    def __init__(self, title, url):
        self._title = title
        self._url = f'https://www.youtube.com{url}'
        self._cleaned_title = title.replace(',', '').replace('.', '')
        

class YoutubeDownloader():
    def __init__(self):
        pass

    def download(self, query, output_path):
        #TODO: Add support for direct URL's
        parsed_query = '+'.join(query.split())
        url = f'https://www.youtube.com/results?search_query={parsed_query}'
        json_results = self.get_search_results(url)

        song = SongInfo(
            json_results['contents'][0]['videoRenderer']['title']['runs'][0]['text'],
            json_results['contents'][0]['videoRenderer']['navigationEndpoint']['commandMetadata']['webCommandMetadata']['url']
        )

        YouTube(song.url).streams.first().download(output_path=output_path)
        song_mp4 = f"{output_path}\\{song.cleaned_title}.mp4"
        song_mp3 = f"{output_path}\\{song.cleaned_title}.mp3"
        ffmpeg.input(song_mp4).output(song_mp3).run()
        if os.path.exists(song_mp4):
            os.remove(song_mp4)
        else:
            print("The file doesn't exist")

    def get_search_results(self, url):
        session = HTMLSession()
        res = session.get(url)
        search_results = res.html.find('script', containing='var ytInitialData', first=True)
        return self.parse_json(search_results)

    def parse_json(self, search_results):
        regex = r"\/\/ scraper_data_begin var ytInitialData = ([\S\s]*)\/\/ scraper_data_end"

        filter_json = re.search(regex, search_results.text)
        search_json = json.loads(filter_json.group(1)[:-2])
        song_list_json = search_json['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']
        return song_list_json


if __name__ == "__main__":
    # Testing
    yt = YoutubeDownloader()
    yt.download("First Time", os.getcwd())