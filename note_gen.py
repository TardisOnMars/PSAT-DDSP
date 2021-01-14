from math import floor, ceil

import numpy as np
import tensorflow as tf


class Song:
    def __init__(self, list_notes, list_beats, beats_per_minute=160):
        self.list_notes = list_notes

        self.list_beats = list_beats

        self.beats_per_second = beats_per_minute / 60

        self.n_beats = sum([beat.value for beat in self.list_beats])

    def gen_tensor(self):
        n_frames_per_second = 250

        n_frames_per_beat = n_frames_per_second / self.beats_per_second

        n_frames = 0

        notes = []
        notes_loudness = []
        for i in range(len(self.list_notes)):
            note_n_frame = ceil(self.list_beats[i].value * n_frames_per_beat)

            n_frames += note_n_frame

            notes.append(
                tf.convert_to_tensor(self.list_notes[i].value * np.ones([1, note_n_frame, 1], dtype=np.float32),
                                     dtype=tf.float32))

            attack = floor(note_n_frame * 0.35)
            decay = floor(note_n_frame * 0.10)
            sustain = floor(note_n_frame * 0.45)
            release = note_n_frame - attack - decay - sustain

            note_loudness = np.concatenate((np.linspace(-40.0, 0.0, attack), np.linspace(0.0, -10.0, decay),
                                            np.linspace(-10.0, -10.0, sustain), np.linspace(-10.0, -40.0, release)),
                                           axis=None)

            notes_loudness.append(note_loudness)

        f0_confidence = tf.convert_to_tensor(1.0 * np.ones([1, n_frames, 1], dtype=np.float32), dtype=tf.float32)

        f0_hz = tf.concat(notes, 1)

        loudness_db = tf.convert_to_tensor(np.concatenate(notes_loudness)[np.newaxis, :, np.newaxis], dtype=tf.float32)

        return f0_confidence, f0_hz, loudness_db, n_frames
