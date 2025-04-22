import cv2
import numpy as np
import matplotlib.pyplot as plt

#现有24色卡标准参数
basic_24color_RBG = [[121, 85, 72], [215, 169, 147], [83, 133, 160], [89, 110, 68], [128, 148, 181], [119, 218, 192], 
                    [154, 145, 47], [61, 95, 163], [161, 94, 104], [86, 64, 112], [170, 195, 72], [205, 183, 33],
                    [49, 60, 138], [70, 152, 82], [136, 33, 33], [174, 204, 18], [171, 88, 145], [4, 133, 165],
                    [253, 253, 254], [207, 210, 208],[164, 164, 165], [127, 127, 128], [86, 86, 87], [55, 56, 55]]

basic_24color_S = [103,81, 123, 97, 75, 116,
                   177, 160, 106, 109, 161, 214,
                   164, 138, 193, 233, 124, 249, 
                   1, 4, 2, 2, 3, 5]



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

def ROI(image_path):
    #截取24色卡的roi区域
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at {image_path}")
    
    cv2.namedWindow("Select Edge ROI", cv2.WINDOW_NORMAL)
    roi = cv2.selectROI("Select Edge ROI", image)
    x, y, w, h = map(int, roi)
    #roi_image = image[y:y+h, x:x+w] 
    roi_image = image[y:y+h, x:x+w]   

    return roi_image, w, h


def RGB2HSV(roi, w, h):
    # 读取图像并转换到HSV空间

    #获取24色块区域数组
    delta = 1 / 24

    PiecesList = []
    w_list = [1, 3, 5, 7, 9, 11]
    h_list = [-1, -3, -5, -7]

    ColorList = []

    for j in h_list:
        for i in w_list:
            #point_x = x + w * (i / 12)
            #point_y = y + h * (j / 8)
            point_x = w * (i / 12)
            point_y = -h * (j / 8)
            color_piece = roi[int(point_y-delta*h):int(point_y+delta*h), int(point_x-delta*w):int(point_x+delta*w)]
            hsv_image = cv2.cvtColor(color_piece, cv2.COLOR_BGR2HSV)
            saturation = hsv_image[:, :, 1]
            ColorList.append(saturation[0:int(delta*2*h-1), 0:int(delta*2*w-1)])
            # 计算统计指标
            stats = {
                "mean": np.mean(saturation),
                "median": np.median(saturation),
                "max": np.max(saturation),
                "min": np.min(saturation),
                "std": np.std(saturation)
            }
            PiecesList.append(stats)

    v_pic = ColorList[0]
    for i in range(1, 6):
        v_pic = np.hstack((v_pic, ColorList[i]))
        
    for i in range(1, 4):
        h_pic = ColorList[i*6]
        for j in range(1, 6):
            h_pic = np.hstack((h_pic, ColorList[i*6 + j]))
        v_pic = np.vstack((v_pic, h_pic))    

    return PiecesList, v_pic

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


def output_saturation(result, v_pic, roi):
    i = 0
    total_mean = 0
    total_std = 0
    for stats in result:
        total_mean += abs(stats['mean'] - int(basic_24color_S[i]))
        total_std += (stats['std'] + abs((stats['mean'] - int(basic_24color_S[i]))))
        i = i + 1
        
    total_mean = total_mean / (len(result))
    total_std = total_std / (len(result))

    print("===== 色彩饱和度分析结果" + str(i) + " =====")
    print(f"色彩饱和度均值差: {total_mean:.2f}")
    print(f"色彩饱和度标准差: {total_std:.2f}")

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]

    # 可视化
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.imshow(v_pic, cmap='hot')
    plt.title("Saturation Heatmap")
    plt.colorbar()
    plt.axis('off')

    # 直方图
    plt.subplot(1, 2, 2)
    plt.hist(v_pic.ravel(), bins=50, range=(0, 255), color='blue', alpha=0.7)
    plt.title("Saturation Histogram")
    plt.xlabel("Saturation Value")
    plt.ylabel("Frequency")
    plt.grid(True)

    plt.tight_layout()
    plt.show()

def main(filepath):
    '''result = []
    Hotpot = []


    for file in filepath:
        stat, saturation = analyze_saturation(file)
        result.append(stat)
        Hotpot.append(saturation)
        
        
    output(result, Hotpot)'''

    roi, w, h = ROI(filepath)
    print(w, h)
    stats, v_pic = RGB2HSV(roi, w, h)

    output_saturation(stats, v_pic, roi)
    


if __name__ == "__main__":
    #filepath = ["24color_SNR.jpg", "24color_SNR.jpg"]
    #main(filepath)

    filepath = "24color_SNR.jpg"
    main(filepath)