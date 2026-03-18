import numpy as np
import pyworld as pw
from scipy.ndimage import gaussian_filter1d

class SynthesisMethods:
    @staticmethod
    def vocode_natural(f0, sp, ap, fs):
        """Mode 1: High-fidelity naturalism."""
        f0 = np.ascontiguousarray(f0, dtype=np.float64)
        sp = np.ascontiguousarray(sp, dtype=np.float64)
        ap = np.ascontiguousarray(ap, dtype=np.float64)
        y = pw.synthesize(f0, sp, ap, fs)
        return y.flatten().astype(np.float32)

    @staticmethod
    def filter_robotic(f0, sp, ap, fs):
        """Mode 2: Roboticist. Quantized pitch and sharp formants."""
        f0_fixed = np.copy(f0)
        voiced = f0 > 0
        if np.any(voiced):
            f0_fixed[voiced] = np.round(f0_fixed[voiced])
        ap_robot = np.ones_like(ap) * 0.9 
        ap_robot[voiced, :] = 0.001 
        sp_robot = np.power(sp, 1.6) 
        f0_fixed = np.ascontiguousarray(f0_fixed, dtype=np.float64)
        sp_robot = np.ascontiguousarray(sp_robot, dtype=np.float64)
        ap_robot = np.ascontiguousarray(ap_robot, dtype=np.float64)
        y = pw.synthesize(f0_fixed, sp_robot, ap_robot, fs)
        return y.flatten().astype(np.float32)

    @staticmethod
    def resynth_singer(f0, sp, ap, fs):
        """Mode 3: Singer. Smoothed transitions for liquid vowels."""
        smooth_sp = gaussian_filter1d(sp, sigma=3.0, axis=0)
        f0 = np.ascontiguousarray(f0, dtype=np.float64)
        smooth_sp = np.ascontiguousarray(smooth_sp, dtype=np.float64)
        ap = np.ascontiguousarray(ap, dtype=np.float64)
        y = pw.synthesize(f0, smooth_sp, ap, fs)
        return y.flatten().astype(np.float32)
