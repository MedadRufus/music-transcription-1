# Created by Medad Rufus Newman on 10/03/2020


import guitarpro

song = guitarpro.parse('Lullaby.gp5')



# for track in song.tracks:
#     for measure in track.measures:
#         for voice in measure.voices:
#             for beat in voice.beats:
#                 for note in beat.notes:
#                     print(note.durationPercent)
#                     for i in dir(note.effect):
#                         print(note.effect,getattr(note.effect,i))
#


note_attributes = [ 'beat', 'durationPercent', 'effect', 'realValue', 'string', 'swapAccidentals', 'type', 'value', 'velocity']

# for track in song.tracks:
#     for measure in track.measures:
#         for voice in measure.voices:
#             for beat in voice.beats:
#                 for note in beat.notes:
#                     for attr in note_attributes:
#                         print(attr,": ",getattr(note,attr))
#                     print(dir(note.beat))
#
#                     for attr in dir(note.beat):
#                         print(attr,": ",getattr(note.beat,attr))
#
#                     print("=======================================================")

for track in song.tracks:
    for measure in track.measures:
        for voice in measure.voices:
            for beat in voice.beats:
                for note in beat.notes:
                    print("Note pitch in number(realValue)",": ",getattr(note,"realValue"))
                    # print("Value",": ",getattr(note,"value"))

                    print("start",": ",getattr(note.beat,"start"))
                    # print("realStart",": ",getattr(note.beat,"realStart"))

                    print("=======================================================")