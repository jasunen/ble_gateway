#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
# This file deal with RuuviTag formated message
#
# Copyright (c) 2017 François Wautier
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
# IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE

from math import sqrt

#
# A few convenience functions
#


def twos_complement(val, n):
    if (val & (1 << (n - 1))) != 0:
        val = val - (1 << n)
    return val


def rshift(val, n):
    """
    Arithmetic right shift, preserves sign bit.
    https://stackoverflow.com/a/5833119 .
    """
    return (val % 0x100000000) >> n


def scale_n_round(d, key, scale, digits):
    if key in d:
        d[key] = round(d[key] * scale, digits)


# Ruuvi tag stuffs


class RuuviTagRaw(object):
    """
    Class defining the content of an Ruuvi Tag advertisement.
    Decodes RAWv1 and RAWv2 (Data Formats 3 and 5).
    """

    def __init__(self):
        pass

    # Get sign using first bit and return value with sign + fraction
    def _helper_temp_df3(self, int, frac):
        if (int >> 7) & 1:
            return -(int & ~(1 << 7)) - frac / 100.0
        return (int & ~(1 << 7)) + frac / 100.0

    def _decode_df3(self, data, result):
        result["data_format"] = 3
        result["humidity"] = data[1] / 2.0
        result["temperature"] = self._helper_temp_df3(data[2], data[3])
        result["pressure"] = int.from_bytes(data[4:6], "big") + 50000
        dx = int.from_bytes(data[6:8], "big", signed=True)
        dy = int.from_bytes(data[8:10], "big", signed=True)
        dz = int.from_bytes(data[10:12], "big", signed=True)
        length = sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        result["acceleration"] = length
        result["acceleration_x"] = int(dx)
        result["acceleration_y"] = int(dy)
        result["acceleration_z"] = int(dz)
        result["battery"] = int.from_bytes(data[12:14], "big")

    def _decode_df5(self, data, result):
        result["data_format"] = 5

        if data[1:2] == 0x7FFF:
            temp = None
        else:
            temp = twos_complement((data[1] << 8) + data[2], 16) / 200
        result["temperature"] = temp

        if data[3:4] == 0xFFFF:
            humidity = None
        else:
            humidity = ((data[3] & 0xFF) << 8 | data[4] & 0xFF) / 400
        result["humidity"] = humidity

        if data[5:6] == 0xFFFF:
            pressure = None
        else:
            pressure = ((data[5] & 0xFF) << 8 | data[6] & 0xFF) + 50000
        result["pressure"] = pressure

        dx = twos_complement((data[7] << 8) + data[8], 16)
        dy = twos_complement((data[9] << 8) + data[10], 16)
        dz = twos_complement((data[11] << 8) + data[12], 16)
        length = sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        result["acceleration"] = length
        result["acceleration_x"] = int(dx)
        result["acceleration_y"] = int(dy)
        result["acceleration_z"] = int(dz)
        result["movement_counter"] = data[15] & 0xFF
        result["measurement_sequence_number"] = (data[16] & 0xFF) << 8 | data[17] & 0xFF

        """Return battery voltage and tx power"""
        power_info = (data[13] & 0xFF) << 8 | (data[14] & 0xFF)
        battery_voltage = rshift(power_info, 5) + 1600
        tx_power = (power_info & 0b11111) * 2 - 40

        if rshift(power_info, 5) == 0b11111111111:
            battery_voltage = None
        if (power_info & 0b11111) == 0b11111:
            tx_power = None

        result["battery"] = battery_voltage
        result["tx_power"] = tx_power

    def decode(self, packet):  # must return none for unsuccesfull decode
        result = {}

        mfg_specific_data = packet.retrieve("Payload for mfg_specific_data")
        if mfg_specific_data:
            val = mfg_specific_data[0].val
            if val[0] == 0x99 and val[1] == 0x04:  # looks like Ruuvi
                val = val[2:]
                if val[0] == 0x03:  # data format 3
                    self._decode_df3(val, result)
                elif val[0] == 0x05:  # data format 5
                    self._decode_df5(val, result)
                else:
                    return None

                # Scale and round results
                scale_n_round(result, "humidity", 1, 1)
                scale_n_round(result, "temperature", 1, 2)
                scale_n_round(result, "pressure", 1 / 100, 2)
                scale_n_round(result, "acceleration", 1, None)
                scale_n_round(result, "battery", 1 / 1000, 2)

                return result

        return None
