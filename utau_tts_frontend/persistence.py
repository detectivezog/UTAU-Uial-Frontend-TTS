import pandas as pd
import re
import os
try:
    from pykakasi import Kakasi
    kakasi_engine = Kakasi()
except ImportError:
    kakasi_engine = None

def import_ust_format(filename):
    """Groups Japanese moras into short manageable blocks (max 4)."""
    with open(filename, 'r', encoding='shift-jis', errors='ignore') as f:
        data = f.read()

    tempo = float(re.search(r"Tempo=([\d.]+)", data).group(1)) if "Tempo=" in data else 120.0
    notes_raw = re.findall(r"\[#\d+\]\nLength=(\d+)\nLyric=(.*?)\nNoteNum=(\d+)", data, re.DOTALL)
    
    words_data = []
    text_buffer, note_buffer = "", []

    for length, lyric, nnum in notes_raw:
        if lyric == "R":
            if note_buffer: words_data.append(_create_block(text_buffer, note_buffer))
            text_buffer, note_buffer = "", []
            continue

        ms = (int(length) / 480) * (60 / tempo) * 1000
        hz = 440 * (2**((int(nnum)-69)/12))
        text_buffer += lyric
        note_buffer.append({'alias': lyric, 'hz': hz, 'dur': ms, 'porta': 60, 'air': 0.1, 'croak': False})

        if len(note_buffer) >= 4:
            words_data.append(_create_block(text_buffer, note_buffer))
            text_buffer, note_buffer = "", []

    if note_buffer: words_data.append(_create_block(text_buffer, note_buffer))
    return words_data

def _create_block(raw_text, notes):
    display_text = raw_text
    if kakasi_engine and any(ord(c) > 128 for c in raw_text):
        res = kakasi_engine.convert(raw_text)
        display_text = "".join([item['hepburn'] for item in res])
    return {'word': display_text, 'flow': 0.6, 'tilt': 0.0, 'offset': 0.0, 'phonemes': notes}

def export_to_standard_csv(word_nodes, filename):
    rows = []
    for node in word_nodes:
        for seg in node.seg_data:
            row = seg.copy()
            row.update({'word': node.word_text, 'flow': node.flow_var.get(), 'tilt': node.tilt_var.get(), 'offset': node.offset_var.get()})
            rows.append(row)
    pd.DataFrame(rows).to_csv(filename, index=False)

def import_from_csv(filename):
    df = pd.read_csv(filename)
    words, current_word, cur_data = [], None, None
    for _, r in df.iterrows():
        if r['word'] != current_word:
            if cur_data: words.append(cur_data)
            current_word = r['word']
            cur_data = {'word': current_word, 'flow': r.get('flow', 0.6), 'tilt': r.get('tilt', 0.0), 'offset': r.get('offset', 0.0), 'phonemes': []}
        cur_data['phonemes'].append(r.to_dict())
    if cur_data: words.append(cur_data)
    return words
