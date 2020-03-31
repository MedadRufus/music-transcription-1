# MuTr
Transcribe guitar recordings in WAVE format to Midi format.  
Pipeline steps:
- Onset detection
- Polyphonic pitch detection
- String and fret detection
- Tempo detection
- Mapping of onset times to discrete notes in measures
- Midi export
  
The system is implemented in Python 3.5.

## Installation
This is currently only tested for Windows 10, but other platforms should work as well.
1. Download and extract this repository.
2. Download and install Anaconda3 64-bit (https://www.continuum.io/downloads).
3. Create and activate a new environment containing all relevant modules using the following commands in an Anaconda prompt:
   ```
   conda env create -f $INSTALLDIR/conda_env.yml
   activate music_transcription_3
   ```
4. Change the following Keras attributes in the file %USERPROFILE%/.keras/keras.json ($HOME/.keras/keras.json for \*nix):
   ```
   "image_data_format": "channels_first"
   "backend": "theano"
   ```
   More info: https://keras.io/backend/  
5. (optional) To speed up the CNNs used for onset and pitch detection and if you have a fast GPU, consider running Keras / Theano on the   GPU. For even more speed, activate CuDNN and CNMeM. See these two links:  
   http://ankivil.com/installing-keras-theano-and-dependencies-on-windows-10/  
   http://ankivil.com/making-theano-faster-with-cudnn-and-cnmem-on-windows-10/  
   
   This is recommended if you plan to train new models.

## Getting started
Open an Anaconda Prompt and switch the working directory to $INSTALLDIR/pipelines.  
  
Transcribe a recording using polyphonic pitch detection:
```
python guitar_pipeline.py ..\example_recordings\instrumental_lead.wav
```
Transcribe a recording using monophonic pitch detection and a custom output path:
```
python guitar_pipeline.py ..\example_recordings\instrumental_lead.wav -m mono -p instrumental_lead.mono.gp5
```