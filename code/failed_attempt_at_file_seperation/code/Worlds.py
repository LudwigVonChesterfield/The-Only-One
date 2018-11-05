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
from code.Turfs import *


class World:
    name = ""
    map_c = {}
    contents = []
    max_x = 50
    max_y = 34
    z = -1
    allowed_turfs = {"Plains": 100, "Hills": 25, "Rocky": 10}
    struc_per_tile = 3
    struc_chance_per_tile = 75
    lakes = 5
    forests = 7
    initiated = False
    processing = False
    process_atoms = []
    GUIs = []

    def __init__(self, z):
        self.z = z
        self.time = 0
        self.generate_world()
        self.initiated = True
        Globals.worlds.append(self)

    def ClickedOn(self, GUI, x_, y_):
        if(not self.coords_sanitized(x_, y_)):
            return
        strucs = self.get_tile_contents(x_, y_)
        for struc in strucs:
            # If they override click, they issue their own code,
            # stop click handling from here.
            if(struc.overrideClick(GUI, x_, y_)):
                return

        self.show_turf(GUI, x_, y_)

    def show_turf(self, GUI, x_, y_):
        GUI.open_window(Examine, "examine",
                        x_ * GUI.pixels_per_tile,
                        y_ * GUI.pixels_per_tile
                        )

    def get_world(self):
        return self

    def coords_sanitized(self, x, y):
        if(x >= 0 and y >= 0 and x < self.max_x and y < self.max_y):
            return True
        return False

    def is_overcrowded(self, x, y, additional_size):
        """Additional_size argument is used by Citizens
        to determine if they can build something."""
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
            self.generate_cluster(random.randrange(0, self.max_x),
                                  random.randrange(0, self.max_y),
                                  2, 2, Water, 80, True
                                  )

        for F in range(self.forests):
            self.generate_cluster(random.randrange(0, self.max_x),
                                  random.randrange(0, self.max_y),
                                  4, 4, Forest, 50, False
                                  )

    def generate_turf_type(self):
        return text_to_path(pick_weighted(self.allowed_turfs))

    def generate_tile(self, x, y):
        new_turf = self.generate_turf_type()(self, x, y)
        if(len(new_turf.allowed_contents) == 0):
            return
        for N in range(self.struc_per_tile):
            if(prob(self.struc_chance_per_tile)):
                new_turf.generate_contents()(self, x, y)

    def update_coord_icon(self, x, y):
        if(not self.initiated):
            return

        tile = self.get_tile_contents(x, y)

        overlays = []
        icons = []

        max_priority = 0
        max_atom = None

        for atom in tile:
            if(atom.priority > max_priority):
                max_priority = atom.priority
                max_atom = atom
            if(atom.is_overlayable()):
                overlays.append(atom)

        if(max_atom and max_atom not in overlays):
            overlays.append(max_atom)

        if(overlays):
            if(max_atom.block_overlays):
                icons.append(max_atom.get_icon())
            else:
                overlays = sort_by_priority(overlays)
                for overlay in overlays:
                    icons.append(overlay.get_icon())

            if(icons):
                for GUI in self.GUIs:
                    GUI.update_icon_for(x, y, icons)

    def update_world_icons(self):
        for coord in self.map_c:
            coord_list = coord_to_list(coord)
            x = coord_list["x"]
            y = coord_list["y"]
            self.update_coord_icon(x, y)

    def generate_cluster(self, x: int, y: int,
                         x_range: int, y_range: int,
                         tile_type: type, chance: int, turf: bool
                         ):
        for y_ in range(y - y_range, y + y_range + 1):
            for x_ in range(x - x_range, x + x_range + 1):
                if(self.coords_sanitized(x_, y_)):
                    if(not prob(chance)):
                        continue
                    if(turf):
                        tile = self.get_turf(x_, y_)
                        tile.qdel()
                        del tile
                        tile_c = self.get_tile_contents(x_, y_)
                        for struc in tile_c:
                            if(struc.name not in tile_type.allowed_contents):
                                tile_c.remove(struc)
                                struc.qdel()
                                del struc
                    else:
                        tile = self.get_turf(x_, y_)
                        if(tile_type.name not in tile.allowed_contents):
                            continue
                    tile_type(self, x_, y_)

    def process(self):
        self.processing = True
        self.process_time()
        if(prob(1)):
            if(prob(1)):
                Citizens(self, random.randrange(0, 29),
                         random.randrange(0, 29)
                         )
        self.processing = False

    def process_time(self):
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