"""Compose the demo video: phone recording in a bezel with captions, then the staff screen in a window. 1920x1080, H.264."""
import json
import subprocess
import sys
from pathlib import Path

take, assets, output = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
markers = json.loads((take / "markers.json").read_text())
phone, desk = markers["phone"], markers["desk"]
P, D, X = phone["duration"], desk["duration"], 0.5
pm = [m["t"] for m in phone["markers"]] + [P]
dm = [m["t"] for m in desk["markers"]] + [D]

inputs = ["-f", "concat", "-safe", "0", "-i", str(take / "phone" / "list.ffconcat"),
          "-f", "concat", "-safe", "0", "-i", str(take / "desk" / "list.ffconcat"),
          "-loop", "1", "-framerate", "30", "-t", f"{P:.3f}", "-i", str(assets / "bezel.png"),
          "-loop", "1", "-framerate", "30", "-t", f"{D:.3f}", "-i", str(assets / "window.png")]
for i in range(len(phone["markers"])):
    inputs += ["-loop", "1", "-framerate", "30", "-t", f"{P:.3f}", "-i", str(assets / f"cap_phone_{i}.png")]
for i in range(len(desk["markers"])):
    inputs += ["-loop", "1", "-framerate", "30", "-t", f"{D:.3f}", "-i", str(assets / f"cap_desk_{i}.png")]

f = [f"color=c=0x0c0a09:s=1920x1080:r=30:d={P:.3f}[bgp]", f"color=c=0x0c0a09:s=1920x1080:r=30:d={D:.3f}[bgd]",
     "[0:v]fps=30,scale=434:940:flags=lanczos,setsar=1,format=yuv420p[ph]",
     "[1:v]fps=30,scale=1440:900:flags=lanczos,setsar=1,format=yuv420p[dk]",
     "[bgp][ph]overlay=350:60:eof_action=repeat[p0]", "[p0][2:v]overlay=0:0[p1]",
     "[bgd][dk]overlay=240:150:eof_action=repeat[d0]", "[d0][3:v]overlay=0:0[d1]"]

def captions(prefix, first_input, times, start_label):
    last = start_label
    for i in range(len(times) - 1):
        a, b = times[i], times[i + 1]
        fade_in = f"fade=t=in:st={a:.3f}:d=0.35:alpha=1"
        fade_out = f"fade=t=out:st={max(b - 0.35, a):.3f}:d=0.35:alpha=1"
        f.append(f"[{first_input + i}:v]format=rgba,{fade_in},{fade_out}[{prefix}c{i}]")
        f.append(f"[{last}][{prefix}c{i}]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[{prefix}o{i}]")
        last = f"{prefix}o{i}"
    return last

p_last = captions("p", 4, pm, "p1")
d_last = captions("d", 4 + len(phone["markers"]), dm, "d1")
f.append(f"[{p_last}]trim=duration={P:.3f},setpts=PTS-STARTPTS,format=yuv420p[pv]")
f.append(f"[{d_last}]trim=duration={D:.3f},setpts=PTS-STARTPTS,format=yuv420p[dv]")
f.append(f"[pv][dv]xfade=transition=fade:duration={X}:offset={P - X:.3f},format=yuv420p[v]")

cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs, "-filter_complex", ";".join(f), "-map", "[v]",
       "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", output]
subprocess.run(cmd, check=True)
print(f"{output}: {P + D - X:.1f} s")
