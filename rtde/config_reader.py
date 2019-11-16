# ------------------------------------------------------------------------------------
## Classes: config_reader.py
## Author: Universal Robots
##
## Commented by: Frederic Vaugeois (f.vaugeois@robotiq.com)
##
##
## Class that contains two objects that are used to read a XML configuration file.
##
## More info here:
##  https://www.universal-robots.com/how-tos-and-faqs/how-to/ur-how-tos/real-time-data-exchange-rtde-guide-22229/
##
# ------------------------------------------------------------------------------------
# Copyright (c) 2016, Universal Robots A/S,
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the Universal Robots A/S nor the names of its
#      contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL UNIVERSAL ROBOTS A/S BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ------------------------------------------------------------------------------------
# Used librairies
# ------------------------------------------------------------------------------------
from __future__ import absolute_import, division, print_function

import sys  # Program execution management
import xml.etree.ElementTree as ET  # XML file parser library


# Recipe python object that represents a recipe XML object.
class Recipe:
    # These are the keywords found in the XML file for each recipe
    __slots__ = ["key", "names", "types"]

    # Recipe parser
    #
    # @param-in recipe_node (XMLRecipe): The recipe to parse
    #
    #
    # @param-out rmd (Recipe): The Python recipe obtained from parsing the XML
    @staticmethod
    def parse(recipe_node):
        # Create a recipe
        recipe = Recipe()
        # Get the key value of the recipe node
        recipe.key = recipe_node.get("key")
        # Get all the names in that recipe
        recipe.names = [f.get("name") for f in recipe_node.findall("field")]
        # Get all the types in that recipe
        recipe.types = [f.get("type") for f in recipe_node.findall("field")]
        # Return the Python recipe object
        return recipe

    # Recipe creator
    @staticmethod
    def createRecipe(key, names, types):
        # Create a recipe
        recipe = Recipe()
        # Set its values
        recipe.key = key
        recipe.names = names
        recipe.types = types
        # Return the new recipe
        return recipe


# Config python object that represents the XML file.
class ConfigFile:

    # Constructor (from a file)
    def __init__(self, filename, recipes=[]):
        # If the filename is empty and the recipes are empty aswell, raise an exception
        if filename == "" and len(recipes) == 0:
            # If I don't know how to use my own methods, I want them to crash the server so that I stop messing around
            sys.exit(
                "Either the config file path or a list of recipes must be specified to create a config file!"
            )
        # If the filename is not empty and the recipes are empty (else, we'll create a configfile from a recipe list)
        if filename != "" and len(recipes) == 0:
            # Set the filename
            self.__filename = filename
            # Create the XML tree of the config file
            tree = ET.parse(self.__filename)
            # Find the root of the xml file
            root = tree.getroot()
            # Get all the recipes in the config file
            recipes = [Recipe.parse(r) for r in root.findall("recipe")]
        # Create a dictionary that will contain all the recipes
        self.__dictionary = dict()
        # For all recipes in the XML file
        for r in recipes:
            # Store the recipe in the dictionary with the recipe key as the dictionary key
            self.__dictionary[r.key] = r

    # Recipe getter
    #
    # @param-in key (DictionnaryKey): Key index of the element
    #
    #
    # @param-out names (List[String]): All the names of the specified recipe
    #
    # @param-out types (List[String]): All the types of the specified recipe
    #
    def getRecipe(self, key):
        # Get the recipe object
        recipe = self.__dictionary[key]
        # Return the names and types of the specified recipe
        return recipe.names, recipe.types
