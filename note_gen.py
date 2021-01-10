from math import floor, ceil

import numpy as np
import tensorflow as tf
from enum import Enum


class Notes(Enum):
    Sil = 0.0
    C4 = 261.63
    D4 = 293.66
    F4 = 349.23
    F4d = 369.99
    G4 = 392.0
    G4d = 415.3
    A4 = 440.0
    B4b = 466.16
    B4 = 493.88
    C5 = 523.25
    D5 = 587.33
    E5b = 622.25
    E5 = 659.25


class Beats(Enum):
    Full = 4
    Half = 2
    Quarter = 1
    Eighth = 0.5
    Sixteenth = 0.25


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

            attack = floor(note_n_frame * 0.60)
            decay = floor(note_n_frame * 0.20)
            sustain = floor(note_n_frame * 0.10)
            release = note_n_frame - attack - decay - sustain

            note_loudness = np.concatenate((np.linspace(-60.0, 0.0, attack), np.linspace(0.0, -10.0, decay),
                                            np.linspace(-10.0, -10.0, sustain), np.linspace(-10.0, -60.0, release)),
                                           axis=None)
            notes_loudness.append(note_loudness)

        f0_confidence = tf.convert_to_tensor(1.0 * np.ones([1, n_frames, 1], dtype=np.float32), dtype=tf.float32)

        f0_hz = tf.concat(notes, 1)

        loudness_db = tf.convert_to_tensor(np.concatenate(notes_loudness)[np.newaxis, :, np.newaxis], dtype=tf.float32)

        return f0_confidence, f0_hz, loudness_db, n_frames


CANTINA_NOTES = [Notes.A4, Notes.D5, Notes.A4, Notes.D5,
                 Notes.A4, Notes.D5, Notes.A4, Notes.G4d,
                 Notes.A4, Notes.A4, Notes.G4d, Notes.A4,
                 Notes.G4, Notes.Sil, Notes.F4d, Notes.G4,
                 Notes.F4d, Notes.F4, Notes.D4, Notes.Sil,
                 Notes.A4, Notes.D5, Notes.A4, Notes.D5,
                 Notes.A4, Notes.D5, Notes.A4, Notes.G4d,
                 Notes.A4, Notes.G4, Notes.G4, Notes.F4d,
                 Notes.G4, Notes.C5, Notes.B4b, Notes.A4,
                 Notes.G4, Notes.A4, Notes.D5, Notes.A4,
                 Notes.D5, Notes.A4, Notes.D5, Notes.A4,
                 Notes.G4d, Notes.A4, Notes.C5, Notes.C5,
                 Notes.A4, Notes.G4, Notes.F4, Notes.D4,
                 Notes.D4, Notes.F4, Notes.A4, Notes.C5,
                 Notes.E5b, Notes.D5, Notes.G4d, Notes.A4,
                 Notes.F4]

CANTINA_BEATS = [Beats.Quarter, Beats.Quarter, Beats.Quarter, Beats.Quarter,
                 Beats.Quarter, Beats.Quarter, Beats.Eighth, Beats.Eighth,
                 Beats.Quarter, Beats.Eighth, Beats.Eighth, Beats.Eighth,
                 Beats.Eighth, Beats.Eighth, Beats.Eighth, Beats.Eighth,
                 Beats.Eighth, Beats.Half, Beats.Quarter, Beats.Quarter,
                 Beats.Quarter, Beats.Quarter, Beats.Quarter, Beats.Quarter,
                 Beats.Quarter, Beats.Quarter, Beats.Eighth, Beats.Eighth,
                 Beats.Quarter, Beats.Quarter, Beats.Quarter, Beats.Quarter,
                 Beats.Quarter, Beats.Quarter, Beats.Quarter, Beats.Quarter,
                 Beats.Quarter, Beats.Quarter, Beats.Quarter, Beats.Quarter,
                 Beats.Quarter, Beats.Quarter, Beats.Quarter, Beats.Eighth,
                 Beats.Eighth, Beats.Quarter, Beats.Quarter, Beats.Quarter,
                 Beats.Quarter, Beats.Quarter, Beats.Half, Beats.Half,
                 Beats.Half, Beats.Half, Beats.Half, Beats.Half,
                 Beats.Quarter, Beats.Quarter, Beats.Quarter, Beats.Quarter,
                 Beats.Full]

COUNTDOWN_NOTES = [Notes.C4, Notes.C5, Notes.B4, Notes.C5,
                   Notes.F4, Notes.D4, Notes.D5, Notes.C5,
                   Notes.D5, Notes.C5, Notes.B4, Notes.D4,
                   Notes.D5, Notes.C5, Notes.D5]

TEST_NOTES = [Notes.A4, Notes.B4, Notes.C5, Notes.D4]
TEST_BEATS = [Beats.Full, Beats.Full, Beats.Full, Beats.Full]

ONE_NOTES = [Notes.A4]
ONE_BEATS = [Beats.Full]

if __name__ == '__main__':
    cantina = Song(CANTINA_NOTES, CANTINA_BEATS)
    f0_confidence, f0_hz, loudness_db, n_frames = cantina.gen_tensor()
    print("Cantina Created")
