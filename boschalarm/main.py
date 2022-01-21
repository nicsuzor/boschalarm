"""Main module."""
import inspect
import logging
import select
import sys
import time
import backoff
from logging import getLogger
from socket import *

import numpy as np
from tlslite.api import *
import ssl

from boschalarm.codes import (
    BoschComands,
    Languages,
    areaStatus,
    AlarmTypes,
    ArmingType,
    ActionResults,
    ResponseTypes,
)

TIMEOUT_SECONDS = 5


def list_to_bit_array_int(indices, n=None):
    # Output an integer that is the representation of a binary array
    # with each bit in _indices_ switched on and the rest zero.
    # e.g. list_to_bit_array_int([4,6], n=8) = int(01010000) = 80 = 0x50

    if not n:
        n = max(indices)

    out = ""

    for i in range(n):
        out += "1" if i in indices else "0"

    return int(out, 2)


def bitArray(n, reverse=False):
    if isinstance(n, str):
        n = int(n, 16)  # presume hex
    try:
        bit_list = [1 if digit == "1" else 0 for digit in bin(n)[2:]]
        if reverse:
            return bit_list[::-1]
        else:
            return bit_list

    except TypeError as e:
        getLogger().error('Unable to convert "{n}" to bit array: {e}.')
        return None


def hex(integer_value, bytes=1):
    if bytes == 1:
        return f"{integer_value:0>02X}"
    elif bytes == 2:
        return f"{integer_value:0>04X}"
    elif bytes == 4:
        return f"{integer_value:0>08X}"
    else:
        raise NotImplementedError


class Bosch:
    ### This library attempts to replicate with a Bosch security system B426 IP module.
    ### It is primarily aimed at the Solution 2000/3000 devices, but should work for others.
    ### The protocol is not complete. It uses a serial format that has to be reverse-engineered, and
    ### MANY features are still not working.
    ###
    ### The main methods are connect(), auth(), and send_receive()
    ### send_receive() expects a string of hex formatted bytes.

    def __init__(self, ip, port=7700, logger=None):
        if logger:
            self.logger = logger
        else:
            self.logger = getLogger(__name__)
        self.ip = ip
        self.port = port
        self.ssock = None

        self.configured_points = None
        self.configured_areas = None
        self.configured_outputs = None
        self.numberOfPoints = None
        self.numberOfOutputs = None
        self.numberOfUsers = None
        self.numberOfKeypads = None
        self.numberOfDoors = None
        self.eventRecordSize = None

        try:
            self.connect()
        except ssl.SSLError as e:
            raise OSError(f'Could not connect to socket: {e}')

        self.auth()
        self.requestCapacities()
        self.requestConfiguredAreas()
        self.requestConfiguredPoints()
        self.requestConfiguredOutputs()

    @backoff.on_exception(backoff.expo, OSError, max_tries=5)
    def connect(self):
        # retry on SSL errors and other connection errors
        # All should be inherited from OSError: https://www.python.org/dev/peps/pep-3151/

        sock = socket.create_connection((self.ip, self.port))
        context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        self.ssock = context.wrap_socket(sock)
        self.ssock.setblocking(False)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.ssock.close()

    def auth(self):
        self.whatareyou()
        self.checkpass()
        self.checkpin()

    def send_receive(self, data):
        self.send(data)
        try:
            return self.receive()
        except TimeoutError:
            self.logger.error(f"Timeout reading from stream...")
            return None, None

    def send(self, data):
        data = bytes.fromhex(data)
        length = len(data)
        length = bytes.fromhex(f"{length:0>2X}")
        start = bytes.fromhex("01")

        to_send = start + length + data
        self.ssock.send(to_send)

    def receive(self):
        ## Format is:
        ## REPLY_TYPE LENGTH_BYTE RESPONSE_TYPE SUCCESS DATA
        ## e.g.: 01 04 ff 0a0b0c0d

        self.ssock.setblocking(0)
        ready = select.select([self.ssock], [], [], TIMEOUT_SECONDS)
        if ready[0]:
            try:
                data = self.ssock.recv(4096)
                n = data[1]  # length of data excluding header info

                if len(data) != n + 2:
                    self.logger.error(
                        f"Received incorrect data from socket. Expected {n+2} bytes, received: {data}."
                    )

                if n <= 0:
                    self.logger.error(f"Empty response received: {data}")
                    return None, None

                try:
                    response_type = ResponseTypes(data[2]).name
                except (ValueError, TypeError):
                    self.logger.error(
                        f"Unable to translate response code into ResponseTypes: {data}."
                    )
                    response_type = None

                if response_type == ResponseTypes.Ack:
                    return True, None
                elif response_type == ResponseTypes.Nak:
                    return False, None

                # Otherwise, process data
                response = data[3:]  # main body of data received, after length byte
                if response[0] >= 65 and response[0] <= 122:  # ascii character
                    response = "".join(
                        [chr(int(r)) for r in response[:-1]]
                    )  # ignore last byte, which should be \x00
                else:
                    response = response.hex()

                return True, response

            except (ConnectionError, ssl.SSLError) as e:
                self.logger.error(f"Unable to read from stream: {e}")
                return None, None
        else:
            self.logger.error(f"Timeout waiting for response.")
            return None, None

    def panelState(self):
        return self.request(BoschComands.PANEL_STATE)

    def subscribe(self):
        return self.request(BoschComands.SUBSCRIBE_ALL)

    def whatareyou(self):
        response = self.request(BoschComands.WHATAREYOU)
        response = bytes.fromhex(response)
        self.logger.info(f"Product id: {response[0]}")
        self.logger.info(f"RPS Protocol version: {[r for r in response[1:4]]}")
        self.logger.info(f"Automation Protocol version: {[r for r in response[5:8]]}")
        self.logger.info(f"Execute Protocol version: {[r for r in response[9:12]]}")
        self.logger.info(f"Busy: {response[13]}")

    def checkpass(self, passcode="0000000000"):
        data = "0600" + passcode + "00"
        return self.request(data)

    def checkpin(self, pin="2580"):
        data = "3E" + pin
        return self.request(data)

    def requestCapacities(self):
        response = self.request(BoschComands.REQUEST_CAPACITIES)

        maxAreas = int(response[5:6], 16) - 1
        self.numberOfPoints = int(response[7:11], 16)
        self.numberOfOutputs = int(response[11:15], 16)
        self.numberOfUsers = int(response[16:19], 16)
        self.numberOfKeypads = int(response[20:21], 16)
        self.numberOfDoors = int(response[21:22], 16)
        self.eventRecordSize = int(response[23:24], 16)

        self.logger.info(
            f"Areas: {maxAreas}; Points: {self.numberOfPoints}; Outputs: {self.numberOfOutputs}; Users: {self.numberOfUsers}; Keypads: {self.numberOfKeypads}; Doors: {self.numberOfDoors}; Event record size: {self.eventRecordSize}"
        )
        return response

    def requestConfiguredPoints(self):
        response = self.request(BoschComands.REQUEST_CONFIGURED_POINTS)
        active = np.nonzero(bitArray(response))
        active = [n for areas in active for n in areas]
        names = [self.requestPointText(n) for n in active]

        self.configured_points = dict(zip(active, names))

        self.logger.info(f"Configured points: {self.configured_points}")
        return active

    def requestConfiguredAreas(self):
        response = self.request(BoschComands.REQUEST_CONFIGURED_AREAS)
        active = np.nonzero(bitArray(response, reverse=False))
        active = [int(n + 1) for n in active]
        names = [self.requestAreaText(n) for n in active]
        self.configured_areas = dict(zip(active, names))

        self.logger.info(f"Configured areas: {self.configured_areas}")
        return active

    def requestAreaText(self, area):
        data = BoschComands.REQUEST_AREA_TEXT + hex(area, 2) + hex(Languages.English.value, 2)
        return self.request(data)

    def requestPointText(self, point):
        data = BoschComands.REQUEST_POINT_TEXT + hex(point, 2) + hex(Languages.English.value, 2)
        return self.request(data)

    def requestAlarmPriorities(self):
        return self.request(BoschComands.REQUEST_ALARM_PRIORITIES)

    def RequestAlarmAreasByPriority(self, value):
        data = BoschComands.REQUEST_ALARM_AREAS + f"{value:0>4X}"
        return self.request(data)

    def requestAllPoints(self):
        response = self.request(BoschComands.REQUEST_FAULTED_POINTS)

        end_length = 16
        try:
            binary_response = bin(int(response, 16))[2:].zfill(end_length)
        except (ValueError, TypeError):
            self.logger.error(f"Unable to update points. Response: {response}.")
            return None

        zones = []
        for i, status in enumerate(binary_response):
            state = status == "1"
            z = dict(index=i, state=state)
            zones.append(z)
        self.logger.info(f"All points: {response}: {zones}")

        return zones

    def requestAreaStatus(self, area):
        response = self.request(BoschComands.REQUEST_AREA_STATUS + hex(area, 4))

        try:
            response = bytes.fromhex(response)
            area_number = int(response[:1].hex(), 16) + 1
            arming_state = areaStatus(response[5]).name
            alarm_mask = "{:08b}".format(int(response[3:4].hex(), 16))
            status = dict(state=arming_state, alarm_mask=alarm_mask)
            self.logger.info(
                f"Area {area_number} state: {arming_state}, alarms: {alarm_mask}"
            )
        except (TypeError, KeyError, IndexError) as e:
            self.logger.error(
                f"Unable to decode area status: {response}, {[w for w in response]}.\n{e}"
            )
            return None
        except ValueError as e:
            self.logger.error(f"Unable to decode area status: {response}.\n{e}")
            return None

        return status

    def requestFaultedPoints(self):
        zones = self.requestAllPoints()
        zones = [z for z in zones if z["state"]]
        self.logger.info(f"Faulted points: {zones}")

        return zones

    def requestAreasNotReady(self):
        return self.request(BoschComands.REQUEST_AREAS_NOT_READY)

    def armAreas(self, arm_type: ArmingType, area_indices=None):
        # Format: 01 LEN 0x27 BIT_ARRAY_FOR_AREAS
        # e.g. 01 02 27 80
        if area_indices:
            data = list_to_bit_array_int(area_indices, n=4)
        else:
            # appply to all configured areas
            data = list_to_bit_array_int(self.configured_areas.keys(), 4)

        data = hex(data, bytes=1)

        data = BoschComands.ARM_AREAS + hex(arm_type.value, bytes=1) + data

        result = self.action_command(data)

        self.logger.info(f"Setting alarm state to {arm_type.name}. Result: {result}.")
        return result

    def requestTextHistoryLimits(self):
        command = f"{BoschComands.REQUEST_TEXT_HISTORY}0100000000"
        response = self.request(command)
        command = f"{BoschComands.REQUEST_TEXT_HISTORY}01FFFFFFFF"
        response = self.request(command)
        return response

    def requestTextHistory(self, numEvents=1, lastEvent=0):
        command = f"{BoschComands.REQUEST_TEXT_HISTORY}{numEvents:0>2X}{lastEvent:0>8X}"
        return self.request(command)

    def requestHistory(self, numEvents, lastEvent):
        command = f"{BoschComands.REQUEST_TEXT_HISTORY}{numEvents:0>2X}{lastEvent:0>8X}"
        return self.request(command)

    def requestOutputText(self, output, language=0):
        command = (
                BoschComands.REQUEST_OUTPUT_TEXT + hex(output) + hex(Languages.English.value, 2)
        )
        return self.request(command)

    def requestConfiguredOutputs(self):
        response = self.request(BoschComands.REQUEST_OUTPUTS)
        active = np.nonzero(bitArray(response))
        active = [n for areas in active for n in areas]

        names = [self.requestOutputText(n) for n in active]
        self.configured_outputs = dict(zip(active, names))

        self.logger.info(f"Configured outputs: {active}")
        return active

    def requestConfiguredDoors(self):
        return self.request(BoschComands.REQUEST_CONFIGURED_DOORS)

    def requestOutputStatus(self):
        data = BoschComands.REQUEST_OUTPUT_STATUS
        response = self.request(data)

        response = bitArray(response, reverse=True)

        for o in self.configured_outputs:
            self.logger.info(f"Output {o.value} state: {response[o]}")

        return np.nonzero(response)

    def requestPointsInArea(self, area):
        data = BoschComands.REQUEST_POINTS_IN_AREA + hex(area, 2)
        return self.request(data)

    def requestPointStatus(self, points):
        data = BoschComands.REQUEST_POINTS_IN_AREA + hex(points, 2)
        return self.request(data)

    def request(self, data):
        result, response = self.send_receive(data)
        caller = inspect.currentframe().f_back.f_code.co_name
        self.logger.debug(
            f"{caller} sent: {data}. Success: {result}. Received: {response}."
        )
        return response

    def action_command(self, data):
        result, response = self.send_receive(data)
        try:
            response = ActionResults(int(response)).name
        except (ValueError, TypeError, KeyError):
            self.logger.error(
                f"Unable to translate response code into ActionResults: {response}."
            )

        caller = inspect.currentframe().f_back.f_code.co_name
        self.logger.debug(
            f"{caller} sent: {data}. Success: {result}. Received: {response}."
        )
        return response

    def getStatus(self):
        status = []
        for i in self.configured_areas.keys():
            state = dict(area=self.configured_areas[i])
            state.update(self.requestAreaStatus(i))
            state.update(alarms=self.RequestAlarmAreasByPriority(i))

            status.append(state)

        self.logger.info(f"Status update: {status}")
        return status

    def requestSubscriptions(self):
        return self.request(BoschComands.REQUEST_SUBSCRIPTIONS)

    def requestAlarmDetail(self, alarm_type):
        data = BoschComands.GET_ALARM_MEMORY + hex(alarm_type, 2)
        return self.request(data)

    def silenceAlarms(self, *areas):
        data = [hex(area, 2) for area in areas]
        data = BoschComands.SILENCE_ALARMS + " ".join(data)
        return self.request(data)

    def soundAlarms(self, *areas):
        data = [hex(area, 2) for area in areas]
        data = BoschComands.SOUND_ALARMS + " ".join(data)
        return self.request(data)

    def setOutput(self, output, state: bool):
        data = BoschComands.SET_OUTPUT_STATE + hex(output) + hex(int(state))
        return self.request(data)

    def getReport(self, test_report: bool):
        if test_report:
            return self.request(BoschComands.GET_REPORT_TEST)
        else:
            return self.request(BoschComands.GET_REPORT)

