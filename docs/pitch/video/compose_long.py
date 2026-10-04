"""Long demo video: alternating phone and desktop segments, a caption per scene, the voice-over of every scene placed on
the shared timeline. Usage: python3 compose_long.py TAKE_DIR ASSETS_DIR VOICE_DIR OUTPUT.mp4"""
import json
import subprocess
import sys
from pathlib import Path

take, assets, voice, output = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
segments = json.loads((take / "markers.json").read_text())["segments"]
X = 0.5  # cross-fade between segments
inputs, f, labels = [], [], []
n = 0

def add_input(*args):
    global n
    inputs.extend(args)
    n += 1
    return n - 1

offsets, t = [], 0.0
for k, seg in enumerate(segments):
    offsets.append(t)
    t += seg["duration"] - (X if k < len(segments) - 1 else 0)
total = t

for k, seg in enumerate(segments):
    D = seg["duration"]
    src = add_input("-f", "concat", "-safe", "0", "-i", str(take / seg["name"] / "list.ffconcat"))
    frame = add_input("-loop", "1", "-framerate", "30", "-t", f"{D:.3f}", "-i", str(assets / ("bezel.png" if seg["layout"] == "phone" else "window.png")))
    f.append(f"color=c=0x0c0a09:s=1920x1080:r=30:d={D:.3f}[bg{k}]")
    if seg["layout"] == "phone":
        f.append(f"[{src}:v]fps=30,scale=434:940:flags=lanczos,setsar=1,format=yuv420p[sc{k}]")
        f.append(f"[bg{k}][sc{k}]overlay=350:60:eof_action=repeat[a{k}]")
    else:
        f.append(f"[{src}:v]fps=30,scale=1280:800:flags=lanczos,setsar=1,format=yuv420p[sc{k}]")
        f.append(f"[bg{k}][sc{k}]overlay=320:120:eof_action=repeat[a{k}]")
    f.append(f"[a{k}][{frame}:v]overlay=0:0[b{k}]")
    last = f"b{k}"
    times = [m["t"] for m in seg["markers"]] + [D]
    for i, m in enumerate(seg["markers"]):
        a, b = times[i], times[i + 1]
        cap = add_input("-loop", "1", "-framerate", "30", "-t", f"{D:.3f}", "-i", str(assets / f"cap_{m['label']}.png"))
        f.append(f"[{cap}:v]format=rgba,fade=t=in:st={a:.3f}:d=0.3:alpha=1,fade=t=out:st={max(b - 0.3, a):.3f}:d=0.3:alpha=1[c{k}_{i}]")
        f.append(f"[{last}][c{k}_{i}]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[o{k}_{i}]")
        last = f"o{k}_{i}"
    f.append(f"[{last}]trim=duration={D:.3f},setpts=PTS-STARTPTS,format=yuv420p[v{k}]")

video = "v0"
for k in range(1, len(segments)):
    f.append(f"[{video}][v{k}]xfade=transition=fade:duration={X}:offset={offsets[k]:.3f}[x{k}]")
    video = f"x{k}"

voices = []
for k, seg in enumerate(segments):
    for m in seg["markers"]:
        idx = add_input("-i", str(voice / f"{m['label']}.aiff"))
        delay = int((offsets[k] + m["t"] + 0.25) * 1000)
        f.append(f"[{idx}:a]aresample=48000,adelay={delay}|{delay}[s{idx}]")
        voices.append(f"[s{idx}]")
f.append(f"{''.join(voices)}amix=inputs={len(voices)}:normalize=0,apad,atrim=duration={total:.3f}[aud]")

cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs, "-filter_complex", ";".join(f),
       "-map", f"[{video}]", "-map", "[aud]", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
       "-r", "30", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", output]
subprocess.run(cmd, check=True)
print(f"{output}: {total:.1f} s")
