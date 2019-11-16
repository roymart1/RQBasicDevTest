"""
Classes: serialize.py
Class that contains all the logic of the rdte server.
https://www.universal-robots.com/how-tos-and-faqs/how-to/ur-how-tos/
real-time-data-exchange-rtde-guide-22229/

Copyright (c) 2016, Universal Robots A/S,
All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
   * Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
   * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.
   * Neither the name of the Universal Robots A/S nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL UNIVERSAL ROBOTS A/S BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from __future__ import absolute_import, division, print_function

import logging
import select
import socket
import struct
import sys

import rtde.serialize as Serialize
from common import CREDENTIALS_DICTIONNARY

LOGNAME = "rtde"
_log = logging.getLogger(LOGNAME)


class Command:
    """
    Command object that represents all the possible commands to send to the
    rdte server
    """

    RTDE_REQUEST_PROTOCOL_VERSION = 86  # ascii V
    RTDE_GET_URCONTROL_VERSION = 118  # ascii v
    RTDE_TEXT_MESSAGE = 77  # ascii M
    RTDE_DATA_PACKAGE = 85  # ascii U
    RTDE_CONTROL_PACKAGE_SETUP_OUTPUTS = 79  # ascii O
    RTDE_CONTROL_PACKAGE_SETUP_INPUTS = 73  # ascii I
    RTDE_CONTROL_PACKAGE_START = 83  # ascii S
    RTDE_CONTROL_PACKAGE_PAUSE = 80  # ascii P


class ConnectionState:
    """
    Connection state object that represents all the possible stats of the rdte
    connection
    """

    DISCONNECTED = 0
    CONNECTED = 1
    STARTED = 2
    PAUSED = 3


class RTDEException(Exception):
    """
    Exception object that will occur when there is an error in the rdte
    connection.
    """

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


def __unpack_protocol_version_package(payload):
    """
    Method that can unpack the protocol version package structure.
    If the size is not 1, it is not the correct payload.

    Args:
        payload (List[Bytes]): Received data.

    Returns:
    success (bool): True if it succeeded, false otherwise.
    """
    if len(payload) != 1:
        _log.error("RTDE_REQUEST_PROTOCOL_VERSION: Wrong payload size")
        return None
    # Else, serialize the payload.
    result = Serialize.ReturnValue.unpack(payload)
    # Return true if it was a success, false otherwise.
    return result.success


def __unpack_urcontrol_version_package(payload):
    """
    All the next methods are doing the same thing for their specific awaited
    payload.

    Args:
        payload (List[Bytes]): Received data.

    Returns:

    """
    if len(payload) != 16:
        _log.error("RTDE_GET_URCONTROL_VERSION: Wrong payload size")
        return None
    version = Serialize.ControlVersion.unpack(payload)
    return version


def __unpack_text_message(payload):
    if len(payload) < 1:
        _log.error("RTDE_TEXT_MESSAGE: No payload")
        return None
    msg = Serialize.Message.unpack(payload)
    if (
        msg.level == Serialize.Message.EXCEPTION_MESSAGE
        or msg.level == Serialize.Message.ERROR_MESSAGE
    ):
        _log.error(msg.source + ": " + msg.message)
    elif msg.level == Serialize.Message.WARNING_MESSAGE:
        _log.warning(msg.source + ": " + msg.message)
    elif msg.level == Serialize.Message.INFO_MESSAGE:
        _log.info(msg.source + ": " + msg.message)


def __unpack_setup_outputs_package(payload):
    if len(payload) < 1:
        _log.error("RTDE_CONTROL_PACKAGE_SETUP_OUTPUTS: No payload")
        return None
    output_config = Serialize.DataConfig.unpack_recipe(payload)
    return output_config


def __unpack_setup_inputs_package(payload):
    if len(payload) < 1:
        _log.error("RTDE_CONTROL_PACKAGE_SETUP_INPUTS: No payload")
        return None
    input_config = Serialize.DataConfig.unpack_recipe(payload)
    return input_config


def __unpack_start_package(payload):
    if len(payload) != 1:
        _log.error("RTDE_CONTROL_PACKAGE_START: Wrong payload size")
        return None
    result = Serialize.ReturnValue.unpack(payload)
    return result.success


def __unpack_pause_package(payload):
    if len(payload) != 1:
        _log.error("RTDE_CONTROL_PACKAGE_PAUSE: Wrong payload size")
        return None
    result = Serialize.ReturnValue.unpack(payload)
    return result.success


def __unpack_data_package(payload, output_config):
    if output_config is None:
        _log.error("RTDE_DATA_PACKAGE: Missing output configuration")
        return None
    output = output_config.unpack(payload)
    return output


def __list_equals(l1, l2):
    """
    Equality operator between two lists, If the lenght is different, the lists
    are different

    Args:
        (List[Object]): First list.
        (List[Object]): Second list.

    Returns:
        (Bool): True if the list has the same content, false otherwise
    """
    if len(l1) != len(l2):
        return False
    # If any value is different, the lists are different
    for i in range(len(l1)):
        if l1[i] != l2[i]:
            return False
    # Else, they are the same
    return True


class RTDE(object):
    """
    Constructor
    RTDE object that represents an RDTE connection with a robot
    """

    def __init__(
        self,
        hostname,
        port=CREDENTIALS_DICTIONNARY["RTDE_PORT"],
        defaultTimeout=1.0,
        rtdeProtocolVersion=2,
    ):
        """
        Args:
            hostname (String): Ip address to connect to.
            port (Int): Port to use (should be 30 004
            defaultTimeout:
            rtdeProtocolVersion:
        """
        self.hostname = hostname
        self.port = port
        self.defaultTimeout = defaultTimeout
        self.rtdeProtocolVersion = rtdeProtocolVersion

        self.__conn_state = ConnectionState.DISCONNECTED
        self.__sock = None
        self.__output_config = None
        self.__input_config = {}
        self.__buf = b""  # buffer data in binary format

    # Connection method that will connect to the desired socket
    def connect(self):
        # If there is already a socket, exit that function
        if self.__sock:
            return

        try:
            # Create the socket with the correct values
            self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.__sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # Set the timeout
            self.__sock.settimeout(self.defaultTimeout)
            # Connect to the robot on the correct port
            self.__sock.connect((self.hostname, self.port))
            # Change the state of the connection to "Connected"
            self.__conn_state = ConnectionState.CONNECTED

        # If there is a socket error or the timeout exceeds, raise an
        # error and close the socket
        except (socket.timeout, socket.error):
            self.__sock = None
            raise

        # If we didn't manage to negotiate the protocol version, raise an error
        if not self.negotiate_protocol_version():
            raise RTDEException("Unable to negotiate protocol version")

    # Disconnect from the server
    def disconnect(self):
        # If there is a socket in use
        if self.__sock:
            # Close it and set it to none
            self.__sock.close()
            self.__sock = None
        # Set the connection state to "Disconnected"
        self.__conn_state = ConnectionState.DISCONNECTED

    # Boolean method that will return true if the connection state is
    # different than "DISCONNECTED"
    def is_connected(self):
        return self.__conn_state is not ConnectionState.DISCONNECTED

    def get_controller_version(self):
        """
        Method that will get the version of the robot to which we are connected

        Returns:
        major (String): Major version of the robot (None if failed to connect)
        minor (String): Minor version of the robot (None if failed to connect)
        bugfix (String): Bugfix version of the robot (None if failed to connect
        build (String): Build version of the robot (None if failed to connect)
        """
        # Set the command to set to "RTDE_GET_URCONTROL_VERSION" (ascii = V)
        cmd = Command.RTDE_GET_URCONTROL_VERSION
        # Send the command and store the result
        version = self.__sendAndReceive(cmd)
        # If the result is not none
        if version:
            # Log the controller version (major, minor, bugfix and build)
            _log.info(
                "Controller version: "
                + str(version.major)
                + "."
                + str(version.minor)
                + "."
                + str(version.bugfix)
                + "."
                + str(version.build)
            )

            # If the version is not valid
            if (
                version.major == 3
                and version.minor <= 2
                and version.bugfix < 19171
            ):
                # Log an error and exit the method
                _log.error(
                    "Please upgrade your controller to minimally "
                    "version 3.2.19171"
                )
                sys.exit()

            # Return the major, minor, bugfix and build versions
            return version.major, version.minor, version.bugfix, version.build
        # If we didn't connect, return 4 none objects.
        return None, None, None, None

    def negotiate_protocol_version(self):
        """
        Method that will try to find a compatible protocol to communicate with
        the RDTE server

        Returns:
            success (Object): Object representing the answer from the server.
            None if it is not a success.
        """
        # Set the command to the request protocol version (ascii = v)
        cmd = Command.RTDE_REQUEST_PROTOCOL_VERSION
        # Set the requested protocol version to the one we selected above
        payload = struct.pack(">H", self.rtdeProtocolVersion)
        # Send the command and store its result
        success = self.__sendAndReceive(cmd, payload)
        # Return true if it was successful, false otherwise
        return success

    # Method that will send the input format that we want from the server
    def send_input_setup(self, variables, types=[]):
        cmd = Command.RTDE_CONTROL_PACKAGE_SETUP_INPUTS
        payload = bytearray(",".join(variables), "utf-8")
        result = self.__sendAndReceive(cmd, payload)
        if len(types) != 0 and not __list_equals(result.types, types):
            _log.error(
                "Data type inconsistency for input setup: "
                + str(types)
                + " - "
                + str(result.types)
            )
            return None
        result.names = variables
        self.__input_config[result.id] = result
        return Serialize.DataObject.create_empty(variables, result.id)

    def send_output_setup(self, variables, types=[], frequency=125):
        """
        Method that will send the output format that we want from the server

        Args:
            variables:
            types:
            frequency:

        Returns:

        """
        cmd = Command.RTDE_CONTROL_PACKAGE_SETUP_OUTPUTS
        payload = struct.pack(">d", frequency)
        payload = payload + (",".join(variables).encode("utf-8"))
        result = self.__sendAndReceive(cmd, payload)
        if len(types) != 0 and not __list_equals(result.types, types):
            _log.error(
                "Data type inconsistency for output setup: "
                + str(types)
                + " - "
                + str(result.types)
            )
            return False
        result.names = variables
        self.__output_config = result
        return True

    def send_start(self):
        """
        Method that will synchronize with the RDTE server

        Returns:
            success (Object): Object representing the answer from the server.
            None if it is not a success.
        """
        # Set the required command
        cmd = Command.RTDE_CONTROL_PACKAGE_START
        # Send it to the server and store the answer
        success = self.__sendAndReceive(cmd)
        # If it was a success, change the connection state
        if success:
            _log.info("RTDE synchronization started")
            self.__conn_state = ConnectionState.STARTED
        # Else, log the synchronization error
        else:
            _log.error("RTDE synchronization failed to start")
        # Return the server's answer
        return success

    # Same as send_start, but to pause the data transfer.
    def send_pause(self):
        cmd = Command.RTDE_CONTROL_PACKAGE_PAUSE
        success = self.__sendAndReceive(cmd)
        if success:
            _log.info("RTDE synchronization paused")
            self.__conn_state = ConnectionState.PAUSED
        else:
            _log.error("RTDE synchronization failed to pause")
        return success

    def send(self, input_data):
        """
        Send data to the RDTE server

        Args:
            input_data (List[Bytes]): Data to send.

        Returns:
            (Bool): True if it was a success, false otherwise.
        """
        # Check is the connection is started
        if not self.__connection_started_check():
            return

        # If the configuration id was not found, log an error
        if input_data.recipe_id not in self.__input_config:
            _log.error(
                "Input configuration id not found: "
                + str(input_data.recipe_id)
            )
            return
        # Get the configuration using the recipe ID
        config = self.__input_config[input_data.recipe_id]
        # Pack and send the package. Return true if it was a success,
        # false otherwise.
        return self.__sendall(
            Command.RTDE_DATA_PACKAGE, config.pack(input_data)
        )

    def receive(self):
        """
        Receive data from the RDTE server

        Returns:
            (List[Bytes]): Received data.
        """
        # If the output configuration is not initialized, log an error.
        if self.__output_config is None:
            _log.error("Output configuration not initialized")
            return None
        # Check is the connection is started
        if not self.__connection_started_check():
            return None

        # Return the received data
        return self.__recv(Command.RTDE_DATA_PACKAGE)

    def send_message(
        self,
        message,
        source="Python Client",
        data_type=Serialize.Message.INFO_MESSAGE,
    ):
        """
        Sends a text message to the server

        Args:
            message (String): Text message to send.
            source (String): Source of the message.
            data_type (Serialize.Message.type): Type of the data to send.

        Returns:
            (Bool): True if it was a success, false otherwise.
        """
        # Set the command to a text message
        cmd = Command.RTDE_TEXT_MESSAGE
        # Create the message header
        fmt = ">B%dsB%dsB" % (len(message), len(source))
        # Pack the message into a list
        payload = struct.pack(
            fmt, len(message), message, len(source), source, data_type
        )
        # Send the message. Return true if it's a success, false otherwise.
        return self.__sendall(cmd, payload)

    def __on_packet(self, cmd, payload):
        """
        Method that is called when we receive a packet from the RDTE server to
        unpack the data depending on the incoming
        message type.

        Args:
            cmd (String): Command that was used.
            payload (List[Bytes]): Payload of the message.

        Returns:
            (Object): Unpacked data
        """
        if cmd == Command.RTDE_REQUEST_PROTOCOL_VERSION:
            return __unpack_protocol_version_package(payload)
        elif cmd == Command.RTDE_GET_URCONTROL_VERSION:
            return __unpack_urcontrol_version_package(payload)
        elif cmd == Command.RTDE_TEXT_MESSAGE:
            return __unpack_text_message(payload)
        elif cmd == Command.RTDE_CONTROL_PACKAGE_SETUP_OUTPUTS:
            return __unpack_setup_outputs_package(payload)
        elif cmd == Command.RTDE_CONTROL_PACKAGE_SETUP_INPUTS:
            return __unpack_setup_inputs_package(payload)
        elif cmd == Command.RTDE_CONTROL_PACKAGE_START:
            return __unpack_start_package(payload)
        elif cmd == Command.RTDE_CONTROL_PACKAGE_PAUSE:
            return __unpack_pause_package(payload)
        elif cmd == Command.RTDE_DATA_PACKAGE:
            return __unpack_data_package(payload, self.__output_config)
        # If it was not a known command, log an error.
        else:
            _log.error("Unknown package command: " + str(cmd))

    def __sendAndReceive(self, cmd, payload=b""):
        """
        Method that sends a command with a paylod and returns the server's response

        Args:
            cmd (String): Command to send.
            payload (List[Bytes]): Payload (data) to send.

        Returns:
            (Object): Server's answer if it exists, none otherwise.
        """
        # Send the message to the server and see if it worked
        if self.__sendall(cmd, payload):
            # If it did, return the received data object
            return self.__recv(cmd)
        # Else, return none.
        else:
            return None

    def __sendall(self, command, payload=b""):
        """
        Method that will send all the data (often when too big) and manage I/O interruptions.

        Args:
            command (String): Command to send.
            payload (List[Bytes]): Payload (data) to send.

        Returns:
            (Bool): True if it succeeded, false otherwise.
        """
        # Create the message header
        fmt = ">HB"
        # Calculate the size of the message
        size = struct.calcsize(fmt) + len(payload)
        # Pack the data
        buf = struct.pack(fmt, size, command) + payload

        # If there is no socket, log an error
        if self.__sock is None:
            _log.error("Unable to send: not connected to Robot")
            return False

        # Else, wait for the socket to be usable
        _, writable, _ = select.select(
            [], [self.__sock], [], self.defaultTimeout
        )

        # If it is available
        if len(writable):
            # Send the message and return true
            self.__sock.sendall(buf)
            return True
        # Else, return false and trigger the disconnected method
        else:
            self.__trigger_disconnected()
            return False

    def has_data(self):
        """
        Method that returns true when the socket has readable data

        Returns:
            (Bool): True if the socket has readable data, false otherwise
        """
        # Set the timeout to 0 (we don't want to wait)
        timeout = 0
        # Wait for the socket to be available and store its content
        readable, _, _ = select.select([self.__sock], [], [], timeout)
        # If it has any data, return true. Else, return false.
        return len(readable) != 0

    def __recv(self, command):
        """
        Method that will manage the reception of a RDTE message

        Args:
            command (String): Command that has been received

        Returns:
            data (List[Bytes]): Received data.
        """
        # While the server is connected
        while self.is_connected():
            # Check the availability of the sockets
            readable, _, xlist = select.select(
                [self.__sock], [], [self.__sock], self.defaultTimeout
            )
            # If there is some readable data
            if len(readable):
                # Receive the data (4096b sized packet)
                more = self.__sock.recv(4096)
                # If the received data is empty
                if len(more) == 0:
                    # Disconnect the server
                    self.__trigger_disconnected()
                    return None
                # Else, add the packet to the data
                self.__buf = self.__buf + more

            if (
                len(xlist) or len(readable) == 0
            ):  # Effectively a timeout of DEFAULT_TIMEOUT seconds
                _log.info("lost connection with controller")
                self.__trigger_disconnected()
                return None

            # unpack_from requires a buffer of at least 3 bytes
            while len(self.__buf) >= 3:
                # Attempts to extract a packet
                packet_header = Serialize.ControlHeader.unpack(self.__buf)

                # If our buffer is bigger or equal to the header of the packet
                if len(self.__buf) >= packet_header.size:
                    # Do some packet magic
                    packet, self.__buf = (
                        self.__buf[3 : packet_header.size],
                        self.__buf[packet_header.size :],
                    )
                    # Call the "on_packet" method to create the correct
                    # data strucutre
                    data = self.__on_packet(packet_header.command, packet)
                    # Basically, do some RDTE specific stuff
                    if (
                        len(self.__buf) >= 3
                        and command == Command.RTDE_DATA_PACKAGE
                    ):
                        next_packet_header = Serialize.ControlHeader.unpack(
                            self.__buf
                        )
                        if next_packet_header.command == command:
                            _log.info("skipping package(1)")
                            continue
                    if packet_header.command == command:
                        return data
                    else:
                        _log.info("skipping package(2)")
                else:
                    break
        return None

    def __trigger_disconnected(self):
        """
        Method that will simply disconnect the server and log the information.
        """
        _log.info("RTDE disconnected")
        self.disconnect()

    def __connection_started_check(self):
        """
        Method that will make sure the connection has the state "Started"
        If the connection is not started, log an error and return false

        Returns:
            (Bool): True if the connection has the state Started, false otherwise.
        """
        if self.__conn_state != ConnectionState.STARTED:
            _log.error("Cannot receive when RTDE synchronization is inactive")
            return False

        return True
