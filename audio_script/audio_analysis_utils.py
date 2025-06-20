import numpy as np
import librosa
from pesq import pesq
from scipy.signal import correlate

# 音频对齐（互相关或DTW）
def align_audio_signal(ref_audio, test_audio, sr, method='cc'):
    if method == 'cc':
        # 互相关对齐
        offset = np.argmax(correlate(test_audio, ref_audio, mode='valid'))
    else:
        # DTW对齐
        ref_mfcc = librosa.feature.mfcc(y=ref_audio, sr=sr)
        test_mfcc = librosa.feature.mfcc(y=test_audio, sr=sr)
        from dtw import dtw
        alignment = dtw(test_mfcc.T, ref_mfcc.T)
        offset = alignment.index1[0]
    aligned_audio = test_audio[offset:offset+len(ref_audio)]
    if len(aligned_audio) < len(ref_audio):
        aligned_audio = np.concatenate([aligned_audio, np.zeros(len(ref_audio)-len(aligned_audio))])
    return aligned_audio[:len(ref_audio)], offset

# RMS计算
def calculate_rms(audio):
    return np.sqrt(np.mean(audio**2))

# 匹配增益（用于PESQ前归一化）
def calc_match_gain(test_audio, ref_audio, eps=1e-8):
    rms_ref = calculate_rms(ref_audio)
    rms_test = calculate_rms(test_audio)
    return rms_ref / (rms_test + eps)

# SNR计算
def calculate_snr(ref_audio, test_audio):
    signal_rms = calculate_rms(ref_audio)
    total_rms = calculate_rms(test_audio)
    noise_rms = np.sqrt(max(total_rms**2 - signal_rms**2, 1e-12))
    return 20 * np.log10(signal_rms / noise_rms) if noise_rms > 0 else float('inf')

# PESQ主流程（自动采样率、增益归一化、长度对齐）
def pesq_score(ref_path, deg_path, method='cc'):
    # 加载音频
    ref_audio, sr_ref = librosa.load(ref_path, sr=None, mono=True)
    deg_audio, sr_deg = librosa.load(deg_path, sr=sr_ref, mono=True)
    # 对齐
    aligned_audio, offset = align_audio_signal(ref_audio, deg_audio, sr_ref, method=method)
    # 增益归一化
    gain = calc_match_gain(aligned_audio, ref_audio)
    aligned_audio = aligned_audio * gain
    # 长度对齐
    min_len = min(len(ref_audio), len(aligned_audio))
    ref_audio = ref_audio[-min_len:]
    aligned_audio = aligned_audio[-min_len:]
    # PESQ
    bw = 'wb' if sr_ref >= 16000 else 'nb'
    try:
        pesq_val = pesq(sr_ref, ref_audio, aligned_audio, bw)
    except Exception as e:
        pesq_val = None
    # SNR、RMS
    snr = calculate_snr(ref_audio, aligned_audio)
    rms = calculate_rms(aligned_audio)
    return {
        'pesq': pesq_val,
        'snr': snr,
        'rms': rms,
        'offset': offset,
        'ref_audio': ref_audio,
        'test_audio': aligned_audio,
        'sr': sr_ref
    } 