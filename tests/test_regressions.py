"""Runnable regression cases for the two read-only checks and white-background helper.

Run: python3 -m unittest discover -s tests -v
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DIVERSE = ROOT/'scripts/check_diversity.py'
IMAGE = ROOT/'scripts/check_image.py'
WHITEN = ROOT/'scripts/normalize_white_background.py'


def run(*args):
    proc = subprocess.run([sys.executable, *map(str,args)],capture_output=True,text=True)
    try: data=json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise AssertionError(f'Not JSON output: {proc.stdout}, stderr={proc.stderr}')
    return proc.returncode, data


class SkillChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.char = dict(id='first',theme='postgirl',hair_style='bob',hair_color='brown',outfit_silhouette='dress',signature_prop='envelope',pose='standing',expression='smile',palette_id='warm')
        self.plan = self.folder/'plan.json'
        self.plan.write_text(json.dumps({'mode':'new_character','characters':[self.char]}))
        self.history = self.folder/'accepted.jsonl'

    def history_record(self, **fields):
        record={**self.char,'id':'second',**fields}
        self.history.write_text(json.dumps(record)+'\n')

    def test_unreviewed_history_is_skipped(self):
        self.history_record()
        code,data=run(DIVERSE,'--plan',self.plan,'--history',self.history)
        self.assertEqual(code,0)
        self.assertEqual(data['history_records_skipped'],1)
        self.assertEqual(data['history_records_used'],0)
        self.assertIsNone(data['diversity_checks_passed'])

    def test_accepted_history_is_checked(self):
        self.history_record(quality_status='passed')
        code,data=run(DIVERSE,'--plan',self.plan,'--history',self.history)
        self.assertEqual(code,1)
        self.assertEqual(data['collisions'][0]['scope'],'loaded_history')

    def test_contradictory_quality_is_skipped(self):
        self.history_record(quality_status='failed', visual_review={'status':'passed'})
        code,data=run(DIVERSE,'--plan',self.plan,'--history',self.history)
        self.assertEqual(code,0)
        self.assertEqual(data['history_records_skipped'],1)

    def test_missing_requested_history_is_error(self):
        code,data=run(DIVERSE,'--plan',self.plan,'--history',self.folder/'missing.jsonl')
        self.assertEqual(code,2)
        self.assertEqual(data['status'],'error')

    def test_edit_mode_skips_diversity(self):
        self.plan.write_text(json.dumps({'mode':'edit','characters':[self.char]}))
        code,data=run(DIVERSE,'--plan',self.plan,'--history',self.folder/'missing.jsonl')
        self.assertEqual(code,0)
        self.assertEqual(data['status'],'not_applicable')

    def test_near_white_is_not_exact_white(self):
        p=self.folder/'near-white.png'
        im=Image.new('RGB',(128,128),(253,254,255))
        for x in range(32,96):
            for y in range(32,96): im.putpixel((x,y),(190,100,70))
        im.save(p)
        code,data=run(IMAGE,p,'--require-exact-white-border')
        self.assertEqual(code,1)
        self.assertIn('border_not_exact_white',data['issues'])

    def test_safe_background_normalization(self):
        p=self.folder/'near-white.png'; out=self.folder/'white.png'
        im=Image.new('RGB',(128,128),(253,254,255))
        for x in range(32,96):
            for y in range(32,96): im.putpixel((x,y),(190,100,70))
        im.save(p)
        code,data=run(WHITEN,p,out)
        self.assertEqual(code,0,data)
        self.assertEqual(Image.open(out).getpixel((0,0)),(255,255,255))
        self.assertEqual(Image.open(out).getpixel((60,60)),(190,100,70))
        code,data=run(IMAGE,out,'--require-exact-white-border')
        self.assertEqual(code,0,data)

    def test_refuses_dark_screen_capture(self):
        p=self.folder/'dark-frame.png'; out=self.folder/'white.png'
        Image.new('RGB',(128,128),(20,20,20)).save(p)
        code,data=run(WHITEN,p,out)
        self.assertEqual(code,2)
        self.assertFalse(out.exists())

    def test_refuses_transparency(self):
        p=self.folder/'transparent.png'; out=self.folder/'white.png'
        im=Image.new('RGBA',(128,128),(254,254,254,255)); im.putpixel((0,0),(254,254,254,0));im.save(p)
        code,data=run(WHITEN,p,out)
        self.assertEqual(code,2)
        self.assertFalse(out.exists())


if __name__=='__main__':
    unittest.main()
