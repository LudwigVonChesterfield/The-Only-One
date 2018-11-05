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
from code.Worlds import *
from code.Factions import *
from code.Atoms import *
from code.Areas import *
from code.Turfs import *
from code.Objects import *
from code.Mobs import *
from code.Cities import *
from code.GUIs import *

# Uncomment if you want to export output to a log file.
# sys.stdout = open('log.txt', 'w')


def prepare_lists():
    atom_classes = get_all_subclasses(Atom)
    for atom in atom_classes:
        Globals.atoms_by_name[atom.name] = atom


def master_controller():
    while(runtime):
        if(freeze_time):
            continue
        for world in Globals.worlds:
            if(world.initiated):
                if(world.processing):
                    continue
                world.process()


def main():
    prepare_lists()

    Globals.The_Map = World(1)  # World initiation on z = 1.

    Tall_Grass(Globals.The_Map, 27, 24)
    Tall_Grass(Globals.The_Map, 29, 25)
    Tall_Grass(Globals.The_Map, 27, 24)
    Tall_Grass(Globals.The_Map, 29, 25)
    Tall_Grass(Globals.The_Map, 28, 26)
    Tall_Grass(Globals.The_Map, 28, 26)
    Forest(Globals.The_Map, 27, 24)
    City(Globals.The_Map, 28, 25)
    Mountain(Globals.The_Map, 29, 26)
    Iron_Deposit(Globals.The_Map, 29, 26)
    Gold_Deposit(Globals.The_Map, 29, 26)

    threading.Thread(target=master_controller).start()  # Controller start up.

    Globals.GUI = Game_Window(The_Map)  # Opening the gui window.
