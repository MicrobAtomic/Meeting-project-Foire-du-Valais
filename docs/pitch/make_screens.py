"""Fresh, isolated demo -> static UI screenshots -> optional deck exports.
Run from repo root: .venv/bin/python docs/pitch/make_screens.py [--assets-only | --reuse-captures]
No SMTP, no dependency changes, no access to db.sqlite3. Requires Chrome, Node, uv.
"""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
WORK = HERE / '.build'
CAPTURES = HERE / 'screens'
PYTHON = ROOT / '.venv/bin/python'
parser = argparse.ArgumentParser()
parser.add_argument('--assets-only', action='store_true')
parser.add_argument('--reuse-captures', action='store_true')
parser.add_argument('--only-intros', action='store_true', help='Refresh only the introductions screenshot; requires --assets-only.')
parser.add_argument('--only-referral', action='store_true', help='Refresh only referral screenshots; requires --assets-only.')
args = parser.parse_args()
if (args.only_intros or args.only_referral) and (not args.assets_only or args.reuse_captures):
    parser.error('Partial capture requires --assets-only and cannot use --reuse-captures')
if args.only_intros and args.only_referral:
    parser.error('Choose one partial capture mode')
WORK.mkdir(exist_ok=True)
env = dict(os.environ, DEBUG='1', DATABASE_URL=f'sqlite:///{WORK}/screens.sqlite3', DEMO_BANNER='0', NOTIFICATIONS_ENABLED='0', BASE='http://127.0.0.1:8010')
def run(argv, cwd=ROOT):
    subprocess.run([str(x) for x in argv], cwd=cwd, env=env, check=True)

if not args.reuse_captures:
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',8010)) == 0:
            raise SystemExit('Port 8010 already in use; refusing to stop an existing server.')
    run([PYTHON,'manage.py','migrate','--verbosity','0'])
    run([PYTHON,'manage.py','seed_demo','--reset'])
    with (WORK/'screens-server.log').open('w') as log:
        server = subprocess.Popen([str(PYTHON),'manage.py','runserver','127.0.0.1:8010','--noreload'],cwd=ROOT,env=env,stdout=log,stderr=log)
        try:
            for _ in range(60):
                if server.poll() is not None:
                    raise RuntimeError('Capture server stopped; see screens-server.log')
                try:
                    with urlopen(env['BASE'],timeout=1) as response:
                        if response.status == 200: break
                except OSError: time.sleep(.25)
            else: raise RuntimeError('Capture server did not start')
            capture_args=['--only-intros'] if args.only_intros else ['--only-referral'] if args.only_referral else []
            run(['node','capture_screens.mjs',CAPTURES,*capture_args],cwd=HERE)
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill(); server.wait()

if not args.assets_only:
    run(['node','build_deck.mjs','--tests','402'],cwd=HERE)
    env['UV_CACHE_DIR'] = '/tmp/club-pitch-uv'
    run(['uv','run','--no-project','--with','python-pptx','python','build_pptx.py'],cwd=HERE)
