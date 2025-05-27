import numpy as np
import librosa
import matplotlib.pyplot as plt
from fastdtw import fastdtw  # 需安装：pip install fastdtw
from scipy.spatial.distance import euclidean
from sklearn.metrics import mean_squared_error
from scipy.stats import pearsonr

def compute_mel_spectrogram(audio_path, sr=16000, n_mels=80, hop_length=160):
    """计算梅尔图谱（转置为 (时间帧, 梅尔频带) 格式）"""
    y, sr = librosa.load(audio_path, sr=sr)
    mel_spec = librosa.feature.melspectrogram(
        y=y, sr=sr, n_mels=n_mels, hop_length=hop_length, fmax=8000
    )
    return librosa.power_to_db(mel_spec, ref=np.max).T

def align_with_fastdtw(ref_feats, test_feats, radius=10):
    """使用fastdtw对齐特征序列（radius控制搜索窗口大小）"""
    distance, path = fastdtw(
        ref_feats, test_feats, 
        dist=euclidean,
        radius=radius  # 限制搜索范围以平衡精度和速度
    )
    # 提取对齐后的索引
    ref_indices = np.array([i for i, _ in path])
    test_indices = np.array([j for _, j in path])
    return ref_indices, test_indices, distance

def dtw_adjusted_metrics(ref_log_mel, test_log_mel):
    """基于fastdtw对齐后的指标计算"""
    # 1. 使用fastdtw对齐
    ref_indices, test_indices, dtw_dist = align_with_fastdtw(ref_log_mel, test_log_mel)
    aligned_ref = ref_log_mel[ref_indices]
    aligned_test = test_log_mel[test_indices]
    
    # 2. 计算对齐后的指标
    metrics = {
        "DTW Distance": dtw_dist,
        "Spectral MSE": mean_squared_error(aligned_ref, aligned_test),
        "Spectral Correlation": pearsonr(aligned_ref.flatten(), aligned_test.flatten())[0],
    }
    return metrics, (aligned_ref, aligned_test)

def plot_aligned_mel(ref_aligned, test_aligned, sr, hop_length=160):
    """绘制对齐后的梅尔图谱对比"""
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 1, 1)
    librosa.display.specshow(
        ref_aligned.T, x_axis="time", y_axis="mel", 
        sr=sr, hop_length=hop_length, fmax=8000
    )
    plt.colorbar(format="%+2.0f dB")
    plt.title("Aligned Reference Speech")
    
    plt.subplot(2, 1, 2)
    librosa.display.specshow(
        test_aligned.T, x_axis="time", y_axis="mel", 
        sr=sr, hop_length=hop_length, fmax=8000
    )
    plt.colorbar(format="%+2.0f dB")
    plt.title("Aligned Test Speech")
    
    plt.tight_layout()
    plt.show()

def enhanced_intelligibility_analysis(ref_audio, test_audio):
    """主分析函数（集成fastdtw）"""
    # 1. 计算梅尔图谱
    ref_log_mel = compute_mel_spectrogram(ref_audio)
    test_log_mel = compute_mel_spectrogram(test_audio)
    
    # 2. DTW对齐并计算指标
    metrics, (ref_aligned, test_aligned) = dtw_adjusted_metrics(ref_log_mel, test_log_mel)
    
    # 3. 原始指标（未对齐）作为参考
    raw_metrics = {
        "Raw Spectral MSE": mean_squared_error(ref_log_mel, test_log_mel),
        "Raw Spectral Correlation": pearsonr(ref_log_mel.flatten(), test_log_mel.flatten())[0],
    }
    metrics.update(raw_metrics)
    
    # 4. 可视化对齐结果
    plot_aligned_mel(ref_aligned, test_aligned, sr=16000)
    
    return metrics


# 示例调用
if __name__ == "__main__":
    #ref_audio = "D:\\work\\Repository\\bot_acoustic_test\\plays\\p232_023_man.wav"
    ref_audio = "D:\\work\\Repository\\bot_acoustic_test\\plays\\p232_023_man.wav"
    test_audio = "D:\\work\\Repository\\bot_acoustic_test\\records\\zoom1\\zoom_jabra_man.wav"  # 故意放慢语速的测试语音
    #test_audio = "D:\\work\\Repository\\bot_acoustic_test\\plays\\p232_023_man.wav"

    results = enhanced_intelligibility_analysis(ref_audio, test_audio)
    print("FastDTW-Enhanced Intelligibility Metrics:")
    for k, v in results.items():
        print(f"{k}: {v:.4f}")
