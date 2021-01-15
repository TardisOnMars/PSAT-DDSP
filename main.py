import os
import warnings

import ddsp.training
import gin
import librosa
import numpy as np
import matplotlib.pyplot as plt

from jukebox_prompt import JBPrompt
from note_gen import Song
from midi_gen import MidiSong
from utils import play, detect_notes, fit_quantile_transform, shift_f0, auto_tune, get_tuning_factor

warnings.filterwarnings("ignore")

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

jbprompt = JBPrompt()

if jbprompt.selected_song[0] == 'midi':
    song = MidiSong(jbprompt.selected_song[1])
else:
    song = Song(jbprompt.selected_song[0], jbprompt.selected_song[1], jbprompt.selected_song[2])

hop_size = 64
f0_confidence, f0_hz, loudness_db, n_frames = song.gen_tensor()
n_samples = n_frames * hop_size

batch = {"f0_confidence": f0_confidence, "f0_hz": f0_hz, "loudness_db": loudness_db}

# Parse the gin config.
gin_file = os.path.join(jbprompt.selected_instrument[0], 'operative_config-0.gin')

gin_params = [
    'Additive.n_samples = {}'.format(n_samples),
    'FilteredNoise.n_samples = {}'.format(n_samples),
    'DefaultPreprocessor.time_steps = {}'.format(n_frames),
    'oscillator_bank.use_angular_cumsum = True',  # Avoids cumsum accumulation errors.
]

gin.parse_config_file(gin_file, skip_unknown=True)
gin.parse_config(gin_params)

model = ddsp.training.models.Autoencoder()
model.restore(jbprompt.selected_instrument[1])

DATASET_STATS = jbprompt.selected_instrument[2]

audio_features_mod = None

# Apply modification to synthesized audio to better match dataset
if DATASET_STATS is not None:
    # Detect sections that are "on".
    f0_confidence_np = batch['f0_confidence'].numpy().copy()
    f0_confidence_np = f0_confidence_np.squeeze()
    f0_hz_np = batch['f0_hz'].numpy().copy()
    f0_hz_np = f0_hz_np.squeeze()
    loudness_db_np = batch['loudness_db'].numpy().copy()
    loudness_db_np = loudness_db_np.squeeze()
    batch_np = {"f0_confidence": f0_confidence_np, "f0_hz": f0_hz_np, "loudness_db": loudness_db_np}

    mask_on, note_on_value = detect_notes(batch_np['loudness_db'], batch_np['f0_confidence'], 1)
    batch_mod = batch_np.copy()
    quiet = 20
    autotune = 0

    if np.any(mask_on):
        # Shift the pitch register.
        target_mean_pitch = DATASET_STATS['mean_pitch']
        pitch = ddsp.core.hz_to_midi(batch_np['f0_hz'])
        mean_pitch = np.mean(pitch[mask_on])
        p_diff = target_mean_pitch - mean_pitch
        p_diff_octave = p_diff / 12.0
        round_fn = np.floor if p_diff_octave > 1.5 else np.ceil
        p_diff_octave = round_fn(p_diff_octave)
        audio_features_mod = shift_f0(batch_mod, p_diff_octave)

        # Quantile shift the note_on parts.
        _, loudness_norm = fit_quantile_transform(batch_np['loudness_db'], mask_on,
                                                  inv_quantile=DATASET_STATS['quantile_transform'])

        # Turn down the note_off parts.
        mask_off = np.logical_not(mask_on).squeeze()
        loudness_norm[mask_off] -= quiet * (1.0 - note_on_value[mask_off][:, np.newaxis])
        loudness_norm = np.reshape(loudness_norm, batch_np['loudness_db'].shape)

        audio_features_mod['loudness_db'] = loudness_norm

        # Auto-tune.
        if autotune:
            f0_midi = np.array(ddsp.core.hz_to_midi(audio_features_mod['f0_hz']))
            tuning_factor = get_tuning_factor(f0_midi, audio_features_mod['f0_confidence'], mask_on)
            f0_midi_at = auto_tune(f0_midi, tuning_factor, mask_on, amount=autotune)
            audio_features_mod['f0_hz'] = ddsp.core.midi_to_hz(f0_midi_at)

        # Plot Features.
        has_mask = int(mask_on is not None)
        n_plots = 3 if has_mask else 2
        fig, axes = plt.subplots(nrows=n_plots, ncols=1, sharex=True, figsize=(2 * n_plots, 8))

        if has_mask:
            TRIM = -15
            ax = axes[0]
            ax.plot(np.ones_like(mask_on[:TRIM]), 'k:')
            ax.plot(note_on_value[:TRIM])
            ax.plot(mask_on[:TRIM])
            ax.set_ylabel('Note-on Mask')
            ax.set_xlabel('Time step [frame]')
            ax.legend(['Threshold', 'Likelihood', 'Mask'])

        ax = axes[0 + has_mask]
        ax.plot(batch_np['loudness_db'][:TRIM])
        ax.plot(audio_features_mod['loudness_db'][:TRIM])
        ax.set_ylabel('loudness_db')
        ax.legend(['Original', 'Adjusted'])

        ax = axes[1 + has_mask]
        ax.plot(librosa.hz_to_midi(batch_np['f0_hz'][:TRIM]))
        ax.plot(librosa.hz_to_midi(audio_features_mod['f0_hz'][:TRIM]))
        ax.set_ylabel('f0 [midi]')
        _ = ax.legend(['Original', 'Adjusted'])

        plt.show()

    else:
        print('\nSkipping auto-adjust (no notes detected or ADJUST box empty).')

# Resynthesize audio.
af = batch if audio_features_mod is None else audio_features_mod
outputs = model(af, training=False)

audio_gen = model.get_audio_from_outputs(outputs)

play(audio_gen, savefile=jbprompt.selected_filename)

print("Finished Playing Sound")
