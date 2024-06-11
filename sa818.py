#!/usr/bin/env python3
#
# BSD 2-Clause License
#
# Copyright (c) 2022-2023 Fred W6BSD
# All rights reserved.
#

__doc__ = """sa818"""

import argparse
import logging
import os
import re
import sys
import textwrap
import time

import serial

logging.basicConfig(format='%(name)s: %(levelname)s: %(message)s',
                    level=logging.INFO)
logger = logging.getLogger('SA818')


CTCSS = (
  "None", "67.0", "71.9", "74.4", "77.0", "79.7", "82.5", "85.4", "88.5",
  "91.5", "94.8", "97.4", "100.0", "103.5", "107.2", "110.9", "114.8", "118.8",
  "123.0", "127.3", "131.8", "136.5", "141.3", "146.2", "151.4", "156.7",
  "162.2", "167.9", "173.8", "179.9", "186.2", "192.8", "203.5", "210.7",
  "218.1", "225.7", "233.6", "241.8", "250.3"
)

DCS_CODES = [
  "023", "025", "026", "031", "032", "036", "043", "047", "051", "053", "054",
  "065", "071", "072", "073", "074", "114", "115", "116", "125", "131", "132",
  "134", "143", "152", "155", "156", "162", "165", "172", "174", "205", "223",
  "226", "243", "244", "245", "251", "261", "263", "265", "271", "306", "311",
  "315", "331", "343", "346", "351", "364", "365", "371", "411", "412", "413",
  "423", "431", "432", "445", "464", "465", "466", "503", "506", "516", "532",
  "546", "565", "606", "612", "624", "627", "631", "632", "654", "662", "664",
  "703", "712", "723", "731", "732", "734", "743", "754"
]

BAUD_RATES = [300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]

DEFAULT_BAUDRATE = 9600


class SA818:
  EOL = "\r\n"
  INIT = "AT+DMOCONNECT"
  SETGRP = "AT+DMOSETGROUP"
  FILTER = "AT+SETFILTER"
  VOLUME = "AT+DMOSETVOLUME"
  TAIL = "AT+SETTAIL"
  NARROW = 0
  PORTS = ('/dev/serial0', '/dev/ttyUSB0')
  READ_TIMEOUT = 3.0

  def __init__(self, port=None, baud=DEFAULT_BAUDRATE):
    self.serial = None
    if port:
      ports = [port]
    else:
      ports = self.PORTS

    for _port in ports:
      try:
        self.serial = serial.Serial(port=_port, baudrate=baud,
                                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                    bytesize=serial.EIGHTBITS,
                                    timeout=self.READ_TIMEOUT)
        logger.debug(self.serial)
        break
      except serial.SerialException as err:
        logger.debug(err)

    if not isinstance(self.serial, serial.Serial):
      raise IOError('Error openning the serial port')

    self.send(self.INIT)
    reply = self.readline()
    if reply != "+DMOCONNECT:0":
      raise SystemError('Connection error') from None

  def close(self):
    self.serial.close()

  def send(self, *args):
    data = ','.join(args)
    logger.debug('Sending: %s', data)
    data = bytes(data + self.EOL, 'ascii')
    try:
      self.serial.write(data)
    except serial.SerialException as err:
      logger.error(err)

  def readline(self):
    try:
      line = self.serial.readline()
    except serial.SerialException as err:
      logger.warning(err)
      return None
    try:
      line = line.decode('ascii')
    except UnicodeDecodeError:
      logger.debug(line)
      logger.error('Character decode error: Check your baudrate')
    return line.rstrip()

  def version(self):
    self.send("AT+VERSION")
    time.sleep(0.5)
    reply = self.readline()
    try:
      version = re.split(r'[:_]', reply)
    except ValueError:
      logger.error('Unable to decode the firmeare version')
      return None

    logger.info('Firmware %s, version: %s', version[1], '_'.join(version[2:]))
    return version

  def set_radio(self, opts):
    tone = opts.ctcss if opts.ctcss else opts.dcs
    if tone:                # 0000 = No ctcss or dcs tone
      tx_tone, rx_tone = tone
    else:
      tx_tone, rx_tone = ['0000', '0000']

    if opts.offset == 0.0:
      tx_freq = rx_freq = f"{opts.frequency:.4f}"
    else:
      rx_freq = f"{opts.frequency:.4f}"
      tx_freq = f"{opts.frequency + opts.offset:.4f}"

    cmd = f"{self.SETGRP}={opts.bw},{tx_freq},{rx_freq},{tx_tone},{opts.squelch},{rx_tone}"
    self.send(cmd)
    time.sleep(1)
    response = self.readline()
    if response != '+DMOSETGROUP:0':
      logger.error('SA818 programming error')
    else:
      bw_label = ['Narrow', 'Wide'][opts.bw]
      if opts.ctcss:
        msg = "%s, BW: %s, Frequency (RX: %s / TX: %s), CTCSS (TX: %s / RX: %s), squelch: %s, OK"
        logger.info(msg, response, bw_label, rx_freq, tx_freq,
                    CTCSS[int(tx_tone)], CTCSS[int(rx_tone)], opts.squelch)
      elif opts.dcs:
        msg = "%s, BW: %s Frequency (RX: %s / TX: %s), DCD (TX: %s / RX: %s), squelch: %s, OK"
        logger.info(msg, response, bw_label, rx_freq, tx_freq,
                    tx_tone, rx_tone, opts.squelch)
      else:
        msg = "%s, BW: %s, RX frequency: %s, TX frequency: %s, squelch: %s, OK"
        logger.info(msg, response, bw_label, rx_freq, tx_freq, opts.squelch)

    if opts.tail is not None and opts.ctcss is not None:
      self.tail(opts)
    elif opts.tail is not None:
      logger.warning('Ignoring "--tail" specified without ctcss')

  def set_filter(self, opts):
    for key in ("emphasis", "highpass", "lowpass"):
      if getattr(opts, key) is None:
        setattr(opts, key, 1)
    _rx = {0: 'enabled', 1: 'disabled'}
    # filters are pre-emphasis, high-pass, low-pass
    cmd = f"{self.FILTER}={opts.emphasis},{opts.highpass},{opts.lowpass}"
    self.send(cmd)
    time.sleep(1)
    response = self.readline()
    if response != "+DMOSETFILTER:0":
      logger.error('SA818 set filter error')
    else:
      logger.info("%s filters [Pre/De]emphasis: %s, high-pass: %s, low-pass: %s",
                  response, _rx[opts.emphasis], _rx[opts.highpass], _rx[opts.lowpass])

  def set_volume(self, opts):
    cmd = f"{self.VOLUME}={opts.level:d}"
    self.send(cmd)
    time.sleep(1)
    response = self.readline()
    if response != "+DMOSETVOLUME:0":
      logger.error('SA818 set volume error')
    else:
      logger.info("%s Volume level: %d, OK", response, opts.level)

  def tail(self, opts):
    _oc = {True: "open", False: "close"}
    cmd = f"{self.TAIL}={int(opts.tail)}"
    self.send(cmd)
    time.sleep(1)
    response = self.readline()
    if response != "+DMOSETTAIL:0":
      logger.error('SA818 set filter error')
    else:
      logger.info("%s tail: %s", response, _oc[opts.tail])


def type_frequency(parg):
  try:
    frequency = float(parg)
  except ValueError:
    raise argparse.ArgumentError from None

  if not 144 < frequency < 148 and not 420 < frequency < 450:
    logger.error('Frequency outside the amateur bands')
    raise argparse.ArgumentError
  return frequency


def type_ctcss(parg):
  err_msg = 'Invalid CTCSS use the --help argument for the list of CTCSS'
  tone_codes = []
  codes = parg.split(',')
  if len(codes) == 1:
    codes.append(codes[0])
  elif len(codes) > 2:
    logger.error(err_msg)
    raise argparse.ArgumentError from None

  for code in codes:
    try:
      ctcss = str(float(code))
      if ctcss not in CTCSS:
        raise ValueError
      ctcss = CTCSS.index(ctcss)
      tone_codes.append(f"{ctcss:04d}")
    except ValueError:
      logger.error(err_msg)
      raise argparse.ArgumentTypeError from None

  return tone_codes


def type_dcs(parg):
  err_msg = 'Invalid DCS use the --help argument for the list of DCS'
  dcs_codes = []
  codes = parg.split(',')
  if len(codes) == 1:
    codes.append(codes[0])
  elif len(codes) > 2:
    logger.error(err_msg)
    raise argparse.ArgumentError from None

  for code in codes:
    if code[-1] not in ('N', 'I'):
      logger.error(err_msg)
      raise argparse.ArgumentError from None

    code, direction = code[:-1], code[-1]
    try:
      dcs = f"{int(code):03d}"
      if dcs not in DCS_CODES:
        logger.error(err_msg)
        raise argparse.ArgumentError
    except ValueError:
      raise argparse.ArgumentTypeError from None
    dcs_codes.append(dcs + direction)

  return dcs_codes


def type_squelch(parg):
  try:
    value = int(parg)
  except ValueError:
    raise argparse.ArgumentTypeError from None

  if value not in range(0, 9):
    logger.error('The value must must be between 0 and 8 (inclusive)')
    raise argparse.ArgumentError
  return value


def type_level(parg):
  try:
    value = int(parg)
  except ValueError:
    raise argparse.ArgumentTypeError from None

  if value not in range(1, 9):
    logger.error('The value must must be between 1 and 8 (inclusive)')
    raise argparse.ArgumentError
  return value


def enabledisable(parg):
  if parg.lower() == 'enable':
    return 0
  if parg.lower() == 'disable':
    return 1
  raise argparse.ArgumentTypeError("Possible values are [Enable/Disable]") from None


def openclose(parg):
  if parg is None:
    return None
  if parg.lower() in "open":
    return True
  if parg.lower() in "close":
    return False
  raise argparse.ArgumentTypeError("Possible values are [Open/Close]") from None


def set_loglevel():
  loglevel = os.getenv('LOGLEVEL', 'INFO')
  loglevel = loglevel.upper()
  try:
    logger.root.setLevel(loglevel)
  except ValueError:
    logger.warning('Loglevel error: %s', loglevel)


def format_codes():
  ctcss = textwrap.wrap(', '.join(CTCSS[1:]))
  dcs = textwrap.wrap(', '.join(DCS_CODES))

  codes = (
    "You can specify a different code for transmit and receive by separating "
    "them by a comma.\n",
    "> Example: --ctcss 94.8,127.3 or --dcs 043N,047N\n\n",
    f"CTCSS codes (PL Tones)\n{chr(10).join(ctcss)}",
    "\n\n",
    "DCS Codes:\n"
    "DCS codes must be followed by N or I for Normal or Inverse:\n",
    f"> Example: 047I\n{chr(10).join(dcs)}"
  )
  return ''.join(codes)


def command_parser():
  parser = argparse.ArgumentParser(
    description="generate configuration for switch port",
    epilog=format_codes(),
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )
  parser.add_argument("--debug", action="store_true", default=False)
  parser.add_argument("--port", type=str,
                      help="Serial port [default: linux console port]")
  parser.add_argument('--speed', type=int, choices=BAUD_RATES, default=DEFAULT_BAUDRATE,
                      help="Connection speed")
  subparsers = parser.add_subparsers()

  p_radio = subparsers.add_parser("radio", help='Program the radio (frequency/tome/squelch)')
  p_radio.set_defaults(func="radio")
  p_radio.add_argument('--bw', type=int, choices=(0, 1), default=1,
                       help="Bandwidth 0=NARROW (12.5KHz), 1=WIDE (25KHx) [default: WIDE]")
  p_radio.add_argument("--frequency", required=True, type=type_frequency,
                       help="Receive frequency")
  p_radio.add_argument("--offset", default=0.0, type=float,
                       help="Offset in MHz, 0 for no offset [default: %(default)s]")
  p_radio.add_argument("--squelch", type=type_squelch, default=4,
                       help="Squelch value (0 to 8) [default: %(default)s]")
  code_group = p_radio.add_mutually_exclusive_group()
  code_group.add_argument("--ctcss", default=None, type=type_ctcss,
                          help="CTCSS (PL Tone) 0 for no CTCSS [default: %(default)s]")
  code_group.add_argument("--dcs", default=None, type=type_dcs,
                          help=("DCS code must be the number followed by [N normal] or "
                                "[I inverse]  [default: %(default)s]"))
  p_radio.add_argument("--tail", default=None, type=openclose,
                       help="Close CTCSS Tail Tone (Open/Close)")

  p_volume = subparsers.add_parser("volume", help="Set the volume level")
  p_volume.set_defaults(func="volume")
  p_volume.add_argument("--level", type=type_level, default=4,
                        help="Volume value (1 to 8) [default: %(default)s]")

  p_filter = subparsers.add_parser("filters", aliases=['filter'], help="Enable/Disable filters")
  p_filter.set_defaults(func="filters")
  p_filter.add_argument("--emphasis", type=enabledisable,
                        help="[Pr/De]-emphasis (Enable/Disable) [default: disable]")
  p_filter.add_argument("--highpass", type=enabledisable,
                        help="High pass filter (Enable/Disable) [default: disable]")
  p_filter.add_argument("--lowpass", type=enabledisable,
                        help="Low pass filters (Enable/Disable) [default: disable]")

  p_version = subparsers.add_parser("version", help="Show the firmware version of the SA818")
  p_version.set_defaults(func="version")

  try:
    opts = parser.parse_args()
  except argparse.ArgumentTypeError as err:
    parser.error(str(err))

  if not hasattr(opts, 'func'):
    print('sa818: error: the following arguments are required: {radio,volume,filters,version}\n'
          'use --help for more informatiion',
          file=sys.stderr)
    raise SystemExit('Argument Error') from None

  return opts


def main():
  set_loglevel()
  opts = command_parser()

  if opts.debug:
    logger.setLevel(logging.DEBUG)

  logger.debug(opts)

  try:
    radio = SA818(opts.port, opts.speed)
  except (IOError, SystemError) as err:
    raise SystemExit(err) from None

  if opts.func == 'version':
    radio.version()
  elif opts.func == 'radio':
    radio.set_radio(opts)
  elif opts.func == 'filters':
    for key in ('emphasis', 'highpass', 'lowpass'):
      if getattr(opts, key) is not None:
        break
    else:
      logger.error('filters need at least one argument')
      raise SystemExit('Argument error') from None
    radio.set_filter(opts)
  elif opts.func == 'volume':
    radio.set_volume(opts)


if __name__ == "__main__":
  main()
