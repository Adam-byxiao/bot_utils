import cv2
import numpy as np
import matplotlib.pyplot as plt

def analyze_saturation(image_path):
    # 读取图像并转换到HSV空间
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at {image_path}")
    
    cv2.namedWindow("Select Edge ROI", cv2.WINDOW_NORMAL)
    roi = cv2.selectROI("Select Edge ROI", image)
    x, y, w, h = map(int, roi)
    #roi_image = image[y:y+h, x:x+w] 
    roi_image = image[y:y+h, x:x+w]     
    
    hsv_image = cv2.cvtColor(roi_image, cv2.COLOR_BGR2HSV)
    saturation = hsv_image[:, :, 1]

    # 计算统计指标
    stats = {
        "mean": np.mean(saturation),
        "median": np.median(saturation),
        "max": np.max(saturation),
        "min": np.min(saturation),
        "std": np.std(saturation)
    }
    return stats, saturation

def output(result, saturation):
    # 打印结果
    i = 0
    for stats in result:
        i += 1
        print("===== 色彩饱和度分析结果" + str(i) + " =====")
        print(f"均值: {stats['mean']:.2f}")
        print(f"中位数: {stats['median']:.2f}")
        print(f"最大值: {stats['max']}")
        print(f"最小值: {stats['min']}")
        print(f"标准差: {stats['std']:.2f}")

    m = len(result)

    # 可视化
    plt.figure(figsize=(10, 4 * m))
    
    '''# 原图与饱和度热力图
    plt.subplot(1, 2, 1)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    plt.axis('off')'''
    
    for i in range(m):
        print(m, 2, i * 2 +1)
        plt.subplot(m, 2, i * 2 +1)
        plt.imshow(saturation[i], cmap='hot')
        plt.title("Saturation Heatmap")
        plt.colorbar()
        plt.axis('off')

        # 直方图
        plt.subplot(m, 2, i * 2 +2)
        plt.hist(saturation[i].ravel(), bins=50, range=(0, 255), color='blue', alpha=0.7)
        plt.title("Saturation Histogram")
        plt.xlabel("Saturation Value")
        plt.ylabel("Frequency")
        plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def main(filepath):
    result = []
    Hotpot = []

    for file in filepath:
        stat, saturation = analyze_saturation(file)
        result.append(stat)
        Hotpot.append(saturation)

    output(result, Hotpot)


if __name__ == "__main__":
    filepath = ["24color_SNR.jpg", "24color_SNR.jpg"]
    main(filepath)