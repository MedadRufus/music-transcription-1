"""Run the current guitar recording transcription pipeline.

Input: guitar recording (wave file)
Output: transcribed notes and tabs (gp5 file)

Parts:
- onset detection
- pitch detection
- string and fret detection
- tempo detection
- beat transformation (mapping of onsets and strings/frets to discrete notes in measures)
- gp5 export
"""

import argparse
import os
import sys

module_path = os.path.abspath('..')
if module_path not in sys.path:
    sys.path.append(module_path)
from music_transcription.beat_transformation.simple_beat_transformation import SimpleBeatTransformer
from music_transcription.fileformat.guitar_pro.utils import Header, Measure, Track
from music_transcription.fileformat.guitar_pro.gp5_writer import write_gp5
from music_transcription.onset_detection.cnn_onset_detection import CnnOnsetDetector
from music_transcription.pitch_detection.cnn_cqt_pitch_detection import CnnCqtPitchDetector
from music_transcription.pitch_detection.aubio_pitch_detection import AubioPitchDetector
from music_transcription.string_fret_detection.sequence_string_fret_detection import SequenceStringFretDetection
from music_transcription.tempo_detection.aubio_tempo_detection import AubioTempoDetector

# CONFIG
# Tuning and number of frets are currently not really configurable since we only have
# models for the standard tuning with 24 frets.
# Standard tuning:
# string/fret
# 0/0 = 64
# 1/0 = 59
# 2/0 = 55
# 3/0 = 50
# 4/0 = 45
# 5/0 = 40
TUNING = (64, 59, 55, 50, 45, 40)
N_FRETS = 24

TEMPO_DEFAULT = -1

SHORTEST_NOTES = {
    '1/1': 4.0, '1/2': 2.0, '1/4': 1.0, '1/8': 0.5, '1/16': 0.25, '1/32': 0.125, '1/64': 0.0625
}

parser = argparse.ArgumentParser(description='Transcribe guitar recording (WAV) to notes and tabs (GP5)')
parser.add_argument('path_to_wav', help='Path to guitar recording in WAV format')
parser.add_argument('-d', '--model_dir', default=os.path.join('..', 'models'), help='Path to models directory')
parser.add_argument('-m', '--musical_texture', default='poly', choices=['mono', 'poly'],
                    help='Is your recording strictly monophonic or does it also contain polyphonic chords?')
parser.add_argument('-t', '--tempo', type=int, default=TEMPO_DEFAULT,
                    help="Tempo of the recording in BPM. We'll try to determine this automatically if not set.")
parser.add_argument('-b', '--beats_per_measure', type=int, default=4,
                    help='Time signature / number of quarter notes per measure')
parser.add_argument('-s', '--shortest_note', default='1/16', choices=SHORTEST_NOTES.keys(),
                    help='Shortest possible note')
parser.add_argument('-i', '--instrument_id', type=int, default=20, help='Instrument id for GP5 file')
parser.add_argument('--track_title', help='Track title for GP5 file')
parser.add_argument('-p', '--path_to_gp5', help='Output path of GP5 file')
parser.add_argument('-v', '--verbose', action='store_true', help='Print verbose output')


args = parser.parse_args()
assert os.path.isfile(args.path_to_wav), 'Recording file not found'
assert args.tempo == -1 or args.tempo > 0, 'Tempo is invalid, should be -1 or > 0'
assert args.beats_per_measure > 0, 'Beats per measure is invalid, should be > 0'
assert args.instrument_id > 0, 'Instrument ID is invalid, should be > 0'



# PIPELINE

# convert music to mono track
from pydub import AudioSegment
sound = AudioSegment.from_wav(args.path_to_wav)
sound = sound.set_channels(1)
sound.export(args.path_to_wav, format="wav")


print('Detecting onsets')
onset_detector = CnnOnsetDetector.from_zip(
    os.path.join(args.model_dir, 'onset_detection', 'ds1-4_100-perc.zip')
)

onset_times_seconds = onset_detector.predict_onsets(args.path_to_wav)
# print(onset_times_seconds)
# print(len(onset_times_seconds))

print('Detecting pitches')
if args.musical_texture == 'mono':
    pitch_detector = AubioPitchDetector()
else:
    pitch_detector = CnnCqtPitchDetector.from_zip(
        os.path.join(args.model_dir, 'pitch_detection', 'cqt_ds12391011_100-perc_proba-thresh-0.3.zip')
    )
list_of_pitch_sets = pitch_detector.predict_pitches(args.path_to_wav, onset_times_seconds)
# print(list_of_pitch_sets)
# print(len(list_of_pitch_sets))



print('Detecting strings and frets')
string_fret_detector = SequenceStringFretDetection(TUNING, N_FRETS)
list_of_string_lists, list_of_fret_lists = string_fret_detector.predict_strings_and_frets(args.path_to_wav,
                                                                                          onset_times_seconds,
                                                                                          list_of_pitch_sets)

if args.verbose:
    for onset, pitch, string, fret in zip(onset_times_seconds, list_of_pitch_sets,
                                          list_of_string_lists, list_of_fret_lists):
        print('onset={}, pitch={}, string={}, fret={}'.format(onset, sorted(pitch, reverse=True), string, fret))

if args.tempo == TEMPO_DEFAULT:
    print('Detecting tempo')
    tempo_detector = AubioTempoDetector()
    tempo = tempo_detector.predict(args.path_to_wav, onset_times_seconds)
else:
    tempo = args.tempo

print('Running beat transformer')
beat_transformer = SimpleBeatTransformer(shortest_note=SHORTEST_NOTES[args.shortest_note],
                                         beats_per_measure=float(args.beats_per_measure))
beats = beat_transformer.transform(args.path_to_wav, onset_times_seconds,
                                   list_of_string_lists, list_of_fret_lists, tempo)


"""
    beats: list
        List of lists (each representing a measure) of tuples (each representing a track) with two
        lists of Beat objects. The first list is played on MIDI channel 1, the second on channel 2
        [  # measures
            [  # measure, tracks
                (  # track, 2 voices
                    [  # voice 1, beats (onsets with corresponding notes) go here

                    ],
                    [] # voice 2 is empty
                ),
            ],
        ]
"""
beat_list = []
for measures in beats:
    beat_list+=measures[0][0]

note_lengths = []
for i in beat_list:
    note_lengths.append(i.duration)

print('Exporting to GP5')

measures = []
for i, measure in enumerate(beats):
    if i == 0:
        measures.append(Measure(args.beats_per_measure, 4, beam8notes=(2, 2, 2, 2)))
    else:
        measures.append(Measure())

tracks = [
    Track(
        "Electric Guitar",
        len(TUNING), TUNING + (-1,),
        1, 1, 2, N_FRETS, 0, (200, 55, 55, 0), args.instrument_id
    ),
]

recording_name = os.path.basename(args.path_to_wav)
if recording_name.endswith('.wav'):
    recording_name = recording_name[:-4]
if args.track_title is None:
    track_title = recording_name
else:
    track_title = args.track_title

if args.path_to_gp5 is None:
    path_to_gp5 = recording_name + '.gp5'
else:
    path_to_gp5 = args.path_to_gp5

path_to_midi = recording_name + '.mid'

write_gp5(measures, tracks, beats, tempo=tempo, outfile=path_to_gp5, header=Header(title=track_title))


print('Exporting to Midi file')

from midiutil import MIDIFile


track    = 0
channel  = 0
time     = 0    # In beats
duration = 1    # In beats
#tempo    = 60   # In BPM
volume   = 100  # 0-127, as per the MIDI standard

MyMIDI = MIDIFile(1)  # One track, defaults to format 1 (tempo track is created
                      # automatically)
MyMIDI.addTempo(track, time, tempo)

note_counter = 0
for i, pitches in enumerate(list_of_pitch_sets):
    for pitch in pitches:
        if note_counter<len(onset_times_seconds)-1:
            duration = onset_times_seconds[note_counter + 1] - onset_times_seconds[note_counter]
        else:
            duration = 1

        MyMIDI.addNote(track, channel, pitch, onset_times_seconds[note_counter],duration , volume)
        note_counter+=1


#print("note counter:",note_counter)
#print("note_lengths", len(note_lengths))

with open(path_to_midi, "wb") as output_file:
    MyMIDI.writeFile(output_file)

