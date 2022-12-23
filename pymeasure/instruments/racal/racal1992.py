#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2022 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
import time

from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import strict_discrete_range

log = logging.getLogger(__name__)   # https://docs.python.org/3/howto/logging.html#library-config
log.addHandler(logging.NullHandler())


class Racal1992(Instrument):
    """ Represents the Racal-Dana 1992 Universal counter

    .. code-block:: python

        from pymeasure.instruments.racal import Racal1992
        counter = Racal1992("GPIB0::10")

    This class should also work for Racal-Dana 1991, it has the same
    product manual, as long as you don't use functionality that requires
    channel B.
    """

    resolution = Instrument.setting(
            " SRS %d",
            """ An integer from 3 to 9 that specifies the number
            of significant digits. """,
            validator=strict_discrete_range,
            values=range(3, 10),
            map_values=True
    )

    def __init__(self, adapter, name="Racal-Dana 1992", **kwargs):
        kwargs.setdefault('write_termination', '\r\n')

        super().__init__(
            adapter,
            name,
            **kwargs
        )

    int_types = ['SF', 'RS', 'UT', 'MS', 'TA']
    float_types = ['CK', 'FA', 'PA', 'TI', 'PH', 'RA', 'MX', 'MZ', 'LA', 'LB', 'FC', 'RC']

    channel_params = {
        'A' : {                                                         # noqa
            'coupling'      : { 'AC'   : 'AAC',  'DC'     : 'ADC' },    # noqa
            'attenuation'   : { 'X1'   : 'AAD',  'X10'    : 'AAE' },    # noqa
            'trigger'       : { 'auto' : 'AAU',  'manual' : 'AMN' },    # noqa
            'impedance'     : { '50'   : 'ALI',  '1M'     : 'AHI' },    # noqa
            'slope'         : { 'pos'  : 'APS',  'neg'    : 'ANS' },    # noqa
            'filtering'     : { True   : 'AFE',  False    : 'AFD' },    # noqa
            'trigger_level' : None,                                     # noqa
            },
        'B' : {                                                         # noqa
            'coupling'      : { 'AC'        : 'BAC',  'DC'     : 'BDC' },    # noqa
            'attenuation'   : { 'X1'        : 'BAD',  'X10'    : 'BAE' },    # noqa
            'trigger'       : { 'auto'      : 'BAU',  'manual' : 'BMN' },    # noqa
            'impedance'     : { '50'        : 'BLI',  '1M'     : 'BHI' },    # noqa
            'slope'         : { 'pos'       : 'BPS',  'neg'    : 'BNS' },    # noqa
            'input_select'  : { 'separate'  : 'BCS',  'common' : 'BCC' },    # noqa
            'trigger_level' : None,                                     # noqa
            },
    }

    operating_modes = {
        'self_check'      : 'CK',    # noqa
        'frequency_a'     : 'FA',    # noqa
        'period_a'        : 'PA',    # noqa
        'phase_a_rel_b'   : 'PH',    # noqa
        'ratio_a_to_b'    : 'RA',    # noqa
        'ratio_c_to_b'    : 'RC',    # noqa
        'interval_a_to_b' : 'TI',    # noqa
        'total_a_by_b'    : 'TA',    # noqa
        'frequency_c'     : 'FC',    # noqa
    }

    def read_and_decode(self, allowed_types=None):
        v = self.read_bytes(21)
        val_type = v[0:2].decode('utf-8')
        val = float(v[2:19].decode('utf-8'))

        if allowed_types and val_type not in allowed_types:
            raise Exception("Unexpected value type returned")

        if val_type in Racal1992.int_types:
            return int(val)
        elif val_type in Racal1992.float_types:
            return val
        else:
            raise Exception("Unsupported return type")

    def set_param(self, param, value=None):
        self.write(f" S{param} {value}")

    def fetch_param(self, param):
        self.write(' R' + param)
        self.wait_for()
        return self.read_and_decode(allowed_types=param)

    # ============================================================
    # Channel-specific settings
    # ============================================================
    def channel_settings(self, channel_name, **kwargs):
        if channel_name not in Racal1992.channel_params:
            raise Exception("Channel name must by 'A' or 'B'")

        settings_str = ""
        trigger_str = ""

        for setting, value in kwargs.items():
            if setting not in Racal1992.channel_params[channel_name]:
                raise Exception(f"Channel {channel_name} does not support a {setting} setting")

            accepted_values = Racal1992.channel_params[channel_name][setting]
            if accepted_values is None:
                # Trigger level has a float parameter...
                # Use special string for that because it's used the
                # last setting of all.
                if value < -51 or value > 51:
                    raise Exception(f"{value} is out of range for {setting}")
                trigger_str = f" SL{channel_name} {value}"
                continue

            if value not in accepted_values:
                raise Exception(f"{value} is not an acceptable value for {setting}")

            command = accepted_values[value]

            settings_str += " " + command

        self.write(settings_str + trigger_str)

    # ============================================================
    # IP - Instrument Preset
    # ============================================================
    def preset(self):
        self.write(' IP')
        pass

    # ============================================================
    # RE - Reset measurement
    # ============================================================
    def reset_measurement(self):
        self.write(' RE')
        pass

    # ============================================================
    # MS - Software Version
    # ============================================================
    @property
    def software_version(self):
        """Special function. An integer value between 10 and 78.

        Check manual for further information.

        """
        return self.fetch_param('MS')

    # ============================================================
    # MX - Math Constant X
    # ============================================================
    @property
    def math_x(self):
        """Math constant X.

        """
        return self.fetch_param('MX')

    @math_x.setter
    def math_x(self, value):
        self.set_param('MX', value)

    # ============================================================
    # MZ - Math Constant Z
    # ============================================================
    @property
    def math_z(self):
        """Math constant Z.

        """
        return self.fetch_param('MZ')

    @math_z.setter
    def math_z(self, value):
        self.set_param('MZ', value)

    # ============================================================
    # ME/MD - Math function enable/disable
    # ============================================================
    # FIXME: How to make this a setter when there's no corresponding getter?
    def math_mode(self, enable):
        """Math mode

        enable: True enables math mode. False disables it.

        """
        if enable:
            self.write(' ME')
        else:
            self.write(' MD')

    # ============================================================
    # RS - Resolution
    # ============================================================
    @property
    def resolution(self):
        """Number of significant digits.

        This must be an integer from 3 to 10.

        """
        return self.fetch_param('RS')

    @resolution.setter
    def resolution(self, value):
        strict_discrete_range(value, range(3, 11), 1)
        self.set_param('RS', value)

    # ============================================================
    # SF - Special Function
    # ============================================================
    @property
    def special_function(self):
        """Special function. An integer value between 10 and 78.

        Check manual for further information.

        """
        return self.fetch_param('SF')

    # ============================================================
    # UT - Unit
    # ============================================================
    @property
    def unit(self):
        """Device type. Should return 1992."""
        return self.fetch_param('UT')

    # ============================================================
    # Lx - Trigger level A or B
    # ============================================================
    def trigger_level(self, channel_name):
        if channel_name not in ('A', 'B'):
            raise Exception("Channel name must by 'A' or 'B'")

        return self.fetch_param(f'L{channel_name}')

    # ============================================================
    # Set operating mode
    # ============================================================
    def operating_mode(self, mode):
        if mode not in Racal1992.operating_modes:
            raise Exception(f"{mode} is not a valid operating mode")

        self.write(' ' + Racal1992.operating_modes[mode])
        pass

    # ============================================================
    # Wait for measurement value
    # ============================================================
    def wait_for_measurement(self, timeout=None, progressDots=False):
        if timeout is not None:
            end_time = time.time() + timeout

        while True:
            if progressDots:
                log.info(".")

            stb = self.adapter.connection.read_stb()
            if stb & 0x10:
                break

            if timeout is not None and time.time() > end_time:
                raise Exception("Timeout while waiting for measurement")

        return stb

    # ============================================================
    # Measured value
    # ============================================================
    @property
    def measured_value(self):
        """Measured value."""
        return self.read_and_decode(allowed_types=Racal1992.operating_modes.values())
