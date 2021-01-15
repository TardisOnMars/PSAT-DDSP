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
    def gen_tensor(self, tempo = 500000):

        set_tempo (tempo)

        n_frames = 0

        notes = []
        notes_loudness = []

        for i in range(len(track)) :

            msg = track[i]

            if (msg.type == "note_on" and msg.velocity > 0) :
                #New note
                #All durations are expressed in ticks

                #TODO : determiner dt depuis note precedente : dt
                #TODO : ajouter du "vide" si dt > 0

                note = msg.note
                f = get_freq_from_midi_code(msg.note)
                v = msg.velocity

                #Note duration
                duration = 0
                end_found = False
                for j in i+1:i+10
                    msj = track[j]
                    if not msj.is_meta :
                        duration += msj.time
                        if (msj.note == note) and (msj.velocity == 0) : #End of note
                        end_found = True
                        break
                if not end_found :
                    duration = 4*self.tick_per_beat #Default duration
                #TODO : set velocity to 0 for other notes that would start before the end of this note

                notes.append(f * np.ones([1, note_n_frame, 1], dtype=np.float32)
                #-----When using TF use instead:
                #notes.append(
                #tf.convert_to_tensor(f * np.ones([1, note_n_frame, 1], dtype=np.float32),
                #                     dtype=tf.float32))

                #TODO : calculer loudness et les coeffs ADSR (en fonction de v)
                #TODO : ajouter enveloppe ADSR dans notes_loudness

                #TODO : increment n_frames
                
            elif (msg.type == "set_tempo") :
                #New tempo
                set_tempo(msg.tempo)
                
        #-----When using TF :
        #f0_confidence = tf.convert_to_tensor(1.0 * np.ones([1, n_frames, 1], dtype=np.float32), dtype=tf.float32)
        #f0_hz = tf.concat(notes, 1)
        #loudness_db = tf.convert_to_tensor(np.concatenate(notes_loudness)[np.newaxis, :, np.newaxis], dtype=tf.float32)
        
        #return f0_confidence, f0_hz, loudness_db, n_frames

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
    song.disp_midi_file(10)
