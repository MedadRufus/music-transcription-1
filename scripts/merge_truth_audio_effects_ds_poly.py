from collections import defaultdict
from os import listdir
from os.path import isdir, isfile, join
from warnings import warn
from xml.etree import ElementTree

from music_transcription.fileformat.truth import write_truth_file
from music_transcription.string_fret_detection.plausibility import get_all_fret_possibilities


def merge_truth(root_dir):
    pitches = read_pitches(root_dir)
    n_files_written = 0
    for dataset_part in listdir(root_dir):
        if dataset_part == 'Gitarre polyphon':
            path_to_dataset_part = join(root_dir, dataset_part)
            if isdir(path_to_dataset_part):
                print(dataset_part)
                path_to_samples = join(path_to_dataset_part, 'Samples')
                for fx_folder in listdir(path_to_samples):
                    path_to_fx_folder = join(path_to_samples, fx_folder)
                    if isdir(path_to_fx_folder):
                        print(fx_folder)
                        for wav_file in listdir(path_to_fx_folder):
                            path_to_wav_file = join(path_to_fx_folder, wav_file)
                            if isfile(path_to_wav_file) and wav_file.endswith('.wav'):
                                file_id = wav_file[:-4]
                                path_to_onset_file = join(path_to_dataset_part, 'Onsets', fx_folder, file_id + '.txt')
                                if isfile(path_to_onset_file):
                                    with open(path_to_onset_file) as f:
                                        onset_time = f.read().rstrip()
                                    if onset_time == '':
                                        warn('No onset available for {}'.format(path_to_wav_file))
                                    else:
                                        write_truth_file(
                                            [join(path_to_dataset_part, 'annotation', fx_folder, file_id + '.xml')],
                                            [[onset_time]],
                                            [[pitches[dataset_part][fx_folder][file_id]]]
                                        )
                                        n_files_written += 1
                                else:
                                    warn('No onset file found for {}'.format(path_to_wav_file))
                            else:
                                warn('Not a WAV file: {}'.format(path_to_wav_file))
                    else:
                        warn('Not an FX folder: {}'.format(path_to_fx_folder))
                print('')

    print('n_files_written={}'.format(n_files_written))


def read_pitches(root_dir):
    pitches = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: dict())))
    for dataset_part in listdir(root_dir):
        if dataset_part == 'Gitarre polyphon':
            path_to_dataset_part = join(root_dir, dataset_part)
            if isdir(path_to_dataset_part):
                path_to_lists = join(path_to_dataset_part, 'Lists')
                for fx_folder in listdir(path_to_lists):
                    path_to_fx_folder = join(path_to_lists, fx_folder)
                    if isdir(path_to_fx_folder):
                        for xml_file in listdir(path_to_fx_folder):
                            path_to_xml_file = join(path_to_fx_folder, xml_file)
                            if isfile(path_to_xml_file) and xml_file.endswith('.xml'):
                                tree = ElementTree.parse(path_to_xml_file)
                                root = tree.getroot()
                                for root_child in root:
                                    if root_child.tag == 'audiofile':
                                        pitch = None
                                        file_id = None
                                        polysort = None
                                        polytype = None
                                        for attribute in root_child:
                                            if attribute.tag == 'midinr':
                                                pitch = attribute.text
                                            elif attribute.tag == 'fileID':
                                                file_id = attribute.text
                                            elif attribute.tag == 'polysort':
                                                polysort = attribute.text
                                            elif attribute.tag == 'polytype':
                                                polytype = attribute.text
                                        if pitch is None:
                                            warn('No pitch in {}'.format(path_to_xml_file))
                                        elif file_id is None:
                                            warn('No file id in {}'.format(path_to_xml_file))
                                        elif polysort is None:
                                            warn('No polysort in {}'.format(path_to_xml_file))
                                        elif int(polysort) < 1 or int(polysort) > 2:
                                            warn('Invalid polysort {} in {}'.format(polysort, path_to_xml_file))
                                        elif polytype is None:
                                            warn('No polytype in {}'.format(path_to_xml_file))
                                        elif int(polytype) < 1 or int(polytype) > 7:
                                            warn('Invalid polytype {} in {}'.format(polytype, path_to_xml_file))
                                        else:
                                            file_pitches = calc_poly_pitches(pitch, polysort + polytype)
                                            assert len(get_all_fret_possibilities([int(p) for p in file_pitches])) > 0
                                            pitches[dataset_part][fx_folder][file_id] = file_pitches
                            else:
                                warn('Not an XML file: {}'.format(path_to_xml_file))
                    else:
                        warn('Not an FX folder: {}'.format(path_to_fx_folder))

    return pitches


def calc_poly_pitches(pitch, poly_id):
    # 11 - kleine Terz - +3
    # 12 - große Terz - +4
    # 13 - reine Quarte - +5
    # 14 - reine Quinte - +7
    # 15 - kleine Septime - +10
    # 16 - große Septime - +11
    # 17 - Oktave - +12
    # 21 - Dur - Dreiklang - +4, +7
    # 22 - Moll - Dreiklang - +3, +7
    # 23 - Sus4 - Dreiklang - +5, +7
    # 24 - Power Chord - +7, +12
    # 25 - Grosser Durseptimenakkord - +7, +11, +16 (changed from +4 to +16 since this is what's actually played)
    # 26 - Kleiner Durseptimenakkord - +7, +10, +16 (changed from +4 to +16 since this is what's actually played)
    # 27 - Kleiner Mollseptimenakkord - +7, +10, +15 (changed from +3 to +15 since this is what's actually played)
    if poly_id == '11':
        return pitch, str(int(pitch) + 3)
    elif poly_id == '12':
        return pitch, str(int(pitch) + 4)
    elif poly_id == '13':
        return pitch, str(int(pitch) + 5)
    elif poly_id == '14':
        return pitch, str(int(pitch) + 7)
    elif poly_id == '15':
        return pitch, str(int(pitch) + 10)
    elif poly_id == '16':
        return pitch, str(int(pitch) + 11)
    elif poly_id == '17':
        return pitch, str(int(pitch) + 12)
    elif poly_id == '21':
        return pitch, str(int(pitch) + 4), str(int(pitch) + 7)
    elif poly_id == '22':
        return pitch, str(int(pitch) + 3), str(int(pitch) + 7)
    elif poly_id == '23':
        return pitch, str(int(pitch) + 5), str(int(pitch) + 7)
    elif poly_id == '24':
        return pitch, str(int(pitch) + 7), str(int(pitch) + 12)
    elif poly_id == '25':
        return pitch, str(int(pitch) + 7), str(int(pitch) + 11), str(int(pitch) + 16)
    elif poly_id == '26':
        return pitch, str(int(pitch) + 7), str(int(pitch) + 10), str(int(pitch) + 16)
    elif poly_id == '27':
        return pitch, str(int(pitch) + 7), str(int(pitch) + 10), str(int(pitch) + 15)
    else:
        raise ValueError('Invalid poly_id {}'.format(poly_id))

root_dir = '../data/IDMT-SMT-AUDIO-EFFECTS'
merge_truth(root_dir)

# pitches = read_pitches(root_dir)
# for file_id, notes in pitches['Gitarre polyphon']['NoFX'].items():
#     if len(get_all_fret_possibilities([int(n) for n in notes])) == 0:
#         print(file_id)
