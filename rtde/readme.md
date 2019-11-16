# Description
This directory contains all the files and classes created by UR for the RTDE connection with
a robot. It is in a separate folder because it is not homemade, but if it was, it would be
stored in common. The files have been commented to help users understand how it works, but
mainly to help programmers understand how to use it.

It has also been slightly modified to suit our personal needs. For example, the feature to
create a recipe from a program and not an XML file has been added to the library.

- The ConfigReader.py file will read an XML file or a list of recipes to understand what the
user wants to receive for its query.

- The Rtde.py file is the class representation of an RDTE client/connection.

- The Serialize.py file will manage the parsing and casting of the result of queries to make
it understandble for both sides (server and client).

# Usage
Example:

```python
import sys
import os

# THIS LINE IS IMPORTANT
sys.path.append(os.getcwd() + "/")      # This is used to make sure "./" works.

from python.rdte.Rtde import RTDE as RtdeClient

rdte = RtdeClient([arg1], [arg2], [arg3]...
```
