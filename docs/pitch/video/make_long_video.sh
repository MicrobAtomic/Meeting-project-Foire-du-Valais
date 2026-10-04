#!/bin/zsh
# The long demo video (about 3 to 4 minutes, English, synthetic voice-over): a prospect requests an invitation, the team
# accepts it, Camille lives her evening, the team prepares the dinner. Fresh demo data in a scratch database.
# Usage, from the repository root: docs/pitch/video/make_long_video.sh
set -e
REPO=${0:A:h:h:h:h}
WORK=$REPO/docs/pitch/.build/long
mkdir -p $WORK
cd $REPO && source .venv/bin/activate
export DATABASE_URL="sqlite:///$WORK/long.sqlite3" DEMO_BANNER=0 DEBUG=1
PID=$(lsof -ti tcp:8010 || true); [ -n "$PID" ] && kill $PID && sleep 1
python manage.py migrate -v 0
python manage.py seed_demo --reset | head -1
(python manage.py runserver 127.0.0.1:8010 --noreload > $WORK/server.log 2>&1 &)
sleep 3
V=$REPO/docs/pitch/video
python3 $V/long_tts.py $WORK
cd $V
BASE=http://127.0.0.1:8010 node record_long.mjs $WORK/take $WORK/timing.json
node long_assets.mjs $WORK/assets
python3 compose_long.py $WORK/take $WORK/assets $WORK/voice $REPO/docs/pitch/demo-long.mp4
PID=$(lsof -ti tcp:8010 || true); [ -n "$PID" ] && kill $PID
echo "done: docs/pitch/demo-long.mp4"
