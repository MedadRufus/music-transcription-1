import numpy as np
from os import listdir
import os.path
from os.path import isdir, isfile
import soundfile
from xml.etree import ElementTree
from warnings import warn

DATA_DIR = r'..\data'


def read_data(active_datasets, frame_rate_hz, expected_sample_rate, subsampling_step):
    """Read data, returning a tuple (X_parts, y_parts, y_actual_onset_only_parts, ds_labels)

    Input:
    active_datasets: set of datasets to be loaded
    frame_rate_hz: number of frames per second
    expected_sample_rate: (unit: Hz) files with a different sample rate will be skipped
    subsampling_step: Do a subsampling on the samples, only keeping every nth frame. subsampling_step=1 means no subsampling.

    Output:
    X_parts: List of numpy arrays of samples (one per file)
    y_parts: List of numpy arrays of labels (one per file)
    y_actual_onset_only_parts: List of numpy arrays of labels (no neighbors, one per file)
    ds_labels: List of dataset labels
    """

    dir_tuples = []
    if 1 in active_datasets:
        path_to_ds_1 = os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset1')
        for guitar_desc in listdir(path_to_ds_1):
            dir_tuples.append((
                os.path.join(path_to_ds_1, guitar_desc, 'audio'),
                os.path.join(path_to_ds_1, guitar_desc, 'annotation'),
                1,
            ))

    if 2 in active_datasets:
        dir_tuples.append((
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset2\audio'),
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset2\annotation'),
            2,
        ))
    if 3 in active_datasets:
        dir_tuples.append((
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset3\audio'),
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset3\annotation'),
            3,
        ))

    file_tuples = []
    for audio_dir, annotation_dir, ds in dir_tuples:
        for wav_file in listdir(audio_dir):
            path_to_wav = os.path.join(audio_dir, wav_file)
            if wav_file.endswith('.wav'):
                path_to_xml = os.path.join(annotation_dir, wav_file.replace('.wav', '.xml'))
                if isfile(path_to_xml):
                    file_tuples.append((path_to_wav, path_to_xml, ds, 'xml'))
                else:
                    warn('Skipping ' + wav_file + ', no truth found.')
            else:
                warn('Skipping ' + path_to_wav + ', not a .wav file.')

    if 4 in active_datasets:
        for path_to_ds in [
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset4\Career SG'),
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset4\Ibanez 2820')
        ]:
            for tempo in listdir(path_to_ds):
                path_to_tempo = os.path.join(path_to_ds, tempo)
                for genre in listdir(path_to_tempo):
                    path_to_genre = os.path.join(path_to_tempo, genre)
                    path_to_audio = os.path.join(path_to_genre, 'audio')
                    for wav_file in listdir(path_to_audio):
                        path_to_wav = os.path.join(path_to_audio, wav_file)
                        if wav_file.endswith('.wav'):
                            path_to_onsets = os.path.join(path_to_genre, 'annotation', 'onsets')
                            if isdir(path_to_onsets):
                                path_to_csv = os.path.join(path_to_onsets, wav_file.replace('.wav', '.csv'))
                                if isfile(path_to_csv):
                                    file_tuples.append((path_to_wav, path_to_csv, 4, 'csv'))
                                else:
                                    # TODO fallback to other formats
                                    warn('Skipping ' + path_to_wav + ', no truth csv found.')
                            else:
                                warn('Skipping ' + path_to_wav + ', no onset folder.')
                        else:
                            warn('Skipping ' + path_to_wav + ', not a .wav file.')

    X_parts = []
    y_parts = []
    y_actual_onset_only_parts = []
    ds_labels = []
    for path_to_wav, path_to_truth, dataset, truth_format in file_tuples:
        X_part, y_part, y_actual_onset_only_part = read_X_y(path_to_wav, frame_rate_hz, expected_sample_rate,
                                                            subsampling_step, path_to_truth, truth_format, dataset)
        if X_part is not None and y_part is not None and y_actual_onset_only_part is not None:
            X_parts.append(X_part)
            y_parts.append(y_part)
            y_actual_onset_only_parts.append(y_actual_onset_only_part)
            ds_labels.append(dataset)

    return X_parts, y_parts, y_actual_onset_only_parts, ds_labels


def get_wav_and_truth_files(active_datasets):
    """Get wave files and truth information. Return a tuple (wav_file_paths, truth_dataset_format_tuples)

    Input:
    active_datasets: set of datasets to be loaded

    Output:
    wav_file_paths: List of wave file paths
    truth_dataset_format_tuples: List of tuples (path_to_truth_file, dataset, format)

    dataset labels: one of 1, 2, 3, 4
    truth formats: one of 'csv', 'xml'
    """

    dir_tuples = []
    if 1 in active_datasets:
        path_to_ds_1 = os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset1')
        for guitar_desc in listdir(path_to_ds_1):
            dir_tuples.append((
                os.path.join(path_to_ds_1, guitar_desc, 'audio'),
                os.path.join(path_to_ds_1, guitar_desc, 'annotation'),
                1,
            ))

    if 2 in active_datasets:
        dir_tuples.append((
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset2\audio'),
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset2\annotation'),
            2,
        ))
    if 3 in active_datasets:
        dir_tuples.append((
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset3\audio'),
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset3\annotation'),
            3,
        ))

    wav_file_paths = []
    truth_dataset_format_tuples = []
    for audio_dir, annotation_dir, ds in dir_tuples:
        for wav_file in listdir(audio_dir):
            path_to_wav = os.path.join(audio_dir, wav_file)
            if wav_file.endswith('.wav'):
                path_to_xml = os.path.join(annotation_dir, wav_file.replace('.wav', '.xml'))
                if isfile(path_to_xml):
                    wav_file_paths.append(path_to_wav)
                    truth_dataset_format_tuples.append((path_to_xml, ds, 'xml'))
                else:
                    warn('Skipping ' + wav_file + ', no truth found.')
            else:
                warn('Skipping ' + path_to_wav + ', not a .wav file.')

    if 4 in active_datasets:
        for path_to_ds in [
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset4\Career SG'),
            os.path.join(DATA_DIR, r'IDMT-SMT-GUITAR_V2\dataset4\Ibanez 2820')
        ]:
            for tempo in listdir(path_to_ds):
                path_to_tempo = os.path.join(path_to_ds, tempo)
                for genre in listdir(path_to_tempo):
                    path_to_genre = os.path.join(path_to_tempo, genre)
                    path_to_audio = os.path.join(path_to_genre, 'audio')
                    for wav_file in listdir(path_to_audio):
                        path_to_wav = os.path.join(path_to_audio, wav_file)
                        if wav_file.endswith('.wav'):
                            path_to_onsets = os.path.join(path_to_genre, 'annotation', 'onsets')
                            if isdir(path_to_onsets):
                                path_to_csv = os.path.join(path_to_onsets, wav_file.replace('.wav', '.csv'))
                                if isfile(path_to_csv):
                                    wav_file_paths.append(path_to_wav)
                                    truth_dataset_format_tuples.append((path_to_csv, 4, 'csv'))
                                else:
                                    # TODO fallback to other formats
                                    warn('Skipping ' + path_to_wav + ', no truth csv found.')
                            else:
                                warn('Skipping ' + path_to_wav + ', no onset folder.')
                        else:
                            warn('Skipping ' + path_to_wav + ', not a .wav file.')

    return wav_file_paths, truth_dataset_format_tuples


def read_X_y(path_to_wav, frame_rate_hz, expected_sample_rate, subsampling_step,
             path_to_truth, truth_format, dataset):
    """Read samples and labels of a wave file.

    Returns a tuple (X_part, y_part, y_actual_onset_only_part)
    """

    X_part, length_seconds = read_X(path_to_wav, frame_rate_hz, expected_sample_rate, subsampling_step)
    if X_part is not None:
        y_part, y_actual_onset_only_part = read_y(truth_format, path_to_truth, length_seconds, frame_rate_hz, dataset)
        if X_part.shape[0] != y_part.shape[0]:
            raise ValueError('X_part vs. y_part shape mismatch: ' + str(X_part.shape[0]) + ' != ' + str(y_part.shape[0]))
        return X_part, y_part, y_actual_onset_only_part
    else:
        return None, None, None


def read_X(path_to_wav, frame_rate_hz, expected_sample_rate, subsampling_step):
    """Read samples of a wave file. Returns a tuple (sample_np_array, length_seconds)."""

    # scipy.io.wavfile is not able to read 24-bit data, hence the need to use this alternative library
    samples, sample_rate = soundfile.read(path_to_wav)
    if len(samples.shape) > 1:
        warn('Skipping ' + path_to_wav + ', cannot handle stereo signal.')
        return None, -1
    elif sample_rate != expected_sample_rate:
        warn('Skipping ' + path_to_wav +
             ', sample rate ' + str(sample_rate) + ' != expected sample rate ' + str(expected_sample_rate) + '.')
        return None, -1

    if sample_rate % frame_rate_hz != 0:
        raise ValueError('Sample rate ' + str(sample_rate) + ' % frame rate ' + str(frame_rate_hz) + ' != 0')
    samples_per_frame = int(sample_rate / frame_rate_hz)
    offset = 0
    X = []
    # Cut off last samples
    while offset <= len(samples) - samples_per_frame:
        X.append(samples[offset:offset + samples_per_frame:subsampling_step])
        offset += samples_per_frame

    X = np.array(X)
    return X, offset / sample_rate


def read_y(truth_format, path_to_truth, length_seconds, frame_rate_hz, dataset):
    """Read labels of a wave file. Returns a tuple (y_part, y_actual_onset_only_part)."""

    if truth_format == 'xml':
        y_part, y_actual_onset_only_part = read_y_xml(path_to_truth, length_seconds, frame_rate_hz, dataset)
    elif truth_format == 'csv':
        y_part, y_actual_onset_only_part = read_y_csv(path_to_truth, length_seconds, frame_rate_hz, dataset)
    else:
        raise ValueError('Unknown truth format')

    return y_part, y_actual_onset_only_part


def read_y_xml(path_to_xml, length_seconds, frame_rate_hz, dataset):
    """Read labels of a wave file (xml format, datasets 1, 2, 3). Returns a tuple (y_part, y_actual_onset_only_part)."""

    tree = ElementTree.parse(path_to_xml)
    root = tree.getroot()
    y = _init_y(length_seconds, frame_rate_hz)
    y_actual_onset_only = _init_y(length_seconds, frame_rate_hz)
    for root_child in root:
        if root_child.tag == 'transcription':
            for event in root_child:
                if event.tag != 'event':
                    raise ValueError('Unexpected XML element, expected event, got ' + event.tag)
                for event_child in event:
                    if event_child.tag == 'onsetSec':
                        onset_time = float(event_child.text)
                        index = _onset_index(onset_time, frame_rate_hz)
                        # _set_onset_label_orig_with_neighbors(y, y_actual_onset_only, index)
                        _set_onset_label_adjusted_with_neighbors(y, y_actual_onset_only, index, dataset)
            break

    return y, y_actual_onset_only


def read_y_csv(path_to_csv, length_seconds, frame_rate_hz, dataset):
    """Read labels of a wave file (csv format, dataset 4). Returns a tuple (y_part, y_actual_onset_only_part)."""

    y = _init_y(length_seconds, frame_rate_hz)
    y_actual_onset_only = _init_y(length_seconds, frame_rate_hz)
    with open(path_to_csv) as f:
        for line in f:
            line_split = line.rstrip().split(',')
            onset_time = float(line_split[0])
            index = _onset_index(onset_time, frame_rate_hz)
            # _set_onset_label_orig_with_neighbors(y, y_actual_onset_only, index)
            _set_onset_label_adjusted_with_neighbors(y, y_actual_onset_only, index, dataset)

    return y, y_actual_onset_only


def _init_y(length_seconds, frame_rate_hz):
    return np.zeros(int(round(frame_rate_hz * length_seconds)), dtype=np.int8)


def _onset_index(onset_time, frame_rate_hz):
    return int(onset_time * frame_rate_hz)


def _set_onset_label_orig(y, y_actual_onset_only, index):
    y[index] = 1
    y_actual_onset_only[index] = 1


def _set_onset_label_orig_with_neighbors(y, y_actual_onset_only, index):
    # index = 5: start = 4, end = 7, 4:7 = 1 -> 4, 5, 6 = 1
    start = max(0, index - 1)
    end = min(len(y), index + 2)
    y[start:end] = 1
    y_actual_onset_only[index] = 1


def _set_onset_label_adjusted_with_neighbors(y, y_actual_onset_only, index, dataset):
    """Adjusted by fitting a model on dataset 4 with original labels and setting the offset per dataset to where
    the prediction results were best using this model."""

    # No adjustment needed for 1 and 3.
    # The labels of dataset 4 seem to be on spot - the onset is visible around the original label.
    if dataset == 2:
        index += 3

    start = max(0, index - 1)
    end = min(len(y), index + 2)
    y[start:end] = 1
    y_actual_onset_only[index] = 1
