from music_transcription.onset_detection.cnn_onset_detection import CnnOnsetDetector
from sklearn.model_selection import train_test_split

from music_transcription.onset_detection.read_data import get_wav_and_truth_files


def predict_test_split():
    """Load model, predict test split and show metrics."""

    active_datasets = {1, 2, 3, 4}

    wav_file_paths, truth_dataset_format_tuples = get_wav_and_truth_files(active_datasets)
    wav_file_paths_train, wav_file_paths_test, truth_dataset_format_tuples_train, truth_dataset_format_tuples_test = train_test_split(
        wav_file_paths, truth_dataset_format_tuples, test_size=0.2, random_state=42
    )

    onset_detector = CnnOnsetDetector.from_zip('../models/20170511-3-channels_ds1-4_80-perc_adjusted-labels.zip')

    print('TEST')
    onset_detector.predict_print_metrics(wav_file_paths_test, truth_dataset_format_tuples_test)


def predict_file(wav_file):
    """Predict single file and show metrics."""
    active_datasets = {1, 2, 3, 4}
    wav_file_paths, truth_dataset_format_tuples = get_wav_and_truth_files(active_datasets)
    wav_file_paths_train, wav_file_paths_test, truth_dataset_format_tuples_train, truth_dataset_format_tuples_test = train_test_split(
        wav_file_paths, truth_dataset_format_tuples, test_size=0.2, random_state=42
    )

    # print([wav_file_path
    #        for wav_file_path, truth_dataset_format_tuple
    #        in zip(wav_file_paths_test, truth_dataset_format_tuples_test)
    #        if 'metal' in wav_file_path])
    # exit()

    tuples_train = [(wav_file_path, truth_dataset_format_tuple)
                    for wav_file_path, truth_dataset_format_tuple
                    in zip(wav_file_paths_train, truth_dataset_format_tuples_train)
                    if wav_file_path.endswith(wav_file)]
    assert len(tuples_train) == 0

    tuples_test = [(wav_file_path, truth_dataset_format_tuple)
                    for wav_file_path, truth_dataset_format_tuple
                    in zip(wav_file_paths_test, truth_dataset_format_tuples_test)
                    if wav_file_path.endswith(wav_file)]

    onset_detector = CnnOnsetDetector.from_zip('../models/20170511-3-channels_ds1-4_80-perc_adjusted-labels.zip')
    onset_detector.predict_print_metrics([tuples_test[0][0]], [tuples_test[0][1]])

# predict_test_split()
predict_file(r'Ibanez 2820\fast\metal\audio\metal_2_180BPM.wav')
predict_file(r'IDMT-SMT-GUITAR_V2\dataset3\audio\pathetique_mono.wav')
