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
from code.Factions import *
from code.Atoms import *
from code.Areas import *
from code.Turfs import *
from code.Objects import *
from code.Mobs import *
from code.GUIs import *


class Tool(Object):
    name = ""
    job = ""

    def __init__(self, loc, x, y, materials={"wood" : 5}, quality_modifier=1):
        self.x = x
        self.y = y
        self.loc = loc
        self.materials = materials
        self.quality = random.uniform(2.0, 3.0) * quality_modifier

    def qdel(self):
        self.qdeling = True
        if(self in self.loc.inventory, self):
            self.loc.inventory.remove(self)
        del self


class Hoe(Tool):
    name = "Hoe"
    job = "Farmer"


class Hammer(Tool):
    name = "Hammer"
    job = "Builder"


class Axe(Tool):
    name = "Axe"
    job = "Lumberjack"


class Sledgehammer(Tool):
    name = "Sledgehammer"
    job = "Blacksmith"


class Sharphammer(Tool):
    name = "Sharphammer"
    job = "Weaponsmith"


class Pickaxe(Tool):
    name = "Pickaxe"
    job = "Miner"


class Chisel(Tool):
    name = "Chisel"
    job = "Stonecutter"


class Saw(Tool):
    name = "Saw"
    job = "Carpenter"


class City(Object):
    icon_color = "grey"
    icon_symbol = "1"
    name = "City"
    default_description = ""  # Uses custom code.
    priority = 30  # Should actually be above mob layer.
    size = 5

    starting_citizens = 5

    needs_processing = True
    action_time = 5

    def __init__(self, loc, x, y, faction=None):
        self.faction = faction
        if(faction):
            faction.add_to_faction(self)
        else:
            self.faction = Faction(self)

        super().__init__(loc, x, y)
        self.display_name = self.name + " " + str(random.randrange(1, 999))
        self.max_population = 10
        self.citizens = []
        self.inventory = []
        self.job_requests = {"Peasant" : 0,
                             "Builder" : 1,
                             "Farmer" : 0,
                             "Miner" : 0,
                             "Stonecutter" : 1,
                             "Blacksmith" : 0,
                             "Weaponsmith" : 0,
                             "Lumberjack" : 0,
                             "Carpenter" : 1}
        self.structure_requests = []
        self.tasks = []
        self.resources = {"food" : 100,
                          "wood" : 0,
                          "stone" : 0,
                          "iron" : 0,
                          "gold" : 0}

        for N in range(self.starting_citizens):
            self.add_citizen(Peasant)

        Globals.log += self.display_name + " has been settled in " + x_y_to_coord(self.x, self.y) + " at " + time_to_date(self.world.time) + "\n"

    def getExamineText(self):
        text = super().getExamineText()
        text += "It is a city of " + self.faction.display_name + " and it has " + str(len(self.citizens)) + " citizens in it!"
        return text

    def qdel(self):
        global log
        self.qdeling = True
        Globals.log += self.display_name + " has been destroyed in " + x_y_to_coord(self.x, self.y) + " at " + time_to_date(self.world.time) + "\n"
        for cit in self.citizens:
            cit.qdel()
            del cit
        self.citizens = []
        for tool in self.inventory:
            tool.qdel()
            del tool
        self.inventory = []
        self.tasks = []
        self.faction.members.remove(self)
        self.faction = None
        super().qdel()

    def does_obstruct(self, atom):
        if(isinstance(atom, Citizens)):
            if(atom.resources["food"] < 3 * len(atom.citizens) * atom.action_time):
                atom.transfer_resources_to(atom.resources, self)
                for citizen in atom.citizens:
                    citizen.move_atom_to(self, self.x, self.y)
                atom.citizens = []
                atom.qdel()
                del atom
                return False
            else:
                return True
        return False

    def process(self):
        if(not len(self.citizens)):
            self.qdel()
            del self
            return

        food_required = 0
        for cit in self.citizens:
            food_required += cit.hunger_rate

        actual_food_required = food_required

        strucs = self.world.get_region_contents(self.x, self.y, 2, 2)
        random.shuffle(strucs)

        dummy = random.choice(self.citizens)
        self.job_requests = dummy.required_citizens(strucs)
        self.structure_requests = dummy.required_strucs(strucs)

        self.tasks = []

        houses_count = 0
        for struc in strucs:
            struc.been_used = False
            task = struc.get_task(self)  # We pass ourselves as city argument.
            if(not task):  # This thing dindu tasking.
                continue

            if(isinstance(struc, City)):
                if(self.faction and struc.faction != self.faction):
                    self.faction.adjust_relationship(struc.faction, -3)

            elif(isinstance(struc, Resource) and struc.resource):
                if(self.resources[struc.resource] >= 50 * len(self.citizens)):  # We have enough of this...
                    continue

                if(isinstance(struc, Tall_Grass)):
                    if(food_required > 0):
                        food_required -= struc.resource_multiplier * struc.default_resource_multiplier

                elif(isinstance(struc, Structure)):
                    if(self.faction != struc.faction and struc.faction):  # If it's Neutral, nobody cares.
                        struc.faction.adjust_relationship(self.faction, -1)  # Using other faction's strucs is a no-no.

                    elif(isinstance(struc, Farm)):
                        if(food_required > 0):
                            food_required -= struc.resource_multiplier * struc.default_resource_multiplier

                    elif(isinstance(struc, House)):
                        houses_count += 1

            self.tasks.append(task)

        for job_request in self.job_requests:
            if(job_request == "Farmer"):
                for task in range(0, self.job_requests[job_request]):
                    self.tasks.append({"priority" : 1, "job" : "Carpenter", "task" : "create", "target" : Hoe, "res_required" : {"wood" : 5}, "allowed_peasants" : False})
            elif(job_request == "Builder"):
                for task in range(0, self.job_requests[job_request]):
                    self.tasks.append({"priority" : 2, "job" : "Carpenter", "task" : "create", "target" : Hammer, "res_required" : {"wood" : 5}, "allowed_peasants" : False})
            elif(job_request == "Carpenter"):
                for task in range(0, self.job_requests[job_request]):
                    self.tasks.append({"priority" : 2, "job" : "Peasant", "task" : "create", "target" : Saw, "res_required" : {"wood" : 5}, "allowed_peasants" : True})
            elif(job_request == "Stonecutter"):
                for task in range(0, self.job_requests[job_request]):
                    self.tasks.append({"priority" : 3, "job" : "Peasant", "task" : "create", "target" : Chisel, "res_required" : {"stone" : 5}, "allowed_peasants" : True})
            elif(job_request == "Miner"):
                for task in range(0, self.job_requests[job_request]):
                    self.tasks.append({"priority" : 3, "job" : "Stonecutter", "task" : "create", "target" : Pickaxe, "res_required" : {"stone" : 5}, "allowed_peasants" : False})
            elif(job_request == "Lumberjack"):
                for task in range(0, self.job_requests[job_request]):
                    self.tasks.append({"priority" : 3, "job" : "Stonecutter", "task" : "create", "target" : Axe, "res_required" : {"stone" : 5}, "allowed_peasants" : False})
            elif(job_request == "Blacksmith"):
                for task in range(0, self.job_requests[job_request]):
                    self.tasks.append({"priority" : 4, "job" : "Stonecutter", "task" : "create", "target" : Sledgehammer, "res_required" : {"stone" : 5}, "allowed_peasants" : False})
            elif(job_request == "Weaponsmith"):
                for task in range(0, self.job_requests[job_request]):
                    self.tasks.append({"priority" : 4, "job" : "Stonecutter", "task" : "create", "target" : Weaponhammer, "res_required" : {"stone" : 5}, "allowed_peasants" : False})

        for structure_request in self.structure_requests:
            if(structure_request == "Farm"):
                for task in range(0, self.structure_requests[structure_request]):
                    self.tasks.append({"priority" : 1, "job" : "Builder", "task" : "build", "target" : Farm, "res_required" : {"wood" : 30}, "allowed_peasants" : False})
            elif(structure_request == "Mine"):
                for task in range(0, self.structure_requests[structure_request]):
                    self.tasks.append({"priority" : 3, "job" : "Builder", "task" : "build", "target" : Mine, "res_required" : {"wood" : 30}, "allowed_peasants" : False})
            elif(structure_request == "House"):
                for task in range(0, self.structure_requests[structure_request]):
                    self.tasks.append({"priority" : 3, "job" : "Builder", "task" : "build", "target" : House, "res_required" : {"wood" : 30, "stone" : 30}, "allowed_peasants" : False})

        actual_food_supply = 0
        cur_priority = 1
        while(cur_priority <= 10):
            tasks = self.get_priority_tasks_list(cur_priority)
            if(not tasks):
                cur_priority = cur_priority + 1
                continue
            for task in tasks:
                cits = self.get_susceptible_citizens_list(task)
                if(not cits):
                    continue
                for citizen in cits:
                    if(citizen.qdeling):
                        continue
                    if(isinstance(citizen, Toddler)):  # Toddlers don't even try to work.
                        continue
                    if(citizen.actions_to_perform <= 0 and prob(round((citizen.age / 8760) * abs(citizen.actions_to_perform)))):  # The older the person, the less he'd want to overwork.
                        continue
                    if(citizen.actions_to_perform <= -citizen.max_actions_to_perform):  # See: citizens overworking themselves to death.
                        continue
                    #print(citizen.display_name + " is trying to perform " + str(task))
                    #print("Has actions left: " + str(citizen.actions_to_perform))
                    if(citizen.perform_task(strucs, task)):
                        #print(citizen.display_name + " performed " + str(task))
                        if(isinstance(task["target"], Resource) and task["target"].resource == "food"):
                            actual_food_supply += task["target"].resource_multiplier * task["target"].default_resource_multiplier
                        self.tasks.remove(task)
                        break
            cur_priority = cur_priority + 1

        if(len(self.citizens) > 30):
            cit = Citizens(self.loc, self.x, self.y, self.faction)
            cit.resources["food"] = 0
            for c in range(5):
                cit.add_citizen(Peasant)
                self.remove_citizen(None)

        if(self.resources["food"] > 30 and actual_food_supply - 1 > actual_food_required and len(self.citizens) < self.max_population):
            self.add_citizen(Toddler)

        for citizen in self.citizens:
            if(not citizen.qdeling):
                if(citizen.life() and not citizen.qdeling):
                    citizen.try_equip()  # Even old people steal tools.

        self.max_population = 10 + houses_count * 2

        if(len(self.citizens) < 100):
            self.icon_symbol = str(int(len(self.citizens) // 10))
        elif(len(self.citizens) < 1000):
             self.icon_symbol = "L"
        elif(len(self.citizens) < 10000):
             self.icon_symbol = "M"

        if(len(self.citizens) > self.max_population): # Overpopulation - DEATH!
            self.remove_citizen(None)

        self.size = 5 + int(len(self.citizens) // 10)
        if(self.world.is_overcrowded(self.x, self.y, 0)):
            for struc in self.world.get_tile_contents(self.x, self.y):
                if(struc == self):
                    continue
                if(struc.crumble(self.size)):
                    continue
        self.update_icon()

        #print(self.display_name)
        #print(self.faction.display_name)
        #print(self.resources)
        #print(self.inventory)
        l = ""
        for cit in self.citizens:
            l = l + cit.display_name + " "
        #print(l)

    def add_citizen(self, citizen_type):
        citizen = citizen_type(self, -2, -2) #Huehuehue. -2 -2 won't be qdeled.
        citizen.try_equip()
        self.update_icon()

    def remove_citizen(self, citizen_):
        if(citizen_):
            citizen_.qdel()
            del citizen_
        elif(len(self.citizens) > 0):
            citizen_ = random.choice(self.citizens)
            citizen_.qdel()
            del citizen_
        self.update_icon()
        if(len(self.citizens) == 0):
            self.qdel()

    def get_priority_tasks_list(self, priority):
        list_ = []
        for task in self.tasks:
            if(task["priority"] == priority):
                list_.append(task)
        return list_

    def get_susceptible_citizens_list(self, task):
        list_ = []
        for citizen in self.citizens:
            if(citizen.name == task["job"]):
                list_.append(citizen)
        # It actually allows not just peasants, but everybody.
        if(task["allowed_peasants"]):
            for citizen in self.citizens:
                if(citizen.name == "Peasant"):
                    list_.append(citizen)
            for citizen in self.citizens:
                if(citizen not in list_):
                    list_.append(citizen)
        return list_

    def get_icon(self):
        return {"symbol": self.icon_symbol, "color": self.faction.color if self.faction else self.icon_color, "font": self.icon_font}

    def get_task(self, city):
        if(city.faction != self.faction):
            relation = self.faction.get_relationship(city.faction)
            if(relation == "Unfriendly" or relation == "Neutral"):
                return {"priority" : 1, "job" : "Peasant", "task" : "gift", "res_required" : {random.choice(["food", "wood", "stone"]) : random.randint(1, 10)}, "target" : self, "allowed_peasants" : True}
            if(relation == "Hostile"):
                return {"priority" : 1, "job" : "Peasant", "task" : "kidnap", "target" : self, "allowed_peasants" : True}
        return super().get_task(city)

    def fire_act(self, severity):
        for cit in range(severity):
            if(not len(self.citizens)):
                return False
            citizen = random.choice(self.citizens)
            if(not citizen.qdeling):
                citizen.fire_act(severity)
                return True
        return False


class Structure(Resource):
    icon_color = "grey"
    block_overlays = True
    size = 5
    priority = 12

    def __init__(self, loc, x, y, faction=None):
        self.faction = faction
        if(faction):
            faction.add_to_faction(self)
        super().__init__(loc, x, y)

    def get_icon(self):
        return {"symbol": self.icon_symbol, "color": self.faction.color if self.faction else self.icon_color, "font": self.icon_font}

    def get_task(self, city):
        if(city.faction != self.faction):
            relation = city.faction.get_relationship(self.faction)
            if(relation == "Hostile"):
                return {"priority" : 1, "job" : "Peasant", "task" : "claim", "target" : self, "allowed_peasants" : True}
        return super().get_task(city)

    def qdel(self):
        if(self.faction):
            self.faction.members.remove(self)
        self.faction = None
        super().qdel()

class Construction(Structure):
    icon_symbol = "c"
    name = "Construction"

    def __init__(self, loc, x, y, to_construct, struc_type, faction=None):
        super().__init__(loc, x, y, faction)
        self.to_construct = to_construct
        self.struc_type = struc_type

    def construct(self, severity):
        self.to_construct = max(self.to_construct - severity, 0)
        if(self.to_construct <= 0):
            self.struc_type(self.loc, self.x, self.y, self.faction)
            self.qdel()
            del self

    def get_task(self, city):
        if(city.faction != self.faction):
            relation = city.faction.get_relationship(self.faction)
            if(relation == "Hostile"):
                return {"priority" : 1, "job" : "Peasant", "task" : "claim", "target" : self, "allowed_peasants" : True}
        return {"priority" : 2, "job" : "Builder", "task" : "construct", "target" : self, "allowed_peasants" : False}

    def qdel(self):
        self.qdeling = True
        self.struc_type = None
        super().qdel()


class House(Structure):
    icon_symbol = "h"
    name = "House"
    work_required = 15

    def get_task(self, city):
        if(city.faction != self.faction):
            relation = city.faction.get_relationship(self.faction)
            if(relation == "Hostile"):
                return {"priority" : 1, "job" : "Peasant", "task" : "claim", "target" : self, "allowed_peasants" : True}
        return {"priority" : 1, "job" : "Peasant", "task" : "rest", "target" : self, "allowed_peasants" : True}

    def fire_act(self, severity):
        self.crumble(severity)
        return True


class Farm(Structure):
    icon_symbol = "w"
    name = "Farm"
    work_required = 10

    harvestable = True
    allow_peasants = False
    resource = "food"
    job_to_harvest = "Farmer"
    harv_priority = 1

    default_resource_multiplier = 1.3
    def_amount = 100

    def fire_act(self, severity):
        self.crumble(severity)
        return True


class Mine(Structure):
    icon_symbol = "m"
    name = "Mine"
    work_required = 20

    harvestable = True
    allow_peasants = False
    resource = "stone"
    job_to_harvest = "Miner"
    harv_priority = 5

    default_resource_multiplier = 1.3
    def_amount = 100


class Citizen(Mob):
    icon_symbol = ""
    max_actions_to_perform = 2
    priority = 0

    def __init__(self, loc, x, y):
        self.loc = None
        self.move_atom_to(loc, x, y)
        self.display_name = self.name + " " + str(random.randrange(1, 999))
        self.actions_to_perform = self.max_actions_to_perform

        self.max_health = random.randrange(2, 4)
        self.health = self.max_health
        self.age = 8760  # At least one year.

        self.max_saturation = random.randrange(50, 100)
        self.saturation = self.max_saturation
        self.hunger_rate = random.uniform(0.8, 1.2)
        self.malnutrition = 0

        self.qdeling = False
        self.quality_modifier = random.uniform(0.8, 1.2)
        self.tool = None

    def move_atom_to(self, loc, x, y):
        if(self.loc):  # We are already initialized, and have a loc.
            if(self in self.loc.contents):
                self.loc.contents.remove(self)
            if(self in self.loc.citizens):
                self.loc.citizens.remove(self)

        self.loc = loc
        self.loc.contents.append(self)
        self.x = x
        self.y = y
        # Currently citizens can't be bothered to move out of the town/ Citizens mob.self
        # So this bootleg makes sense.
        self.loc.citizens.append(self)

    def life(self):
        self.actions_to_perform = min([self.max_actions_to_perform, self.actions_to_perform + 1])
        if(prob(self.health)):  # A healthy spirit in a healthy body.
            self.actions_to_perform = min([self.max_actions_to_perform, self.actions_to_perform + 1])
        self.saturation = max(self.saturation - round(self.hunger_rate * self.loc.action_time), 0)
        to_grab = min([self.max_saturation - self.saturation, self.loc.resources["food"]])
        self.loc.resources["food"] = max([self.loc.resources["food"] - to_grab, 0])
        self.saturation = self.saturation + to_grab
        self.age_by(self.loc.action_time)

        if(self.actions_to_perform <= 0):  # OVERWORKING: Citizens can work more than they should, but they will die quicker.
            if(prob(round((self.age / 8760) * abs(self.actions_to_perform)))):
                self.crumble(abs(self.actions_to_perform))
                return False

        if(self.saturation == 0):
            self.malnutrition += 1 + (self.age // 8760) # Age in years.
            if(prob(self.malnutrition)):
                self.crumble(self.malnutrition)
                return False # Dead. Gray dead.

        if(prob(self.age // 8760)): # Sometimes they just die.
            self.crumble(self.age // 87600)
            return False

        if(self.malnutrition > 0):
            self.malnutrition = max([self.malnutrition - round(self.saturation / (self.max_saturation + 0.0001)), 0])

        return True # If it didn't die this iteration.

    def age_by(self, time):
        if(prob(time)):  # Special actions ensue.
            self.quality_modifier += 0.1
        self.age += time  # Normal behavior.

    def qdel(self):
        self.qdeling = True
        if(self.tool):
            self.tool.qdel()
            tool = None
        if(self.loc):
            if(self in self.loc.citizens):
                self.loc.citizens.remove(self)
            if(self in self.loc.contents):
                self.loc.contents.remove(self)
        self.loc = None
        del self

    def perform_task(self, strucs, task):
        if(task["task"] == "harvest"):
            return self.harvest(task["target"])
        elif(task["task"] == "create"):
            return self.create(task["res_required"], task["target"])
        elif(task["task"] == "construct"):
            return self.construct(task["target"])
        elif(task["task"] == "build"):
            look_for = []
            if(task["target"] == Farm):
                look_for = [Plains]
            if(task["target"] == Mine):
                look_for = [Rocky]
            if(task["target"] == House):
                look_for = [Plains, Hills]
            for struc in strucs:
                if(is_instance_in_list(struc, look_for)):
                    return self.build(task["res_required"], task["target"], struc.world, struc.x, struc.y)
            return False
        elif(task["task"] == "rest"):
            return self.rest(task["target"])
        elif(task["task"] == "destroy"):
            return self.destroy(task["target"])
        elif(task["task"] == "kidnap"):
            return self.kidnap(task["target"])
        elif(task["task"] == "gift"):
            return self.gift(task["res_required"], task["target"])
        elif(task["task"] == "claim"):
            return self.claim(task["target"])
        return False

    def create(self, resources_required, item_type):
        for res in resources_required:
            if(self.loc.resources[res] <= resources_required[res]):
                return False
        for res in resources_required:
            self.loc.resources[res] = self.loc.resources[res] - resources_required[res]
        self.loc.inventory.append(item_type(self.loc, -2, -2, resources_required, self.quality_modifier))
        self.actions_to_perform -= 1
        return True

    def build(self, resources_required, struc_, world, x, y):
        if(self.loc.world.is_overcrowded(x, y, 5)): # Since most strucs are size 5.
            return False
        for res in resources_required:
            if(self.loc.resources[res] <= resources_required[res]):
                return False
        for res in resources_required:
            self.loc.resources[res] = self.loc.resources[res] - resources_required[res]
        self.actions_to_perform -= 1
        Construction(world, x, y, struc_.work_required, struc_, self.loc.faction)
        return True

    def construct(self, target):
        target.construct(round(self.quality_modifier * self.loc.action_time))
        self.actions_to_perform -= 1
        return True

    def harvest(self, target):
        if(not target.been_used):
            to_harvest = round(self.loc.action_time * target.resource_multiplier * self.get_tool_quality(target.job_to_harvest))
            harvested = target.harvest(self, to_harvest)
            if(harvested > 0):
                self.loc.resources[target.resource] = self.loc.resources[target.resource] + harvested
                self.actions_to_perform -= 1
                return True
        return False

    def rest(self, target):
        if(target.been_used):
            return False
        else:
            self.actions_to_perform = min([self.actions_to_perform + 2, self.max_actions_to_perform])
            self.health = min([self.health + 1, self.max_health])
            return True

    def destroy(self, target):
        damage_to_do = round(self.actions_to_perform + (self.max_saturation / (self.saturation + 0.0001)) - (self.malnutrition // 100) - (self.age // 87600))
        if(damage_to_do >= 1):
            if(not target.react_to_attack(self)):
                target.crumble(int(damage_to_do))
                self.actions_to_perform -= int(damage_to_do)  # Hitting hard takes more effort.
                return True
        return False

    def kidnap(self, target):
        if(len(target.citizens)):
            citizen = random.choice(target.citizens)
            citizen.move_atom_to(self.loc, -2, -2)
            self.actions_to_perform -= 1
            return True
        return False

    def gift(self, resources_required, target):
        for res in resources_required:
            if(self.loc.resources[res] <= resources_required[res]):
                return False
        for res in resources_required:
            self.loc.resources[res] = self.loc.resources[res] - resources_required[res]
        self.actions_to_perform -= 1
        target.faction.adjust_relationship(self.loc.faction, 10)
        return True

    def claim(self, target):
        if(not target.faction):
            target.faction = self.loc.faction
            self.loc.faction.add_to_faction(target)
            target.update_icon()
        elif(not target.crumble(1)):  # By "capturing" it, we of course mean murdering it slightly.
            target.faction.members.remove(target)
            target.faction = None
            target.update_icon()
        self.actions_to_perform -= 1
        return True

    def crumble(self, severity):
        self.health = self.health - severity
        if(self.health <= 0):
            self.qdeling = True
            self.loc.remove_citizen(self)
            del self
            return True # Fully crumbled.
        return False

    def fire_act(self, severity):
        self.crumble(severity)
        return False  # I mean, you can't spread fire by just the Citizen. Neither you really could.


    def required_citizens(self, strucs):
        requests = {"Peasant" : 0,
                    "Builder" : 1 + (len(self.loc.citizens) // 10),
                    "Farmer" : 0,
                    "Miner" : 0,
                    "Stonecutter" : (len(self.loc.citizens) // 10),
                    "Blacksmith" : 0,
                    "Weaponsmith" : 0,
                    "Lumberjack" : 0,
                    "Carpenter" : 1,
                    "Toddler" : 0}
        for struc in strucs:
            if(isinstance(struc, Farm)):
                requests["Farmer"] = requests["Farmer"] + 1
            if(isinstance(struc, Mine)):
                requests["Miner"] = requests["Miner"] + 1
            if(isinstance(struc, Forest)):
                requests["Lumberjack"] = requests["Lumberjack"] +1
        for citizen in self.loc.citizens:
            requests[citizen.name] = requests[citizen.name] - 1
        for tool in self.loc.inventory:
            if(not isinstance(tool, Tool)):
                continue
            requests[tool.job] = requests[tool.job] - 1
        return requests

    def required_strucs(self, strucs):
        requests = {"House" : 0,
                    "Farm" : 0,
                    "Mine" : 0}
        for struc in strucs:
            if(isinstance(struc, Farm)):
                requests["Farm"] = requests["Farm"] - 1
            if(isinstance(struc, Rocky)):
                requests["Mine"] = requests["Mine"] + 1
        requests["Farm"] = requests["Farm"] + round(len(self.loc.citizens) / 3)
        requests["House"] = requests["House"] + int(round(self.loc.max_population - len(self.loc.citizens)) == 0)
        return requests

    def get_citizen_count(self, citizen_name):
        count = 0
        for citizen in self.loc.citizens:
            if(citizen.name == citizen_name):
                count = count + 1
        return count

    def get_item_count(self, item_name):
        return self.loc.inventory.count(item_name)

    def is_job_required(self, citizen_name):
        if(self.loc.job_requests[citizen_name] > 0):
            return True
        return False

    def accomplish_job_request(self, citizen_name):
        if(self.is_job_required(citizen_name)):
            self.loc.job_requests[citizen_name] = self.loc.job_requests[citizen_name] - 1
            return True
        return False

    def is_struc_required(self, struc_name):
        if(self.loc.structure_requests[struc_name] > 0):
            return True
        return False

    def accomplish_struc_request(self, struc_name):
        if(self.is_struc_required(struc_name)):
            self.loc.structure_requests[struc_name] = self.loc.structure_requests[struc_name] - 1
            return True
        return False

    def get_tool_quality(self, job_to_check):
        if(self.tool and self.tool.job == job_to_check):
            return self.tool.quality
        return 1

    def become_job(self, job):
        for tool in self.loc.inventory:
            if(not isinstance(tool, Tool)):
                continue
            if(tool.job == job.name):
                #if(self.accomplish_job_request(job.name)): # Uncomment if do something better.
                self.loc.add_citizen(job)
                self.loc.remove_citizen(self)
                return True
        return False

    def try_equip(self):
        for tool in self.loc.inventory:
            if(not isinstance(tool, Tool)):
                continue
            if(tool.job != self.name):
                continue
            if(tool.quality > self.get_tool_quality(self.name)):
                if(self.tool):
                    self.loc.inventory.append(self.tool)
                self.tool = tool
                self.loc.inventory.remove(self.tool)


class Toddler(Citizen):
    icon_symbol = "t"
    name = "Toddler"

    def __init__(self, loc, x, y):
        super().__init__(loc, x, y)
        self.age = 0  # Since citizen is set to 8760.

        self.max_health = 1
        self.health = self.max_health

        self.max_saturation = random.randrange(10, 20)
        self.saturation = self.max_saturation
        self.hunger_rate = random.uniform(0.2, 0.3)

    def perform_task(self, strucs, task):
        return False  # Toddlers do no work.

    def become_job(self, job):
        return False

    def life(self):
        if(not super().life()):
            return False

        if((self.age / 8760) >= 1):
            self.become_adult()
        return True

    def become_adult(self):
        # Read somewhere above about the -2 -2.
        peasant = Peasant(self.loc, -2, -2)
        self.loc.citizens.append(peasant)
        peasant.try_equip()
        peasant.health = self.health
        peasant.age = self.age

        peasant.saturation = self.saturation
        peasant.malnutrition = self.malnutrition

        peasant.quality_modifier = self.quality_modifier
        self.loc.remove_citizen(self)


class Peasant(Citizen):
    icon_symbol = "p"
    name = "Peasant"

    def perform_task(self, strucs, task): # These are in that very order for a reason.
        if(self.become_job(Farmer)):
            return False
        elif(self.become_job(Carpenter)):
            return False
        elif(self.become_job(Builder)):
            return False
        elif(self.become_job(Stonecutter)):
            return False
        elif(self.become_job(Lumberjack)):
            return False
        elif(self.become_job(Miner)):
            return False
        elif(self.become_job(Blacksmith)):
            return False
        elif(self.become_job(Weaponsmith)):
            return False
        return super().perform_task(strucs, task)


class Builder(Citizen):
    icon_symbol = "b"
    name = "Builder"


class Farmer(Citizen):
    icon_symbol = "f"
    name = "Farmer"


class Miner(Citizen):
    icon_symbol = "m"
    name = "Miner"


class Stonecutter(Citizen):
    icon_symbol = "s"
    name = "Stonecutter"


class Blacksmith(Citizen):
    icon_symbol = "B"
    name = "Blacksmith"


class Weaponsmith(Citizen):
    icon_symbol = "w"
    name = "Weaponsmith"


class Lumberjack(Citizen):
    icon_symbol = "l"
    name = "Lumberjack"


class Carpenter(Citizen):
    icon_symbol = "c"
    name = "Carpenter"


class Citizens(Mob):
    icon_symbol = "o"
    icon_color = "grey"
    name = "Citizens"
    priority = 29
    size = 1
    starting_citizens = 5

    needs_processing = True
    action_time = 1

    def __init__(self, loc, x, y, faction=None, target=None):
        super().__init__(loc, x, y)
        self.try_new = 3
        self.citizens = []
        self.inventory = []
        if(faction):
            self.faction = faction
            self.faction.add_to_faction(self)
        else:
            self.faction = Faction(self)
        self.target = target
        self.resources = {"food" : 50,
                          "wood" : 0,
                          "stone" : 0,
                          "iron" : 0,
                          "gold" : 0}
        for N in range(self.starting_citizens):
            self.add_citizen(Peasant)

    def qdel(self):
        self.qdeling = True
        self.inventory = []
        self.target = None
        for cit in self.citizens:
            cit.qdel()
            del cit
        self.citizens = []
        super().qdel()

    def life(self):
        if(not len(self.citizens)):
            self.qdel()
            del self
            return

        if(self.resources["food"] > 100):
            self.resources["food"] = max([self.resources["food"] - 50, 0])
            self.add_citizen(Toddler)

        for citizen in self.citizens:
            if(not citizen.qdeling):
                citizen.life()

        if(self.qdeling):
            del self
            return

        self.handle_ai_movement()

        self.size = int(len(self.citizens) // 10)

        if(self.world.is_overcrowded(self.x, self.y, 0)):
            for struc in self.world.get_tile_contents(self.x, self.y):
                if(struc == self):
                    continue
                if(struc.crumble(self.size)):
                    return
        self.update_icon()

    def add_citizen(self, citizen_type):
        citizen = citizen_type(self, -2, -2) #Huehuehue. -2 -2 won't be qdeled.
        citizen.try_equip()
        self.update_icon()

    def remove_citizen(self, citizen_):
        if(citizen_):
            citizen_.qdel()
            del citizen_
        elif(len(self.citizens) > 0):
            citizen_ = random.choice(self.citizens)
            citizen_.qdel()
            del citizen_
        self.update_icon()
        if(len(self.citizens) == 0):
            self.qdel()
            del self
    
    def handle_ai_movement(self):
        self.resources["food"] = max([self.resources["food"] - (len(self.citizens) * self.action_time), 0])
        if(self.target):
            self.move_towards_to(self.world, target.x, target.y)
            return
        spot_x = self.x
        spot_y = self.y
        best_index = 0
        coords = self.world.get_region_coordinates(self.x, self.y, 2, 2)
        random.shuffle(coords)
        for coord in coords:
            coord = coord_to_list(coord)
            x_ = coord["x"]
            y_ = coord["y"]
            if(not self.world.coords_sanitized(x_, y_)):
                continue
            ind = self.get_spot_quality_index(x_, y_)
            if(ind > best_index):
                spot_x = x_
                spot_y = y_
                best_index = ind
        if(spot_x == self.x and spot_y == self.y):
            self.attempt_settle()
            return
        if(not self.move_towards_to(self.world, spot_x, spot_y)):
           self.attempt_settle()

    def get_spot_quality_index(self, x, y):
        quality = 0
        #requirements = ["Forest", "Tall_Grass", "Tall_Grass", "Tall_Grass"]
        if(self.world.is_overcrowded(x, y, 5 + int(len(self.citizens) // 10))):
            return -10000 # I don't think it will ever get any lower.
        for struc in self.world.get_tile_contents(x, y):
            if(isinstance(struc, Tall_Grass)):
                #requirements.remove("Tall_Grass")
                quality = quality + 3 * struc.resource_multiplier
            elif(isinstance(struc, Forest)):
                #requirements.remove("Forest")
                quality = quality + 2 * struc.resource_multiplier
            elif(isinstance(struc, Mountain)):
                quality = quality + 2 * struc.resource_multiplier
            elif(isinstance(struc, Iron_Deposit)):
                quality = quality + 1 * struc.resource_multiplier
            elif(isinstance(struc, Gold_Deposit)):
                quality = quality + 1 * struc.resource_multiplier
            elif(isinstance(struc, City)):
                if(struc.faction != self.faction):
                    quality += 10
                elif(self.resources["food"] >= 3 * len(self.citizens) * self.action_time):
                    quality = quality + 10
                else:
                    quality = quality - 10 # Citizens won't move into cities if they can continue on searching for a spot.
        #if(len(requirements)):
            #return 0
        return quality

    def attempt_settle(self):
        strucs = self.world.get_tile_contents(self.x, self.y)
        for struc in strucs:
            if(isinstance(struc, City)):
                return
        if(self.world.is_overcrowded(self.x, self.y, 5 + int(len(self.citizens) // 10))):
            return
        city = City(self.loc, self.x, self.y, self.faction)
        city.resources = self.resources
        for citizen in city.citizens:
            citizen.qdel()
            del citizen
        for citizen in self.citizens:
            citizen.loc = city
            city.citizens.append(citizen)
        self.citizens = []
        self.qdel()
        del self

    def transfer_resources_to(self, resource_list, target):
        for resource in resource_list:
            target.resources[resource] = target.resources[resource] + resource_list[resource]

    def fire_act(self, severity):
        for cit in range(severity):
            if(not len(self.citizens)):
                return False
            citizen = random.choice(self.citizens)
            if(not citizen.qdeling):
                citizen.fire_act(severity)
                return True
        return False
