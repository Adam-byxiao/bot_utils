import cv2
import math
import numpy as np
import matplotlib.pyplot as plt



def separate_gray(roi, x, y, w, h, num):
    deltax = 1 / (num * 3)
    deltay = 1 / 3
    PiecesList = []
    w_list = [i*2+1 for i in range(num)]
    for i in w_list:
        point_x = w * (i / (num * 2))
        point_y = -h * (1 / 2)
        color_piece = roi[int(point_y-deltay*h):int(point_y+deltay*h), int(point_x-deltax*w):int(point_x+deltax*w)]
        PiecesList.append(color_piece)

    return PiecesList


def HDR_calculation(pieces):
    hdr = 0
    gray_mean = []
    i = 0
    for k in range(len(pieces)):
        point_mean = np.mean(pieces[k])
        gray_mean.append(point_mean)
        i = i+1

    hdr = gray_mean[0] - gray_mean[len(gray_mean)-1]

    return hdr, gray_mean

def GrayList_Detection(graylist):
    grayrange = graylist[0] - graylist[len(graylist)-1]
    k = 255/grayrange
    for i in range(len(graylist)):
        graylist[i] -= graylist[len(graylist)-1]
        graylist[i] = graylist[i] * k
    print(graylist)
    print(len(graylist))
    gray_difference = [graylist[i] - graylist[i-1] for i in range(1, 20)]
    print(gray_difference)
    old = gray_difference[0]
    #k1:当灰度数组的差分值第一次小于8时返回该值 k2：当灰度数组的差分值第一次不是递减是返回该值
    k1 = 1
    k2 = 1
    k3 = 1
    print(gray_difference)
    for i in range(1, len(gray_difference)):
        if(old - gray_difference[i]) < 0:
            break
        else:
            k2 = k2 + 1
            old = gray_difference[i]
    
    for i in range(len(gray_difference)):
        if abs(gray_difference[i]) < 8:
            break
        else:
            k1 = k1 + 1
    for i in range(len(gray_difference)):
        if abs(gray_difference[i]) < 8:
            continue
        else:
             k3 =  k3 + 1
            
    return k1, k2, k3

        

def main(image_path, num = 20):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 手动选择ROI
    cv2.namedWindow("Select Edge ROI", cv2.WINDOW_NORMAL)
    roi = cv2.selectROI("Select Edge ROI", gray)
    x, y, w, h = map(int, roi)
    #roi_image = image[y:y+h, x:x+w] 
    roi_gray = gray[y:y+h, x:x+w]     

    cv2.imwrite("roi_1.png", roi_gray)

    List = separate_gray(roi_gray, x, y, w, h, num)

    Gray_List = []
    hdr,  Gray_List = HDR_calculation(List)
    k1, k2, k3 = GrayList_Detection(Gray_List)

    #OUTPUT
    print("===== 动态范围分析结果 =====")
    print(f"动态范围: {hdr} (0-255)")
    print(f"顺序灰度阶数（从头计算灰度差大于8）: {k1}")
    print(f"总灰度阶数（灰度差大于6）: {k3}")

    #plot
    plt.plot(Gray_List, 'g-', linewidth=2)
    plt.title('Gray States Function')
    plt.xlabel('Stats')
    plt.ylabel('Grayscale')
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main("gray.png", 20)