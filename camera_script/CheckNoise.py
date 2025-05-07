import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft2, fftshift

def analyze_image_noise(image_path, n_frame = 10):

    bright_images = []
    for filename in image_path:
        img = cv2.imread(filename, cv2.IMREAD_GRAYSCALE).astype(np.float32)
        bright_images.append(img)
    bright_stack = np.stack(bright_images, axis=0)

    # 计算时域噪声（标准差）
    temporal_noise = np.std(bright_stack, axis=0)
    random_noise_mean = np.mean(temporal_noise)
    random_noise_std = np.std(temporal_noise)

 # ==================== 3. 噪声功率谱分析 ====================
    # 取单帧亮场图像中心区域（512x512）
    height, width = bright_images[0].shape
    roi = bright_images[0][height//2-256:height//2+256, width//2-256:width//2+256]
    roi = roi - np.mean(roi)  # 去均值化

    # 计算二维FFT和功率谱
    fft = fft2(roi)
    fft_shifted = fftshift(fft)
    nps_2d = np.abs(fft_shifted)**2 / (roi.size)  # 功率谱密度

    # 径向平均得到一维NPS
    y, x = np.indices(nps_2d.shape)
    center = np.array([(x.max()-x.min())/2.0, (y.max()-y.min())/2.0])
    r = np.hypot(x - center[0], y - center[1])
    max_radius = int(np.ceil(r.max()))
    r_bins = np.arange(0, max_radius + 1)
    r_idx = np.digitize(r.ravel(), r_bins)
    nps_1d = np.bincount(r_idx, nps_2d.ravel()) / np.bincount(r_idx)

    # ==================== 4. 结果可视化 ====================
    plt.figure(figsize=(15, 10))

    # 随机噪声热力图
    plt.subplot(2, 2, 1)
    plt.imshow(temporal_noise, cmap='hot')
    plt.colorbar(label='Noise (ADU)')
    plt.title(f"Random Noise Map\nMean: {random_noise_mean:.2f}, Std: {random_noise_std:.2f}")
    plt.axis('off')

    # 固定模式噪声（若有）
    '''if dark_image_path:
        plt.subplot(2, 2, 2)
        plt.imshow(dark_image, cmap='gray')
        plt.title(f"Fixed Pattern Noise (FPN)\nStd: {fpn:.2f}")
        plt.axis('off')'''

    # 噪声功率谱（2D）
    plt.subplot(2, 2, 2)
    plt.imshow(np.log10(nps_2d + 1e-6), cmap='jet')
    plt.colorbar(label='Log10(NPS)')
    plt.title("2D Noise Power Spectrum")
    plt.axis('off')

    # 噪声功率谱（1D径向平均）
    plt.subplot(2, 2, 3)
    plt.plot(r_bins[:-1], nps_1d[:-1])
    plt.yscale('log')
    plt.xlabel("Spatial Frequency (cycles/pixel)")
    plt.ylabel("NPS (ADU²)")
    plt.title("1D Radial NPS")
    plt.grid(True)

    plt.tight_layout()
    plt.show()

    # 返回统计结果
    results = {
        "random_noise_mean": random_noise_mean,
        "random_noise_std": random_noise_std,
        #"fpn": fpn,
        "nps_1d": nps_1d
    }
    return results

def analyze_color_noise(image_path):
    img = cv2.imread(image_path)
    img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    y, u, v = cv2.split(img_yuv)
    
    # 亮度噪声
    noise_y = np.std(y)
    
    # 色度噪声
    noise_u = np.std(u)
    noise_v = np.std(v)
    
    print(f"亮度噪声 (Y): {noise_y:.2f}")
    print(f"色度噪声 (U): {noise_u:.2f}")
    print(f"色度噪声 (V): {noise_v:.2f}")

if __name__ == "__main__":
    image_path = ["bot-gm1.png", "bot-gm2.png"]

    # 示例调用
    results = analyze_image_noise(
        image_path,
        n_frame=2
    )
    print("===== 噪声测试结果 =====")
    print(f"随机噪声均值: {results['random_noise_mean']:.2f} ADU")
    print(f"随机噪声标准差: {results['random_noise_std']:.2f} ADU")
    #print(f"固定模式噪声: {results['fpn']:.2f} ADU")