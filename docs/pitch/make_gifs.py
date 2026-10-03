"""Fresh, isolated demo -> real UI captures -> slow looping GIFs -> optional deck exports.
Run from repo root: .venv/bin/python docs/pitch/make_gifs.py [--assets-only | --reuse-captures]
No SMTP, no dependency changes, no access to db.sqlite3. Requires Chrome, ffmpeg, Node, uv.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
WORK = HERE / '.build'
CAPTURES = WORK / 'gif-captures'
PYTHON = ROOT / '.venv/bin/python'
parser = argparse.ArgumentParser()
parser.add_argument('--assets-only', action='store_true')
parser.add_argument('--reuse-captures', action='store_true')
args = parser.parse_args()
WORK.mkdir(exist_ok=True)
env = dict(os.environ, DEBUG='1', DATABASE_URL=f'sqlite:///{WORK}/gifs.sqlite3', DEMO_BANNER='0', NOTIFICATIONS_ENABLED='0', BASE='http://127.0.0.1:8010')
def run(argv, cwd=ROOT):
    subprocess.run([str(x) for x in argv], cwd=cwd, env=env, check=True)

if not args.reuse_captures:
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',8010)) == 0:
            raise SystemExit('Port 8010 already in use; refusing to stop an existing server.')
    run([PYTHON,'manage.py','migrate','--verbosity','0'])
    run([PYTHON,'manage.py','seed_demo','--reset'])
    with (WORK/'gif-server.log').open('w') as log:
        server = subprocess.Popen([str(PYTHON),'manage.py','runserver','127.0.0.1:8010','--noreload'],cwd=ROOT,env=env,stdout=log,stderr=log)
        try:
            for _ in range(60):
                if server.poll() is not None:
                    raise RuntimeError('Capture server stopped; see gif-server.log')
                try:
                    with urlopen(env['BASE'],timeout=1) as response:
                        if response.status == 200: break
                except OSError: time.sleep(.25)
            else: raise RuntimeError('Capture server did not start')
            run(['node','capture_gifs.mjs',CAPTURES],cwd=HERE)
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill(); server.wait()

source = json.loads((CAPTURES/'manifest.json').read_text())
summary = {}
for name, frames in source['scenes'].items():
    lines = ['ffconcat version 1.0']
    for frame in frames:
        lines += [f"file '{frame['file']}'",f"duration {frame['duration']}"]
    lines += [f"file '{frames[-1]['file']}'"]
    listing = CAPTURES/name/'list.ffconcat'
    listing.write_text('\n'.join(lines)+'\n')
    gif = HERE/'gifs'/f'{name}.gif'
    run(['ffmpeg','-v','error','-y','-safe','0','-f','concat','-i',listing,
         '-vf','fps=8,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle',
         '-t',str(sum(f['duration'] for f in frames)),'-loop','0',gif])
    # PDF images deliberately show the key proof, independently of GIF playback position.
    poster_index = {'web':2,'event':4,'referral':0,'admin':0}[name]
    (HERE/'gifs'/f'{name}.png').write_bytes((CAPTURES/name/frames[poster_index]['file']).read_bytes())
    summary[name] = {'gif':f'gifs/{name}.gif','poster':f'gifs/{name}.png',
                     'planned_duration':sum(f['duration'] for f in frames),'bytes':gif.stat().st_size,
                     'states':[{k:v for k,v in f.items() if k != 'url'} for f in frames]}
(HERE/'gifs/manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
print('GIFs:',json.dumps({n:round(v['bytes']/1048576,2) for n,v in summary.items()}),'MiB')
if not args.assets_only:
    run(['node','build_deck.mjs','--tests','401'],cwd=HERE)
    env['UV_CACHE_DIR'] = '/tmp/club-pitch-uv'
    run(['uv','run','--no-project','--with','python-pptx','python','build_pptx.py'],cwd=HERE)
