from math import floor, ceil

import numpy as np
import tensorflow as tf
from mido.midifiles import MidiFile


def get_freq_from_midi_code(code):
    f = pow(2, ((code - 69.0) / 12.0)) * 440
    return f


class MidiSong:
    def __init__(self, midi_path, n_track=-1):

        self.midi_path = midi_path
        self.mid = MidiFile(midi_path)

        self.tempo = 0
        self.n_frames_per_tick = 0

        self.tick_per_beat = self.mid.ticks_per_beat
        self.n_frames_per_second = 250

        self.n_track = n_track
        if self.n_track >= len(self.mid.tracks):
            print(
                f"WARNING n_track = {self.n_track} larger than the amount of available tracks.\nLongest track used "
                f"instead.\n")
            self.n_track = -1
        if self.n_track == -1:
            max_len = -1
            for track in self.mid.tracks:
                if len(track) > max_len:
                    self.track = track
                    max_len = len(track)
        else:
            self.track = self.mid.tracks[self.n_track]

    def set_tempo(self, new_tempo):
        self.tempo = new_tempo
        self.n_frames_per_tick = pow(10, -6) * self.n_frames_per_second * new_tempo / self.tick_per_beat

    # tempo is the default tempo in microseconds per beat
    # the tempo should usually be specified in the midi file and can be changed by meta messages of type set_tempo
    # default_duration is the default duration of a note in number of beats
    # attack_dur, decay_dur and release_dur are the duration of the ADSR envelope in number of beats
    # if velocity_adsr is True, the ADSR envelope depends on the velocity of the note
    # v_def is the default velocity : above is high velovity and uder v_def is low velocity
    # all durations in a midi file are expressed in ticks
    def gen_tensor(self, tempo=500000, default_duration=4, attack_dur=0.5, decay_dur=0.25, release_dur=0.5,
                   def_attack_loudness=0.0, def_sustain_loudness=-10.0, velocity_adsr=True, v_def=75.0):

        self.set_tempo(tempo)

        n_frames = 0

        notes = []
        notes_loudness = []

        track = self.track
        i_max = len(track) - 1

        for i in range(len(track)):
            msg = track[i]
            if msg.type == "note_on" and msg.velocity > 0:
                # New note
                note = msg.note
                f = get_freq_from_midi_code(msg.note)
                v = msg.velocity

                # Note duration
                duration = 0
                end_found = False
                for j in range(min(i + 1, i_max), min(i + 10, i_max)):
                    msj = track[j]
                    if not msj.is_meta:
                        duration += msj.time
                        if ((msj.type == "note_on") and (msj.note == note) and (msj.velocity == 0)) or (
                                (msj.type == "note_off") and (msj.note == note)):  # End of note
                            end_found = True
                            break
                if not end_found:
                    duration = default_duration * self.tick_per_beat
                    # Disable overlay notes :
                    dur_temp = 0
                    if i < i_max:
                        j = i + 1
                        while dur_temp < duration:
                            msj = track[j]
                            if (not msj.is_meta) and (msj.type == "note_on"):
                                dur_temp += msj.time
                                msj.velocity = 0
                            if j < i_max:
                                j += 1
                            else:
                                break
                else:
                    # Disable overlay notes :
                    for j in range(min(i + 1, i_max), min(i + 10, i_max)):
                        msj = track[j]
                        if not msj.is_meta:
                            if msj.type == "note_on":
                                if (msj.note == note) and (msj.velocity == 0):  # End of note note_on
                                    break
                                else:
                                    msj.velocity = 0
                            elif (msj.type == "note_off") and (msj.note == note):  # Enf of note note_off
                                break

                note_n_frame = ceil(duration * self.n_frames_per_tick)
                n_frames += note_n_frame

                notes.append(f * np.ones(note_n_frame, dtype=np.float32))

                # ADSR
                remaining_frames = note_n_frame
                if velocity_adsr:
                    v_factor = v_def / v
                else:
                    v_factor = 1
                attack = min(floor(attack_dur * v_factor * self.tick_per_beat * self.n_frames_per_tick),
                             remaining_frames)
                remaining_frames -= attack
                decay = min(floor(decay_dur * v_factor * self.tick_per_beat * self.n_frames_per_tick), remaining_frames)
                remaining_frames -= decay
                release = min(floor(release_dur * v_factor * self.tick_per_beat * self.n_frames_per_tick),
                              remaining_frames)
                remaining_frames -= release
                sustain = remaining_frames

                if velocity_adsr:
                    attack_loudness = def_attack_loudness * v / v_def
                    sustain_loudness = def_sustain_loudness * v / v_def
                else:
                    attack_loudness = def_attack_loudness
                    sustain_loudness = def_sustain_loudness

                note_loudness = np.concatenate(
                    (np.linspace(-60.0, attack_loudness, attack), np.linspace(attack_loudness, sustain_loudness, decay),
                     np.linspace(sustain_loudness, sustain_loudness, sustain),
                     np.linspace(sustain_loudness, -60.0, release)),
                    axis=None)
                notes_loudness.append(note_loudness)

                # Managing dt between end of this note and beginning of the next
                if i < i_max:
                    dt = 0
                    j = i + 1
                    while True:
                        msj = track[j]
                        if (not msj.is_meta) and (msj.type == "note_on"):
                            dt += msj.time
                            if msj.velocity > 0:
                                break
                        if j < i_max:
                            j += 1
                        else:
                            break
                    dt = dt - duration
                    dt_frames = ceil(dt * self.n_frames_per_tick)
                    if dt_frames > 0:
                        n_frames += dt_frames
                        notes.append(0 * np.ones(dt_frames, dtype=np.float32))
                        notes_loudness.append(-60 * np.ones(dt_frames, dtype=np.float32))

            elif msg.type == "set_tempo":
                # New tempo
                self.set_tempo(msg.tempo)

        f0_confidence = tf.convert_to_tensor(1.0 * np.ones([1, n_frames, 1], dtype=np.float32), dtype=tf.float32)
        f0_hz = tf.convert_to_tensor(np.concatenate(notes)[np.newaxis, :, np.newaxis], dtype=tf.float32)
        loudness_db = tf.convert_to_tensor(np.concatenate(notes_loudness)[np.newaxis, :, np.newaxis], dtype=tf.float32)

        return f0_confidence, f0_hz, loudness_db, n_frames

    # Displays the [max] firsts lines in the midi file. If max is not specified, all are displayed
    def disp_midi_file(self, max_lines=None):
        for msg in self.track[0:max_lines]:
            print("--------------")
            print(msg)
            print(f"is meta : {msg.is_meta}")
            print(f"type : {msg.type}")
            if msg.type == "note_on":
                print(f"note : {msg.note}")
                print(f"velocity : {msg.velocity}")
                print(f"time : {msg.time}")


if __name__ == '__main__':
    midi_files = ("37808.mid", "Prelude_Bach.mid", "Test1.mid")
    midi_index = 2
    song = MidiSong("midi_files/" + midi_files[midi_index])
    song.disp_midi_file(20)
    f0_confidence, notes, notes_loudness, n_frames = song.gen_tensor()
