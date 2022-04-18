#!/usr/bin/env python3
"""Load an audio file into memory and play its contents.

NumPy and the soundfile module (https://python-soundfile.readthedocs.io/)
must be installed for this to work.

This example program loads the whole file into memory before starting
playback.
To play very long files, you should use play_long_file.py instead.

This example could simply be implemented like this::

    import sounddevice as sd
    import soundfile as sf

    data, fs = sf.read('my-file.wav')
    sd.play(data, fs)
    sd.wait()

... but in this example we show a more low-level implementation
using a callback stream.

"""
import argparse
import threading

import sounddevice as sd
import soundfile as sf
import numpy as np
from numpy import convolve as np_convolve

from scipy import signal

# Build a Kaiser window filter with "optimal" length and
# "beta" for -40 dB of passband and stopband ripple and a
# 0.05 transition bandwidth. Prescale the coefficients to
# preserve the input amplitude.
#print(len(subband))

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    'filename', metavar='FILENAME',
    help='audio file to be played back')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='output device (numeric ID or substring)')
args = parser.parse_args(remaining)

event = threading.Event()

try:
    data, fs = sf.read(args.filename, always_2d=True)

    nopt, bopt = signal.kaiserord(-40, 0.05)
    print(nopt)
    subband = signal.firwin(1, 0.45, window=('kaiser', bopt), width = 0.05, pass_zero=False)
    
    b = signal.firwin(1, [0.05, 0.95], width=0.05, pass_zero=False)

    #filteredData = np.array([np_convolve(xi, subband, mode='valid') for xi in data])
    filteredData = signal.lfilter(subband, [1.0], data)[:, len(subband) - 1:]
    print(len(filteredData))
    current_frame = 0

    #filteredData = np.zeros(len(data), dtype = float)

    #for i in range(fs):
    #    for j in range(len(data)):
    #        filteredData[i] = subband[1] * data[i - j]

    decimationData = filteredData[::2]

    def callback(outdata, frames, time, status):
        global current_frame
        if status:
            print(status)
        chunksize = min(len(data) - current_frame, frames)
        outdata[:chunksize] = data[current_frame:current_frame + chunksize]
        if chunksize < frames:
            outdata[chunksize:] = 0
            raise sd.CallbackStop()
        current_frame += chunksize

    sf.write('r' + args.filename, decimationData, int(fs / 2))
    stream = sd.OutputStream(
        samplerate=fs, device=args.device, channels=data.shape[1],
        callback=callback, finished_callback=event.set)
    with stream:
        event.wait()  # Wait until playback is finished
except KeyboardInterrupt:
    parser.exit('\nInterrupted by user')
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))