from __future__ import print_function, unicode_literals
from PyInquirer import prompt
from pyfiglet import Figlet

import constants


class JBPrompt:
    def __init__(self):
        f = Figlet(font='slant')
        print(f.renderText('DDSP JukeBox'))

        questions = [
            {
                'type': 'list',
                'name': 'song',
                'message': 'What song would you like to play ?',
                'choices': ['Test', 'Cantina', 'One', 'Test_Midi'],
                'filter': lambda val: val.lower()
            },
            {
                'type': 'list',
                'name': 'instrument',
                'message': 'What instrument would you like to use ?',
                'choices': ['Saxo', 'Violin', 'Flute'],
                'filter': lambda val: val.lower()
            },
            {
                'type': 'confirm',
                'name': 'save',
                'message': 'Do you want to save your song ?',
                'default': False
            },
            {
                'type': 'input',
                'name': 'save_name',
                'message': 'Provide a file name for your song:',
                'when': lambda answers: answers['save']
            },
        ]

        answers = prompt(questions)

        instruments = {
            "saxo": ["./data/ddsp-saxo", "./data/ddsp-saxo/ckpt-20000", constants.SAXO_STATS_OBJECT],
            "flute": ["./data/ddsp-saxo", "./data/ddsp-flute/ckpt-20000", constants.FLUTE_STATS_OBJECT],
            "violin": ["./data/ddsp-saxo", "./data/ddsp-violin/ckpt-40000", constants.VIOLIN_STATS_OBJECT],
        }
        self.selected_instrument = (instruments.get(answers['instrument'], "Invalid Instrument"))

        songs = {
            "cantina": [constants.CANTINA_NOTES, constants.CANTINA_BEATS, 131],
            "test": [constants.TEST_NOTES, constants.TEST_BEATS, 140],
            "one": [constants.ONE_NOTES, constants.ONE_BEATS, 160],
            "test_midi": ["midi", "midi_files/Test1.mid"]
        }
        self.selected_song = (songs.get(answers['song'], "Invalid Song"))

        self.selected_filename = answers['save_name'] + '.wav' if answers['save'] is True else ""


if __name__ == '__main__':
    jbprompt = JBPrompt()
