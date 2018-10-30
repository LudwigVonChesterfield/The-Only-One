import random
import tkinter
import math
import threading
import time
import sys
import copy

#Order of these is indeed important.
import code.Globals
from code.Funcs import *
from code.Coords import *
from code.Time import *
from code.Factions import *
from code.Atoms import *
from code.Areas import *
from code.Turfs import *
from code.Objects import *
from code.Mobs import *
from code.Cities import *
from code.GUIs import *

#sys.stdout = open('log.txt', 'w') # Uncomment if you want to export to a log file.

def prepare_lists():
    atom_classes = get_all_subclasses(Atom)
    for atom in atom_classes:
        atoms_by_name[atom.name] = atom

def master_controller():
    while(runtime):
        if(freeze_time):
            continue
        for world in worlds:
            if(world.initiated):
                if(world.processing):
                    continue
                world.process()

class World:
    name = ""
    map_c = {}
    contents = []
    max_x = 50
    max_y = 34
    z = -1
    allowed_turfs = {"Plains" : 100, "Hills" : 25, "Rocky" : 10}
    struc_per_tile = 3
    struc_chance_per_tile = 75
    lakes = 5
    forests = 7
    initiated = False
    processing = False
    process_atoms = []
    time = 0

    def __init__(self, z):
        self.z = z
        self.generate_world()
        self.initiated = True
        worlds.append(self)

    def ClickedOn(self, GUI, x_, y_):
        strucs = self.get_tile_contents(x_, y_)
        for struc in strucs:
            if(struc.overrideClick(GUI, x_, y_)):  # If they override click, they issue their own code, stop click handling from here.
                return

        self.show_turf(GUI, x_, y_)


    def show_turf(self, GUI, x_, y_):
        strucs = sort_by_priority(self.get_tile_contents(x_, y_))
        if(not strucs):
            return  # Nothing to see.
        show = ""
        for struc in strucs:
            show = show + struc.symbol + "[" + str(struc.priority) + "]\n"

        def on_click(event):
            """Try-hard hack to make these objects clickable."""
            y_ = int(round(event.y / (3 * GUI.pixels_per_tile)))
            if(y_ >= 0 and y_ < len(GUI.showing_turf_strucs)):
                atom = GUI.showing_turf_strucs[y_]
                atom.ClickedOn(GUI, atom.x, atom.y)  # Cheap hack to get at least some x and y to be passed.

        GUI.showing_turf_rel_x = int(round(x_ * GUI.pixels_per_tile))
        GUI.showing_turf_rel_y = int(round(y_ * GUI.pixels_per_tile))

        if(GUI.showing_turf):
            GUI.showing_turf_strucs = strucs
            wid = int(round(4 * GUI.pixels_per_tile))
            hei = int(round(len(strucs) * 3 * GUI.pixels_per_tile))
            GUI.showing_turf.configure(width=wid, height=hei)
            GUI.showing_turf.coords(GUI.showing_turf_content, int(round(wid / 2)), int(round(hei / 2)))
            GUI.showing_turf.itemconfigure(GUI.showing_turf_content, text=show)
            GUI.showing_turf.lift(GUI)
            GUI.showing_turf.master.geometry("+%d+%d" % (GUI.wind.winfo_x() + GUI.showing_turf_rel_x, GUI.wind.winfo_y() + GUI.showing_turf_rel_y))
            return

        temp_wind = tkinter.Toplevel(GUI.wind)
        temp_wind.title(u'The Tile')
        temp_wind.resizable(False, False)
        temp_wind.geometry("+%d+%d" % (GUI.wind.winfo_x() + GUI.showing_turf_rel_x, GUI.wind.winfo_y() + GUI.showing_turf_rel_y))
        temp_wind.attributes("-topmost", True)

        wid = int(round(4 * GUI.pixels_per_tile))
        hei = int(round(len(strucs) * 3 * GUI.pixels_per_tile))

        def on_close():
            GUI.showing_turf = None
            GUI.showing_turf_content = None
            GUI.showing_turf_strucs = []
            temp_wind.destroy()

        temp_wind.protocol("WM_DELETE_WINDOW", on_close)

        temp_map_field = tkinter.Canvas(temp_wind, width=wid, height=hei, bg='black')
        temp_map_field.bind("<ButtonPress-1>", on_click)
        temp_map_bg = temp_map_field.create_text(int(round(wid / 2)), int(round(hei / 2)), text=show, fill = 'green', font = 'TkFixedFont')

        GUI.showing_turf = temp_map_field
        GUI.showing_turf_content = temp_map_bg
        GUI.showing_turf_strucs = strucs

        temp_map_field.pack()

    def get_world(self):
        return self

    def coords_sanitized(self, x, y):
        if(x >= 0 and y >= 0 and x < self.max_x and y < self.max_y):
            return True
        return False

    def is_overcrowded(self, x, y, additional_size): # additional_size argument is used by citizens to determine if they can build something.
        tile = self.get_turf(x, y)
        if(not tile):
            return False
        strucs = self.get_tile_contents(x, y)
        overall_size = 0
        for struc in strucs:
            if(isinstance(struc, Turf)):
                continue
            overall_size = overall_size + struc.size
        if(overall_size + additional_size > tile.size):
            return True
        return False

    def get_turf(self, x, y):
        for struc in self.get_tile_contents(x, y):
            if(isinstance(struc, Turf)):
                return struc

    def get_tile_contents(self, x, y):
        if(self.coords_sanitized(x, y)):
            return self.map_c[x_y_to_coord(x, y)]

    def get_region_coordinates(self, x, y, x_range, y_range):
        coords = []
        for x_ in range(x - x_range, x + x_range + 1):
            for y_ in range(y - y_range, y + y_range + 1):
                if(not self.coords_sanitized(x_, y_)):
                    continue
                coords.append(x_y_to_coord(x_, y_))
        return coords

    def get_region_contents(self, x, y, x_range, y_range):
        contents = []
        for x_ in range(x - x_range, x + x_range + 1):
            for y_ in range(y - y_range, y + y_range + 1):
                if(not self.coords_sanitized(x_, y_)):
                    continue
                for content in self.get_tile_contents(x_, y_):
                    contents.append(content)
        return contents

    def generate_world(self):
        for y in range(self.max_y):
            for x in range(self.max_x):
                self.map_c[x_y_to_coord(x, y)] = []
                self.generate_tile(x, y)
        for L in range(self.lakes):
            self.generate_cluster(random.randrange(0, self.max_x), random.randrange(0, self.max_y), 2, 2, Water, 80, True)
        for F in range(self.forests):
            self.generate_cluster(random.randrange(0, self.max_x), random.randrange(0, self.max_y), 4, 4, Forest, 50, False)

    def generate_turf_type(self):
        return text_to_path(pick_weighted(self.allowed_turfs))

    def generate_tile(self, x, y):
        new_turf = self.generate_turf_type()(self, x, y)
        if(len(new_turf.allowed_contents) == 0):
            return
        for N in range(self.struc_per_tile):
            if(prob(self.struc_chance_per_tile)):
                new_turf.generate_contents()(self, x, y)

    def world_to_string(self):
        map_string = ""
        for y in range(self.max_y):
            for x in range(self.max_x):
                strucs = self.get_tile_contents(x, y)
                sym = ""
                prior = 0
                for struc in strucs:
                    if(struc.priority > prior):
                        prior = struc.priority
                        sym = struc.symbol
                map_string = map_string + sym + " "
            map_string = map_string + "\n"
        return map_string

    def generate_cluster(self, x, y, x_range, y_range, tile_type, chance, turf):
        for y_ in range(y - y_range, y + y_range + 1):
            for x_ in range(x - x_range, x + x_range + 1):
                if(self.coords_sanitized(x_, y_)):
                    if(not prob(chance)):
                        continue
                    if(turf):
                        for struc in self.get_tile_contents(x_, y_):
                            if(isinstance(struc, Turf)):
                                self.map_c[x_y_to_coord(x_, y_)].remove(struc)
                    else:
                        tile = self.get_turf(x_, y_)
                        if(not find_in_list(tile.allowed_contents, tile_type.name)):
                            continue
                    tile_type(self, x_, y_)

    def process(self):
        self.processing = True
        self.process_time()
        for atom in atoms:
            if(atom.x == -1 or atom.y == -1):
                atom.qdel()
                del atom
        if(prob(1)):
            if(prob(1)):
                Citizens(self, random.randrange(0, 29), random.randrange(0, 29))
                #if(prob(1)):
                    #Fire(self, random.randrange(0, 29), random.randrange(0, 29))
        self.processing = False

    def process_time(self):
        global to_sleep_chance
        if(prob(to_sleep_chance)):
            time.sleep(1)
        closest_time = self.time + 1
        atoms_action = None
        for atom in self.process_atoms:
            if(atom.last_action + atom.action_time < closest_time):
                closest_time = atom.last_action + atom.action_time
                atoms_action = atom
        if(not atoms_action):
            closest_time = math.inf
            for atom in self.process_atoms:
                if(atom.last_action + atom.action_time < closest_time):
                    closest_time = atom.last_action + atom.action_time
                    atoms_action = atom
            if(not atoms_action):
                closest_time = self.time + 1
        if(atoms_action and not atoms_action.qdeling):
            atoms_action.last_action = closest_time
            atoms_action.process()
        self.time = closest_time

def main():
    prepare_lists()

    The_Map = World(1)  # World initiation on z = 1.

    Tall_Grass(The_Map, 27, 24)
    Tall_Grass(The_Map, 29, 25)
    Tall_Grass(The_Map, 27, 24)
    Tall_Grass(The_Map, 29, 25)
    Tall_Grass(The_Map, 28, 26)
    Tall_Grass(The_Map, 28, 26)
    Forest(The_Map, 27, 24)
    City(The_Map, 28, 25)
    Mountain(The_Map, 29, 26)
    Iron_Deposit(The_Map, 29, 26)
    Gold_Deposit(The_Map, 29, 26)

    threading.Thread(target=master_controller).start()  # Controller start up.

    GUI = Game_Window(The_Map)  # Opening the gui window.
