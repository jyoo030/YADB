import json
import re
from dataclasses import dataclass

import aiohttp
import cchardet # this and lxml are used to increase parsing speed of BeautifulSoup
import lxml
from bs4 import BeautifulSoup
from pytube import YouTube


@dataclass
class Song:
    title: str
    video_url: str
    length: str
    thumbnail: str
    requester: str = None
    avatar_url: str = None

    @property
    def audio_url(self):
        return YouTube(self.video_url).streams.filter(only_audio=True, file_extension='mp4').first().url


YT_DATA_REGEX = re.compile('(var ytInitialData|window["ytInitialData"])\s*=\s*(.*);')
async def search_youtube(query, max_results = 10, max_attempts = 3):
    """
    Searches youtube through the results url and search_query parameter. In one of the scripts tags in the html, youtube sets
    a variable called 'ytInitialData' to an object with all the initial youtube results for the query. We find this line of code with
    a regex search. Then we take the object portion and parse it into a json object that we then lookup the video search results from.
    From the list of video search results we get the video title and the video's url in the form of '/watch?v=dQw4w9WgXcQ'.
    """

    formatted_query = '+'.join(query.strip().split())
    search_url = f'https://www.youtube.com/results?search_query={formatted_query}'
    async with aiohttp.ClientSession() as client:
        for _ in range(max_attempts):
            async with client.get(search_url) as response:
                soup = BeautifulSoup(await response.content.read(), 'lxml')

            script = soup.find("script", string=YT_DATA_REGEX)
            if not script:
                continue
            ytdata = json.loads(re.search(YT_DATA_REGEX, script.string).group(2))

            search_content = ytdata['contents']['twoColumnSearchResultsRenderer']['primaryContents'].get('sectionListRenderer', None)
            if not search_content:
                continue
            search_results = search_content['contents'][0]['itemSectionRenderer']['contents']
            video_results = [result for result in search_results if 'videoRenderer' in result.keys()][:max_results]

            song_titles = [result['videoRenderer']['title']['runs'][0]['text'] for result in video_results]
            song_urls = [result['videoRenderer']['navigationEndpoint']['commandMetadata']['webCommandMetadata']['url'] for result in video_results]
            LIVE_LENGTH_DATA = {'simpleText': 'LIVE'}
            #FIXME: When attempting to stream LIVE videos the bot exits after a few seconds
            song_lengths = [result['videoRenderer'].get('lengthText', LIVE_LENGTH_DATA)['simpleText'] for result in video_results]
            song_thumbnails = [result['videoRenderer']['thumbnail']['thumbnails'][0]["url"] for result in video_results]
            return [Song(title, url, length, thumbnail) for title, url, length, thumbnail in zip(song_titles, song_urls, song_lengths, song_thumbnails)]

    return []
