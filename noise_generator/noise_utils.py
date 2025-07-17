import numpy as np
from scipy.signal import butter, lfilter

class NoiseGeneratorBase:
    def __init__(self, duration, sr, amplitude=1.0):
        self.duration = duration
        self.sr = sr
        self.amplitude = amplitude
        self.samples = int(duration * sr)

    def generate(self):
        raise NotImplementedError

class WhiteNoiseGenerator(NoiseGeneratorBase):
    def generate(self):
        return self.amplitude * np.random.normal(0, 1, self.samples)

class PinkNoiseGenerator(NoiseGeneratorBase):
    def generate(self):
        # 专业IIR滤波器法生成粉噪声
        # 参考: https://www.dsprelated.com/showarticle/908.php
        b = [0.049922035, 0.095993537, 0.050612699, -0.004408786]
        a = [1, -2.494956002, 2.017265875, -0.522189400]
        white = np.random.randn(self.samples)
        from scipy.signal import lfilter
        pink = lfilter(b, a, white)
        pink = pink / np.max(np.abs(pink))  # 归一化
        return self.amplitude * pink

def apply_envelope(signal, sr, env_type='none', **kwargs):
    if env_type == 'none':
        return signal
    elif env_type == 'linear':
        env = np.linspace(0, 1, len(signal))
        return signal * env
    elif env_type == 'adsr':
        # Simple ADSR stub
        a, d, s, r = kwargs.get('a',0.1), kwargs.get('d',0.1), kwargs.get('s',0.7), kwargs.get('r',0.1)
        total = len(signal)
        a_len = int(a * total)
        d_len = int(d * total)
        s_len = int((1-a-d-r) * total)
        r_len = total - (a_len + d_len + s_len)
        env = np.concatenate([
            np.linspace(0, 1, a_len, endpoint=False),
            np.linspace(1, s, d_len, endpoint=False),
            np.full(s_len, s),
            np.linspace(s, 0, r_len)
        ])
        return signal * env
    elif env_type == 'lfo':
        freq = kwargs.get('freq', 2)
        t = np.arange(len(signal)) / sr
        lfo = 0.5 * (1 + np.sin(2 * np.pi * freq * t))
        return signal * lfo
    else:
        return signal

def butter_filter(signal, sr, filter_type='none', cutoff=None, order=5, band=None):
    if filter_type == 'none' or cutoff is None:
        return signal
    nyq = 0.5 * sr
    if filter_type in ['lowpass', 'highpass']:
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype=filter_type.replace('pass',''))
    elif filter_type in ['bandpass', 'bandstop'] and band is not None:
        low, high = band
        b, a = butter(order, [low/nyq, high/nyq], btype=filter_type.replace('pass',''))
    else:
        return signal
    return lfilter(b, a, signal)

def apply_periodic_modulation(signal, sr, freq=2, depth=0.5):
    t = np.arange(len(signal)) / sr
    lfo = 1 + depth * np.sin(2 * np.pi * freq * t)
    return signal * lfo

def generate_noise(noise_type, duration, sr, amplitude=1.0, env_type='none', env_kwargs=None, filter_type='none', filter_kwargs=None, periodic_modulation=False, periodic_kwargs=None):
    if noise_type == 'White Noise':
        generator = WhiteNoiseGenerator(duration, sr, amplitude)
    elif noise_type == 'Pink Noise':
        generator = PinkNoiseGenerator(duration, sr, amplitude)
    else:
        raise ValueError(f"Unsupported noise type: {noise_type}")
    signal = generator.generate()
    if env_kwargs is None:
        env_kwargs = {}
    signal = apply_envelope(signal, sr, env_type, **env_kwargs)
    if filter_kwargs is None:
        filter_kwargs = {}
    signal = butter_filter(signal, sr, filter_type, **filter_kwargs)
    if periodic_modulation:
        if periodic_kwargs is None:
            periodic_kwargs = {}
        signal = apply_periodic_modulation(signal, sr, **periodic_kwargs)
    return signal

# Example usage:
# noise = generate_noise('White Noise', 5, 16000, amplitude=0.5, env_type='linear', filter_type='lowpass', filter_kwargs={'cutoff':3000}) 