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


class Turf(Atom):
    overlayable = True
    priority = 1
    allowed_contents = []
    size = 20  # Turfs are really big.

    def generate_contents(self):
        return text_to_path(pick_weighted(self.allowed_contents))

    def crumble(self, severity):
        return False


class Plains(Turf):
    icon_symbol = "_"
    name = "Plains"
    default_description = "A plain sight, not much to see."
    allowed_contents = {"Nothing": 100, "Tall_Grass": 30, "Forest": 5}


class Hills(Turf):
    icon_symbol = "-"
    name = "Hills"
    default_description = "Hilly terrain. Up and down..."
    allowed_contents = {"Nothing": 100, "Forest": 1}


class Rocky(Turf):
    icon_symbol = "="
    name = "Rocky"
    default_description = "Hills, but with a slight chance of rocks being around."
    allowed_contents = {"Nothing": 100, "Mountain": 10, "Iron_Deposit": 3, "Gold_Deposit": 1, "Forest": 1}


class Water(Turf):
    icon_symbol = "~"
    icon_color = "blue"
    name = "Water"
    default_description = "Wet. Moist. Is a fluid."
    obstruction = True
