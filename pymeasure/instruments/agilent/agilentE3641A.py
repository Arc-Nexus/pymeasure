#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2017 PyMeasure Developers
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
#

from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import truncated_range,strict_range,strict_discrete_set

from io import StringIO
import numpy as np
import pandas as pd


class AgilentE3641A(Instrument):
    """ Represents the AgilentE3641A power supply.
    """

    voltage_dc = Instrument.measurement("MEAS:VOLT:DC? DEF,DEF", "DC voltage, in Volts")
    
    current_dc = Instrument.measurement("MEAS:CURR:DC? DEF,DEF", "DC current, in Amps")

    voltage = Instrument.control(
        ":VOLT?", ":VOLT %g", 
        """ A floating point property that controls the voltage
        in Volts. This property can be set.
        """,
        validator=strict_range,
        values=[0,60]
        )

    output = Instrument.control(
        ":OUTP?", ":OUTP %s"
        """ Set the ouput state: ON, OFF
        """,
        validator=strict_discrete_set,
        values=["ON","OFF"]
    )
    def __init__(self, resourceName, **kwargs):
        super(HP34401A, self).__init__(
            resourceName,
            "Agilent E3641A",
            **kwargs
        )