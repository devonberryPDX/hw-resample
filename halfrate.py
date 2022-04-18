# HW2 - Resampling
# Devon Berry 2022

import argparse
import threading

import sounddevice as sd
import soundfile as sf

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
# Guide I used: https://scipy-cookbook.readthedocs.io/items/ApplyFIRFilter.html?highlight=half%20band%20filter
data, fs = sf.read(args.filename, always_2d=True)

nopt, bopt = signal.kaiserord(-40, 0.05)
subband = signal.firwin(1, 0.45, window=('kaiser', bopt), scale=True)

filteredData = signal.lfilter(subband, [1.0], data)[:, len(subband) - 1:]

decimationData = filteredData[::2]

sf.write('r' + args.filename, decimationData, int(fs / 2))