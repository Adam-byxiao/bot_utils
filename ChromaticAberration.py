import cv2
import numpy as np
import matplotlib.pyplot as plt

def detect_lateral_ca(image_path, edge_threshold=50, roi_size=1000):
    """
    检测横向色差（Lateral Chromatic Aberration）
    :param image_path: 输入图像路径
    :param edge_threshold: 边缘检测阈值（0-255）
    :param roi_size: 分析区域大小（像素）
    :return: 色差偏移量统计结果及可视化图像
    """
    # 1. 读取图像并分离通道
    img = cv2.imread(image_path)

    cv2.namedWindow("Select Edge ROI", cv2.WINDOW_NORMAL)
    roi = cv2.selectROI("Select Edge ROI", img)
    x, y, w, h = map(int, roi)
    roi_img = img[y:y+h, x:x+w]

    if roi_img is None:
        raise FileNotFoundError(f"图像未找到: {image_path}")
    roi_img_rgb = cv2.cvtColor(roi_img, cv2.COLOR_BGR2RGB)
    r, g, b = cv2.split(roi_img_rgb)

    # 2. 在绿色通道中检测边缘
    edges = cv2.Canny(g, edge_threshold, edge_threshold * 2)
    edge_coords = np.column_stack(np.where(edges > 0))
    

    # 3. 随机选择部分边缘区域进行偏移量计算
    #np.random.shuffle(edge_coords)
    #sampled_coords = edge_coords[:roi_size]

    # 4. 计算红、蓝通道相对于绿通道的横向偏移
    offsets = {"red": [], "blue": []}
    window_size = 15  # 互相关窗口大小（奇数）



    for y, x in edge_coords:
        if((x - window_size//2) > 5 and (y - window_size//2) > 5) :
        # 提取绿通道的局部窗口
            g_patch = g[y - window_size//2 : y + window_size//2 + 1,
                        x - window_size//2 : x + window_size//2 + 1]
            if g_patch.shape != (window_size, window_size):
                continue

            # 红通道偏移计算
            r_patch = r[y - window_size//2- 5 : y + window_size//2 + 6,
                        x - window_size//2 - 5 : x + window_size//2 + 6]  # 扩大搜索范围
            res_r = cv2.matchTemplate(r_patch.astype(np.float32), g_patch.astype(np.float32), cv2.TM_CCOEFF_NORMED)
            _, _, _, max_loc_r = cv2.minMaxLoc(res_r)
            offset_r = max_loc_r[0] - 5  # 偏移量（红通道相对于绿通道）

            # 蓝通道偏移计算
            b_patch = b[y - window_size//2 : y + window_size//2 + 1,
                        x - window_size//2 - 5 : x + window_size//2 + 6]
            res_b = cv2.matchTemplate(b_patch.astype(np.float32), g_patch.astype(np.float32), cv2.TM_CCOEFF_NORMED)
            _, _, _, max_loc_b = cv2.minMaxLoc(res_b)
            offset_b = max_loc_b[0] - 5  # 偏移量（蓝通道相对于绿通道）

            offsets["red"].append(offset_r)
            offsets["blue"].append(offset_b)

    # 5. 统计结果
    stats = {
        "red_mean": np.mean(offsets["red"]),
        "red_std": np.std(offsets["red"]),
        "blue_mean": np.mean(offsets["blue"]),
        "blue_std": np.std(offsets["blue"]),
        "max_abs_offset": max(np.max(np.abs(offsets["red"])), np.max(np.abs(offsets["blue"])))
    }

    # 6. 可视化
    plt.figure(figsize=(15, 5))
    
    # 原图与边缘标注
    plt.subplot(1, 3, 1)
    plt.imshow(roi_img_rgb)
    #plt.scatter(edge_coords[:, 1], edge_coords[:, 0], c='yellow', s=5, alpha=0.5)
    plt.title("Original Image with Sampled Edges")
    plt.axis('off')

    # 红通道偏移分布
    plt.subplot(1, 3, 2)
    plt.hist(offsets["red"], bins=20, color='red', alpha=0.7)
    plt.xlabel("Red Channel Offset (pixels)")
    plt.ylabel("Frequency")
    plt.title("Red Channel Offset Distribution")

    # 蓝通道偏移分布
    plt.subplot(1, 3, 3)
    plt.hist(offsets["blue"], bins=20, color='blue', alpha=0.7)
    plt.xlabel("Blue Channel Offset (pixels)")
    plt.ylabel("Frequency")
    plt.title("Blue Channel Offset Distribution")

    plt.tight_layout()
    plt.show()

    return stats

if __name__ == "__main__":
    result = detect_lateral_ca("12233_2.jpg", edge_threshold=50, roi_size=1000)
    print("===== 横向色差分析结果 =====")
    print(f"红通道平均偏移: {result['red_mean']:.2f} px (±{result['red_std']:.2f})")
    print(f"蓝通道平均偏移: {result['blue_mean']:.2f} px (±{result['blue_std']:.2f})")
    print(f"最大绝对偏移量: {result['max_abs_offset']} px")