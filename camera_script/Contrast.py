import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import kurtosis, skew

def analyze_contrast(image_path, block_size=32, method='RMS'):
    """
    图像对比度系统性分析
    :param image_path: 输入图像路径
    :param block_size: 局部对比度分析的窗口大小
    :param method: 局部对比度算法（'RMS'或'Weber'）
    :return: 对比度统计结果及可视化图表
    """
    # ==================== 1. 数据准备 ====================
    # 读取图像并转换为灰度图
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"图像未找到: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_float = gray.astype(np.float32) / 255.0  # 归一化到[0,1]

    # ==================== 2. 全局对比度分析 ====================
    # 动态范围 (DR)
    dr = gray.max() - gray.min()
    
    # Michelson对比度（适用于周期性图像）
    michelson = (gray.max() - gray.min()) / (gray.max() + gray.min() + 1e-6)
    
    # RMS对比度
    rms_global = np.std(gray_float)
    
    # 直方图统计
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist /= hist.sum()  # 归一化
    kurt = kurtosis(hist.ravel())
    skewness = skew(hist.ravel())

    # ==================== 3. 局部对比度分析 ====================
    def local_contrast(image, window_size, method='RMS'):
        h, w = image.shape
        contrast_map = np.zeros_like(image)
        pad = window_size // 2
        padded = cv2.copyMakeBorder(image, pad, pad, pad, pad, cv2.BORDER_REFLECT)
        
        for y in range(h):
            for x in range(w):
                window = padded[y:y+window_size, x:x+window_size]
                if method == 'RMS':
                    # RMS对比度：窗口标准差
                    contrast_map[y, x] = np.std(window)
                elif method == 'Weber':
                    # Weber对比度：(I_max - I_min) / I_avg
                    i_max = window.max()
                    i_min = window.min()
                    i_avg = window.mean()
                    contrast_map[y, x] = (i_max - i_min) / (i_avg + 1e-6)
        return contrast_map

    # 计算局部对比度图
    lc_map = local_contrast(gray_float, block_size, method)
    lc_mean = np.mean(lc_map)
    lc_std = np.std(lc_map)

    # ==================== 4. 可视化 ====================
    plt.figure(figsize=(18, 12))
    
    # 原图与灰度图
    plt.subplot(2, 3, 1)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    plt.axis('off')
    
    plt.subplot(2, 3, 2)
    plt.imshow(gray, cmap='gray')
    plt.title("Grayscale Image")
    plt.axis('off')

    # 直方图与统计
    plt.subplot(2, 3, 3)
    plt.plot(hist, color='black')
    plt.fill_between(np.arange(256), hist.ravel(), alpha=0.3)
    plt.title(f"Histogram\nKurtosis: {kurt:.2f}, Skewness: {skewness:.2f}")
    plt.xlabel("Pixel Value")
    plt.ylabel("Frequency")
    plt.grid(True)

    # 局部对比度热图
    plt.subplot(2, 3, 4)
    plt.imshow(lc_map, cmap='hot')
    plt.colorbar(label='Local Contrast')
    plt.title(f"Local Contrast Map ({method})\nMean: {lc_mean:.3f}, Std: {lc_std:.3f}")
    plt.axis('off')

    # 全局对比度指标表格
    plt.subplot(2, 3, 5)
    cell_text = [
        [f"{dr}", "0-255"],
        [f"{michelson:.3f}", "(Lmax-Lmin)/(Lmax+Lmin)"],
        [f"{rms_global:.3f}", "标准差"]
    ]
    plt.table(cellText=cell_text,
              rowLabels=["Dynamic Range", "Michelson Contrast", "RMS Contrast"],
              colLabels=["Value", "Formula"],
              loc='center')
    plt.axis('off')

    plt.tight_layout()
    plt.show()

    return {
        "dynamic_range": dr,
        "michelson_contrast": michelson,
        "rms_contrast": rms_global,
        "histogram_kurtosis": kurt,
        "histogram_skewness": skewness,
        "local_contrast_mean": lc_mean,
        "local_contrast_std": lc_std
    }

def output(results):
    print("===== 对比度分析结果 =====")
    print(f"动态范围: {results['dynamic_range']} (0-255)")
    print(f"Michelson对比度: {results['michelson_contrast']:.3f}")
    print(f"RMS全局对比度: {results['rms_contrast']:.3f}")
    print(f"直方图峰度: {results['histogram_kurtosis']:.2f}")
    print(f"直方图偏度: {results['histogram_skewness']:.2f}")
    print(f"局部对比度均值: {results['local_contrast_mean']:.3f}")

if __name__ == "__main__":
    results = analyze_contrast(
        image_path="roi_1.png",
        block_size=32,
        method='RMS'
    )
    
    output(results)