import cv2
import math
import numpy as np
import matplotlib.pyplot as plt

def separate_24color(roi, x, y, w, h):
    #zeropoint_x = x - 0.5 * w
    #zeropoint_y = y + 0.5 * h
    delta = 1 / 24

    PiecesList = []
    w_list = [1, 3, 5, 7, 9, 11]
    h_list = [-1, -3, -5, -7]
    for j in h_list:
        for i in w_list:
            #point_x = x + w * (i / 12)
            #point_y = y + h * (j / 8)
            point_x = w * (i / 12)
            point_y = -h * (j / 8)
            color_piece = roi[int(point_y-delta*h):int(point_y+delta*h), int(point_x-delta*w):int(point_x+delta*w)]
            PiecesList.append(color_piece)
    return PiecesList

def SNR_calculation(pieces):
    snr = 0
    for Color_piece in pieces:
        i, j, k  = Color_piece.shape
        x = i // 2
        y = j // 2
        base_point = int(Color_piece[x, y, 0])**2 + int(Color_piece[x, y, 1])**2 + int(Color_piece[x, y, 2])**2
        tmp_cala = 0
        tmp_calb = 0
        for m in range(i):
            for n in range(j):
                delta_point = 0
                for k in range(3):
                    delta_point += (int(Color_piece[m, n, 0]) - int(Color_piece[x, y, 0])) ** 2
                tmp_cala += base_point
                tmp_calb += delta_point
        snr += (10 * math.log10(tmp_cala/tmp_calb)) ** 2
    
    snr = math.sqrt((snr / len(pieces)))

    return snr
        

def main(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)

    # 手动选择ROI
    cv2.namedWindow("Select Edge ROI", cv2.WINDOW_NORMAL)
    roi = cv2.selectROI("Select Edge ROI", image)
    x, y, w, h = map(int, roi)
    #roi_image = image[y:y+h, x:x+w] 
    roi_image = image[y:y+h, x:x+w]     

    cv2.imwrite("roi_1.png", roi_image)

    List = []
    List = separate_24color(roi_image, x, y, w, h)

    snr = SNR_calculation(List)
    print(snr)



if __name__ == "__main__":
    main("24color_SNR.jpg")
