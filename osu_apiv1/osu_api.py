import base64
import requests
import datetime
import hashlib 
import struct
import json
import time
import os

from .rate_limited import rate_limited



class OsuApiv1Error(Exception):
    pass


class OsuApiv1():

    REPLAY_RATE_FETCHING_LIMIT = 10  # seconds

    '''
    Returns the LZMA stream containing the cursor and key data, not the full *.osr file
    '''
    @staticmethod
    @rate_limited(rate_limit=REPLAY_RATE_FETCHING_LIMIT)
    def fetch_replay_stream(beatmap_id, user_name, gamemode, api_key=''):
        param = []
        param.append(f'k={api_key}')
        param.append(f'm={gamemode}')
        param.append(f'b={beatmap_id}')
        param.append(f'u={user_name}')

        url = 'https://osu.ppy.sh/api/get_replay?'
        url += '&'.join(param)

        try: response = requests.get(url, timeout=5)
        except requests.exceptions.ReadTimeout as e:
            raise e from None

        try:
            base_64 = json.loads(response.content.decode('utf-8'))
            return base64.b64decode(base_64['content'])
        except KeyError:
            error = json.loads(response.content.decode('utf-8'))
            raise OsuApiv1Error(error['error']) from None

    
    @staticmethod
    @rate_limited(rate_limit=0.1)
    def fetch_beatmap_info(beatmap_id=None, map_md5=None, api_key=''):
        param = []
        param.append(f'k={api_key}')

        if beatmap_id != None: param.append(f'b={beatmap_id}')
        if map_md5 != None:    param.append(f'h={map_md5}')

        url = 'https://osu.ppy.sh/api/get_beatmaps?'
        url += '&'.join(param)

        try: response = requests.get(url, timeout=5)
        except requests.exceptions.ReadTimeout as e:
            raise e from None

        return json.loads(response.content.decode('utf-8'))


    @staticmethod
    @rate_limited(rate_limit=0.1)
    def fetch_score_info(beatmap_id, user_name=None, gamemode=None, mods=None, api_key=''):
        param = []
        param.append(f'k={api_key}')
        param.append(f'b={beatmap_id}')
        
        if user_name != None: param.append(f'u={user_name}')
        if gamemode  != None: param.append(f'm={gamemode}')
        if mods      != None: param.append(f'mods={mods}')

        url = 'https://osu.ppy.sh/api/get_scores?'
        url += '&'.join(param)

        try: response = requests.get(url, timeout=5)
        except requests.exceptions.ReadTimeout as e:
            raise e from None

        return json.loads(response.content.decode('utf-8'))


    # Thanks https://github.com/Xferno2/CSharpOsu/blob/master/CSharpOsu/CSharpOsu.cs
    @staticmethod
    def fetch_replay_file(beatmap_id, user_name, gamemode, mods=None, api_key=''):
        replay_data  = OsuApiv1.fetch_replay_stream(beatmap_id=beatmap_id, user_name=user_name, gamemode=gamemode, api_key=api_key)
        beatmap_info = OsuApiv1.fetch_beatmap_info(beatmap_id=beatmap_id, api_key=api_key)[0]
        score_info   = OsuApiv1.fetch_score_info(beatmap_id=beatmap_id, user_name=user_name, gamemode=gamemode, mods=mods, api_key=api_key)[0]

        version     = 0
        rank        = score_info['rank']
        count_300   = score_info['count300']
        count_100   = score_info['count100']
        count_50    = score_info['count50']
        count_geki  = score_info['countgeki']
        count_katsu = score_info['countkatu']
        count_miss  = score_info['countmiss']
        score       = score_info['score']
        max_combo   = score_info['maxcombo']
        perfect     = score_info['perfect']
        mods        = score_info['enabled_mods']
        lifebar_hp  = ''
        score_date  = score_info['date']
        score_id    = score_info['score_id']

        beatmap_md5 = beatmap_info['file_md5']
        replay_hash = hashlib.md5(str(max_combo + 'osu' + user_name + beatmap_md5 + score + rank).encode('utf-8')).hexdigest()

        data =  struct.pack('<bi', int(gamemode), int(version))
        data += struct.pack(f'<x{len(beatmap_md5)}sx', str(beatmap_md5).encode('utf-8'))
        data += struct.pack(f'<x{len(user_name)}sx', str(user_name).encode('utf-8'))
        data += struct.pack(f'<x{len(replay_hash)}sx', str(replay_hash).encode('utf-8'))
        data += struct.pack('<hhhhhhih?i',
            int(count_300), int(count_100), int(count_50), int(count_geki), int(count_katsu), int(count_miss),
            int(score), int(max_combo), int(perfect), int(mods))
        data += struct.pack(f'<x{len(lifebar_hp)}sx', str(lifebar_hp).encode('utf-8'))

        score_date, score_time = score_date.split(' ')
        score_year, score_month, score_day = score_date.split('-')
        score_hour, score_min, score_sec   = score_time.split(':')
        timestamp = datetime.datetime.timestamp(datetime.datetime(int(score_year), month=int(score_month), day=int(score_day), hour=int(score_hour), minute=int(score_min), second=int(score_sec)))
        
        data += struct.pack('<qi', int(timestamp), int(len(replay_data)))
        data += replay_data
        data += struct.pack('<q', int(score_id))

        return data


    @staticmethod
    def fetch_replays_from_map(beatmap_id, gamemode, mods, api_key='', progress_callback=None):
        score_info = OsuApiv1.fetch_score_info(beatmap_id=beatmap_id, gamemode=gamemode, mods=mods, api_key=api_key)
        replays = []
        error = False

        for i in range(len(score_info)):
            score = score_info[i]
            if progress_callback != None:
                progress_callback(progress=i, total=len(score_info), user_name=score['username'])

            replays.append(OsuApiv1.fetch_replay_file(beatmap_id=beatmap_id, user_name=score['username'], gamemode=gamemode, mods=mods, api_key=api_key))

            # TODO: Handle request failing
            #try: 
            #    replays.append(OsuApiv1.fetch_replay_file(score['username'], beatmap_id, gamemode, mods, api_key=api_key))
            #    error = False
            #except urllib.error.HTTPError:
            #    if error: break
            #    i -= 1  # Try again
            #    error = True

        return replays