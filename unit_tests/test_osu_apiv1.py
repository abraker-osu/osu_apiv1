import unittest

from .api_key import api_key
from osu_apiv1.osu_api import OsuApiv1, OsuApiv1Error



class TestOsuApiv1(unittest.TestCase):

    def test_fetch_replay_stream(self):
        # Test when replay is unavailable
        with self.assertRaises(OsuApiv1Error):
            data = OsuApiv1.fetch_replay_stream(beatmap_id=767046, user_name='abraker', gamemode=3, api_key=api_key)

        # Test when replay is available
        data = OsuApiv1.fetch_replay_stream(beatmap_id=2323855, user_name='abraker', gamemode=3, api_key=api_key)


    def test_fetch_beatmap_info(self):
        # Test when beatmap is unavailable
        data = OsuApiv1.fetch_beatmap_info(beatmap_id=0, api_key=api_key)
        self.assertEqual(len(data), 0)

        # Test when beatmap is available
        data = OsuApiv1.fetch_beatmap_info(beatmap_id=767046, api_key=api_key)
        self.assertEqual(len(data), 1)


    def test_fetch_score_info(self):
        # Test when score is unavailable
        data = OsuApiv1.fetch_score_info(beatmap_id=0, user_name='abraker', gamemode=3, mods=0, api_key=api_key)
        self.assertEqual(len(data), 0)

        # Test when score is available
        data = OsuApiv1.fetch_score_info(beatmap_id=767046, user_name='abraker', gamemode=3, mods=0, api_key=api_key)
        self.assertEqual(len(data), 1)


    def test_fetch_replay_file(self):
        # Test when replay is unavailable
        with self.assertRaises(OsuApiv1Error):
            data = OsuApiv1.fetch_replay_file(beatmap_id=767046, user_name='abraker', gamemode=3, api_key=api_key)

        # Test when replay is available
        data = OsuApiv1.fetch_replay_file(beatmap_id=2323855, user_name='abraker', gamemode=3, api_key=api_key)


    def test_fetch_replays_from_map(self):
        def progress_callback(progress, total, user_name):
            print(f'({progress}/{total}) Gettings replay for {user_name}')

        # Test invalid map
        data = OsuApiv1.fetch_replays_from_map(beatmap_id=0, gamemode=3, mods=0, api_key=api_key, progress_callback=progress_callback)
        self.assertEqual(len(data), 0)

        # Test valid map
        data = OsuApiv1.fetch_replays_from_map(beatmap_id=2323855, gamemode=3, mods=0, api_key=api_key, progress_callback=progress_callback)
        self.assertEqual(len(data), 50)
