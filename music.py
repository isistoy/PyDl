import asyncio
import functools
import hashlib
import os
import datetime
from asyncio.queues import Queue
from concurrent.futures import ThreadPoolExecutor
import youtube_dl


ytdl_params = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': '%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': False,
    'no_warnings': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}


class QueueItem(object):
    def __init__(self, item_info: dict):
        self.item_info = item_info
        self.url = self.item_info.get('webpage_url')
        self.video_id = self.item_info.get('id', self.url)
        self.uploader = self.item_info.get('uploader', 'Unknown')
        self.title = self.item_info.get('title')
        self.duration = int(self.item_info.get('duration', 0))
        self.downloaded = False
        self.loop = asyncio.get_event_loop()
        self.threads = ThreadPoolExecutor()
        self.ytdl_params = ytdl_params
        self.ytdl = youtube_dl.YoutubeDL(self.ytdl_params)
        self.token = self.tokenize()
        self.location = None

    def tokenize(self):
        name = 'yt_' + self.video_id
        crypt = hashlib.new('md5')
        crypt.update(name.encode('utf-8'))
        final = crypt.hexdigest()
        return final

    async def download(self):
        if self.url:
            out_location = f'/media/sf_vmtransfer/' + self.ytdl_params['outtmpl']
            if not os.path.exists(out_location):
                self.ytdl.params.update({'outtmpl': out_location})
                task = functools.partial(self.ytdl.extract_info, self.url)
                await self.loop.run_in_executor(self.threads, task)
                self.downloaded = True
            self.location = out_location


class MusicCore(object):
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.threads = ThreadPoolExecutor()
        self.queues = {}
        self.currents = {}
        self.repeaters = []
        self.ytdl_params = ytdl_params
        self.ytdl = youtube_dl.YoutubeDL(self.ytdl_params)

    async def extract_info(self, url: str):
        task = functools.partial(self.ytdl.extract_info, url, False)
        information = await self.loop.run_in_executor(self.threads, task)
        return information

    def get_queue(self, guild_id=1):
        queue = self.queues.get(guild_id, Queue())
        self.queues.update({guild_id: queue})
        return queue

    async def queue(self, args: list):
        if args:
            lookup = ' '.join(args)
            if '/watch?' in lookup:
                lookup = lookup.split('&')[0]
                playlist_url = False
                print('💽 Processing URL...')
            elif '/playlist?' in lookup:
                playlist_url = True
                print('💽 Processing playlist. This might take a long time...')
            else:
                if lookup.startswith('http'):
                    playlist_url = True
                else:
                    playlist_url = False
                print('💽 Searching...')

            extracted_info = await self.extract_info(lookup)
            if extracted_info:
                if '_type' in extracted_info:
                    if extracted_info['_type'] == 'playlist':
                        if not playlist_url:
                            song_item = extracted_info['entries'][0]
                            playlist = False
                        else:
                            song_item = None
                            playlist = True
                    else:
                        song_item = extracted_info
                        playlist = False
                else:
                    song_item = extracted_info
                    playlist = False
                if playlist:
                    pl_title = extracted_info['title']
                    entries = extracted_info['entries']
                    for song_entry in entries:
                        if song_entry:
                            queue_item = QueueItem(song_entry)
                            queue_container = self.get_queue()
                            await queue_container.put(queue_item)
                    print(f'💽 Added {len(entries)} songs from {pl_title}.')
                else:
                    if song_item:
                        queue_item = QueueItem(song_item)
                        queue_container = self.get_queue()
                        await queue_container.put(queue_item)
                        duration = str(datetime.timedelta(seconds=int(song_item.get('duration', 0))))
                        print('✅ Added To Queue', song_item.get('title', "No Title"))
                        print(f'Duration: {duration}')
                    else:
                        print('🔍 Addition returned a null item.')
            else:
                print('🔍 No results.')
        # else:
        #     music_queue = music.get_queue()
        #     if not music_queue.empty():
        #         music_queue = music.listify_queue(music_queue)
        #         stats_desc = f'There are **{len(music_queue)}** songs in the queue.'
        #         if message.guild.id in cmd.bot.music.currents:
        #             curr = cmd.bot.music.currents[message.guild.id]
        #             stats_desc += f'\nCurrently playing: [{curr.title}]({curr.url})'
        #         list_desc_list = []
        #         boop_headers = ['#', 'Title', 'Requester', 'Duration']
        #         order_num = 0
        #         for item in music_queue[:5]:
        #             order_num += 1
        #             duration = str(datetime.timedelta(seconds=item.duration))
        #             title = item.title
        #             if ' - ' in title:
        #                 title = ' - '.join(title.split('-')[1:])
        #                 while title.startswith(' '):
        #                     title = title[1:]
        #             if len(title) > 20:
        #                 title = title[:20] + '...'
        #             req = item.requester.name
        #             if len(req) > 9:
        #                 req = req[:6] + '...'
        #             list_desc_list.append([order_num, title, req, duration])
        #         list_desc = boop(list_desc_list, boop_headers)
        #         list_title = f'List of {len(music_queue[:5])} Upcoming Queued Items'
        #         response = discord.Embed(color=0x3B88C3)
        #         response.set_author(name=message.guild.name, icon_url=message.guild.icon_url)
        #         response.add_field(name='Current Music Queue', value=stats_desc)
        #         response.add_field(name=list_title, value=f'```bat\n{list_desc}\n```')
        #     else:
        #         response = discord.Embed(color=0x3B88C3, title='🎵 The queue is empty.')
        #     await message.channel.send(embed=response)

    async def process_queue(self, guild_id=1):
        queue_container = self.get_queue(guild_id)
        if not queue_container.empty():
            while queue_container.qsize() > 0:
                q = await queue_container.get()
                await q.download()


    # @staticmethod
    # async def listify_queue(queue: asyncio.Queue):
    #     item_list = []
    #     while not queue.empty():
    #         item = await queue.get()
    #         item_list.append(item)
    #     for item in item_list:
    #         await queue.put(item)
    #     return item_list
