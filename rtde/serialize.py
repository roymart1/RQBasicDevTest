"""
Classes: serialize.py
Author: Universal Robots

Commented by: Frederic Vaugeois (f.vaugeois@robotiq.com)


Class that contains all the objects needed to serialize/deserialize a rdte
message.

More info here:
#  https://www.universal-robots.com/how-tos-and-faqs/how-to/ur-how-tos/
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

import struct  # Data structure manager


def getItemSize(dataType):
    """
    Gets the size of an object depending on its data type name

    Args:
        dataType (String): Data type of the object

    Returns:
        (Integer): Size of the object
    """
    # If it's a vector 6, its size is 6
    if dataType.startswith("VECTOR6"):
        return 6
    # If it,s a vector 3, its size is 6
    elif dataType.startswith("VECTOR3"):
        return 3
    # Else its size is only 1
    return 1


def unpackField(data, offset, dataType):
    """
    Unpacks a message in the correct type
    Args:
        data (Object): The data object
        offset (Int): Offset showing where the real data starts
        dataType (String): Data type of the object

    Returns:
        (Object): The casted result of the message.
    """
    # Lets start by getting the size of the object
    size = getItemSize(dataType)
    # If it's a vector 6D or 3D
    if dataType == "VECTOR6D" or dataType == "VECTOR3D":
        # Return a float list of the data
        return [float(data[offset + i]) for i in range(size)]
    # Else, if it's a vector6 uint 32
    elif dataType == "VECTOR6UINT32":
        # Return an integer list of the data
        return [int(data[offset + i]) for i in range(size)]
    # Else, if it's double
    elif dataType == "DOUBLE":
        # Return a float list of the data
        return float(data[offset])
    # You get the gist.
    elif dataType == "UINT32" or dataType == "UINT64":
        return int(data[offset])
    elif dataType == "VECTOR6INT32":
        return [int(data[offset + i]) for i in range(size)]
    elif dataType == "INT32" or dataType == "UINT8":
        return int(data[offset])
    elif dataType == "BOOL":
        return bool(data[offset])
    # If no data was found, the data type was not recognized
    raise ValueError("unpackField: unknown data type: " + dataType)


class ControlHeader(object):
    """
    Found strings in the message that represent a header
    """

    __slots__ = ["command", "size"]

    @staticmethod
    def unpack(buf):
        """
        Unpack method of the header

        Args:
            buf (List[bytes]): List containing the data.

        Returns:
            (ControlHeader): Control header object representation of the data.
        """
        rmd = ControlHeader()
        (rmd.size, rmd.command) = struct.unpack_from(">HB", buf)
        return rmd


class ControlVersion(object):
    """
    The next two classes are a copy of the header object, but specific to
    their object representation.
    """

    __slots__ = ["major", "minor", "bugfix", "build"]

    @staticmethod
    def unpack(buf):
        rmd = ControlVersion()
        (rmd.major, rmd.minor, rmd.bugfix, rmd.build) = struct.unpack_from(
            ">IIII", buf
        )
        return rmd


class ReturnValue(object):
    __slots__ = ["success"]

    @staticmethod
    def unpack(buf):
        rmd = ReturnValue()
        rmd.success = bool(struct.unpack_from(">B", buf)[0])
        return rmd


# Message object
class Message(object):
    # Found strings in a message representing a message object
    __slots__ = ["level", "message", "source"]

    # List of the types of messages
    EXCEPTION_MESSAGE = 0
    ERROR_MESSAGE = 1
    WARNING_MESSAGE = 2
    INFO_MESSAGE = 3

    @staticmethod
    def unpack(buf):
        """
        Unpack method for a message

        Args:
            buf (List[bytes]): List containing the data.

        Returns:
            (Message): Message object representation of the data.
        """
        # Create a message object
        rmd = Message()
        # Set the offset to 0
        offset = 0
        # Find the length of the message
        msgLength = struct.unpack_from(">B", buf, offset)[0]

        # Add 1 to the offset to read the message data
        offset = offset + 1
        # The message is the part of the array between the offset and
        # the end of the message
        rmd.message = buf[offset : offset + msgLength]

        # Update the offset to be at the end of the message
        offset = offset + msgLength
        # Get the length of the source of the message
        srcLength = struct.unpack_from(">B", buf, offset)[0]

        # Update the offset to read the source data
        offset = offset + 1
        # The source is the part of the array between the offset
        # and the end of the source
        rmd.source = buf[offset : offset + srcLength]

        # Update the offset to be at the end of the source
        offset = offset + srcLength
        # The level is the remaining part of the buffer
        rmd.level = struct.unpack_from(">B", buf, offset)[0]

        return rmd


class DataObject(object):
    # Set the id of the recipe to none
    recipeId = None

    def pack(self, names, types):
        """
        A method that will pack a recipe into a data object

        Args:
            names (List[String]): List of the names of the recipe.
            types (List[String]): List of the types of the recipe.

        Returns:
            packedData (List[bytes]): List of the bytes of the data object
        """
        # If there is a different ammount of names and types, it doesn't match
        if len(names) != len(types):
            raise ValueError("List sizes are not identical.")

        # Create the list of the packedData
        packedData = []

        # If the id of the recipe is not none
        if self.recipeId is not None:
            # Add the recipe id to the packed data
            packedData.append(self.recipeId)

        # For all names in the recipe
        for i in range(len(names)):
            # If the names have not already been initialized,
            # there has been an error
            if self.__dict__[names[i]] is None:
                raise ValueError("Uninitialized parameter: " + names[i])

            # If the data is a vector
            if types[i].startswith("VECTOR"):
                # Extend the list with the names
                packedData.extend(self.__dict__[names[i]])
            # Else, its a single value
            else:
                # So append it
                packedData.append(self.__dict__[names[i]])

        # Return the resulting list
        return packedData

    @staticmethod
    def unpack(data, names, types):
        """
        A method that will unpack a message

        Args:
            data (List[Bytes]): List of bytes to unpack
            names (List[String]): List of names of the recipe.
            types (List[String]): List of types of the recipe.

        Returns:
            obj (DataObject): Unpacked data.
        """
        # If the names and types don't have the same length, it doesn't match
        if len(names) != len(types):
            raise ValueError("List sizes are not identical.")
        # Create a data object to store the unpacked data
        obj = DataObject()
        # Set the offset to 0
        offset = 0
        # The recipeId of the object should be at index 0
        obj.recipeId = data[0]
        # For all the names of the recipe
        for i in range(len(names)):
            # Fetch the name in the data array with the unpack field method
            obj.__dict__[names[i]] = unpackField(data[1:], offset, types[i])
            # Update the offset to be equal to the length of the fetched data
            offset += getItemSize(types[i])
        # Return the resulting data object
        return obj

    @staticmethod
    def create_empty(names, recipeId):
        """
        A method that will create an empty data object with an Id

        Args:
            names (List[String]): List of the names of the recipe.
            recipeId (String): Id of the recipe.

        Returns:
            obj (DataObject): Empty unpacked data.
        """
        # Create a data object
        obj = DataObject()
        # For all the desired names
        for i in range(len(names)):
            # Set them to none
            obj.__dict__[names[i]] = None
        # Set the desired recipe ID to the desired one
        obj.recipeId = recipeId
        # Return the empty data object
        return obj


class DataConfig(object):
    """
    Data config object that is the complete representation of a configuration
    object
    """

    # Strings found int he data object representing a configuration object
    __slots__ = ["id", "names", "types", "fmt"]

    @staticmethod
    def unpack_recipe(buf):
        """
        A method that will unpack a data object that is expected to be a recipe

        Args:
            buf (List[bytes]): Data list of the message.

        Returns:
            recipe (Recipe): Recipe obtained by parsing the data of the message
        """
        # Create a data configuration object
        recipe = DataConfig()
        # The ID should be the first index of the array
        recipe.id = struct.unpack_from(">B", buf)[0]
        # All the types should be separated by commas, so the list of
        # types should be easily obtainable by splitting the array with
        # that char, starting at index 1.
        recipe.types = buf.decode("utf-8")[1:].split(",")
        # String that will hold a keyword representing the data types.
        recipe.fmt = ">B"
        # For all types
        for i in recipe.types:
            # If it's int32, add the keyword i.
            if i == "INT32":
                recipe.fmt += "i"
            # Etc.
            elif i == "UINT32":
                recipe.fmt += "I"
            elif i == "VECTOR6D":
                recipe.fmt += "d" * 6
            elif i == "VECTOR3D":
                recipe.fmt += "d" * 3
            elif i == "VECTOR6INT32":
                recipe.fmt += "i" * 6
            elif i == "VECTOR6UINT32":
                recipe.fmt += "I" * 6
            elif i == "DOUBLE":
                recipe.fmt += "d"
            elif i == "UINT64":
                recipe.fmt += "Q"
            elif i == "UINT8":
                recipe.fmt += "B"
            elif i == "BOOL":
                recipe.fmt += "?"
            # If the type is "IN_USE", that parameter is already in use!
            elif i == "IN_USE":
                raise ValueError("An input parameter is already in use.")
            # If we have found an unkown data type, raise an error.
            else:
                raise ValueError("Unknown data type: " + i)

        # Return the created recipe
        return recipe

    def pack(self, state):
        """
        Dark magic shenanigans that were created by UR

        Args:
            state:

        Returns:
        """
        state_pack = state.pack(self.names, self.types)
        return struct.pack(self.fmt, *state_pack)

    def unpack(self, data):
        """
        Method that will unpack data to create a data configuration object

        Args:
            data (List[Bytes]): List of the data.

        Returns:
            (DataObject): The unpacked data.
        """
        # Unpack the data with the structure library
        li = struct.unpack_from(self.fmt, data)
        # Unpack it with our DataObject implementation and return the result
        return DataObject.unpack(li, self.names, self.types)
