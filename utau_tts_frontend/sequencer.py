import tkinter as tk
from tkinter import ttk, simpledialog

PLOSIVES =['p', 'b', 't', 'd', 'k', 'g']
FRICATIVES =['s', 'f', 'S', 'h', 'th', 'tS', 'dZ', 'dh']
NASALS = ['m', 'n', 'N']

class HScrollableFrame(ttk.Frame):
    """Provides infinite horizontal scrolling for lanes."""
    def __init__(self, container, height=200):
        super().__init__(container)
        self.canvas = tk.Canvas(self, height=height)
        scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(xscrollcommand=scrollbar.set)
        self.canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")

class PhonemePicker(tk.Toplevel):
    def __init__(self, parent, available_aliases, callback):
        super().__init__(parent)
        self.title("Phoneme Picker")
        self.geometry("300x450")
        self.callback = callback
        self.transient(parent)
        self.grab_set()
        
        ttk.Label(self, text="Search Alias:", font=("Arial", 10, "bold")).pack(pady=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_list)
        self.entry = ttk.Entry(self, textvariable=self.search_var)
        self.entry.pack(fill=tk.X, padx=10, pady=5)
        
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.listbox = tk.Listbox(self.frame, font=("Arial", 10), selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sb = ttk.Scrollbar(self.frame, orient="vertical", command=self.listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=sb.set)
        
        self.all_aliases = sorted(available_aliases)
        self.filter_list()
        self.listbox.bind("<Double-Button-1>", self.on_select)
        ttk.Button(self, text="Select Phoneme", command=self.on_select).pack(fill=tk.X, padx=10, pady=10)

    def filter_list(self, *args):
        search = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        for a in self.all_aliases:
            if search in a.lower(): self.listbox.insert(tk.END, a)

    def on_select(self, event=None):
        sel = self.listbox.curselection()
        if sel: 
            self.callback(self.listbox.get(sel[0]))
            self.destroy()

class SegmentBlock(ttk.Frame):
    def __init__(self, parent, alias, data, available_aliases):
        super().__init__(parent, relief="raised", borderwidth=1, padding=2)
        self.data = data
        self.available_aliases = available_aliases
        self.alias_var = tk.StringVar(value=alias)
        
        # Vertical Stacking
        tk.Button(self, textvariable=self.alias_var, command=self.open_picker, bg="#fdfdfd", font=("Arial", 9, "bold")).pack(fill=tk.X, pady=(0,2))
        
        ttk.Label(self, text="Pitch (Hz)", font=("Arial", 7)).pack()
        self.hz_var = tk.DoubleVar(value=data.get('hz', 220.0))
        tk.Spinbox(self, from_=40, to=1000, textvariable=self.hz_var, width=6, command=self.sync_data).pack(pady=(0,2))
        
        ttk.Label(self, text="Dur (ms)", font=("Arial", 7)).pack()
        self.dur_var = tk.DoubleVar(value=data.get('dur', 250))
        tk.Scale(self, from_=20, to=1000, variable=self.dur_var, orient=tk.HORIZONTAL, length=70, showvalue=0, command=lambda x: self.sync_data()).pack(pady=(0,2))

        ttk.Label(self, text="Slide", font=("Arial", 7)).pack()
        self.p_var = tk.IntVar(value=data.get('porta', 60))
        tk.Scale(self, from_=0, to=400, variable=self.p_var, orient=tk.HORIZONTAL, length=70, showvalue=0, command=lambda x: self.sync_data()).pack(pady=(0,2))

        ttk.Label(self, text="Air", font=("Arial", 7)).pack()
        self.air_var = tk.DoubleVar(value=data.get('air', 0.1))
        tk.Scale(self, from_=0, to=1.0, variable=self.air_var, orient=tk.HORIZONTAL, length=70, showvalue=0, command=lambda x: self.sync_data()).pack(pady=(0,2))

        self.croak_var = tk.BooleanVar(value=data.get('croak', False))
        tk.Checkbutton(self, text="Croak", variable=self.croak_var, command=self.sync_data, font=("Arial", 8)).pack(pady=(0,2))

    def open_picker(self):
        PhonemePicker(self, self.available_aliases, self.update_alias)

    def update_alias(self, new_a): 
        self.alias_var.set(new_a)
        self.sync_data()

    def sync_data(self):
        self.data.update({
            'hz': self.hz_var.get(), 
            'dur': self.dur_var.get(), 
            'porta': self.p_var.get(), 
            'air': self.air_var.get(),
            'croak': self.croak_var.get(), 
            'alias': self.alias_var.get()
        })

class WordGroup(ttk.Frame):
    def __init__(self, parent, word_text, phonemes, on_select, base_hz=220.0):
        super().__init__(parent, relief="ridge", padding=5)
        self.word_text = word_text
        
        tk.Button(self, text=word_text.upper(), command=lambda: on_select(self), font=("Arial", 9, "bold"), bg="#e1e1e1").pack(fill=tk.X, pady=(0,2))
        
        ttk.Label(self, text="Tilt").pack()
        self.tilt_var = tk.DoubleVar(value=0.0) 
        tk.Scale(self, from_=-0.3, to=0.3, resolution=0.01, variable=self.tilt_var, orient=tk.HORIZONTAL, length=70, showvalue=0).pack(pady=(0,2))
        
        ttk.Label(self, text="Offset").pack()
        self.offset_var = tk.DoubleVar(value=0.0)
        tk.Scale(self, from_=-50, to=50, variable=self.offset_var, orient=tk.HORIZONTAL, length=70, showvalue=0).pack(pady=(0,2))
        
        ttk.Label(self, text="Flow").pack()
        self.flow_var = tk.DoubleVar(value=0.6) 
        tk.Scale(self, from_=0, to=1.0, resolution=0.1, variable=self.flow_var, orient=tk.HORIZONTAL, length=70, showvalue=0).pack(pady=(0,2))
        
        self.seg_data =[]
        for p in phonemes:
            dur, air, slide = 250, 0.05, 60
            if p in PLOSIVES: dur, slide = 50, 10
            elif p in FRICATIVES: dur, air = 100, 0.4
            elif p in NASALS: dur = 120
            self.seg_data.append({'alias': p, 'hz': base_hz, 'dur': dur, 'porta': slide, 'air': air, 'croak': False})
