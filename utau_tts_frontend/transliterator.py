import re
from gruut import sentences
try:
    from pykakasi import Kakasi
    kakasi_engine = Kakasi()
except ImportError:
    kakasi_engine = None

IPA_TO_UTAU = {
    'æ': '{', 'ə': '@', 'a': '@', 'ʌ': 'V', 'eɪ': 'eI', 'oʊ': 'oU', 
    'ɑ': 'A', 'ɹ': 'r', 'ɡ': 'g', 'ɪ': 'I', 'ɛ': 'e', 'i': 'i', 
    'u': 'u', 'ʊ': 'U', 'p': 'p', 'b': 'b', 't': 't', 'd': 'd', 
    'k': 'k', 'm': 'm', 'n': 'n', 'f': 'f', 'v': 'v', 's': 's', 
    'z': 'z', 'l': 'l', 'j': 'j', 'w': 'w', 'θ': 'T', 'ð': 'dh', 
    'ʃ': 'S', 'ŋ': 'N', 'ɔ': 'o', 'o': 'o', 'h': 'h',
    'aɪ': 'aI', 'aʊ': 'aU', 'ɔɪ': 'oI', 'ɚ': 'r', 'ɝ': 'r',
    'tʃ': 'tS', 'dʒ': 'dZ'
}

def get_word_segments(text):
    results = []
    if kakasi_engine and any(ord(c) > 128 for c in text):
        res = kakasi_engine.convert(text)
        for item in res:
            results.append({'word': item['hepburn'], 'phonemes': [item['hira']], 'hz': 220.0})
        return results

    for sentence in sentences(text, lang="en-us"):
        for word in sentence:
            clean_p = [IPA_TO_UTAU.get(re.sub(r'[ˈˌ. ]', '', p), p) for p in word.phonemes]
            results.append({'word': word.text, 'phonemes': clean_p, 'hz': 220.0})
    return results
