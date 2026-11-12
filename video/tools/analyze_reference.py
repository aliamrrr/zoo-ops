"""Frame accurate measurements of a reference film: activity, cuts, palette, blur, audio tempo.

    python analyze_reference.py <video.mp4> <out_dir>

Writes frames.csv (one row per frame) and audio.json, and prints a summary. Used to write
MOTION_PLAYBOOK.md from numbers instead of impressions.
"""
import json, subprocess, sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from scipy.io import wavfile
from scipy.signal import find_peaks

video, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
cap = cv2.VideoCapture(video)
fps = cap.get(cv2.CAP_PROP_FPS)
rows, prev, palette = [], None, Counter()
i = 0
while True:
    ok, bgr = cap.read()
    if not ok:
        break
    rgb = bgr[:, :, ::-1]
    h, w = rgb.shape[:2]
    bg = np.median(np.concatenate([rgb[4:24, 4:24].reshape(-1, 3), rgb[-24:-4, -24:-4].reshape(-1, 3)]), axis=0)
    dist = np.abs(rgb.astype(int) - bg).sum(axis=2)
    ink = dist > 40
    ys, xs = np.where(ink)
    box = (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else (0, 0, 0, 0)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (320, 180), interpolation=cv2.INTER_AREA).astype(float)
    diff = float(np.abs(small - prev).mean()) if prev is not None else 0.0
    prev = small
    sharp = float(cv2.Laplacian(gray, cv2.CV_64F)[ink].var()) if ink.sum() > 200 else 0.0
    rows.append((i, round(i / fps, 3), *[int(v) for v in bg], round(float(ink.mean()) * 100, 2), *box, round(diff, 3), round(sharp, 1)))
    if i % 6 == 0:  # coarse palette: quantize to 16 levels
        q = (rgb[::4, ::4] // 16 * 16 + 8).reshape(-1, 3)
        palette.update(map(tuple, q[ink[::4, ::4].reshape(-1)]))
    i += 1
with open(out / "frames.csv", "w") as f:
    f.write("frame,t,bg_r,bg_g,bg_b,ink_pct,x0,y0,x1,y1,diff,sharp\n")
    f.writelines(",".join(map(str, r)) + "\n" for r in rows)

diffs = np.array([r[-2] for r in rows])
print(f"{i} frames at {fps} fps, {i / fps:.2f} s")
print("background colors:", Counter((r[2], r[3], r[4]) for r in rows).most_common(4))
print("hard cuts (diff > 12):", [rows[k][1] for k in np.where(diffs > 12)[0]])
still = diffs < 0.02
runs, start = [], None
for k, s in enumerate(still):
    if s and start is None: start = k
    if not s and start is not None:
        if k - start >= 6: runs.append((rows[start][1], round((k - start) / fps, 2)))
        start = None
print("holds (>= 6 identical frames) as (start, length):", runs)
print("share of frames with motion:", round(float((~still).mean()), 3))
print("ink palette (quantized):", [("#%02x%02x%02x" % c, n) for c, n in palette.most_common(24)])

wav = out / "audio.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ac", "1", "-ar", "22050", str(wav)], check=True)
sr, x = wavfile.read(wav)
x = x.astype(float) / 32768
hop, win = 256, 1024
frames = np.lib.stride_tricks.sliding_window_view(x, win)[::hop] * np.hanning(win)
mag = np.abs(np.fft.rfft(frames, axis=1))
flux = np.maximum(0, np.diff(np.log1p(mag * 50), axis=0)).sum(axis=1)
flux = (flux - flux.mean()) / flux.std()
env_sr = sr / hop
ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
lags = np.arange(len(ac)) / env_sr
band = (lags > 60 / 200) & (lags < 60 / 60)
cands = sorted(((ac[k], 60 / lags[k]) for k in find_peaks(np.where(band, ac, 0))[0]), reverse=True)[:5]
peaks, _ = find_peaks(flux, height=1.5, distance=int(env_sr * 0.12))
onsets = [round(float(p / env_sr), 2) for p in peaks]
rms = [round(float(np.sqrt((x[int(s * sr):int((s + 1) * sr)] ** 2).mean())), 4) for s in range(int(len(x) / sr))]
json.dump({"tempo_candidates_bpm": [round(float(b), 1) for _, b in cands], "onsets": onsets, "rms_per_second": rms},
          open(out / "audio.json", "w"))
print("tempo candidates (bpm):", [round(float(b), 1) for _, b in cands])
print("onsets:", len(onsets), onsets[:60])
print("rms per second:", rms)
