import numpy as np
import pandas as pd

from TTS.api import TTS
import os
import torch

import librosa
import soundfile as sf

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"

# Init TTS
# replace the path with the path to your desired TTS model
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# you can use one or multiple files for a speaker
# for more information, check the TTS documentation or their github (https://github.com/idiap/coqui-ai-TTS)
speaker_voice_files = [
    "path/to/file1.wav",
    "path/to/file2.mp3",
]

PATH_TO_OUTPUT = "path_to_output_dir"
CSV_PATH = "path/to/metadata.csv"


path_to_output_original = f"{PATH_TO_OUTPUT}/original"
path_to_output_22050 = f"{PATH_TO_OUTPUT}/22050"

def generate_voice(index, text):
    print(f"Processing {index}: {text}")
    original_file_path = f"{path_to_output_original}/{index}.wav"
    output_path = f"{path_to_output_22050}/{index}.wav"
    tts.tts_to_file(
        text=text,
        speaker_wav=speaker_voice_files,
        language="en",
        file_path=original_file_path,
    )
    audio_data, original_sr = librosa.load(original_file_path, sr=None, mono=True)
    resampled_data = librosa.resample(
        audio_data,
        orig_sr=original_sr,
        target_sr=22050,
    )
    sf.write(output_path, resampled_data, 22050)


# check if directory exists
if not os.path.exists(PATH_TO_OUTPUT):
    os.makedirs(PATH_TO_OUTPUT)

if not os.path.exists(path_to_output_original):
    os.makedirs(path_to_output_original)

if not os.path.exists(path_to_output_22050):
    os.makedirs(path_to_output_22050)


metadata = pd.read_csv(CSV_PATH, sep="|", header=None, index_col=0)

for i in metadata.index:
    index = metadata.loc[i].name
    sentence = metadata.loc[i, 1]

    generate_voice(index, sentence)
