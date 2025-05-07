import cv2
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import fftpack
from scipy import stats

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

    # 步骤5： SFR计算
    sfr = calculate_sfr(lsf)

    # 步骤6：MTF计算
    freq, mtf = calculate_mtf(sfr)

    # 步骤7：MTF50 & MTF50p 指标计算
    mtf50 = find_mtf50(freq, mtf)
    mtf50_p = find_mtf_value(freq, mtf, 0.5)

    # 步骤8： 标准化MTF计算
    standard_mtf_data, standard_freq_at_50_mtf, mtf_equal, k_sharp, sharpening_radius = get_standard_mtf_data(mtf, mtf50)
    
    return {
        'esf': esf,
        'lsf': lsf,
        'freq': freq,
        'mtf': mtf,
        'mtf50': mtf50,
        'mtf50_p': mtf50_p,
        'standard_mtf_data': standard_mtf_data,
        'standard_freq_at_50_mtf':standard_freq_at_50_mtf,
        'mtf_equal':mtf_equal,
        'k_sharp':k_sharp,
        'sharpening_radius':sharpening_radius,
    }

# ================= 子函数实现 =================

def calculate_edge_angle(image, blur_size=3):
    """
    使用梯度投影法计算边缘角度
    """
    # 预处理：高斯模糊
    #blurred = cv2.GaussianBlur(image, (blur_size, blur_size), 0)
    blurred = image
    
    # 计算梯度
    grad_x = cv2.Scharr(blurred, cv2.CV_64F, 1, 0)
    grad_y = cv2.Scharr(blurred, cv2.CV_64F, 0, 1)
    
    # 构建角度投影矩阵
    angles = np.arctan2(grad_y, grad_x)
    angle_hist, bins = np.histogram(angles, bins=180, range=(-np.pi/2, np.pi/2))
    
    # 找到主角度
    main_angle = np.degrees(bins[np.argmax(angle_hist)])
    return main_angle

def rotate_image(image, angle):
    """
    亚像素级精度的图像旋转
    """
    h, w = image.shape
    center = (w/2, h/2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC + cv2.WARP_FILL_OUTLIERS)

def gamma_correction(image):
    gamma_val = 0.5
    gamma_table = np.array([np.power(x / 255.0, 1/gamma_val) * 255.0 for x in range(256)]).astype("uint8")
    return cv2.LUT(image, gamma_table)

def generate_super_res_esf(aligned, oversampling):

    roi = aligned.astype(np.uint32)
    edge_idx_per_line = []

    for line in roi:
        max_diff=0
        last_px = line[0]
        max_idx = idx = 0
        for px in line:
            diff = abs(int(last_px) - int(px))
            if diff > max_diff:
               max_diff = diff
               max_idx = idx
            last_px = px
            idx += 1
        edge_idx_per_line.append(max_idx)

    slope, intercept, r_value, p_value, std_err = stats.linregress(list(range(len(edge_idx_per_line))), edge_idx_per_line)
    inspection_width = 1
    while inspection_width <= len(roi[0]):
        inspection_width *= 2
    inspection_width = inspection_width//2
    half_inspection_width = inspection_width/2
    print(inspection_width, oversampling, (inspection_width*oversampling + 2))
    esf_sum = [0] * (inspection_width*oversampling + 2)
    hit_count = [0] * (inspection_width*oversampling + 2)    
    x = y = 0
    for line in roi:
        for px in line:
           # only calculate the pixels in the inspection width
           if abs(x-float(y*slope+intercept)) <= half_inspection_width+1/oversampling:
               idx = int((x-(y*slope+intercept)+half_inspection_width)*oversampling+1)
               esf_sum[idx] = esf_sum[idx] + px
               hit_count[idx] += 1
           x += 1
        y += 1
        x = 0
    hit_count = [ 1 if c == 0 else c for c in hit_count ]
    esf_data = np.divide(esf_sum, hit_count).tolist()
    print(len(esf_data))
    return esf_data
    
def calculate_lsf(esf, window='hamming'):
    """
    计算LSF并进行窗函数处理
    """
    #差分计算导数（中心差分法）
    
    lsf = np.convolve(esf, [1, 0, -1], mode='valid') / 2.0
    #lsf = np.gradient(esf)
    # 窗函数应用
    if window == 'hann':
        window = np.hanning(len(lsf))
    elif window == 'hamming':
        window = np.hamming(len(lsf))
    else:
        window = np.ones(len(lsf))
    
    return lsf * window

def calculate_sfr(lsf):
    raw_sfr = np.abs(fftpack.fft(lsf)).tolist()
    sfr_base = raw_sfr[0]
    sfr_data = [ d/sfr_base for d in raw_sfr]
    #print(sfr_data)
    return sfr_data

def calculate_mtf(sfr):
    mtf_data = [0] * int(len(sfr)/2)
    idx = 0
    for sfr_data in sfr[0:len(mtf_data)]:
        freq = idx / (len(mtf_data) - 1)
        if freq == 0:
            mtf_data[idx] = sfr_data
        else:
            mtf_data[idx] = sfr_data * (np.pi * freq/2)/np.sin(np.pi * freq/2)
            print((np.pi * freq/2), np.sin(np.pi * freq/2), (np.pi * freq/2)/np.sin(np.pi * freq/2))
        idx += 1
    #print(mtf_data)
    #print(sfr)
    freq = [f/(len(mtf_data)) for f in range(len(mtf_data))]
    #print(len(freq))
    mtf = np.asarray(mtf_data)
    return freq, mtf

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
    print(type(mtf))
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


def get_standard_mtf_data(mtf_data, freq_at_50_mtf, oversampling_rate = 4):
        if freq_at_50_mtf < 0.2:
            freq_equal = 0.6 * freq_at_50_mtf
            sharpening_radius = 3
        else:
            freq_equal = 0.15
            sharpening_radius = 2
        idx_equal = freq_equal * (len(mtf_data)-1)
        mtf_equal = mtf_data[int(idx_equal)] + (mtf_data[int(idx_equal)+1]-mtf_data[int(idx_equal)])*(idx_equal-idx_equal//1)
        last_sharpening_radius = 0
        while last_sharpening_radius != sharpening_radius:
            last_sharpening_radius = sharpening_radius
            # calculate sharpness coefficient
            #     MTF(system) = MTF(standard) * MTF(sharp) = MTF(system) * (1 - ksharp * cos(2*PI*f*R/dscan)) / (1- ksharp)
            #     When MTF(sharp) = 1, ksharp = (1 - MTF(system)) / (cos(2*PI*f*R/dscan) - MTF(system))
            k_sharp = (1-mtf_equal)/(np.cos(2*np.pi*freq_equal*sharpening_radius)-mtf_equal)
            # standardized sharpening
            standard_freq_at_50_mtf = 0
            idx = 0
            standard_mtf_data = [0] * len(mtf_data)
            for mtf in mtf_data:
                # frequency is from 0 to 1
                freq = idx / (len(mtf_data)-1)
                standard_mtf_data[idx] = mtf/((1-k_sharp*np.cos(2*np.pi*freq*sharpening_radius))/(1-k_sharp))
                # get MTF50
                if standard_freq_at_50_mtf == 0 and standard_mtf_data[idx] < 0.5:
                    standard_freq_at_50_mtf = (idx-1+(0.5-standard_mtf_data[idx])/(standard_mtf_data[idx-1]-standard_mtf_data[idx]))/(len(standard_mtf_data)-1)
                    # If the difference of the original frequency at MTF50 and the frequency at MTF50(corr) is larger than 0.04,
                    # it should increase the radius by one and recalculate the ksharp.
                    if (abs(standard_freq_at_50_mtf-freq_at_50_mtf) > 0.04):
                        sharpening_radius += 1
                        break
                idx += 1
        return standard_mtf_data, standard_freq_at_50_mtf, mtf_equal, k_sharp, sharpening_radius

# ================= 可视化与主流程 =================

def plot_sfr_results(results):
    
    #可视化输出
    
    plt.figure(figsize=(10, 8))
    
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
    #plt.semilogx(results['freq'], 20*np.log10(results['mtf']), 'g-', linewidth=2)
    plt.plot(results['freq'], results['standard_mtf_data'], 'g-', linewidth=2)
    #plt.axhline(-3, color='k', linestyle='--', label='MTF50')
    plt.axvline(results['mtf50'], ymin = 0, ymax = 0.5, color='b', linestyle=':', 
               label=f'MTF50 = {results["mtf50"]:.2f} Cy/Pxl')
    plt.title('SFR/MTF Curve')
    plt.xlabel('Spatial Frequency (Cy/Pxl)')
    plt.ylabel('Modulation (dB)')
    font1 = {'color': 'darkred', 'weight': 'normal', 'size': 12, }
    
    font2 = {'color': 'red','weight': 'light', 'size': 10 }


    plt.text(0, 0.3, "MTF50 = %.2f Cy/Pxl" % (results["mtf50"]), font1)
    plt.text(0, 0.2, "MTF50p = %.2f Cy/Pxl" % (results["mtf50_p"]), font1)
    if results["mtf_equal"] - 1 > 0:
        sharpenss = "Oversharpenss = %.1f" % (results["mtf_equal"] * 100 - 100) + "%"
    else:
        sharpenss = "Undersharpenss = %.1f" % (100 - results["mtf_equal"] * 100) + "%"
    plt.text(0, 0.1, sharpenss, font2)
    plt.legend()
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.show()

def output(results):
    print(f"MTF50: {results['mtf50']:.2f} cycles/mm")
    print(f"MTF50 Position: {results['mtf50_p']:.2f} cyc/pixel")
    print((f"standard_freq_at_50_mtf: {results['standard_freq_at_50_mtf']:.2f} cycles/mm"))
    print((f"mtf_equal: {results['mtf_equal']:.2f} cycles/mm"))
    print((f"k_sharp: {results['k_sharp']:.2f} cycles/mm"))

def main(image_path):
    # 图像加载与预处理
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    #img = gamma_correction(img)
    #img = cv2.GaussianBlur(img, (3,3), 0)
    
    # 手动选择ROI
    cv2.namedWindow("Select Edge ROI", cv2.WINDOW_NORMAL)
    roi = cv2.selectROI("Select Edge ROI", img)
    x, y, w, h = map(int, roi)
    roi_img = img[y:y+h, x:x+w]
    #roi_img_32 = roi_img.astype(np.uint32)
    
    # SFR计算（假设像素尺寸为0.01mm/px）
    results = sfr_calculation(roi_img, pixel_size=0.01)
    
    # 结果输出
    print(f"MTF50: {results['mtf50']:.2f} cycles/mm")
    print(f"MTF50 Position: {results['mtf50_p']:.2f} cyc/pixel")
    print((f"standard_freq_at_50_mtf: {results['standard_freq_at_50_mtf']:.2f} cycles/mm"))
    print((f"mtf_equal: {results['mtf_equal']:.2f} cycles/mm"))
    print((f"k_sharp: {results['k_sharp']:.2f} cycles/mm"))

    output(results)
    # 可视化
    plot_sfr_results(results)

if __name__ == "__main__":
    main("12233_3.jpg")
