import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft2, fftshift

def analyze_chromatic_noise(image_path, color_space='YUV', roi_size=512, n_frames=10):
    """
    色彩噪声分析（支持多帧分析）
    :param image_path: 输入图像路径（支持单帧或多帧）
    :param color_space: 色彩空间（'YUV'或'LAB'）
    :param roi_size: 分析区域大小（中心区域）
    :param n_frames: 多帧平均的帧数（用于分离随机噪声）
    :return: 色度噪声统计结果及可视化图表
    """
    # ==================== 1. 数据准备 ====================
    # 读取多帧图像（模拟多帧拍摄）
    images = []
    for i in range(n_frames):
        img = cv2.imread(image_path[i])
        if img is None:
            raise FileNotFoundError(f"图像未找到: {image_path}")
        images.append(img)
    img_stack = np.stack(images, axis=0)

    # 转换为目标色彩空间
    if color_space == 'YUV':
        converted_stack = [cv2.cvtColor(img, cv2.COLOR_BGR2YUV) for img in img_stack]
    elif color_space == 'LAB':
        converted_stack = [cv2.cvtColor(img, cv2.COLOR_BGR2LAB) for img in img_stack]
    else:
        raise ValueError("仅支持YUV或LAB色彩空间")
    converted_stack = np.stack(converted_stack, axis=0)

    # 提取亮度通道和色度通道
    if color_space == 'YUV':
        Y = converted_stack[..., 0]  # 直接索引更高效
        U = converted_stack[..., 1]
        V = converted_stack[..., 2]
        #Y, U, V = cv2.split(converted_stack)
        chroma_channels = {'U': U, 'V': V}
    else:
        L = converted_stack[..., 0]  # 直接索引更高效
        A = converted_stack[..., 1]
        B = converted_stack[..., 2]
        #L, A, B = cv2.split(converted_stack)
        chroma_channels = {'A': A, 'B': B}

    # 截取中心ROI区域
    h, w = img.shape[:2]
    roi = (slice(h//2 - roi_size//2, h//2 + roi_size//2), 
           slice(w//2 - roi_size//2, w//2 + roi_size//2))
    chroma_roi = {key: val[:, roi[0], roi[1]] for key, val in chroma_channels.items()}

    # ==================== 2. 时域分析 ====================
    # 计算各通道噪声标准差和SNR
    noise_stats = {}
    for ch_name, ch_data in chroma_roi.items():
        # 时域噪声（多帧标准差）
        temporal_noise = np.std(ch_data, axis=0)
        # 信号均值（以第一帧为参考）
        signal = np.mean(ch_data[0])
        # 噪声统计
        noise_stats[ch_name] = {
            'noise_mean': np.mean(temporal_noise),
            'noise_std': np.std(temporal_noise),
            'SNR': 20 * np.log10(signal / np.mean(temporal_noise)) if np.mean(temporal_noise) > 0 else np.inf
        }

    # ==================== 3. 频域分析 ====================
    '''# 取首帧色度通道ROI
    nps_results = {}
    for ch_name, ch_data in chroma_roi.items():
        # 去均值化
        ch_roi = ch_data[0] - np.mean(ch_data[0])
        # 计算2D FFT
        fft = fft2(ch_roi)
        fft_shifted = fftshift(fft)
        nps_2d = np.abs(fft_shifted)**2 / (roi_size**2)
        # 径向平均得到1D NPS
        y, x = np.indices(nps_2d.shape)
        center = np.array([x.mean(), y.mean()])
        r = np.hypot(x - center[0], y - center[1])
        max_radius = int(np.ceil(r.max()))
        r_bins = np.arange(0, max_radius + 1)
        #r_bins = np.arange(0, r.max(), 1)
        r_idx = np.digitize(r.ravel(), r_bins)
        nps_1d = np.bincount(r_idx, nps_2d.ravel()) / np.bincount(r_idx)
        nps_results[ch_name] = nps_1d'''
    nps_results = {}
    for ch_name, ch_data in chroma_roi.items():
        # 参数初始化
        roi_size = ch_data.shape[1]  # 假设ROI为方形
        center = (roi_size - 1) / 2

        # 多帧去均值化
        ch_roi = ch_data - np.mean(ch_data, axis=(1, 2), keepdims=True)

        # 计算多帧平均功率谱
        nps_2d_stack = []
        for frame in ch_roi:
            fft = fft2(frame) / roi_size
            fft_shifted = fftshift(fft)
            nps_2d_stack.append(np.abs(fft_shifted)**2)
        nps_2d = np.mean(nps_2d_stack, axis=0)

        # 径向平均
        y, x = np.indices(nps_2d.shape)
        r = np.hypot(x - center, y - center)
        max_radius = int(np.ceil(r.max()))
        r_bins = np.arange(0, max_radius + 1)
        r_idx = np.digitize(r.ravel(), r_bins, right=True) 
        valid_mask = (r_idx >= 0) & (r_idx < len(r_bins))
        nps_1d = np.bincount(r_idx[valid_mask], nps_2d.ravel()[valid_mask]) / np.bincount(r_idx[valid_mask])
    
    nps_results[ch_name] = nps_1d

    # ==================== 4. 可视化 ====================
    plt.figure(figsize=(18, 12))
    
    # 色度噪声热力图
    for i, (ch_name, ch_data) in enumerate(chroma_roi.items()):
        plt.subplot(2, 3, i+1)
        plt.imshow(ch_data[0], cmap='RdBu' if color_space=='LAB' else 'viridis')
        plt.colorbar()
        plt.title(f"{ch_name} Channel (Frame 0)")
        plt.axis('off')

    # 噪声功率谱
    plt.subplot(2, 3, 3)
    for ch_name, nps in nps_results.items():
        plt.plot(r_bins[:-1], nps[:-1], label=f'{ch_name} NPS')
    plt.yscale('log')
    plt.xlabel('Spatial Frequency (cycles/pixel)')
    plt.ylabel('Power Spectral Density')
    plt.title('Chromatic Noise Power Spectrum')
    plt.legend()
    plt.grid(True)

    # 噪声统计表格
    plt.subplot(2, 3, 6)
    cell_text = []
    for ch_name, stats in noise_stats.items():
        row = [
            f"{stats['noise_mean']:.2f}",
            f"{stats['noise_std']:.2f}",
            f"{stats['SNR']:.1f} dB"
        ]
        cell_text.append(row)
    plt.table(cellText=cell_text,
              rowLabels=list(noise_stats.keys()),
              colLabels=['Noise Mean', 'Noise Std', 'SNR'],
              loc='center')
    plt.axis('off')

    plt.tight_layout()
    plt.show()

    return {'noise_stats': noise_stats, 'nps': nps_results}


def output(results):
    print("===== 色彩噪声分析结果 =====")
    for ch, stats in results['noise_stats'].items():
        print(f"[{ch}通道] 噪声均值: {stats['noise_mean']:.2f}, SNR: {stats['SNR']:.1f} dB")

if __name__ == "__main__":
    image_path = ["bot-gm1.png", "bot-gm2.png"]
    results = analyze_chromatic_noise(
        image_path,
        color_space="YUV",
        roi_size=512,
        n_frames=2
    )

    output(results)
    