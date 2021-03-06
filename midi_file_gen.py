from mido.midifiles import MidiFile, MidiTrack, MetaMessage
from mido.messages import Message

"""
    track.append(Message('note_on', note=value_code, velocity=80, time=32))
    track.append(Message('note_on', note=value_code, velocity=0, time=32))
"""

if __name__ == '__main__':
    out_path = "midi_files/Test1.mid"

    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Tempo
    track.append(MetaMessage('set_tempo', tempo=800000, time=0))

    # Start A
    track.append(Message('note_on', note=23, velocity=80, time=0))
    # End A
    track.append(Message('note_on', note=23, velocity=0, time=560))

    # Start B
    track.append(Message('note_on', note=56, velocity=80, time=40))
    # End B
    track.append(Message('note_on', note=56, velocity=0, time=100))

    # Tempo
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))

    # Start C
    track.append(Message('note_on', note=96, velocity=80, time=320))
    # End C
    track.append(Message('note_on', note=96, velocity=0, time=400))

    # Start D
    track.append(Message('note_on', note=79, velocity=80, time=1150))
    # End D
    track.append(Message('note_on', note=79, velocity=0, time=620))

    # Start E
    track.append(Message('note_on', note=79, velocity=80, time=1150))
    # End E
    track.append(Message('note_on', note=79, velocity=0, time=620))

    mid.save(out_path)

    print(f"tick_per_beat : {mid.ticks_per_beat}")
    print("Execution done")
