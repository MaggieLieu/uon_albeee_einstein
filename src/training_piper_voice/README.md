# Piper Voice Model Training
[Piper](https://github.com/OHF-Voice/piper1-gpl/tree/main) is a fast and local neural text-to-speech engine. However, it requires much data to train the voice model. 
Therefore, we utilised [Coqui TTS](https://github.com/idiap/coqui-ai-TTS), which support zero-shot voice cloning, to generate the training data for training a Piper model.

The reason for using Piper over Coqui TTS is that Piper is quicker than Coqui TTS, which enhances the user experience of 'live chatting'.

## Coqui TTS zero-shot voice cloning

### Install Coqui TTS
First, install `coqui-tts` by following the [Coqui TTS installation guide](https://github.com/idiap/coqui-ai-TTS?tab=readme-ov-file#installation).

It is a good idea to also run the [demo code](https://github.com/idiap/coqui-ai-TTS?tab=readme-ov-file#installation) to ensure that the installation is successful.

### Data for zero-shot voice cloning
You need at least a short (>6 seconds for `XTTS-v2` models) audio clip (tested with mp3 and wav files) for zero-shot voice cloining. 

In this project, we used the audio from [this](https://youtu.be/3e3SaOTpZJA?si=kqVhKNrO_1HyvQSn) clip, trimed away the unrelevent noise (e.g. people clapping), and used [this](https://app.cleanvoice.ai/) website to clean up the voice. 

## Data Preparation for Piper Voice Model Training
Now, we have the voice. Save the voice to a known location. Modify (the directory and path to files) and run [this Python script](/src/training_piper_voice/generate_dataset_for_piper_model_finetuning/create_database.py) to generate some 22050 Hz synthetic speech for sentences stored [here](/src/training_piper_voice/generate_dataset_for_piper_model_finetuning/metadata.csv). 

At this point, you should have a bunch of 22050 Hz wav files. Play them and listen if they are what you wanted. 

## Train/Fine-tune the Piper Voice Model
Follow the instruction in [Piper's guide](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/TRAINING.md). 

We fine-tuned our voice on [this](https://huggingface.co/datasets/rhasspy/piper-checkpoints/blob/main/en/en_GB/alan/medium/epoch%3D6339-step%3D1647790.ckpt) checkpoint, and trained the model on a RTX-3070 (85w 8GB) laptop with 20 batch-size for around 3700 epochs, which took around 16 hours. 

To end the training, simply press (Ctrl + C) once, and wait for it to end. The checkpoint will be automatically saved in `/path/to/piper1-gpl/lightning_logs/version_x/checkpoints/`

#### Trouble shooting
Check [Piper's Issues](https://github.com/OHF-Voice/piper1-gpl/issues?q=is%3Aissue).

What I've faced was, the latest torch is too new, so I needed to downgrade that. 

Also, as the `python3 -m pip install -e .[train]` is not perfect, I needed to install a package/library manually.

Furthermore, if you plan to train on a new set of data, make sure to remove the files in the cache directory. 
