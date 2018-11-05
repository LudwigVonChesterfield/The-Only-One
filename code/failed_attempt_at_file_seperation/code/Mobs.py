import random
import tkinter
import math
import threading
import time
import sys
import copy

# Order of these is indeed important.
import code.Globals as Globals
from code.Funcs import *
from code.Coords import *
from code.Time import *
from code.Atoms import *


class Mob(Moveable):
    priority = 21

    def process(self):
        self.life()

    def life(self):
        return