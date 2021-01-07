from enum import Enum

class Notes(Enum):
    Sil = 0.0
    D4 = 293.66
    F4 = 349.23
    F4d = 369.99
    G4 = 392.0
    G4d = 415.3
    A5 = 440.0
    B5 = 493.88
    C5 = 523.25
    D5 = 587.33
    E5 = 659.25


class Beats(Enum):
    Full = 4
    Half = 2
    Quarter = 1
    Eighth = 0.5


class CantinaSong:
    def __init__(self):
        self.list_notes = [Notes.A5, Notes.D5, Notes.A5, Notes.D5,
                        Notes.A5, Notes.D5, Notes.A5, Notes.G4d,
                        Notes.A5, Notes.A5, Notes.G4d, Notes.A5,
                        Notes.G4, Notes.Sil, Notes.F4d, Notes.G4,
                        Notes.F4d, Notes.F4, Notes.D4, Notes.Sil]

        self.list_beats = [Beats.Quarter, Beats.Quarter, Beats.Quarter, Beats.Quarter,
                      Beats.Quarter, Beats.Quarter, Beats.Eighth, Beats.Eighth,
                      Beats.Quarter, Beats.Eighth, Beats.Eighth, Beats.Eighth,
                      Beats.Eighth, Beats.Eighth, Beats.Eighth, Beats.Eighth,
                      Beats.Eighth, Beats.Half, Beats.Quarter, Beats.Quarter]

        self.beats_per_second = 132 / 60

        self.nb_beats = sum([beat.value for beat in self.list_beats])

        self.length = self.nb_beats / self.beats_per_second

if __name__ == '__main__':
    cantina = CantinaSong()
    print("Cantina Created")
