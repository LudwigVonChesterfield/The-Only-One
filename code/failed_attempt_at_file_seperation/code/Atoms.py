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
from code.GUIs import *

class Atom:
    icon_symbol = ""
    icon_color = "green"
    icon_font = 'TkFixedFont'
    overlayable = False
    block_overlays = False
    priority = 0

    name = ""
    default_description = "I am an Atom."

    obstruction = False
    size = 0

    needs_processing = False

    action_time = 0

    def __init__(self, loc, x, y):
        self.qdeling = False
        self.x = - 1
        self.y = -1
        self.loc = None
        self.world = loc.get_world()
        self.contents = []
        self.move_atom_to(loc, x, y)
        self.last_action = self.world.time
        self.description = self.default_description
        # Since "name" is more of a type, really.
        self.display_name = self.name
        self.integrity = self.size
        Globals.atoms.append(self)
        if(self.needs_processing):
            self.world.process_atoms.append(self)

    # Doesn't work since GUI is not updated during time.sleep().
    """
    def do_damage_anim(self):
        print("Trying to be damaged")
        old_icon_color = self.icon_color
        # Behold! Destruction animation!
        self.icon_color = "white"
        self.update_icon()
        time.sleep(0.5)
        self.icon_color = "red"
        self.update_icon()
        time.sleep(0.5)
        self.icon_color = "white"
        self.update_icon()
        time.sleep(0.5)
        self.icon_color = old_icon_color
        self.update_icon()
        print("Tried to be damaged")
        # / End destruction animation.
    """

    def overrideClick(self, GUI, x_, y_):
        if(self.canClickOn(GUI, x_, y_)):
            return self.ClickedOn(GUI, x_, y_)
        return False

    def canClickOn(self, GUI, x_, y_):
        # Change this in case of special behavior.
        return False

    def ClickedOn(self, GUI, x_, y_):
        # Default behavior of clicking on it, is examinating it.
        self.Examinated(GUI)

    def Examinated(self, GUI):
        Globals.log += self.getExamineText() + "\n"

    def getExamineText(self):
        return str(self.icon_symbol) + " [" + self.display_name + "] " + self.default_description

    def get_world(self):
        if(isinstance(loc, World)):
            return loc
        else:
            return get_world()

    def get_tile_contents(self, x, y):
        return self.contents

    def bump(self, bumped_with):
        # Bumped with is the thing that called the bump proc.
        return

    def bump_into(self, bumped_into):
        return

    def does_obstruct(self, atom):
        return self.obstruction

    def move_atom_to(self, world, x, y):
        self_coord = x_y_to_coord(self.x, self.y)
        if((self_coord in self.world.map_c) and (self in self.world.map_c[self_coord])):
            self.world.map_c[self_coord].remove(self)
            self.update_icon()

        if(self.world.coords_sanitized(x, y)):
            overcrowded = self.world.is_overcrowded(x, y, 0)
            for struc in self.world.get_tile_contents(x, y):
                if(struc == self):
                    continue
                if(overcrowded):
                    if(struc.crumble(self.size)):
                        continue
                struc.bump(self)
                self.bump_into(struc)
            world.map_c[x_y_to_coord(x, y)].append(self)

        self.loc = world
        self.loc.contents.append(self)
        self.x = x
        self.y = y
        self.update_icon()

    def attempt_move_to(self, world, x, y):
        for struc in world.get_tile_contents(x, y):
            if(struc.does_obstruct(self)):
                return False

        # sqrt_2 = math.sqrt(2), because diagonal tiles.
        if(get_distance(self.x, self.y, x, y) > sqrt_2):
            return False

        self.move_atom_to(world, x, y)
        return True

    def move_towards_to(self, world, x, y):
        # Set this to something higher if you want some wacky shit.
        dummy_moves = 3

        x_ = self.x + get_vector(self.x, x)
        y_ = self.y + get_vector(self.y, y)

        while(dummy_moves):
            if(not self.attempt_move_to(world, x_, y_)):
                x_t = self.x + random.randrange(-1, 1)
                y_t = self.y + random.randrange(-1, 1)
                if(self.world.coords_sanitized(x_t, y_t)):
                    x_ = x_t
                    y_ = y_t
                    dummy_moves -= 1
            else:
                return True
        return False

    def process(self):
        return

    def crumble(self, severity):
        self.integrity = self.integrity - severity
        if(self.integrity <= 0):
            self.qdel()
            del self
            return True  # Fully crumbled.
        return False

    def fire_act(self, severity):
        """
        What this atom should do upon being lit on fire.
        Return True if you want this atom to be "burnt",
        aka spread fire.
        """
        return False

    def get_task(self, city):
        # If this returns None, consider skipping trying to get task from this.
        return None

    def react_to_attack(self, attacker):
        """Returns True if attack was parried, False otherwise."""
        return False

    def qdel(self):
        self.qdeling = True
        if(self in atoms):
            atoms.remove(self)

        if(self.needs_processing and (self in self.world.process_atoms)):
            self.world.process_atoms.remove(self)

        self_coord = x_y_to_coord(self.x, self.y)
        if((self_coord in self.world.map_c) and (self in self.world.map_c[self_coord])):
            self.world.map_c[self_coord].remove(self)

        if(self in self.loc.contents):
            self.loc.contents.remove(self)

        self.update_icon()
        self.loc = None
        del self

    def update_icon(self):
        if(isinstance(self.loc, World)):
            self.loc.update_coord_icon(self.x, self.y)

    def get_icon(self):
        return {"symbol": self.icon_symbol, "color": self.icon_color, "font": self.icon_font}

    def is_overlayable(self):
        return self.overlayable


class Moveable(Atom):
    obstruction = False
