import os
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import numpy as np
import sounddevice as sd
import soundfile as sf
import threading
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import librosa
import librosa.display

from .engine import AcousticEngine
from .sequencer import WordGroup, SegmentBlock, HScrollableFrame
from .transliterator import get_word_segments
from .persistence import export_to_standard_csv, import_from_csv, import_ust_format

class UtauStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UTAU UIEL - Definitive Acoustic Studio")
        self.geometry("1200x850")
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.engine = AcousticEngine(self.base_dir)
        self.words =[]
        self._build_ui()

    def _build_ui(self):
        m = tk.Menu(self)
        self.config(menu=m)
        fm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="File", menu=fm)
        fm.add_command(label="Open CSV", command=self.load_csv)
        fm.add_command(label="Save CSV", command=self.save_csv)
        fm.add_command(label="Import UST", command=self.load_ust)

        tb = ttk.Frame(self, padding=10)
        tb.pack(fill=tk.X)
        
        self.play_btn = ttk.Button(tb, text="▶ PLAY", command=self.play_thread, style="Accent.TButton")
        self.play_btn.pack(side=tk.LEFT)
        
        self.export_btn = ttk.Button(tb, text="💾 EXPORT MEDIA", command=self.export_media)
        self.export_btn.pack(side=tk.LEFT, padx=5)

        self.method_var = tk.StringVar(value="Vocode")
        for m_str in ["Vocode", "Filter", "Resynth"]: 
            ttk.Radiobutton(tb, text=m_str, variable=self.method_var, value=m_str).pack(side=tk.LEFT, padx=2)

        ttk.Label(tb, text="Character:").pack(side=tk.LEFT, padx=(10, 2))
        self.formant_scale = tk.Scale(tb, from_=0.5, to=1.5, resolution=0.01, orient=tk.HORIZONTAL, length=70)
        self.formant_scale.set(1.0)
        self.formant_scale.pack(side=tk.LEFT)

        ttk.Label(tb, text="Cons Speed:").pack(side=tk.LEFT, padx=(10, 2))
        self.cons_scale = tk.Scale(tb, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, length=70)
        self.cons_scale.set(1.0)
        self.cons_scale.pack(side=tk.LEFT)
        
        ttk.Label(tb, text="Glue:").pack(side=tk.LEFT, padx=(10, 2))
        self.elastic_scale = tk.Scale(tb, from_=0.5, to=3.0, resolution=0.1, orient=tk.HORIZONTAL, length=70)
        self.elastic_scale.set(1.5)
        self.elastic_scale.pack(side=tk.LEFT)

        self.v_sel = ttk.Combobox(tb, state="readonly", width=15)
        self.v_sel.pack(side=tk.RIGHT)
        self._refresh_vbs()

        self.editor = scrolledtext.ScrolledText(self, height=3, font=("Arial", 12))
        self.editor.pack(fill=tk.X, padx=10, pady=5)
        self.editor.insert(tk.END, "The moon laboratory. Cake bubblegum observatory.")
        
        ttk.Button(self, text="ANALYZE PROSODY", command=self.parse_text).pack(pady=5)

        ttk.Label(self, text="Word Level Prosody", font=("Arial", 10, "bold")).pack(anchor="w", padx=10)
        self.word_scroll = HScrollableFrame(self, height=180)
        self.word_scroll.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self, text="Segment Level Detail", font=("Arial", 10, "bold")).pack(anchor="w", padx=10)
        self.seg_scroll = HScrollableFrame(self, height=300)
        self.seg_scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _clear_blocks(self):
        for w in self.words: 
            w.destroy()
        self.words =[]
        for child in self.seg_scroll.scrollable_frame.winfo_children(): 
            child.destroy()

    def parse_text(self):
        self._clear_blocks()
        data = get_word_segments(self.editor.get(1.0, tk.END).strip())
        base_hz = 220.0
        for i, d in enumerate(data):
            word_hz = base_hz * (0.97 ** i) 
            w = WordGroup(self.word_scroll.scrollable_frame, d['word'], d['phonemes'], self.load_segments, word_hz)
            w.pack(side=tk.LEFT, padx=3)
            self.words.append(w)

    def load_segments(self, word_node):
        # FIX: Properly indented block
        for child in self.seg_scroll.scrollable_frame.winfo_children(): 
            child.destroy()
            
        avail = list(self.engine.oto_map.keys())
        for data in word_node.seg_data:
            block = SegmentBlock(self.seg_scroll.scrollable_frame, data['alias'], data, avail)
            block.pack(side=tk.LEFT, padx=3)

    def trim_silence(self, audio, threshold=0.01):
        if len(audio) == 0: 
            return audio
        valid_indices = np.where(np.abs(audio) > threshold)[0]
        if len(valid_indices) > 0: 
            return audio[valid_indices[0]:valid_indices[-1]]
        return audio

    def generate_audio_buffer(self):
        audio_stream =[]
        prev_hz = 0
        prev_sym = None
        global_elastic = self.elastic_scale.get()
        method = self.method_var.get()
        
        for word in self.words:
            flow_factor = word.flow_var.get()
            tilt = word.tilt_var.get()
            offset = word.offset_var.get()
            
            for i, seg in enumerate(word.seg_data):
                target_hz = seg['hz'] + offset
                
                chunk, ovl_ms = self.engine.synthesize(
                    symbol=seg['alias'], 
                    prev_symbol=prev_sym, 
                    note_hz=target_hz,
                    duration_ms=seg.get('dur', 250), 
                    prev_hz=prev_hz, 
                    porta_ms=seg.get('porta', 80),
                    air=seg.get('air', 0.1), 
                    vibrato=0.0, 
                    cons_speed=self.cons_scale.get(),
                    croak=1.0 if seg.get('croak') else 0.0, 
                    formant=self.formant_scale.get(),
                    word_tilt=tilt, 
                    method=method
                )
                
                if chunk is not None:
                    chunk = self.trim_silence(chunk)
                    if len(chunk) > 0:
                        audio_stream.append((chunk.flatten(), ovl_ms, flow_factor))
                        if target_hz > 20: 
                            prev_hz = target_hz
                prev_sym = seg['alias']
            
            gap = self.engine.generate_breath_gap(150, air_level=0.01)
            audio_stream.append((gap.flatten(), 0, 0))

        if not audio_stream: 
            return None

        final = audio_stream[0][0]
        for i in range(1, len(audio_stream)):
            next_chunk, ovl_ms, flow = audio_stream[i]
            
            ovl_s = int(max(20, ovl_ms) * 44.1 * flow * global_elastic)
            ovl_s = min(ovl_s, len(final), len(next_chunk))
            
            if ovl_s > 5:
                x_curve = np.linspace(-5, 5, ovl_s)
                fade_in = 1 / (1 + np.exp(-x_curve))
                fade_out = 1 - fade_in
                blend = (final[-ovl_s:] * fade_out) + (next_chunk[:ovl_s] * fade_in)
                final = np.concatenate([final[:-ovl_s], blend, next_chunk[ovl_s:]])
            else:
                final = np.concatenate([final, next_chunk])
        
        return final / (np.max(np.abs(final)) + 1e-7)

    def play_thread(self):
        threading.Thread(target=self._play_logic, daemon=True).start()

    def _play_logic(self):
        self.play_btn.config(state="disabled")
        try:
            audio = self.generate_audio_buffer()
            if audio is not None:
                sd.play(audio, 44100)
                sd.wait()
        except Exception as e: 
            print(f"Play Error: {e}")
        finally: 
            self.play_btn.config(state="normal")

    def export_media(self):
        path = filedialog.asksaveasfilename(title="Export Media")
        if not path: return
        base_path = os.path.splitext(path)[0]
        threading.Thread(target=self._export_logic, args=(base_path,), daemon=True).start()

    def _export_logic(self, base_path):
        self.export_btn.config(state="disabled", text="💾 EXPORTING...")
        try:
            audio = self.generate_audio_buffer()
            if audio is None: return

            # 1. High-Res FLAC
            flac_path = f"{base_path}.flac"
            sf.write(flac_path, audio, 44100)
            
            # 2. Spectral Imprint
            try:
                png_path = f"{base_path}.png"
                plt.figure(figsize=(14, 6))
                D = librosa.amplitude_to_db(np.abs(librosa.stft(audio, n_fft=2048, hop_length=256)), ref=np.max)
                librosa.display.specshow(D, sr=44100, hop_length=256, x_axis='time', y_axis='linear', cmap='magma')
                plt.colorbar(format='%+2.0f dB')
                plt.title(f"Spectral Imprint ({self.method_var.get()} Mode)")
                plt.ylim(0, 8000) 
                plt.tight_layout()
                plt.savefig(png_path, dpi=150)
                plt.close()
                self.after(0, lambda: messagebox.showinfo("Success", f"Saved:\n{flac_path}\n{png_path}"))
            except ImportError:
                print("[!] Matplotlib not installed. Skipping PNG generation.")
                self.after(0, lambda: messagebox.showinfo("Export Partial", f"Saved {flac_path}"))

        except Exception as e:
            print(f"Export Error: {e}")
        finally:
            self.export_btn.config(state="normal", text="💾 EXPORT FLAC & PNG")

    def save_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            export_to_standard_csv(self.words, path)

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            self._reconstruct(import_from_csv(path))

    def load_ust(self):
        path = filedialog.askopenfilename(filetypes=[("UST", "*.ust;*.txt")])
        if path:
            data = import_ust_format(path)
            full_text = " ".join([d['word'] for d in data])
            self.editor.delete(1.0, tk.END)
            self.editor.insert(tk.END, full_text)
            self._reconstruct(data)

    def _reconstruct(self, data):
        self._clear_blocks()
        for d in data:
            w = WordGroup(self.word_scroll.scrollable_frame, d['word'],[], self.load_segments, 220.0)
            w.flow_var.set(d['flow'])
            w.tilt_var.set(d['tilt'])
            w.offset_var.set(d['offset'])
            w.seg_data = d['phonemes']
            w.pack(side=tk.LEFT, padx=3)
            self.words.append(w)

    def _refresh_vbs(self):
        p = os.path.join(self.base_dir, "voicebanks")
        if os.path.exists(p):
            vbs =[d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d))]
            self.v_sel['values'] = vbs
            if vbs: 
                self.v_sel.set(vbs[0])

def main():
    root = UtauStudio()
    style = ttk.Style(root)
    try: 
        style.configure("Accent.TButton", font=("Helvetica", 10, "bold"), foreground="blue")
    except tk.TclError: 
        pass
    root.mainloop()

if __name__ == "__main__":
    main()
