from collections import defaultdict
from os import listdir
from os.path import isdir, isfile, join
from warnings import warn
from xml.etree import ElementTree

root_dir = '../data/IDMT-SMT-AUDIO-EFFECTS'
pitches = defaultdict(int)
for dataset_part in listdir(root_dir):
    path_to_dataset_part = join(root_dir, dataset_part)
    if isdir(path_to_dataset_part):
        if dataset_part == 'Gitarre monophon':
            print(dataset_part)
            path_to_lists = join(path_to_dataset_part, 'Lists')
            for fx_folder in listdir(path_to_lists):
                path_to_fx_folder = join(path_to_lists, fx_folder)
                if isdir(path_to_fx_folder):
                    print(fx_folder)
                    for xml_file in listdir(path_to_fx_folder):
                        path_to_xml_file = join(path_to_fx_folder, xml_file)
                        if isfile(path_to_xml_file) and xml_file.endswith('.xml'):
                            tree = ElementTree.parse(path_to_xml_file)
                            root = tree.getroot()
                            for root_child in root:
                                if root_child.tag == 'audiofile':
                                    for attribute in root_child:
                                        if attribute.tag == 'midinr':
                                            pitches[attribute.text] += 1
                                            break
                        else:
                            warn('Not an XML file: {}'.format(path_to_xml_file))
                else:
                    warn('Not an FX folder: {}'.format(path_to_fx_folder))
            print('')

print('PITCHES')
print('min pitch = {}'.format(min(pitches.keys())))
print('max pitch = {}'.format(max(pitches.keys())))
print('nr of pitches = {}'.format(sum(pitches.values())))
for pitch, count in sorted(pitches.items()):
    print('{}: {}'.format(pitch, count))
