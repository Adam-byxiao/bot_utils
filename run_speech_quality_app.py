#!/usr/bin/env python3
# 一键启动语音质量分析主界面
import os
import sys

if __name__ == '__main__':
    script = os.path.join(os.path.dirname(__file__), 'audio_script', 'UnifiedSpeechQualityApp.py')
    if not os.path.exists(script):
        print('找不到 audio_script/UnifiedSpeechQualityApp.py')
        sys.exit(1)
    os.system(f'{sys.executable} "{script}"') 