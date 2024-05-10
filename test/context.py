# This file is used to import functions and classes for testing.
import sys
import os
# Adds the path of the parent folder to the path variable.
# This is required to access the kademlia folder.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import kademlia

