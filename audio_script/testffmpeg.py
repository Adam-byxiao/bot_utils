import numpy as np
import soundfile as sf
import librosa
import matplotlib.pyplot as plt
from scipy import signal
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw
def load_raw_audio(file_path):
    """直接加载原始音频数据，不做任何处理"""
    audio, sr = sf.read(file_path, always_2d=False)
    # 如果是立体声，取左声道
    if audio.ndim > 1:
        audio = audio[:, 0]
    return audio, sr

def find_content_match(reference, recorded, sr):
    """
    在录制音频中寻找与参考音频最匹配的位置
    不做任何预处理，直接使用原始波形数据
    """
    # 计算互相关（使用FFT加速）
    corr = signal.correlate(recorded, reference, mode='valid', method='fft')
    
    # 找到最佳匹配位置
    best_pos = np.argmax(corr)
    best_corr = corr[best_pos]
    
    # 提取匹配部分
    aligned_recorded = recorded[best_pos : best_pos + len(reference)]
    
    # 如果录制音频较短，保留原始长度
    if len(aligned_recorded) < len(reference):
        aligned_recorded = np.pad(aligned_recorded, 
                                (0, len(reference) - len(aligned_recorded)),
                                'constant')
    
    return aligned_recorded, best_pos, best_corr

def calculate_raw_metrics(reference, recorded):
    """直接计算原始音频指标，不做任何预处理"""
    # 确保长度一致
    min_len = min(len(reference), len(recorded))
    ref = reference[:min_len]
    rec = recorded[:min_len]
    
    # 1. 幅度差异（直接比较样本值）
    amplitude_diff = np.mean(np.abs(ref - rec))
    
    # 2. 零交叉率差异
    zcr_ref = np.mean(librosa.zero_crossings(ref))
    zcr_rec = np.mean(librosa.zero_crossings(rec))
    zcr_diff = np.abs(zcr_ref - zcr_rec)
    
    # 3. 能量比
    energy_ratio = np.sum(rec**2) / (np.sum(ref**2) + 1e-10)
    
    # 4. 原始SNR（不做静音检测等处理）
    noise = ref - rec
    raw_snr = 10 * np.log10(np.sum(ref**2) / (np.sum(noise**2) + 1e-10))
    
    # 综合评分（根据实际需求调整权重）
    score = 100 - 50 * amplitude_diff - 20 * zcr_diff - 10 * np.abs(energy_ratio - 1) - 0.5 * max(0, -raw_snr)
    score = max(0, min(100, score))
    
    return {
        'amplitude_diff': amplitude_diff,
        'zcr_diff': zcr_diff,
        'energy_ratio': energy_ratio,
        'raw_snr': raw_snr,
        'overall_score': score
    }

def plot_raw_comparison(reference, recorded, sr, save_path='raw_comparison.png'):
    """绘制原始波形对比图"""
    plt.figure(figsize=(15, 6))
    
    # 时间轴
    t_ref = np.arange(len(reference)) / sr
    t_rec = np.arange(len(recorded)) / sr
    
    plt.plot(t_ref, reference, label='Reference (Original)')
    plt.plot(t_rec, recorded, label='Recorded', alpha=0.7)
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude (Raw)')
    plt.title('Raw Audio Comparison (No Processing)')
    plt.legend()
    plt.grid(True)
    plt.savefig(save_path)
    plt.close()

def main():
    # 输入文件 - 使用原始未处理音频
    reference_file = "./audio_script/p232_023_man.wav"  # 9秒标准音频
    recorded_file = "./audio_script/bot_mic_qa_man1.wav"  # 录制的长音频
    
    # 直接加载原始音频
    print("Loading raw audio files...")
    ref_audio, sr = load_raw_audio(reference_file)
    rec_audio, _ = load_raw_audio(recorded_file)
    
    # 寻找内容匹配（不做预处理）
    print("Finding content match without any preprocessing...")
    aligned_rec, match_pos, match_corr = find_content_match(ref_audio, rec_audio, sr)
    print(f"Best match at position: {match_pos/sr:.2f}s, correlation: {match_corr:.3f}")
    
    # 计算原始指标
    print("Calculating raw metrics...")
    metrics = calculate_raw_metrics(ref_audio, aligned_rec)
    
    # 保存结果
    plot_raw_comparison(ref_audio, aligned_rec, sr)
    
    # 输出原始报告
    print("\n=== Raw Audio Comparison Report ===")
    print(f"Reference duration: {len(ref_audio)/sr:.2f}s")
    print(f"Recorded duration: {len(rec_audio)/sr:.2f}s")
    print(f"Match position: {match_pos/sr:.2f}s")
    print("\nRaw Quality Metrics:")
    print(f"- Amplitude Difference: {metrics['amplitude_diff']:.4f}")
    print(f"- Zero-Crossing Rate Diff: {metrics['zcr_diff']:.4f}")
    print(f"- Energy Ratio: {metrics['energy_ratio']:.2f}")
    print(f"- Raw SNR: {metrics['raw_snr']:.1f} dB")
    print(f"\nOverall Raw Score: {metrics['overall_score']:.1f}/100")

if __name__ == "__main__":
    main()


