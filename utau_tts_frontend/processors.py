import numpy as np

class VocalProcessor:
    @staticmethod
    def shift_formants(sp, factor=1.0):
        """
        Shifts vocal tract resonance to change character (Gender/Size). 
        factor < 1.0 = Deeper/Masculine; factor > 1.0 = Higher/Feminine.
        """
        if factor == 1.0: return sp
        new_sp = np.zeros_like(sp)
        for i in range(sp.shape[0]):
            old_indices = np.arange(sp.shape[1])
            new_indices = old_indices * factor
            new_sp[i, :] = np.interp(old_indices, new_indices, sp[i, :])
        return new_sp

    @staticmethod
    def apply_jitter(f0, intensity=0.001):
        """Adds micro-variations to the pitch to prevent robotic drone sounds."""
        if intensity <= 0: return f0
        noise = 1.0 + (np.random.randn(len(f0)) * intensity)
        return f0 * noise
