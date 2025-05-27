# encoding: utf-8
import cv2
import numpy as np
import matplotlib.pyplot as plt



def ImageLAB(image):

    # 转换为LAB颜色空间（更适合边缘检测）
    image_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(image_lab)

    # 计算亮度梯度（使用Sobel算子）
    gradient_x = cv2.Sobel(l_channel, cv2.CV_64F, 1, 0, ksize=3)
    gradient_y = cv2.Sobel(l_channel, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
    gradient_magnitude = np.uint8(255 * gradient_magnitude / gradient_magnitude.max())

    # 二值化边缘掩膜
    _, edge_mask = cv2.threshold(gradient_magnitude, 50, 255, cv2.THRESH_BINARY)

    return edge_mask

def PurpleDetection(image, edge_mask):
    
    # 使用高斯模糊降噪
    image_blur = cv2.GaussianBlur(image, (5, 5), 0)

    # 分离RGB通道
    r_channel = image_blur[:, :, 0]
    g_channel = image_blur[:, :, 1]
    b_channel = image_blur[:, :, 2]

    # 计算紫色异常区域（紫边通常表现为R和B通道高，G通道低）
    purple_mask = np.zeros_like(edge_mask)
    purple_ratio = (r_channel.astype(float) + b_channel.astype(float)) / (g_channel.astype(float) + 1e-6)  # 防止除零
    purple_mask[(edge_mask > 0) & (purple_ratio > 2.0) & (b_channel > 150)] = 255  # 阈值可调

    # 标注紫边区域
    contours, _ = cv2.findContours(purple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    image_marked = image.copy()
    cv2.drawContours(image_marked, contours, -1, (255, 0, 0), 2)  # 用蓝色轮廓标记紫边

    # 计算紫边面积占比
    total_pixels = image.shape[0] * image.shape[1]
    purple_area = np.sum(purple_mask) / 255
    purple_ratio = purple_area / total_pixels * 100
    

    return purple_mask, image_marked, purple_ratio

'''
# 读取图像并转为RGB格式
image = cv2.imread("brio-local.jpg")
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# 转换为LAB颜色空间（更适合边缘检测）
image_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
l_channel, a_channel, b_channel = cv2.split(image_lab)

# 使用高斯模糊降噪
image_blur = cv2.GaussianBlur(image_rgb, (5, 5), 0)

# 计算亮度梯度（使用Sobel算子）
gradient_x = cv2.Sobel(l_channel, cv2.CV_64F, 1, 0, ksize=3)
gradient_y = cv2.Sobel(l_channel, cv2.CV_64F, 0, 1, ksize=3)
gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
gradient_magnitude = np.uint8(255 * gradient_magnitude / gradient_magnitude.max())

# 二值化边缘掩膜
_, edge_mask = cv2.threshold(gradient_magnitude, 50, 255, cv2.THRESH_BINARY)

# 分离RGB通道
r_channel = image_rgb[:, :, 0]
g_channel = image_rgb[:, :, 1]
b_channel = image_rgb[:, :, 2]

# 计算紫色异常区域（紫边通常表现为R和B通道高，G通道低）
purple_mask = np.zeros_like(edge_mask)
purple_ratio = (r_channel.astype(float) + b_channel.astype(float)) / (g_channel.astype(float) + 1e-6)  # 防止除零
purple_mask[(edge_mask > 0) & (purple_ratio > 2.0) & (b_channel > 150)] = 255  # 阈值可调

# 标注紫边区域
contours, _ = cv2.findContours(purple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
image_marked = image_rgb.copy()
cv2.drawContours(image_marked, contours, -1, (255, 0, 0), 2)  # 用蓝色轮廓标记紫边

# 计算紫边面积占比
total_pixels = image.shape[0] * image.shape[1]
purple_area = np.sum(purple_mask) / 255
purple_ratio = purple_area / total_pixels * 100

# 输出结果
print(f"紫边区域占比: {purple_ratio:.2f}%")

'''

def main(filename):
    image1 = cv2.imread(filename[0])

    mask1 = ImageLAB(image1)
    image_rgb1 = cv2.cvtColor(image1, cv2.COLOR_BGR2RGB)
    purple_mask1, image_marked1, purple_ratio1 = PurpleDetection(image_rgb1, mask1)


    image2 = cv2.imread(filename[1])

    mask2 = ImageLAB(image2)
    image_rgb2 = cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
    purple_mask2, image_marked2, purple_ratio2 = PurpleDetection(image_rgb2, mask2)



    # 输出结果
    print(f"Bot紫边区域占比: {purple_ratio1:.2f}%")
    print(f"Brio紫边区域占比: {purple_ratio2:.2f}%")

    # 显示结果
    plt.figure(figsize=(15, 9))
    plt.subplot(2, 3, 1)
    plt.imshow(image_rgb1)
    plt.title("Bot Original Image")
    plt.axis('off')
    plt.text(300, 1250, "Bot紫边区域占比：%.2f" % (purple_ratio1) + "%", fontproperties = 'Microsoft YaHei', color = 'darkred', fontsize = 14)
    

    plt.subplot(2, 3, 2)
    plt.imshow(purple_mask1, cmap='gray')
    plt.title("Bot Purple Fringe Mask")
    plt.axis('off')

    plt.subplot(2, 3, 3)
    plt.imshow(image_marked1)
    plt.title("Bot Marked Purple Fringes")
    plt.axis('off')
    

    plt.subplot(2, 3, 4)
    plt.imshow(image_rgb2)
    plt.title("Brio Original Image")
    plt.axis('off')
    plt.text(300, 1250, "竞品紫边区域占比：%.2f " % (purple_ratio2) + "%", fontproperties = 'Microsoft YaHei', color = 'darkred', fontsize = 14)

    plt.subplot(2, 3, 5)
    plt.imshow(purple_mask2, cmap='gray')
    plt.title("Brio Purple Fringe Mask")
    plt.axis('off')

    plt.subplot(2, 3, 6)
    plt.imshow(image_marked2)
    plt.title("Brio Marked Purple Fringes")
    plt.axis('off')
    

    plt.suptitle("Bot与竞品的紫边表现对比", fontproperties = 'Microsoft YaHei', fontsize = 20, y = 0.95)
    plt.show()

if __name__ == "__main__":
    filename = ["D:\\work\\image\\subject\\Subjective-HDR-20250516T065214Z-1-001\\Subjective-HDR\\0-local\\bot_local_hdr.jpg", "D:\\work\\image\\subject\\Subjective-HDR-20250516T065214Z-1-001\\Subjective-HDR\\0-local\\Loji_local_hdr.jpg"]
    main(filename)