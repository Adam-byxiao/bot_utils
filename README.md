# bot_utils

该项目编写了一系列用于bot测试的测试脚本以及用户界面

文件结构如下：

bot_tool.py					    bot_tool 是测试入口，编写了数个嵌套的测试类分别实现了测试对象、测试函数、测试对象，目前仅在硬件-电机测试中是完全体

ImageTest.py					    ImageTest.py 是图像测试的界面工具，目前实现了几个单一分析的脚本界面化

NoiseTest.py					    NoiseTest.py是时域分析噪声的测试工具

audio_script				

    AudioAligner.py			    用于将录制音频与原始音频进行时间轴的对齐

    AudioQuality.py			    用于进行一些音频的性能分析，尚未完成和验证

    Video2Audio.py			    用于将会议中录制的mp4格式文件转化为wav音频文件

AudioFile						    音频文件的处理目录

AudioBox.py					    将上述的音频对齐与格式转化工具集成的一个界面脚本

camera_script

    CheckNoise.py				    分析计算噪声（随机噪声），需要处理时域信号

    ChromaticAberration.py	    分析横向色差，表现出在强对比度和Edge边的色差表现

    ColorNoise.py				    分析计算色彩噪声，需要处理时域信号

    ColorSaturation.py			    分析色彩饱和度

    Contrast.py					    计算对比度表现

    hdr.py						    计算动态范围（基于灰阶卡），该用例由于物料规格和计算方法息息相关需要调整标准

    PurpleDetection.py			    进行紫边检测，原理类似横向色差，主要是针对特定的问题专门实现

    SFR.py						    进行空间频率分析，基于ISO12233图卡

    SNR.py						    进行信噪比分析

image							    一些先期测试用的图像

---

ImageTest.py使用方法：运行python ImageTest.py，点击菜单栏选择测试方法，测试方法显示在左下角的状态栏，点击打开图片选择测试图片，即可执行该测试方法
