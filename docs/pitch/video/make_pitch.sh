#!/bin/zsh
# Rebuilds every pitch asset from the current code: fresh demo data in a scratch database (never db.sqlite3),
# the demo video (record + compose), the slide 1 picture, the deck (PNG, PDF, PPTX with the video and the notes).
# Needs: Google Chrome, ffmpeg (brew install ffmpeg), node + `npm install` in docs/pitch, uv.
# Usage, from the repository root:   docs/pitch/video/make_pitch.sh 401     (401 = test count shown on the slides)
set -e
REPO=${0:A:h:h:h:h}
WORK=$REPO/docs/pitch/.build        # git-ignored: frames, overlays, scratch database, server log
TESTS=${1:?usage: make_pitch.sh TEST_COUNT}
mkdir -p $WORK
cd $REPO && source .venv/bin/activate
export DATABASE_URL="sqlite:///$WORK/pitch.sqlite3" DEMO_BANNER=0 DEBUG=1
PID=$(lsof -ti tcp:8010 || true); [ -n "$PID" ] && kill $PID && sleep 1
python manage.py migrate -v 0
python manage.py seed_demo --reset | head -1
(python manage.py runserver 127.0.0.1:8010 --noreload > $WORK/server.log 2>&1 &)
sleep 3
cd $REPO/docs/pitch/video
BASE=http://127.0.0.1:8010 node record_demo.mjs $WORK/take
node video_assets.mjs $WORK/assets captions.json
python3 compose.py $WORK/take $WORK/assets $REPO/docs/pitch/demo.mp4
ffmpeg -v error -y -ss 20 -i $REPO/docs/pitch/demo.mp4 -frames:v 1 $REPO/docs/pitch/demo-poster.png
python $REPO/manage.py demo_reset | tail -1
BASE=http://127.0.0.1:8010 node shot_slide1.mjs $REPO/docs/pitch/img/home.png album
cd $REPO/docs/pitch && node build_deck.mjs --tests $TESTS && uv run --no-project --with python-pptx python build_pptx.py
PID=$(lsof -ti tcp:8010 || true); [ -n "$PID" ] && kill $PID
echo "Pitch rebuilt: docs/pitch/demo.mp4, Club-des-Affaires-pitch.pptx, Club-des-Affaires-pitch.pdf"
