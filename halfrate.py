# HW2 - Resampling
# Devon Berry 2022

import argparse
import threading

import sounddevice as sd
import soundfile as sf
import numpy as np

from scipy import signal

#-----------------------------------------------------------------------
# Argument parser
# From https://python-sounddevice.readthedocs.io/en/0.4.0/examples.html
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
#-----------------------------------------------------------------------
# Resampling
data, fs = sf.read(args.filename)

nopt, bopt = signal.kaiserord(-40, 0.05)
subband = signal.firwin(nopt, 0.45, window=('kaiser', bopt), scale=True)

filteredData = np.zeros(len(data))

for i in range(len(subband), len(data)):
    temp = 0
    for j in range(len(subband - 1)):
         temp += subband[j] * data[i - j]

    filteredData[i] = temp
    
decimationData = filteredData[::2]

sf.write('r' + args.filename, decimationData, int(fs / 2))