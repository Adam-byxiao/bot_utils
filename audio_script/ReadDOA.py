import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf  # 用于读取音频文件

import matplotlib
matplotlib.rc("font",family='Microsoft YaHei')

def process_audio_channel(file_path, channel_num=8, scale_factor=180):
    """
    读取音频文件的指定通道，缩放数据并绘图
    
    参数:
        file_path: 音频文件路径
        channel_num: 要读取的通道号(0-based)
        scale_factor: 缩放因子
    """
    try:
        # 读取音频文件
        data, sample_rate = sf.read(file_path)
        
        # 检查音频文件是否有足够多的通道
        if len(data.shape) == 1:
            raise ValueError("音频文件是单声道，没有第9通道")
        if data.shape[1] <= channel_num:
            raise ValueError(f"音频文件只有{data.shape[1]}个通道，无法读取第{channel_num+1}通道")
        
        # 提取第9通道(索引为8)
        channel_data = data[:, channel_num]
        
        # 将每个帧的值乘以180
        scaled_data = channel_data * scale_factor + 180
        
        # 创建时间轴(秒)
        time_axis = np.arange(len(scaled_data)) / sample_rate
        
        # 绘制图形
        plt.figure(figsize=(12, 6))
        plt.plot(time_axis, scaled_data, linewidth=0.5)

        # 设置纵坐标轴从180开始
        #plt.ylim(bottom=180)

        # 设置纵坐标刻度间隔为10
        max_value = np.max(scaled_data)
        y_ticks = np.arange(180, max_value + 10, 10)
        plt.yticks(y_ticks)
        
        # 设置网格线间隔为5
        plt.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5)
        ax = plt.gca()
        ax.yaxis.set_minor_locator(plt.MultipleLocator(5))
        ax.grid(True, which='minor', axis='y', linestyle=':', linewidth=0.3)
        
        plt.title(f"音频文件第{channel_num+1}通道波形 (缩放{scale_factor}倍)")
        plt.xlabel("时间 (秒)")
        plt.ylabel("信号强度")
        
        # 自动调整x轴范围
        plt.xlim(0, time_axis[-1])
        
        # 显示图形
        plt.tight_layout()
        plt.show()
        
        return scaled_data, sample_rate
        
    except Exception as e:
        print(f"处理音频文件时出错: {e}")
        return None, None

# 使用示例
if __name__ == "__main__":
    # 替换为你的音频文件路径
    audio_file = "D:\\work\\Repository\\bot_utils\\AudioFile\\DOAFile\\block_computer_DOA.wav"  
    
    # 处理第9通道(索引为8)
    processed_data, sr = process_audio_channel(audio_file, channel_num=8)
    
    if processed_data is not None:
        print(f"处理完成! 采样率: {sr} Hz, 处理后的数据长度: {len(processed_data)}")
