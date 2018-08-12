import random
import tkinter
import math
import threading
import time
import sys

# Defines go here.
#sys.stdout = open('log.txt', 'w') # Uncomment if you want to export to a log file.

log = ""
sqrt_2 = math.sqrt(2)
runtime = True
atoms_by_name = {}

def time_to_date(time): # Time is in hours.
    year = 0
    month = 0
    day = 0
    year = int(time // 8760)
    if(year > 0):
        time = time - year * 8760
    month = int(time // 720)
    if(month > 0):
        time = time - month * 720
    day = int(time // 24)
    if(day > 0):
        time = time - day * 24
    return number_to_day(day) + "." + number_to_month(month) + "." + number_to_year(year)
    
def number_to_year(num):
    if(num > 999):
        return str(num)
    elif(num > 99):
        return "0"+str(num)
    elif(num > 9):
        return "00"+str(num)
    return "000"+str(num)

def number_to_month(num):
    if(num > 9):
        return str(num)
    return "0"+str(num)

def number_to_day(num):
    if(num > 9):
        return str(num)
    return "0"+str(num)

def prepare_lists():
    atom_classes = get_all_subclasses(Atom)
    for atom in atom_classes:
        atoms_by_name[atom.name] = atom

def prob(prob):
    if(random.randrange(1, 100) <= prob):
        return True
    return False

def is_instance_in_list(instance, list_):
    for inst in list_:
        if(isinstance(instance, inst)):
            return True
    return False

def pick_weighted(sequence):
    choices = []
    for el in sequence:
        number = sequence[el]
        for choice in range(number):
            choices.append(el)
    return random.choice(choices)

def clamp(val, min_, max_):
    return min(max(val, min_), max_)

def find_in_list(list, obj):
    for item in list:
        if(item == obj):
            return True
    return False

def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses

def get_contents(atom):
    return atom.contents

def sign(val):
    return (val > 0) - (val < 0)

def x_y_to_coord(x, y):
    return "(" + str(x) + ", " + str(y) + ")"

def coord_to_list(coord):
    coord = coord[1:len(coord) - 1]
    y = coord.find(",") + 2
    return {"x" : int(coord[0:y - 2]), "y" : int(coord[y:len(coord)])}

def get_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def get_vector(x1, x2):
    return sign(x2 - x1)

def master_controller():
    while(runtime):
        for world in worlds:
            if(world.initiated):
                if(world.processing):
                    continue
                world.process()

def text_to_path(text):
    return atoms_by_name[text]
        
# World stuff goes here.
worlds = []

class World:
    name = ""
    map_c = {}
    contents = []
    max_x = 50
    max_y = 50
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
        time.sleep(0)
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

# Datums.
factions = []

class Faction:
    name = "" # I should really rename this to type, or use type instead.

    def __init__(self, creator):
        global factions
        self.display_name = random.choice(["Holy ", "Sacred ", "Eternal ", "Benevolent ", "Victorious ", "Glorious ", "Mighty "]) + random.choice(["Guild ", "Faction ", "Unity ", "Family ", "Dominion ", "Empire ", "Den "]) + random.choice(["of ", "for ", "with "]) + random.choice(["Citizens", "People", "Royalties", "Them", "Members", "Creations", "Knights", "Farmers", "Lands"])
        factions.append(self)
        self.members = [creator]
        self.relationships = {}
        for faction in factions:
            if(faction == self):
                continue
            faction.relationships[self] = 0
            self.relationships[faction] = 0

    def add_to_faction(self, member):
        self.members.append(member)

    def qdel(self):
        self.qdeling = True
        for member in self.members:
            member.faction = None
        self.members = []
        for relationship in self.relationships:
            relationship.relationships.remove(self)
        self.relationships = {}
        del self

# Atoms.
atoms = []

class Atom:
    symbol = ""
    priority = 0

    name = ""
    display_name = "" # Since "name" is more of a type, really.
    description = ""

    obstruction = False
    size = 0

    needs_processing = False

    action_time = 0

    resource = ""
    job_to_harvest = ""

    def __init__(self, loc, x, y):
        self.x = - 1
        self.y = -1
        self.loc = None
        self.world = loc.get_world()
        self.contents = []
        self.move_atom_to(loc, x, y)
        self.last_action = self.world.time
        self.display_name = self.name
        self.integrity = self.size
        self.qdeling = False
        self.been_used = False
        self.resource_multiplier = random.uniform(1.0, 1.5)
        atoms.append(self)
        if(self.needs_processing):
            self.world.process_atoms.append(self)

    def get_world(self):
        if(isinstance(loc, World)):
            return loc
        else:
            return get_world()

    def get_tile_contents(self, x, y):
        return self.contents

    def bump(self, bumped_with): # Bumped with is the thing that called the bump proc.
        return

    def bump_into(self, bumped_into):
        return

    def does_obstruct(self, atom):
        return self.obstruction

    def move_atom_to(self, world, x, y):
        if(find_in_list(self.world.map_c, x_y_to_coord(self.x, self.y)) and find_in_list(self.world.map_c[x_y_to_coord(self.x, self.y)], self)):
            self.world.map_c[x_y_to_coord(self.x, self.y)].remove(self)
        if(self.world.coords_sanitized(x, y)):
            overcrowded = self.world.is_overcrowded(x, y, 0)
            for struc in self.world.get_tile_contents(x, y):
                if(struc == self):
                    continue
                if(overcrowded):
                    struc.crumble(self.size)
                struc.bump(self)
                self.bump_into(struc)
            world.map_c[x_y_to_coord(x, y)].append(self)
        self.loc = world
        self.loc.contents.append(self)
        self.x = x
        self.y = y

    def attempt_move_to(self, world, x, y):
        for struc in world.get_tile_contents(x, y):
            if(struc.does_obstruct(self)):
                return False
        if(get_distance(self.x, self.y, x, y) > sqrt_2): # sqrt_2 = math.sqrt(2), because diagonal tiles?
           return False
        self.move_atom_to(world, x, y)
        return True

    def move_towards_to(self, world, x, y):
        dummy_moves = 3 # Set this to something higher if you want some wacky shit.
        x_ = self.x + get_vector(self.x, x)
        y_ = self.y + get_vector(self.y, y)
        while(dummy_moves):
            if(not self.attempt_move_to(world, x_, y_)):
                x_t = self.x + random.randrange(-1, 1)
                y_t = self.y + random.randrange(-1, 1)
                if(self.world.coords_sanitized(x_t, y_t)):
                    x_ = x_t
                    y_ = y_t
                    dummy_moves = dummy_moves - 1
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
            return True # Fully crumbled.
        return False

    def fire_act(self, severity): # Return True if it is susceptible to fires.
        return False

    def qdel(self):
        self.qdeling = True
        if(self in atoms):
            atoms.remove(self)
        if(self.needs_processing and find_in_list(self.world.process_atoms, self)):
            self.world.process_atoms.remove(self)
        if(find_in_list(self.world.map_c, x_y_to_coord(self.x, self.y)) and find_in_list(self.world.map_c[x_y_to_coord(self.x, self.y)], self)):
            self.world.map_c[x_y_to_coord(self.x, self.y)].remove(self)
        if(find_in_list(self.loc.contents, self)):
            self.loc.contents.remove(self)
        self.loc = None
        del self

class Area(Atom):
    priority = 0
    obstruction = False

class Turf(Atom):
    priority = 1
    allowed_contents = []
    size = 20 # Turfs are really big.

    def generate_contents(self):
        return text_to_path(pick_weighted(self.allowed_contents))

    def crumble(self, severity):
        return False

class Moveable(Atom):
    obstruction = False

class Object(Moveable):
    priority = 11

class Mob(Moveable):
    priority = 21

    def process(self):
        self.life()

    def life(self):
        return

#Areas.

#Turfs.
class Plains(Turf):
    symbol = "_"
    name = "Plains"
    allowed_contents = {"Nothing" : 100, "Tall_Grass" : 30, "Forest" : 5}

class Hills(Turf):
    symbol = "-"
    name = "Hills"
    allowed_contents = {"Nothing" : 100, "Forest" : 1}

class Rocky(Turf):
    symbol = "="
    name = "Rocky"
    allowed_contents = {"Nothing" : 100, "Mountain" : 10, "Iron_Deposit" : 3, "Gold_Deposit" : 1, "Forest" : 1}

class Water(Turf):
    symbol = "~"
    name = "Water"
    obstruction = True

#Objects.
class Nothing(Object):
    symbol = ""
    name = "Nothing"

    def __init__(self, world, x, y):
        del self

class Fire(Object):
    symbol = "x"
    name = "Fire"
    size = 3
    priority = 19

    action_time = 3
    needs_processing = True

    def __init__(self, loc, x, y, integrity = 3):
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
                        self.integrity = min(self.integrity + 1, self.size)
                continue
            for struc in strucs:
                if(isinstance(struc, Fire)):
                    break
                if(isinstance(struc, Water)):
                    break
                if(struc.fire_act(1)):
                    self.spread_to(struc.x, struc.y)
                    break
            #if(prob(self.integrity * 5) and not (x_ == self.x and y_ == self.y)):
                #self.spread_to(x_, y_)
        self.crumble(1)

    def spread_to(self, x, y):
        Fire(self.world, x, y, self.integrity)

class Tall_Grass(Object):
    name = "Tall_Grass"
    size = 3
    priority = 0

    resource = "food"
    job_to_harvest = "Farmer"

    def fire_act(self, severity):
        self.crumble(severity)
        return True

class Forest(Object):
    symbol = "^"
    name = "Forest"
    size = 10

    resource = "wood"
    job_to_harvest = "Lumberjack"

    def fire_act(self, severity):
        self.crumble(severity)
        return True

class Mountain(Object):
    symbol = "A"
    name = "Mountain"
    obstruction = True
    size = 15

    resource = "stone"
    job_to_harvest = "Miner"

class Iron_Deposit(Object):
    name = "Iron_Deposit"
    obstruction = True
    size = 3
    priority = 0

    resource = "iron"
    job_to_harvest = "Miner"

class Gold_Deposit(Object):
    name = "Gold_Deposit"
    obstruction = True
    size = 3
    priority = 0

    resource = "gold"
    job_to_harvest = "Miner"

class Tool(Object):
    name = ""
    job = ""

    def __init__(self, loc, x, y, materials = {"wood" : 5}, quality_modifier = 1):
        self.x = x
        self.y = y
        self.loc = loc
        self.materials = materials
        self.quality = random.uniform(2.5, 3.5) * quality_modifier

    def qdel(self):
        self.qdeling = True
        if(find_in_list(self.loc.inventory, self)):
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
    symbol = "1"
    name = "City"
    priority = 30 # Should actually be above mob layer.
    size = 5

    starting_citizens = 5

    needs_processing = True
    action_time = 5

    def __init__(self, loc, x, y, faction = None):
        global log
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
        self.size = self.integrity
        if(faction):
            self.faction = faction
            self.faction.add_to_faction(self)
        else:
            self.faction = Faction(self)
        self.resources = {"food" : 100,
                          "wood" : 0,
                          "stone" : 0,
                          "iron" : 0,
                          "gold" : 0}
        for N in range(self.starting_citizens):
            self.add_citizen(Peasant)
        log = log + self.display_name + " has been settled in " + x_y_to_coord(self.x, self.y) + " at " + time_to_date(self.world.time) + "\n"

    def qdel(self):
        global log
        self.qdeling = True
        log = log + self.display_name + " has been destroyed in " + x_y_to_coord(self.x, self.y) + " at " + time_to_date(self.world.time) + "\n"
        for cit in self.citizens:
            cit.qdel()
            del cit
        self.citizens = []
        for tool in self.inventory:
            tool.qdel()
            del tool
        self.inventory = []
        self.tasks = []
        super().qdel()

    def does_obstruct(self, atom):
        if(isinstance(atom, Citizens)):
            if(atom.resources["food"] < 3 * len(atom.citizens) * atom.action_time):
                atom.transfer_resources_to(atom.resources, self)
                for citizen in atom.citizens:
                    citizen.loc = self
                    self.citizens.append(citizen)
                atom.citizens = []
                atom.qdel()
                del atom
                return False
            else:
                return True
        return False

    def process(self):
        food_required = len(self.citizens)
        food_supply = 0

        strucs = self.world.get_region_contents(self.x, self.y, 1, 1)
        random.shuffle(strucs)

        dummy = random.choice(self.citizens)
        self.job_requests = dummy.required_citizens(strucs)
        self.structure_requests = dummy.required_strucs(strucs)

        self.tasks = []

        for struc in strucs:
            if(isinstance(struc, Tall_Grass)):
                food_supply = food_supply + 1
                if(food_required > 0):
                    self.tasks.append({"priority" : 1, "job" : "Farmer", "task" : "harvest", "target" : struc, "allowed_peasants" : True})
                    food_required = food_required - 1
            if(isinstance(struc, Farm)):
                food_supply = food_supply + 3
                if(food_required > 0):
                    self.tasks.append({"priority" : 1, "job" : "Farmer", "task" : "harvest", "target" : struc, "allowed_peasants" : False})
                    food_required = food_required - 3
            if(isinstance(struc, Mountain)):
                self.tasks.append({"priority" : 5, "job" : "Miner", "task" : "harvest", "target" : struc, "allowed_peasants" : True})
            if(isinstance(struc, Mine)):
                self.tasks.append({"priority" : 5, "job" : "Miner", "task" : "harvest", "target" : struc, "allowed_peasants" : False})
            if(isinstance(struc, Forest)):
                self.tasks.append({"priority" : 3, "job" : "Lumberjack", "task" : "harvest", "target" : struc, "allowed_peasants" : True})
            if(isinstance(struc, Construction)):
                self.tasks.append({"priority" : 2, "job" : "Builder", "task" : "construct", "target" : struc, "allowed_peasants" : False})

        for job_request in self.job_requests:
            if(job_request == "Farmer"):
                for task in range(0, self.job_requests[job_request]):
                    self.tasks.append({"priority" : 2, "job" : "Carpenter", "task" : "create", "target" : Hoe, "res_required" : {"wood" : 5}, "allowed_peasants" : False})
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
                    self.tasks.append({"priority" : 2, "job" : "Builder", "task" : "build", "target" : Farm, "res_required" : {"wood" : 30}, "allowed_peasants" : False})
            elif(structure_request == "Mine"):
                for task in range(0, self.structure_requests[structure_request]):
                    self.tasks.append({"priority" : 3, "job" : "Builder", "task" : "build", "target" : Mine, "res_required" : {"wood" : 30}, "allowed_peasants" : False})
            elif(structure_request == "House"):
                for task in range(0, self.structure_requests[structure_request]):
                    self.tasks.append({"priority" : 3, "job" : "Builder", "task" : "build", "target" : House, "res_required" : {"wood" : 30, "stone" : 30}, "allowed_peasants" : False})

        cur_priority = 1
        while(cur_priority <= 10):
            tasks = self.get_priority_tasks_list(cur_priority)
            if(not tasks):
                cur_priority = cur_priority + 1
            for task in tasks:
                cits = self.get_susceptible_citizens_list(task)
                if(not cits):
                    continue
                for citizen in cits:
                    if(citizen.qdeling):
                        continue
                    if(citizen.actions_to_perform <= 0):
                        continue
                    if(prob(citizen.age)): # Old people just tend to refuse to work sometimes.
                        continue
                    print(citizen.display_name + " is trying to perform " + str(task))
                    print("Has actions left: " + str(citizen.actions_to_perform))
                    if(citizen.perform_task(strucs, task)):
                        print(citizen.display_name + " has succesfully performed above task")
                        self.tasks.remove(task)
                        break
            cur_priority = cur_priority + 1

        if(len(self.citizens) > 99):
            cit = Citizens(self.loc, self.x, self.y, self.faction)
            cit.resources["food"] = 0
            for c in range(5):
                cit.add_citizen(Peasant)
                self.remove_citizen(None)
        if(food_supply > len(self.citizens) and len(self.citizens) <= self.max_population):
            self.add_citizen(Peasant)

        for citizen in self.citizens:
            citizen.actions_to_perform = citizen.actions_to_perform + 1
            if(not citizen.qdeling):
                if(citizen.life()):
                    citizen.try_equip() # Even old people steal tools.

        houses_count = 0
        for struc in strucs:
            struc.been_used = False
            if(isinstance(struc, House) and len(self.citizens)):
                houses_count = houses_count + 1
                citizen = random.choice(self.citizens)
                citizen.actions_to_perform = min(citizen.actions_to_perform + 1, citizen.max_actions_to_perform)
        self.max_population = 10 + houses_count * 2

        if(len(self.citizens) < 100):
            self.symbol = str(int(len(self.citizens) // 10))
        elif(len(self.citizens) < 1000):
             self.symbol = "L"
        elif(len(self.citizens) < 10000):
             self.symbol = "M"

        if(len(self.citizens) > self.max_population): # Overpopulation - DEATH!
            self.remove_citizen(None)

        self.size = 5 + int(len(self.citizens) // 10)
        if(self.world.is_overcrowded(self.x, self.y, 0)):
            for struc in self.world.get_tile_contents(self.x, self.y):
                if(struc == self):
                    continue
                struc.crumble(self.size)
        print(self.display_name)
        print(self.faction.display_name)
        print(self.resources)
        print(self.inventory)
        l = ""
        for cit in self.citizens:
            l = l + cit.display_name + " "
        print(l)

    def add_citizen(self, citizen_type):
        citizen = citizen_type(self, -2, -2) #Huehuehue. -2 -2 won't be qdeled.
        self.citizens.append(citizen)
        citizen.try_equip()

    def remove_citizen(self, citizen_):
        for citizen in self.citizens:
            if(citizen.loc == None):
                citizen.qdel()
                del citizen
        if(citizen_):
            citizen_.qdel()
            del citizen_
        elif(len(self.citizens) > 0):
            citizen_ = random.choice(self.citizens)
            citizen_.qdel()
            del citizen_
        if(len(self.citizens) == 0):
            #time.sleep(30)
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
        if(task["allowed_peasants"]): # It actually allows not just peasants, but everybody.
            for citizen in self.citizens:
                if(citizen.name == "Peasant"):
                    list_.append(citizen)
            for citizen in self.citizens:
                if(not find_in_list(list_, citizen)):
                   list_.append(citizen)
        return list_

    def fire_act(self, severity):
        for cit in range(severity):
            self.remove_citizen(None)
            return True

class Structure(Object): #Only one per tile.
    size = 5
    priority = 12

class Construction(Structure):
    symbol = "c"
    name = "Construction"
    work_required = 1

    def __init__(self, loc, x, y, to_construct, struc_type):
        super().__init__(loc, x, y)
        self.to_construct = to_construct
        self.struc_type = struc_type

    def construct(self, severity):
        self.to_construct = max(self.to_construct - severity, 0)
        if(self.to_construct <= 0):
            self.struc_type(self.loc, self.x, self.y)
            self.qdel()
            del self

    def qdel(self):
        self.qdeling = True
        self.struc_type = None
        super().qdel()

class House(Structure):
    symbol = "h"
    name = "House"
    work_required = 15

    def fire_act(self, severity):
        self.crumble(severity)
        return True

class Farm(Structure):
    symbol = "w"
    name = "Farm"
    work_required = 10

    resource = "wood"

    def fire_act(self, severity):
        self.crumble(severity)
        return True

class Mine(Structure):
    symbol = "m"
    name = "Mine"
    work_required = 20

    resource = "stone"

#Mobs.
class Citizen(Mob):
    symbol = ""
    max_actions_to_perform = 2
    priority = 0

    def __init__(self, loc, x, y):
        self.loc = loc
        self.loc.contents.append(self)
        self.x = x
        self.y = y
        self.display_name = self.name + " " + str(random.randrange(1, 999))
        self.actions_to_perform = self.max_actions_to_perform

        self.age = 0

        self.max_saturation = random.randrange(50, 100)
        self.saturation = self.max_saturation
        self.hunger_rate = random.uniform(0.5, 1.0)
        self.malnutrition = 0

        self.qdeling = False
        self.quality_modifier = random.uniform(0.9, 1.1)
        self.tool = None

    def life(self):
        self.saturation = max(self.saturation - round(self.hunger_rate * self.loc.action_time), 0)
        to_grab = min(self.max_saturation - self.saturation, self.loc.resources["food"])
        self.loc.resources["food"] = max(self.loc.resources["food"] - to_grab, 0)
        self.saturation = self.saturation + to_grab
        self.age = self.age + self.loc.action_time
        if(self.saturation == 0):
            self.malnutrition = self.malnutrition + 1 + (self.age // 8760) # Age in years.
            if(prob(self.malnutrition)):
                self.loc.remove_citizen(self)
                return False # Dead. Gray dead.
        if(prob(self.age // 8760)): # Sometimes they just die.
            self.loc.remove_citizen(self)
            return False
        elif(self.malnutrition > 0):
            self.manlutrition = max(self.malnutrition - round(self.max_saturation / (self.saturation + 1)), 0)
        return True # If it didn't die this iteration.

    def qdel(self):
        self.qdeling = True
        if(self.tool):
            self.tool.qdel()
            tool = None
        if(self.loc):
            if(find_in_list(self.loc.citizens, self)):
                self.loc.citizens.remove(self)
            if(find_in_list(self.loc.contents, self)):
                self.loc.contents.remove(self)
        self.loc = None
        del self

    def perform_task(self, strucs, task):
        if(prob(self.age // 8760)): # They die twice as much if they are working.
            self.loc.remove_citizen(self)
            return False
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
        return False

    def create(self, resources_required, item_type):
        for res in resources_required:
            if(self.loc.resources[res] <= resources_required[res]):
                return False
        for res in resources_required:
            self.loc.resources[res] = self.loc.resources[res] - resources_required[res]
        self.loc.inventory.append(item_type(self.loc, -2, -2, resources_required, self.quality_modifier))
        self.actions_to_perform = self.actions_to_perform - 1
        return True

    def build(self, resources_required, struc_, world, x, y):
        if(self.loc.world.is_overcrowded(x, y, 5)): # Since most strucs are size 5.
            return False
        for res in resources_required:
            if(self.loc.resources[res] <= resources_required[res]):
                return False
        for res in resources_required:
            self.loc.resources[res] = self.loc.resources[res] - resources_required[res]
        self.actions_to_perform = self.actions_to_perform - 1
        Construction(world, x, y, struc_.work_required, struc_)
        return True

    def construct(self, target):
        target.construct(round(self.quality_modifier * self.loc.action_time))
        self.actions_to_perform = self.actions_to_perform - 1
        return True

    def harvest(self, target):
        if(not target.been_used):
            target.been_used = True
            if(prob(self.loc.action_time)):
                if(target.crumble(1)):
                    return False
            self.loc.resources[target.resource] = self.loc.resources[target.resource] + round(self.loc.action_time * target.resource_multiplier * self.get_tool_quality(target.job_to_harvest))
            self.actions_to_perform = self.actions_to_perform - 1
            return True
        return False

    def required_citizens(self, strucs):
        requests = {"Peasant" : 0,
                    "Builder" : 1,
                    "Farmer" : 0,
                    "Miner" : 0,
                    "Stonecutter" : 1,
                    "Blacksmith" : 0,
                    "Weaponsmith" : 0,
                    "Lumberjack" : 0,
                    "Carpenter" : 1}
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
        print(str(requests["Farm"]) + " is estimated required farm number")
        requests["House"] = requests["House"] + (round(self.loc.max_population - len(self.loc.citizens)) == 0)
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

class Peasant(Citizen):
    symbol = "p"
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
    symbol = "b"
    name = "Builder"

class Farmer(Citizen):
    symbol = "f"
    name = "Farmer"

class Miner(Citizen):
    symbol = "m"
    name = "Miner"

class Stonecutter(Citizen):
    symbol = "s"
    name = "Stonecutter"

class Blacksmith(Citizen):
    symbol = "B"
    name = "Blacksmith"

class Weaponsmith(Citizen):
    symbol = "w"
    name = "Weaponsmith"

class Lumberjack(Citizen):
    symbol = "l"
    name = "Lumberjack"

class Carpenter(Citizen):
    symbol = "c"
    name = "Carpenter"

class Citizens(Mob):
    symbol = "o"
    name = "Citizens"
    priority = 29
    size = 1
    starting_citizens = 5

    needs_processing = True
    action_time = 1

    def __init__(self, loc, x, y, faction = None, target = None):
        super().__init__(loc, x, y)
        self.try_new = 3
        self.citizens = []
        self.inventory = []
        self.size = self.integrity
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
        if(self.resources["food"] > 100):
            self.resources["food"] = max(self.resources["food"] - 50, 0)
            self.add_citizen(Peasant)

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
                struc.crumble(self.size)

    def add_citizen(self, citizen_type):
        citizen = citizen_type(self, -2, -2) #Huehuehue. -2 -2 won't be qdeled.
        self.citizens.append(citizen)
        citizen.try_equip()

    def remove_citizen(self, citizen_):
        for citizen in self.citizens:
            if(citizen.loc == None):
                citizen.qdel()
                del citizen
        if(citizen_):
            citizen_.qdel()
            del citizen_
        elif(len(self.citizens) > 0):
            citizen_ = random.choice(self.citizens)
            citizen_.qdel()
            del citizen_
        if(len(self.citizens) == 0):
            self.qdel()
            del self
    
    def handle_ai_movement(self):
        self.resources["food"] = max(self.resources["food"] - (len(self.citizens) * self.action_time), 0)
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
            elif(isinstance(struc, Water)):
                quality = quality + 3 * struc.resource_multiplier
            elif(isinstance(struc, City)):
                if(self.resources["food"] >= 3 * len(self.citizens) * self.action_time):
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
            self.remove_citizen(None)
        return True

#GUI.
class Game_Window:
    wind_wid = 0
    wind_hei = 0
    wind = None
    cur_world = None

    def __init__(self, world):
        self.cur_world = world
        self.wind_wid = int((self.cur_world.max_x * 16.6) // 1)
        self.wind_hei = int((self.cur_world.max_y * 16.6) // 1)

        self.wind = tkinter.Tk()
        self.wind.title(u'The Game')
        self.wind.resizable(False, False)

        left = tkinter.Frame(self.wind, borderwidth=2, relief="solid")
        right = tkinter.Frame(self.wind, borderwidth=2, relief="solid")
        container = tkinter.Frame(left, borderwidth=2, relief="solid")
        box1 = tkinter.Frame(right, borderwidth=2, relief="solid")
        box2 = tkinter.Frame(right, borderwidth=2, relief="solid")

        map_field = tkinter.Canvas(container, width=self.wind_wid, height=self.wind_hei, bg='black')
        map_bg = map_field.create_text(int(self.wind_wid) // 2, int(self.wind_hei // 2), text=self.cur_world.world_to_string(), fill = 'green', font = 'TkFixedFont')
        chatlog = tkinter.Canvas(box1, width=int(self.wind_wid // 2), height=self.wind_hei, bg = 'dark blue')
        chat = chatlog.create_text(int(self.wind_wid // 4), int(self.wind_hei // 2), text=log, fill = 'white', font = 'TkFixedFont 12')

        command_field = tkinter.Entry(left, width=int(self.wind_wid // 8))
        command_field.focus_set()

        def action():
            return

        act_button = tkinter.Button(left, text="Act", width=int(self.wind_wid // 80), command=action)
        current_time = tkinter.Label(box2, text="Current Time: " + time_to_date(self.cur_world.time))

        left.pack(side="left", expand=True, fill="both")
        right.pack(side="right", expand=True, fill="both")
        container.pack(expand=True, fill="both", padx=5, pady=5)
        box1.pack(expand=True, fill="both", padx=10, pady=10)
        box2.pack(expand=True, fill="both", padx=10, pady=10)

        map_field.pack()
        chatlog.pack()
        command_field.pack()
        act_button.pack()
        current_time.pack()

        def cycle():
            current_time.config(text="Current Time: " + time_to_date(self.cur_world.time))
            map_field.itemconfigure(map_bg, text=self.cur_world.world_to_string())
            chatlog.itemconfigure(chat, text=log)
            self.wind.after(1, cycle)

        cycle()

        self.wind.mainloop()

prepare_lists()

The_Map = World(1) # World initiation on z = 1.

"""Tall_Grass(The_Map, 27, 24)
Tall_Grass(The_Map, 29, 25)
Tall_Grass(The_Map, 27, 24)
Tall_Grass(The_Map, 29, 25)
Tall_Grass(The_Map, 28, 26)
Tall_Grass(The_Map, 28, 26)
Forest(The_Map, 27, 24)
City(The_Map, 28, 25)
Mountain(The_Map, 29, 26)
Iron_Deposit(The_Map, 29, 26)
Gold_Deposit(The_Map, 29, 26)"""

threading.Thread(target=master_controller).start() # Controller start up.

GUI = Game_Window(The_Map) # Opening the gui window.
