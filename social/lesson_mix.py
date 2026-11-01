"""Add the Ocean Link music bed under a voice-only lesson video.
Bed sits ~19 dB under the voice and dips 6 dB more while the voice speaks; final -14 LUFS.
usage: python3 social/lesson_mix.py in.mp4 out.mp4 seed   (for the voice-only *_social.mp4 lessons from Drive)
"""
import sys, subprocess, re
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from music import make_bed, BAR

src, dst, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
tmp = dst + '.d'
subprocess.run(['mkdir', '-p', tmp], check=True)
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src],
                           capture_output=True, text=True).stdout)

# end card = end of the last silent gap before the closing silence
log = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', src, '-af', 'silencedetect=n=-50dB:d=1', '-vn', '-f', 'null', '-'],
                     capture_output=True, text=True).stderr
ends = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', log)]
inner = [e for e in ends if e < dur - 0.5]
end_card = round((inner[-1] if inner else dur - 8) / BAR) * BAR
cuts = [BAR * 2, end_card]

make_bed(dur, cuts, f'{tmp}/bed.wav', seed=seed)
norm = lambda i, o: subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', i, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11',
                                    '-ar', '48000', '-ac', '2', o], check=True)
norm(f'{tmp}/bed.wav', f'{tmp}/bedn.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ar', '48000', '-ac', '2', f'{tmp}/v.wav'], check=True)
norm(f'{tmp}/v.wav', f'{tmp}/vn.wav')

sr, v = wavfile.read(f'{tmp}/vn.wav'); v = v.astype(np.float64)
_, b = wavfile.read(f'{tmp}/bedn.wav'); b = b.astype(np.float64)
n = min(len(v), len(b)); v, b = v[:n], b[:n]
if np.abs(v).max() > 2: v /= 32768.0
if np.abs(b).max() > 2: b /= 32768.0

# voice activity: 50 ms RMS above -40 dBFS, smoothed (fast attack, slow release)
hop = sr // 20
rms = np.sqrt((v[:n // hop * hop].mean(1).reshape(-1, hop) ** 2).mean(1))
act = (20 * np.log10(rms + 1e-9) > -40).astype(float)
sm = np.zeros_like(act); s = 0.0
for i, a in enumerate(act):
    s = s + (a - s) * (0.6 if a > s else 0.12); sm[i] = s
gain_db = -19 - 6 * sm
g = np.repeat(10 ** (gain_db / 20), hop)
g = np.concatenate([g, np.full(n - len(g), g[-1])])
mix = v + b * g[:, None]
mix /= max(1.0, np.abs(mix).max() / 0.98)
wavfile.write(f'{tmp}/mix.wav', sr, mix.astype(np.float32))
norm(f'{tmp}/mix.wav', f'{tmp}/mixn.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-i', f'{tmp}/mixn.wav', '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', dst], check=True)
subprocess.run(['rm', '-rf', tmp])
print(dst, 'dur', round(dur, 1), 'end_card', end_card)
