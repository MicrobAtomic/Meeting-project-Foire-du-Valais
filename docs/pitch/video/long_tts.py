"""Voice-over of the long demo video: one audio file per scene (macOS `say`), and their durations.
Usage, from the repository root: python3 docs/pitch/video/long_tts.py docs/pitch/.build/long"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
out = Path(sys.argv[1])
(out / "voice").mkdir(parents=True, exist_ok=True)
scenes = json.loads((HERE / "long_scenes.json").read_text())
timing = {}
for segment in scenes["segments"]:
    for scene in segment["scenes"]:
        audio = out / "voice" / f"{scene['id']}.aiff"
        subprocess.run(["say", "-v", scenes["voice"], "-r", str(scenes["rate"]), "-o", str(audio), scene["say"]], check=True)
        seconds = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(audio)],
                                       capture_output=True, text=True, check=True).stdout)
        timing[scene["id"]] = round(seconds, 2)
(out / "timing.json").write_text(json.dumps(timing, indent=2))
print(f"{len(timing)} scenes, {sum(timing.values()):.0f} s of voice-over")
