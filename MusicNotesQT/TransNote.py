import os
import numpy as np
from midiutil import MIDIFile
import sqlite3
from pydub import AudioSegment
from midi2audio import FluidSynth


def MidiNote(notes, location):
    SlovNote = {'c': 60, 'd': 62, 'e': 64, 'f': 65, 'g': 67, 'a': 69, 'h': 71, 'c1': 72, 'd1': 74, 'e1': 76, 'f1': 77,
                'g1': 79, 'a1': 81, 'h1': 83}
    finaly = []
    for i in notes:
        finaly.append(SlovNote[i])
    print(finaly)
    degrees = finaly  # MIDI note number
    track = 0
    channel = 0
    time = 0  # In beats
    duration = 1  # In beats
    tempo = 60  # In BPM
    volume = 100  # 0-127, as per the MIDI standard

    MyMIDI = MIDIFile(1)  # One track, defaults to format 1 (tempo track
    # automatically created)
    MyMIDI.addTempo(track, time, tempo)

    for pitch in degrees:
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        time = time + 1
    with open(location, "wb") as output_file:
        MyMIDI.writeFile(output_file)

def MidiMp3(midi_file_path,
            soundfont_path=r'1_Giga_piano.sf2',
            mp3_file_path=r'',
            wav_path=r""):
    fs = FluidSynth(sound_font=soundfont_path,sample_rate=96000)
    fs.midi_to_audio(midi_file_path, wav_path)
    audio = AudioSegment.from_wav(wav_path)
    audio.export(mp3_file_path, format='mp3')

def MidiWav(midi_file_path,
            soundfont_path=r'1_Giga_piano.sf2',
            wav_file_path=r''):
    fs = FluidSynth(sound_font=soundfont_path, sample_rate=96000)
    fs.midi_to_audio(midi_file_path, wav_file_path)
    audio = AudioSegment.from_wav(wav_file_path)
    audio.export(wav_file_path, format='wav')