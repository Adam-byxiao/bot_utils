import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy import fftpack
from scipy.ndimage import uniform_filter1d
from scipy.optimize import curve_fit

# ================= 核心SFR计算函数 =================

def sfr_calculation(roi, oversampling=4, pixel_size=None):
    """
    执行完整的SFR分析流程
    :param roi: 包含斜边的ROI区域（灰度图像）
    :param oversampling: 超采样倍数（通常为4）
    :param pixel_size: 物理像素尺寸（mm/px），用于转换为cycles/mm
    :return: MTF曲线数据及关键指标
    """
    # 步骤1：边缘检测与角度计算
    angle_deg = calculate_edge_angle(roi)
    
    # 步骤2：图像旋转对齐
    aligned = rotate_image(roi, angle_deg)
    
    # 步骤3：超采样ESF生成
    esf = generate_super_res_esf(aligned, oversampling)
    
    # 步骤4：LSF计算
    lsf = calculate_lsf(esf)
    
    # 步骤5：MTF计算
    freq, mtf = compute_mtf(lsf, pixel_size)
    
    # 步骤6：关键指标计算
    mtf50 = find_mtf50(freq, mtf)
    mtf50_p = find_mtf_value(freq, mtf, 0.5)
    
    return {
        'esf': esf,
        'lsf': lsf,
        'freq': freq,
        'mtf': mtf,
        'mtf50': mtf50,
        'mtf50_p': mtf50_p
    }

# ================= 子函数实现 =================

def calculate_edge_angle(image, blur_size=5):
    """
    使用梯度投影法计算边缘角度
    """
    # 预处理：高斯模糊
    blurred = cv2.GaussianBlur(image, (blur_size, blur_size), 0)
    
    # 计算梯度
    grad_x = cv2.Scharr(blurred, cv2.CV_64F, 1, 0)
    grad_y = cv2.Scharr(blurred, cv2.CV_64F, 0, 1)
    
    # 构建角度投影矩阵
    angles = np.arctan2(grad_y, grad_x)
    angle_hist, bins = np.histogram(angles, bins=180, range=(-np.pi/2, np.pi/2))
    
    # 找到主角度
    main_angle = np.degrees(bins[np.argmax(angle_hist)])
    print(main_angle)
    return main_angle

def rotate_image(image, angle):
    """
    亚像素级精度的图像旋转
    """
    h, w = image.shape
    center = (w/2, h/2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC + cv2.WARP_FILL_OUTLIERS)

def generate_super_res_esf(aligned, oversampling):
    """
    生成超采样ESF曲线
    """
    # 垂直投影分析
    column_means = aligned.mean(axis=0)
    edge_pos = np.argmax(np.gradient(column_means))
    
    # 提取边缘区域（左右各32像素）
    edge_region = aligned[:, max(0, edge_pos-32):edge_pos+32]
    
    # 超采样处理
    esf = []
    for row in edge_region:
        # 三次样条插值实现4倍超采样
        interp_row = cv2.resize(row, (len(row)*oversampling, 1), 
                             interpolation=cv2.INTER_CUBIC)
        esf.append(interp_row)
    
    return np.mean(esf, axis=0)

def calculate_lsf(esf, window='hann'):
    """
    计算LSF并进行窗函数处理
    """
    # 差分计算导数（中心差分法）
    lsf = np.convolve(esf, [1, 0, -1], mode='valid') / 2.0
    
    # 窗函数应用
    if window == 'hann':
        window = np.hanning(len(lsf))
    elif window == 'hamming':
        window = np.hamming(len(lsf))
    else:
        window = np.ones(len(lsf))
    
    return lsf * window

def compute_mtf(lsf, pixel_size=None):
    """
    计算MTF曲线
    """
    # FFT计算
    mtf = np.abs(fftpack.fft(lsf))
    mtf = mtf[:len(mtf)//2]  # 取单边频谱
    mtf /= mtf.max()  # 归一化
    
    # 频率轴计算
    N = len(lsf)
    freq = np.fft.fftfreq(N)[:N//2]
    
    # 物理单位转换
    if pixel_size is not None:
        freq /= pixel_size  # cycles/mm
    else:
        freq *= 1000  # cycles/pixel ×1000
    
    return freq, mtf

def find_mtf50(freq, mtf):
    """
    精确计算MTF50值（包含插值）
    """
    # 寻找交叉点
    cross_idx = np.where(mtf < 0.5)[0][0]
    x = [freq[cross_idx-1], freq[cross_idx]]
    y = [mtf[cross_idx-1], mtf[cross_idx]]
    
    # 线性插值
    slope = (y[1] - y[0]) / (x[1] - x[0])
    return x[0] + (0.5 - y[0]) / slope

def find_mtf_value(freq, mtf, threshold=0.5):
    # 步骤1：寻找交叉点
    cross_idx = np.argmax(mtf < threshold)
    
    # 边界条件处理
    if cross_idx == 0:  # 未找到交叉点
        return 0.0 if threshold > mtf[0] else freq[-1]
    
    # 步骤2：线性插值
    x = [freq[cross_idx-1], freq[cross_idx]]
    y = [mtf[cross_idx-1], mtf[cross_idx]]
    slope = (y[1] - y[0]) / (x[1] - x[0])
    return x[0] + (threshold - y[0]) / slope

# ================= 可视化与主流程 =================

def plot_sfr_results(results):
    """
    专业级可视化输出
    """
    plt.figure(figsize=(15, 8))
    
    # ESF子图
    plt.subplot(2, 2, 1)
    plt.plot(results['esf'], 'b-', linewidth=1)
    plt.title('Edge Spread Function (4x Oversampled)')
    plt.xlabel('Position (0.25 pixel steps)')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # LSF子图
    plt.subplot(2, 2, 2)
    plt.plot(results['lsf'], 'r-', linewidth=1)
    plt.title('Line Spread Function')
    plt.xlabel('Position')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # MTF曲线
    plt.subplot(2, 1, 2)
    plt.semilogx(results['freq'], 20*np.log10(results['mtf']), 'g-', linewidth=2)
    plt.axhline(-3, color='k', linestyle='--', label='MTF50')
    plt.axvline(results['mtf50'], color='b', linestyle=':', 
               label=f'MTF50 = {results["mtf50"]:.2f} cyc/mm')
    plt.title('SFR/MTF Curve')
    plt.xlabel('Spatial Frequency (cycles/mm)')
    plt.ylabel('Modulation (dB)')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.show()

def main(image_path):
    # 图像加载与预处理
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.GaussianBlur(img, (3,3), 0)
    
    # 手动选择ROI
    cv2.namedWindow("Select Edge ROI", cv2.WINDOW_NORMAL)
    roi = cv2.selectROI("Select Edge ROI", img)
    x, y, w, h = map(int, roi)
    roi_img = img[y:y+h, x:x+w]
    
    # SFR计算（假设像素尺寸为0.01mm/px）
    results = sfr_calculation(roi_img, pixel_size=0.01)
    
    # 结果输出
    print(f"MTF50: {results['mtf50']:.2f} cycles/mm")
    print(f"MTF50 Position: {results['mtf50_p']:.2f} cyc/pixel")
    
    # 可视化
    plot_sfr_results(results)

if __name__ == "__main__":
    main("sfr_test.gif")