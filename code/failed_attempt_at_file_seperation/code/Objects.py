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


class Object(Moveable):
    priority = 11


class Nothing(Object):
    icon_symbol = ""
    name = "Nothing"

    def __init__(self, world, x, y):
        del self


class Fire(Object):
    icon_symbol = "x"
    icon_color = "red"
    priority = 19
    overlayable = True

    name = "Fire"
    default_description = "Full of passion and desire, it is very much a fire."
    size = 3

    action_time = 3
    needs_processing = True

    def __init__(self, loc, x, y, integrity=3):
        super().__init__(loc, x, y)
        self.integrity = integrity

    def process(self):
        coords = self.world.get_region_coordinates(self.x, self.y, 1, 1)
        random.shuffle(coords)
        for coord in coords:
            coord = coord_to_list(coord)
            x_ = coord["x"]
            y_ = coord["y"]
            strucs = self.world.get_tile_contents(x_, y_)
            if(x_ == self.x and y_ == self.y):
                for struc in strucs:
                    if(struc.fire_act(1)):
                        self.integrity = min([self.integrity + 1, self.size])
                continue
            for struc in strucs:
                if(struc.fire_act(1)):
                    self.spread_to(struc.x, struc.y)
                    break
        self.update_icon()
        self.crumble(1)

    def spread_to(self, x, y):
        strucs = self.world.get_tile_contents(x, y)
        for struc in strucs:
            if(isinstance(struc, Water)):
                return
            if(isinstance(struc, Fire)):
                return
        Fire(self.world, x, y, self.integrity)

    def get_task(self, city):
        return {"priority" : 1, "job" : "Peasant", "task" : "destroy", "target" : self, "allowed_peasants" : True}

    def react_to_attack(self, attacker):
        if(prob(10)):
            attacker.fire_act(1)


class Lightning(Object):
    icon_symbol = "z"
    name = "Lightning"
    default_description = "It is before the Thunder."
    size = 1
    priority = 100  # Pretty "light".

    def __init__(self, loc, x, y, power=3):
        super().__init__(loc, x, y)
        coords = self.world.get_region_coordinates(self.x, self.y, 1, 1)
        random.shuffle(coords)
        for coord in coords:
            coord = coord_to_list(coord)
            x_ = coord["x"]
            y_ = coord["y"]
            strucs = self.world.get_tile_contents(x_, y_)
            if(x_ == self.x and y_ == self.y):
                Fire(self.world, x, y, power)
                continue
            for struc in strucs:
                struc.fire_act(power)
        self.qdel()


class Resource(Object):
    harvestable = False
    allow_peasants = False
    resource = ""
    job_to_harvest = ""
    harv_priority = 0

    default_resource_multiplier = 1.0
    def_amount = 0

    def __init__(self, loc, x, y):
        super().__init__(loc, x, y)
        self.been_used = False
        self.resource_multiplier = random.uniform(0.8, 1.2) * self.default_resource_multiplier
        self.resourcefulness = self.get_max_resourcefulness()

    def get_max_resourcefulness(self):
        return int(round(self.def_amount * self.resource_multiplier * self.integrity))

    def get_task(self, city):
        if(self.harvestable):
            return {"priority" : self.harv_priority, "job" : self.job_to_harvest, "task" : "harvest", "target" : self, "allowed_peasants" : self.allow_peasants}

    def harvest(self, harvester, amount):
        """Returns how much resource has actually been harvested."""
        if(not self.harvestable):
            return 0
        self.been_used = True
        to_return = 0
        if(self.resourcefulness >= amount):
            to_return = amount
        else:
            to_return = self.resourcefulness
        if(prob(harvester.loc.action_time)):
            severity = 0
            if(self.resourcefulness > amount * harvester.action_time):
                # The 0.0001 is there to prevent zeroDivision errors.
                severity = int(round(self.resourcefulness / (0.0001 + self.resourcefulness - (amount * harvester.loc.action_time))))
            else:
                severity = self.integrity
            self.crumble(severity)
        return to_return

    def crumble(self, severity):
        if(not super().crumble(severity)):
            self.resourcefulness = min([self.resourcefulness, self.get_max_resourcefulness()])
            if(self.resourcefulness <= 0):
                self.qdel()
                del self
                return True  # We have crumbled due to lack of resource.
            return False
        return True


class Tall_Grass(Resource):
    name = "Tall_Grass"
    default_description = "A grass to eat when hungy."
    size = 3
    priority = 2

    icon_symbol = "|"

    harvestable = True
    allow_peasants = True
    resource = "food"
    job_to_harvest = "Farmer"
    harv_priority = 1

    def_amount = 100

    def fire_act(self, severity):
        self.crumble(severity)
        return True


class Forest(Resource):
    icon_symbol = "^"
    name = "Forest"
    default_description = "A place for trees to go, for a Lumberjack to cut."
    size = 10

    harvestable = True
    allow_peasants = True
    resource = "wood"
    job_to_harvest = "Lumberjack"
    harv_priority = 3

    def_amount = 100

    def fire_act(self, severity):
        self.crumble(severity)
        return True


class Mountain(Resource):
    icon_symbol = "A"
    icon_color = "gray26"
    block_overlays = True
    name = "Mountain"
    default_description = "A rock of rocks, that is rockier than most."
    obstruction = True
    size = 15

    harvestable = True
    allow_peasants = True
    resource = "stone"
    job_to_harvest = "Miner"
    harv_priority = 5

    def_amount = 100


class Iron_Deposit(Resource):
    icon_symbol = "i"
    icon_color = "gray99"
    name = "Iron_Deposit"
    default_description = "It has iron in it!"
    obstruction = True
    size = 3
    priority = 2

    harvestable = True
    allow_peasants = False
    resource = "iron"
    job_to_harvest = "Miner"
    hav_priority = 4

    def_amount = 10


class Gold_Deposit(Resource):
    icon_symbol = "g"
    icon_color = "gold"
    name = "Gold_Deposit"
    default_description = "It has gold in it!"
    obstruction = True
    size = 3
    priority = 2

    harvestable = True
    allow_peasants = False
    resource = "gold"
    job_to_harvest = "Miner"
    harv_priority = 4

    def_amount = 10
