"""Run with python test_system.py. Uses isolated temporary storage and ports."""
import base64
from contextlib import contextmanager
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw
from drum_omr import DrumOMR
from score_grid import compile_grid
from server import StudioHTTPRequestHandler, ThreadingHTTPServer, ROOT


class QuietHandler(StudioHTTPRequestHandler):
    def log_message(self, *_): pass


@contextmanager
def running_server(directory):
    server = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
    server.data_dir = Path(directory)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try: yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def request(url, data=None, headers=None):
    req = urllib.request.Request(url, None if data is None else json.dumps(data).encode(),
                                 {'Content-Type': 'application/json', **(headers or {})})
    try: response = urllib.request.urlopen(req, timeout=20)
    except urllib.error.HTTPError as e: response = e
    with response:
        body = response.read()
        return response.status, json.loads(body) if 'application/json' in response.headers.get('Content-Type', '') else body


def image_bytes(image):
    out = io.BytesIO()
    image.save(out, format='PNG')
    return out.getvalue()


class DrumStudioTests(unittest.TestCase):
    def test_rock_onsets_and_instruments(self):
        r = DrumOMR().process_image((ROOT/'assets/sample_images/rock_beat_sample.png').read_bytes())
        self.assertEqual(r['measuresCount'], 2)
        self.assertEqual(r['totalNotes'], 25)
        expected = [{'hihat','kick'},{'hihat'},{'hihat','snare'},{'hihat'},
                    {'hihat','kick'},{'hihat'},{'hihat','snare'},{'hihat'}]
        self.assertEqual([set(s['instruments']) for s in r['grid'][0]['slots']], expected)
        self.assertEqual(set(r['grid'][1]['slots'][5]['instruments']), {'hihat','kick'})
        self.assertEqual(r['bpmSource'], 'default')
        self.assertEqual(r['config']['bpm'], 120)

    def test_tom_fill_has_no_extra_hits(self):
        r = DrumOMR().process_image((ROOT/'assets/sample_images/tom_fill_sample.png').read_bytes())
        expected = ['snare','snare','tom_high','tom_high','tom_mid','tom_mid','tom_low','tom_low']
        self.assertEqual([s['instruments'] for s in r['grid'][1]['slots']], [[i] for i in expected])
        self.assertEqual(r['totalNotes'],20)

    def test_rotation_and_multiple_systems(self):
        rock = Image.open(ROOT/'assets/sample_images/rock_beat_sample.png').convert('RGB')
        fill = Image.open(ROOT/'assets/sample_images/tom_fill_sample.png').convert('RGB')
        page = Image.new('RGB',(900,550),'white')
        page.paste(rock,(0,0)); page.paste(fill,(0,290))
        for angle in (0,-5,5):
            with self.subTest(angle=angle):
                r = DrumOMR().process_image(image_bytes(page.rotate(angle,expand=True,fillcolor='white')))
                self.assertEqual(r['systemsCount'],2)
                self.assertEqual(r['measuresCount'],4)
                self.assertEqual(r['totalNotes'],45)

    def test_blank_and_nonimage_rejected(self):
        for data in (image_bytes(Image.new('RGB',(900,260),'white')),b'not an image'):
            with self.assertRaises(ValueError): DrumOMR().process_image(data)

    def test_empty_measure_is_not_copied(self):
        image = Image.open(ROOT/'assets/sample_images/rock_beat_sample.png').convert('RGB')
        draw = ImageDraw.Draw(image)
        draw.rectangle((485,70,830,230),fill='white')
        for y in (120,136,152,168,184): draw.line((485,y,830,y),fill='#222222',width=2)
        r = DrumOMR().process_image(image_bytes(image))
        self.assertTrue(all(not s['instruments'] for s in r['grid'][1]['slots']))
        self.assertIn(2,r['reviewMeasures'])

    def test_meters_subdivisions_and_xml_midi_mapping(self):
        for meter,sub in [('4/4',8),('3/4',12),('6/8',8),('9/8',16),('12/8',32),('4/4',24)]:
            n,d=map(int,meter.split('/')); slots=n*sub//d
            grid=[{'measure':1,'slots':[{'instruments':['kick','snare','hihat'] if i==0 else []} for i in range(slots)]}]
            result=compile_grid(grid,{'meter':meter,'subdivision':sub,'bpm':87,'title':'A & B <Test>'})
            root=ET.fromstring(result['musicXml'])
            duration=sum(int(note.findtext('duration')) for note in root.findall('./part/measure/note') if note.find('chord') is None)
            self.assertEqual(duration,24*4*n//d)
            self.assertEqual(root.findtext('./work/work-title'),'A & B <Test>')
            self.assertEqual(root.findtext('.//midi-instrument[@id="P1-I42"]/midi-unpitched'),'43')
            self.assertEqual(len(root.findall('.//time-modification')),slots+2 if sub in (12,24) else 0)

    def test_http_assets_validation_and_persistence_after_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            with running_server(tmp) as url:
                for resource in ['/', '/js/app.js', '/assets/alphatab/alphaTab.min.js', '/assets/soundfont/sonivox.sf2', '/assets/alphatab/font/Bravura.woff2']:
                    status,data=request(url+resource)
                    self.assertEqual(status,200); self.assertTrue(data)
                data=base64.b64encode((ROOT/'assets/sample_images/rock_beat_sample.png').read_bytes()).decode()
                status,scan=request(url+'/api/parse-image',{'image':data,'config':{'bpm':87,'meter':'4/4','subdivision':8}})
                self.assertEqual(status,200); self.assertEqual(scan['config']['bpm'],87)
                # Edit a detected note, compile, save, update and retrieve after a new server starts.
                scan['grid'][0]['slots'][1]['instruments'].append('crash')
                status,compiled=request(url+'/api/compile-grid',{'grid':scan['grid'],'config':scan['config']})
                self.assertEqual(status,200); self.assertEqual(compiled['totalNotes'],26)
                payload={'title':'Mi práctica','filename':'practica.musicxml','data':base64.b64encode(compiled['musicXml'].encode()).decode(),
                         'grid':compiled['grid'],'config':compiled['config'],'settings':{'bpm':60}}
                status,saved=request(url+'/api/scores',payload)
                self.assertEqual(status,200)
                payload['id']=saved['id']; payload['title']='Mi práctica actualizada'
                self.assertEqual(request(url+'/api/scores',payload)[0],200)
                self.assertEqual(len(request(url+'/api/scores')[1]['scores']),1)
                self.assertEqual(request(url+'/api/parse-image',{'image':'bad%'})[0],400)
                self.assertEqual(request(url+'/api/compile-grid',{'grid':[]})[0],400)
                self.assertEqual(request(url+'/api/scores',payload,{'Origin':'https://example.invalid'})[0],403)
                self.assertEqual(request(url+'/data/scores/'+saved['id']+'.json')[0],404)
            with running_server(tmp) as url:
                status,loaded=request(url+'/api/scores/'+saved['id'])
                self.assertEqual(status,200)
                self.assertEqual(loaded['title'],'Mi práctica actualizada')
                self.assertEqual(loaded['settings']['bpm'],60)
                self.assertIn('crash',loaded['grid'][0]['slots'][1]['instruments'])
                self.assertEqual(base64.b64decode(loaded['data']).decode(),compiled['musicXml'])


if __name__ == '__main__': unittest.main(verbosity=2)
