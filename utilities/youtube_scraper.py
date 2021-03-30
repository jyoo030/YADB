import asyncio
import io
import json
import re
from dataclasses import dataclass
from pathlib import Path

import aiohttp
import pytube
from bs4 import BeautifulSoup


@dataclass
class Song:
    title: str
    video_url: str
    filename: str = f"{video_url.split('='[1])}.mp4"


# Every request needs to specify the amount of data we want, by default it is 9MB of data per request
DEFAULT_REQUEST_RANGE = 9437184
async def download_youtube_song(song, output_dir, request_range = DEFAULT_REQUEST_RANGE):
    audio_stream = YouTube(song.url).streams.filter(only_audio=True, file_extension='mp4').first()
    if audio_stream is None:
        return None

    output_path = Path(output_dir) / song.url.split('=')[1]
    if not output_path.exists():
        return output_path

    downloaded = 0
    with output_path.open('wb') as audio_file:
        async with aiohttp.ClientSession() as client:
            while downloaded < audio_stream.filesize:
                async with client.get(url, headers={"Range": f"bytes={downloaded}-{downloaded + request_range}"}) as response:
                    content = await response.content.read()
                    audio_file.write(content)
                    downloaded += len(content)
    return output_path


YT_DATA_REGEX = re.compile('(var ytInitialData|window["ytInitialData"])\s*=\s*(.*);')
async def search_youtube(query, max_results = 10):
    """
    Searches youtube through the results url and search_query parameter. In one of the scripts tags in the html, youtube sets
    a variable called 'ytInitialData' to an object with all the initial youtube results for the query. We find this line of code with
    a regex search. Then we take the object portion and parse it into a json object that we then lookup the video search results from.
    From the list of video search results we get the video title and the video's url in the form of '/watch?v=dQw4w9WgXcQ'.
    """

    formatted_query = '+'.join(query.strip().split())
    async with aiohttp.ClientSession() as client:
        async with client.get(f'https://www.youtube.com/results?search_query={formatted_query}') as response:
            soup = BeautifulSoup(await response.content.read(), "html.parser")

    script = soup.find("script", string=YT_DATA_REGEX)
    ytdata = json.loads(re.search(YT_DATA_REGEX, script.string).group(2))

    search_results = ytdata['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
    video_results = [result for result in search_results if 'videoRenderer' in result.keys()][:max_results]

    song_titles = [result['videoRenderer']['title']['runs'][0]['text'] for result in video_results]
    song_urls = [result['videoRenderer']['navigationEndpoint']['commandMetadata']['webCommandMetadata']['url'] for result in video_results]
    return [Song(title, url) for title, url in zip(song_titles, song_urls)]
