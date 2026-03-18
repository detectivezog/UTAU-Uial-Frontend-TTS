import os
import pickle
import numpy as np
import pyworld as pw
import librosa
import warnings
from .methods import SynthesisMethods

warnings.filterwarnings("ignore", category=FutureWarning)

class AcousticEngine:
    def __init__(self, base_path, cache_dir="vocal_cache"):
        self.base_path = base_path
        self.cache_dir = os.path.join(base_path, cache_dir)
        self.fs = 44100
        self.frame_period = 5.0
        self.oto_map = {}
        os.makedirs(self.cache_dir, exist_ok=True)
        self.discover_voicebanks()

    def discover_voicebanks(self):
        for root, _, files in os.walk(self.base_path):
            if "oto.ini" in files:
                try:
                    with open(os.path.join(root, "oto.ini"), 'r', encoding='shift-jis', errors='ignore') as f:
                        for line in f:
                            if '=' in line:
                                fname, rest = line.strip().split('=')
                                p = rest.split(',')
                                if len(p) >= 6:
                                    self.oto_map[p[0].lower()] = {
                                        'path': os.path.join(root, fname),
                                        'offset': float(p[1]),
                                        'consonant': float(p[2]), 
                                        'preutterance': float(p[4]),
                                        'overlap': float(p[5])
                                    }
                except Exception as e:
                    print(f"Error loading OTO: {e}")

    def _shift_formants(self, sp, factor):
        """Fixes the Character Slider: Mathematically resizes the vocal tract."""
        if factor == 1.0: return sp
        new_sp = np.zeros_like(sp)
        freq_bins = sp.shape[1]
        x = np.arange(freq_bins)
        # To shift formants DOWN (Male), we read from higher frequencies.
        x_lookup = x / factor 
        for i in range(sp.shape[0]):
            new_sp[i, :] = np.interp(x_lookup, x, sp[i, :])
        return new_sp

    def generate_breath_gap(self, duration_ms, air_level=0.01):
        frames = int(duration_ms / self.frame_period)
        if frames < 2: return np.array([], dtype=np.float32)
        f0 = np.zeros(frames, dtype=np.float64)
        ap = np.ones((frames, 1025), dtype=np.float64) * air_level
        sp = np.ones((frames, 1025), dtype=np.float64) * 1e-8 
        return pw.synthesize(f0, sp, ap, self.fs).flatten().astype(np.float32)

    def synthesize(self, symbol, prev_symbol, note_hz, duration_ms, prev_hz, porta_ms, 
                   air=0.1, vibrato=0.0, cons_speed=1.0, croak=0.0, formant=1.0, method="Vocode"):
        
        target = symbol.lower()
        if prev_symbol:
            cv = f"{prev_symbol.lower()} {target}"
            if cv in self.oto_map: target = cv
        
        entry = self.oto_map.get(target)
        if not entry: return None, 0.0

        cache_path = os.path.join(self.cache_dir, f"{target.replace(' ', '_')}.pkl")
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f: feat = pickle.load(f)
        else:
            x, fs = librosa.load(entry['path'], sr=self.fs)
            x_proc = x.astype(np.float64)[int(entry['offset'] * fs / 1000):]
            if len(x_proc) < 512: return None, 0.0
            
            f0, t = pw.dio(x_proc, fs); f0 = pw.stonemask(x_proc, f0, t, fs)
            # Snow Protection
            if np.all(f0 == 0): f0[:] = note_hz
            
            feat = {
                'f0': f0, 'sp': pw.cheaptrick(x_proc, f0, t, fs), 'ap': pw.d4c(x_proc, f0, t, fs),
                'fixed_frames': int(entry['consonant'] / self.frame_period)
            }
            with open(cache_path, 'wb') as f: pickle.dump(feat, f)

        # Consonant Protection (Stretching)
        target_frames = int(duration_ms / self.frame_period)
        fixed = min(feat['fixed_frames'], feat['sp'].shape[0] - 5)
        body_len = max(5, target_frames - fixed)
        
        idxs = np.linspace(feat['fixed_frames'], feat['sp'].shape[0] - 1, body_len)
        def stretch(data):
            return np.array([np.interp(idxs, np.arange(data.shape[0]), data[:, i]) for i in range(data.shape[1])]).T

        sp_final = np.vstack((feat['sp'][:fixed, :], stretch(feat['sp'])))
        ap_final = np.vstack((feat['ap'][:fixed, :], stretch(feat['ap'])))

        # Character & Air
        sp_final = self._shift_formants(sp_final, formant)[:target_frames]
        ap_final = (ap_final * (1.0 + air))[:target_frames]

        # Pitch Generation
        f0_final = np.ones(target_frames) * note_hz
        
        # REAL CROAK (Vocal Fry): 25Hz sub-harmonic pulse
        if croak > 0:
            t_sec = np.arange(target_frames) * self.frame_period / 1000.0
            fry_mod = 1.0 - (croak * 0.4 * (np.sin(2 * np.pi * 25 * t_sec) > 0))
            f0_final *= fry_mod
            ap_final = np.clip(ap_final + (croak * 0.3), 0, 1)

        f0_final *= (1.0 + 0.001 * np.random.randn(target_frames))
        
        # Vibrato
        if vibrato > 0:
            t_axis = np.arange(target_frames) * self.frame_period / 1000.0
            f0_final += vibrato * 5 * np.sin(2 * np.pi * 6.0 * t_axis)

        # Portamento Glide
        if porta_ms > 0 and prev_hz > 20:
            p_f = min(int(porta_ms / self.frame_period), target_frames // 2)
            if p_f > 0:
                slide = 1 / (1 + np.exp(-np.linspace(-5, 5, p_f)))
                f0_final[:p_f] = prev_hz + (f0_final[0] - prev_hz) * slide

        # Memory alignment
        f0_final = np.ascontiguousarray(f0_final, dtype=np.float64)
        sp_final = np.ascontiguousarray(sp_final, dtype=np.float64)
        ap_final = np.ascontiguousarray(ap_final, dtype=np.float64)

        if method == "Filter":
            audio = SynthesisMethods.filter_robotic(f0_final, sp_final, ap_final, self.fs)
        elif method == "Resynth":
            audio = SynthesisMethods.resynth_singer(f0_final, sp_final, ap_final, self.fs)
        else:
            audio = SynthesisMethods.vocode_natural(f0_final, sp_final, ap_final, self.fs)
            
        # THE PRONUNCIATION BREAKTHROUGH: High-Frequency Pre-emphasis (Presence Boost)
        # This acts like a mastering EQ, boosting consonants and adding extreme clarity.
        audio = np.append(audio[0], audio[1:] - 0.85 * audio[:-1])

        return audio.flatten(), entry['overlap']
