from math import floor, ceil

import numpy as np
#import tensorflow as tf
from enum import Enum
from mido import MidiFile

def get_freq_from_midi_code (code):
    f = pow(2,((code-69.0)/12.0))*440
    return f

class Song:
    def __init__(self, midi_path, n_track=0):

        self.midi_path = midi_path
        self.mid = MidiFile(midi_path)

        self.tick_per_beat = self.mid.ticks_per_beat
        self.n_frames_per_second = 250

        self.n_track = n_track
        if (self.n_track >= len(self.mid.tracks)) :
            print(f"WARNING n_track = {self.n_track} larger than the amount of available tracks.\nFirst track used instead.\n")
            self.n_track = 0
        self.track = self.mid.tracks[self.n_track]

    def set_tempo(self, new_tempo) :
        self.tempo = new_tempo
        self.n_frames_per_tick = pow(10,-6)*self.n_frames_per_second*new_tempo/self.tick_per_beat

    #tempo is the default tempo in microseconds per beat
    #the tempo should usually be specified in the midi file and can be changed by meta messages of type set_tempo
    #default_duration is the default duration of a note in number of beats
    def gen_tensor(self, tempo = 500000, default_duration=4):

        self.set_tempo (tempo)

        n_frames = 0

        notes = []
        notes_loudness = []

        track = self.track
        i_max = len(track) -1

        for i in range(len(track)) :

            msg = track[i]

            if (msg.type == "note_on" and msg.velocity > 0) :
                #New note
                #All durations are expressed in ticks

                note = msg.note
                f = get_freq_from_midi_code(msg.note)
                v = msg.velocity

                #Note duration
                duration = 0
                end_found = False
                for j in range(min(i+1,i_max),min(i+10,i_max)) :
                    msj = track[j]
                    if not msj.is_meta :
                        duration += msj.time
                        if (msj.type == "note_on") and (msj.note == note) and (msj.velocity == 0) : #End of note
                            end_found = True
                            break
                if not end_found :
                    duration = default_duration*self.tick_per_beat
                    #Disable overlay notes :
                    dur_temp = 0
                    if (i<i_max) :
                        j = i+1
                        while dur_temp < duration :
                            msj = track[j]
                            if (not msj.is_meta) and (msj.type == "note_on"):
                                dur_temp += msj.time
                                msj.velocity = 0
                            if (j< i_max) :
                                j += 1
                            else : 
                                break
                else :
                    #Disable overlay notes :
                    for j in range(min(i+1,i_max),min(i+10,i_max)) :
                        msj = track[j]
                        if (not msj.is_meta) and (msj.type=="note_on") :
                            if (msj.note == note) and (msj.velocity == 0) : #End of note
                                break
                            else :
                                msj.velocity = 0

                #Managing dt between end of this note and beginning of the next
                if (i<i_max) :
                    dt = 0
                    j = i+1
                    while True :
                        msj = track[j]
                        if (not msj.is_meta) and (msj.type == "note_on"):
                            dt += msj.time
                            if (msj.velocity > 0) :
                                break
                        if (j< i_max) :
                            j += 1
                        else : 
                            break
                    dt = dt - duration
                    dt_frames = ceil(dt*self.n_frames_per_tick)
                    if (dt_frames > 0) :
                        n_frames += dt_frames
                        notes.append(0 * np.ones([1, dt_frames, 1], dtype=np.float32))
                        notes_loudness.append(-60 * np.ones([1, dt_frames, 1], dtype=np.float32))
                

                note_n_frame = ceil(duration*self.n_frames_per_tick)
                n_frames += note_n_frame
                
                notes.append(f * np.ones([1, note_n_frame, 1], dtype=np.float32))
                #----------When using TF use instead:
                #notes.append(
                #tf.convert_to_tensor(f * np.ones([1, note_n_frame, 1], dtype=np.float32),
                #                     dtype=tf.float32))

                #TODO : calculer loudness et les coeffs ADSR en fonction de v
                #ADSR 
                #attack = floor(note_n_frame * 0.60)
                #decay = floor(note_n_frame * 0.20)
                #sustain = floor(note_n_frame * 0.10)
                #release = note_n_frame - attack - decay - sustain

                attack = 0
                decay = 0
                sustain = note_n_frame
                release = 0

                note_loudness = np.concatenate((np.linspace(-60.0, 0.0, attack), np.linspace(0.0, -10.0, decay),
                                                np.linspace(-10.0, -10.0, sustain), np.linspace(-10.0, -60.0, release)),
                                               axis=None)
                notes_loudness.append(note_loudness)
                
            elif (msg.type == "set_tempo") :
                #New tempo
                self.set_tempo(msg.tempo)
                
        #----------When using TF :
        #f0_confidence = tf.convert_to_tensor(1.0 * np.ones([1, n_frames, 1], dtype=np.float32), dtype=tf.float32)
        #f0_hz = tf.concat(notes, 1)
        #loudness_db = tf.convert_to_tensor(np.concatenate(notes_loudness)[np.newaxis, :, np.newaxis], dtype=tf.float32)

        #----------When using TF use instead:
        #return f0_confidence, f0_hz, loudness_db, n_frames
        return notes, notes_loudness, n_frames

    #Displays the [max] firsts lines in the midi file. If max is not specified, all are displayed
    def disp_midi_file (self,max=None) :

        for msg in self.track[0:max]:
            print("--------------")
            print(msg)
            print(f"is meta : {msg.is_meta}")
            print(f"type : {msg.type}")
            if (msg.type=="note_on") :
                print(f"note : {msg.note}")
                print(f"velocity : {msg.velocity}")
                print(f"time : {msg.time}")



if __name__ == '__main__':
    midi_paths = ("midi_files/37808.mid", "Bach_Preludio_BWV997.mid")
    song = Song(midi_paths[0],0)
    song.disp_midi_file(20)
    song.gen_tensor()
