import os
import requests
import numpy as np
from scipy.io import wavfile
import librosa
import random
import pandas as pd

ENV_NOISE_URLS = {
    '人声场景': 'https://cdn.jsdelivr.net/gh/karoldvl/ESC-50@master/audio/1-100032-A-0.wav',
    '键盘敲击声': 'https://cdn.jsdelivr.net/gh/karoldvl/ESC-50@master/audio/1-30226-A-49.wav',
    '空调声': 'https://cdn.jsdelivr.net/gh/karoldvl/ESC-50@master/audio/1-30227-A-40.wav',
    '雨声': 'https://cdn.jsdelivr.net/gh/karoldvl/ESC-50@master/audio/1-30228-A-2.wav',
    '窗外车流声': 'https://cdn.jsdelivr.net/gh/karoldvl/ESC-50@master/audio/1-30229-A-8.wav',
}

ESC50_ROOT = r'D:/work/Repository/ESC-50'  # 可根据实际路径修改
ESC50_AUDIO_DIR = os.path.join(ESC50_ROOT, 'audio')
ESC50_META_CSV = os.path.join(ESC50_ROOT, 'meta', 'esc50.csv')

# 环境类型到ESC-50类别的映射
LOCAL_ENV_CATEGORIES = {
    '人声场景': ['speech', 'crowd', 'laughing', 'crying_baby', 'sneezing', 'coughing', 'breathing'],
    '人声（仅speech）': ['speech'],
    '键盘敲击声': ['keyboard_typing'],
    '空调声': ['air_conditioner'],
    '雨声': ['rain'],
    '窗外车流声': ['engine', 'car_horn'],
}

def get_all_esc50_categories():
    df = pd.read_csv(ESC50_META_CSV)
    return sorted(df['category'].unique())

def get_env_noise(env_type, duration, sr):
    os.makedirs('noise_generator/env_noises', exist_ok=True)
    url = ENV_NOISE_URLS[env_type]
    local_path = f'noise_generator/env_noises/{env_type}.wav'
    try:
        if not os.path.exists(local_path):
            print(f"[INFO] Downloading {url} ...")
            r = requests.get(url)
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                f.write(r.content)
        print(f"[INFO] Loading {local_path} with librosa...")
        y, orig_sr = librosa.load(local_path, sr=sr, mono=True)
        print(f"[INFO] Loaded. orig_sr={orig_sr}, target_sr={sr}, len={len(y)}")
        if len(y) < duration * sr:
            # 循环补齐
            y = np.tile(y, int(np.ceil(duration * sr / len(y))))
        y = y[:int(duration * sr)]
        return y
    except Exception as e:
        print(f"[ERROR] get_env_noise failed: {e}")
        import traceback
        print(traceback.format_exc())
        raise 

def get_local_env_noise(env_type, duration, sr, random_seed=None):
    """
    从本地ESC-50数据集按类别随机选取/拼接音频，返回目标时长的numpy数组
    """
    if random_seed is not None:
        random.seed(random_seed)
    # 读取csv
    df = pd.read_csv(ESC50_META_CSV)
    # 支持多选因子
    categories = LOCAL_ENV_CATEGORIES.get(env_type, [env_type])
    files = df[df['category'].isin(categories)]['filename'].tolist()
    if not files:
        raise ValueError(f"未找到类别 {categories} 的音频样本")
    # 随机选取并拼接补齐
    y_all = []
    total_len = 0
    target_len = int(duration * sr)
    while total_len < target_len:
        fname = random.choice(files)
        wav_path = os.path.join(ESC50_AUDIO_DIR, fname)
        y, orig_sr = librosa.load(wav_path, sr=sr, mono=True)
        y_all.append(y)
        total_len += len(y)
    y_cat = np.concatenate(y_all)[:target_len]
    return y_cat 

def mix_local_env_noises(env_types, weights, duration, sr, mode='add', random_seed=None):
    assert len(env_types) == len(weights)
    weights = np.array(weights) / np.sum(weights)
    if mode == 'add':
        signals = [get_local_env_noise(t, duration, sr, random_seed) * w for t, w in zip(env_types, weights)]
        mix = np.sum(signals, axis=0)
    elif mode == 'concat':
        seg_lengths = (np.array(weights) * duration * sr).astype(int)
        signals = [get_local_env_noise(t, l/sr, sr, random_seed) for t, l in zip(env_types, seg_lengths)]
        mix = np.concatenate(signals)
        if len(mix) < int(duration * sr):
            mix = np.pad(mix, (0, int(duration * sr) - len(mix)))
        else:
            mix = mix[:int(duration * sr)]
    else:
        raise ValueError('mode must be add or concat')
    return mix 