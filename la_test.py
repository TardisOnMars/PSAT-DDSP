import time
import os
import warnings
from enum import Enum

import ddsp
import ddsp.training
import gin
import numpy as np
import tensorflow as tf

from scipy.io import wavfile
import sounddevice as sd


def play(array_of_floats, sample_rate=16000):
    # If batched, take first element.
    if len(array_of_floats.shape) == 2:
        array_of_floats = array_of_floats[0]

    normalizer = float(np.iinfo(np.int16).max)
    array_of_ints = np.array(
        np.asarray(array_of_floats) * normalizer, dtype=np.int16)

    sd.default.samplerate = 16000
    sd.play(array_of_ints, blocking=True)
    wavfile.write("sample.wav", sample_rate, array_of_ints)




warnings.filterwarnings("ignore")

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

n_frames = 1000
hop_size = 64
n_samples = n_frames * hop_size

f0_confidence = tf.convert_to_tensor(1.0 * np.ones([1, n_frames, 1], dtype=np.float32), dtype=tf.float32)

notes = [tf.convert_to_tensor(440.0 * np.ones([1, 250, 1], dtype=np.float32), dtype=tf.float32),
         tf.convert_to_tensor(297.0 * np.ones([1, 250, 1], dtype=np.float32), dtype=tf.float32),
         tf.convert_to_tensor(264.0 * np.ones([1, 250, 1], dtype=np.float32), dtype=tf.float32),
         tf.convert_to_tensor(440.0 * np.ones([1, 250, 1], dtype=np.float32), dtype=tf.float32)]

f0_hz = tf.concat(notes, 1)

note_loudness = np.concatenate((np.linspace(-60.0, 0.0, 100), np.linspace(0.0, -25.0, 50),
                                np.linspace(-25.0, -25.0, 50), np.linspace(-25.0, -60.0, 50)),
                               axis=None)

notes_loudness = np.concatenate((note_loudness, note_loudness, note_loudness, note_loudness), axis=None)[np.newaxis, :, np.newaxis]

loudness_db = tf.convert_to_tensor(notes_loudness, dtype=tf.float32)

# loudness_db = tf.convert_to_tensor(0.0 * np.ones([1, n_frames, 1], dtype=np.float32), dtype=tf.float32)

batch = {"f0_confidence": f0_confidence, "f0_hz": f0_hz, "loudness_db": loudness_db}

# Parse the gin config.
gin_file = os.path.join('./data/ddsp-violin', 'operative_config-0.gin')

gin_params = [
    'Additive.n_samples = {}'.format(n_samples),
    'FilteredNoise.n_samples = {}'.format(n_samples),
    'DefaultPreprocessor.time_steps = {}'.format(n_frames),
    'oscillator_bank.use_angular_cumsum = True',  # Avoids cumsum accumulation errors.
]

gin.parse_config_file(gin_file, skip_unknown=True)
gin.parse_config(gin_params)

model = ddsp.training.models.Autoencoder()
model.restore('./data/ddsp-violin/ckpt-40000')

# Resynthesize audio.
outputs = model(batch, training=False)

audio_gen = model.get_audio_from_outputs(outputs)

play(audio_gen)

print("Finished Playing Sound")
