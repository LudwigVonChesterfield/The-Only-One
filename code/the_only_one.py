import random
import tkinter
import math
import threading
import time
import sys
import copy
import datetime

# Defines go here.
#sys.stdout = open('log.txt', 'w') # Uncomment if you want to export to a log file.

log = ""
sqrt_2 = math.sqrt(2)

runtime = True
to_sleep_time = 10
freeze_time = False

city_output = True

atoms = []
atoms_by_name = {}

factions = []

worlds = []

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
        return "0" + str(num)
    elif(num > 9):
        return "00" + str(num)
    return "000" + str(num)


def number_to_month(num):
    if(num > 9):
        return str(num)
    return "0" + str(num)


def number_to_day(num):
    if(num > 9):
        return str(num)
    return "0" + str(num)


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
    return min([max([val, min_]), max_])


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def sign(val):
    return (val > 0) - (val < 0)


def x_y_to_coord(x, y):
    return "(" + str(x) + ", " + str(y) + ")"


def coord_to_list(coord):
    coord = coord[1:len(coord) - 1]
    y = coord.find(",") + 2
    return {"x": int(coord[0:y - 2]), "y": int(coord[y:len(coord)])}


def get_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def get_vector(x1, x2):
    return sign(x2 - x1)


def text_to_path(text):
    return atoms_by_name[text]


def sort_by_priority(atom_list: list):
    """
    Please, do consider that this function
    works with the list supplied. So do not
    send the list itself, only it's copy.

    TODO: Make it so you don't need to copy,
    and support direct work with the list.
    """
    if(not atom_list):  # Safety measures.
        return []  # Safety measures.
    atoms = []
    while(len(atom_list)):
        max_atom = None
        max_atom_priority = -1
        for atom in atom_list:
            if(atom.priority > max_atom_priority):
                max_atom_priority = atom.priority
                max_atom = atom
        atoms.append(max_atom)
        atom_list.remove(max_atom)
    return atoms


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


# World stuff goes here.
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
        worlds.append(self)

    def Clicked(self, GUI, x_, y_, mods=[]):
        """Mods are buttons held while clicking on
        these coords."""
        if(not self.coords_sanitized(x_, y_)):
            return
        mods.append("from_world")
        strucs = self.get_tile_contents(x_, y_)
        for struc in strucs:
            # If they override click, they issue their own code,
            # stop click handling from here.
            if(struc.overrideClick(GUI, x_, y_, mods)):
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
                overlays = sort_by_priority(copy.deepcopy(overlays))
                for overlay in overlays:
                    icons.append(overlay.get_icon())

            if(icons):
                for GUI in self.GUIs:
                    # We inverse the icons, so the highest priority is actually
                    # highest.
                    GUI.update_icon_for(x, y, icons[::-1])

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


# Datums.
class Faction:
    name = "" # I should really rename this to type, or use type instead.

    def __init__(self, creator):
        global factions
        self.display_name = random.choice(["Holy ", "Sacred ", "Eternal ", "Benevolent ", "Victorious ", "Glorious ", "Mighty "]) + random.choice(["Guild ", "Faction ", "Unity ", "Family ", "Dominion ", "Empire ", "Den "]) + random.choice(["of ", "for ", "with "]) + random.choice(["Citizens", "People", "Royalties", "Them", "Members", "Creations", "Knights", "Farmers", "Lands"])
        # Try to guess why there is no grey, green or black in the list below.
        self.color = random.choice(["red", "blue", "yellow", "magenta", "cyan", "white", "pale green", "royal blue", "orange", "coral", "maroon", "pink", "brown", "gray20"])
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

    def get_relationship(self, faction):
        if(not faction):
            return "Hostile"  # Who doesn't belong to our friends is a foe!
        if(self.relationships[faction] >= 100):
            return "Alliance"
        elif(self.relationships[faction] >= 50):
            return "Friendly"
        elif(self.relationships[faction] >= 0):
            return "Neutral"
        elif(self.relationships[faction] >= -50):
            return "Unfriendly"
        else:
            return "Hostile"

    def adjust_relationship(self, faction, value):
        if(not faction):
            return
        self.relationships[faction] += value

    def qdel(self):
        global factions

        self.qdeling = True
        for member in self.members:
            member.faction = None
        self.members = []
        for relationship in self.relationships:
            relationship.relationships.pop(self)
        self.relationships = {}
        factions.remove(self)
        del self

# Atoms.
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
        self.processing = False
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
        atoms.append(self)
        if(self.needs_processing):
            self.processing = True
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

    def overrideClick(self, GUI, x_, y_, mods=[]):
        if(self.canClickOn(GUI, x_, y_, mods)):
            return self.Clicked(GUI, x_, y_, mods)
        return False

    def canClickOn(self, GUI, x_, y_, mods=[]):
        # Change this in case of special behavior.
        return "from_world" not in mods

    def Clicked(self, GUI, x_, y_, mods=[]):
        # Default behavior of clicking on it, is examinating it.
        if("shift" in mods):
            return self.ShiftClickedOn(GUI, x_, y_)
        return self.ClickedOn(GUI, x_, y_)

    def ClickedOn(self, GUI, x_, y_):
        return False

    def ShiftClickedOn(self, GUI, x_, y_):
        self.Examinated(GUI)
        return True

    def Examinated(self, GUI):
        global log

        log += self.getExamineText() + "\n"

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

    def electrocute_act(self, severity, source):
        """
        What this atom should do upon being hit by an
        electricity source. If you return True, it means
        the atom conducts electricity.
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

        if(self.processing and (self in self.world.process_atoms)):
            self.world.process_atoms.remove(self)

        self_coord = x_y_to_coord(self.x, self.y)
        if(self.world and (self_coord in self.world.map_c) and (self in self.world.map_c[self_coord])):
            self.world.map_c[self_coord].remove(self)

        if(self.loc and self in self.loc.contents):
            self.loc.contents.remove(self)

        self.update_icon()
        self.loc = None
        self.world = None
        del self

    def update_icon(self):
        if(isinstance(self.loc, World)):
            self.loc.update_coord_icon(self.x, self.y)

    def get_icon(self):
        return {"symbol": self.icon_symbol, "color": self.icon_color, "font": self.icon_font}

    def is_overlayable(self):
        return self.overlayable

class Area(Atom):
    priority = 0
    obstruction = False

class Turf(Atom):
    overlayable = True
    priority = 1
    allowed_contents = []
    size = 20  # Turfs are really big.

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

    action_time = 1

    def __init__(self, loc, x, y):
        super().__init__(loc, x, y)
        self.charge = 0

    def process(self):
        self.icon_color = "yellow"
        self.update_icon()
        coords = self.world.get_region_coordinates(self.x, self.y, 1, 1)
        random.shuffle(coords)
        for coord in coords:
            # When it's our own tile, we electrocute everything on it,
            # else, only water.
            el_all_on_tile = False
            coord_list = coord_to_list(coord)
            x_ = coord_list["x"]
            y_ = coord_list["y"]
            if(self.x == x_ and self.y == y_):
                el_all_on_tile = True
            strucs = self.world.get_tile_contents(x_, y_)
            for struc in strucs:
                if(struc == self):
                    continue
                if(el_all_on_tile or isinstance(struc, Water)):
                    # Nothing passes the charge fully.le):
                    struc.electrocute_act(self.charge - 1, self)

        self.charge -= 1
        if(self.charge <= 0):
            self.icon_color = "blue"
            self.update_icon()
            self.processing = False
            self.world.process_atoms.remove(self)


    def electrocute_act(self, severity, source):
        to_shock = severity - self.charge
        if(to_shock > 0):
            self.charge += to_shock
            self.processing = True
            self.world.process_atoms.append(self)
        return True


# Objects.
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
        self.integrity = int(integrity)

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
    icon_color = "yellow"
    name = "Lightning"
    default_description = "It is before the Thunder."
    size = 1
    priority = 100  # Pretty "light".

    def __init__(self, loc, x, y, power=3):
        super().__init__(loc, x, y)
        power = int(power)
        strucs = self.world.get_tile_contents(self.x, self.y)
        for struc in strucs:
            struc.electrocute_act(power, self)
        self.qdel()
        del self


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
        self.resource_multiplier = random.uniform(0.7, 1.3) * self.default_resource_multiplier
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
    default_description = "A grass to eat when hungry."
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

    def electrocute_act(self, severity, source):
        Fire(self.loc, self.x, self.y, severity)
        return False  # It does not actually conduct electricity.


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

    def electrocute_act(self, severity, source):
        Fire(self.loc, self.x, self.y, severity)
        return False  # It does not actually conduct electricity.


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



class Tool(Object):
    name = ""
    job = ""

    def __init__(self, loc, x, y, materials={"wood" : 5}, quality_modifier=1):
        self.x = x
        self.y = y
        self.loc = loc
        self.materials = materials
        self.quality = random.uniform(1.5, 2.5) * quality_modifier

    def qdel(self):
        self.qdeling = True
        if(self in self.loc.inventory):
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
        global log

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

        log += self.display_name + " has been settled in " + x_y_to_coord(self.x, self.y) + " at " + time_to_date(self.world.time) + "\n"

    def getExamineText(self):
        text = super().getExamineText()
        text += "It is a city of " + self.faction.display_name + " and it has " + str(len(self.citizens)) + " citizens in it!"
        return text

    def qdel(self):
        global log

        self.qdeling = True
        log += self.display_name + " has been destroyed in " + x_y_to_coord(self.x, self.y) + " at " + time_to_date(self.world.time) + "\n"
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
        food_required = 0
        for cit in self.citizens:
            food_required += cit.hunger_rate

        actual_food_required = food_required

        strucs = self.world.get_region_contents(self.x, self.y, 2, 2)
        random.shuffle(strucs)

        dummy = None
        for citizen in self.citizens:
            if(not citizen.qdeling):
                dummy = citizen
                break

        self.job_requests = dummy.required_citizens(strucs)
        self.structure_requests = dummy.required_strucs(strucs, food_required)

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

            elif(isinstance(struc, Resource)):
                if(struc.resource):
                    if(self.resources[struc.resource] >= 50 * len(self.citizens)):  # We have enough of this...
                        continue

                    if(isinstance(struc, Tall_Grass)):
                        if(food_required > 0):
                            food_required -= struc.resource_multiplier * struc.default_resource_multiplier

                    elif(isinstance(struc, Farm)):
                        if(food_required > 0):
                            food_required -= struc.resource_multiplier * struc.default_resource_multiplier * 2

                if(isinstance(struc, Structure)):
                    if(self.faction != struc.faction and struc.faction):  # If it's Neutral, nobody cares.
                        relation_to_us = struc.faction.get_relationship(self.faction)
                        if(relation_to_us == "Friendly" or relation_to_us == "Alliance"):
                            struc.faction.adjust_relationship(self.faction, -1)
                        else:
                            struc.faction.adjust_relationship(self.faction, -2)

                        relation_to_them = self.faction.get_relationship(struc.faction)
                        if(relation_to_them == "Friendly" or relation_to_us == "Alliance"):
                            self.faction.adjust_relationship(struc.faction, 1)  # Hey! They let us use their thing. Yay!
                        else:
                            self.faction.adjust_relationship(struc.faction, -1)  # We hate them for them being on our lands.
                    elif(isinstance(struc, House)):  # Can only sleep in YOUR houses.
                        houses_count += 1

            self.tasks.append(task)

        self.max_population = 10 + houses_count * 2

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
        global city_output
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
                    if(citizen.actions_to_perform <= 0 and prob(int(round((citizen.age / 8760) * abs(citizen.actions_to_perform))))):  # The older the person, the less he'd want to overwork.
                        continue
                    if(citizen.actions_to_perform <= -citizen.max_actions_to_perform):  # See: citizens overworking themselves to death.
                        continue
                    if(citizen.perform_task(strucs, task)):
                        if(city_output):
                            print(citizen.display_name + " performed " + str(task) + " and has: " + str(citizen.actions_to_perform) + " actions left.")
                        if(isinstance(task["target"], Resource) and task["target"].resource == "food" and task["task"] == "harvest"):
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

        if(len(self.citizens) < 100):
            self.icon_symbol = str(int(len(self.citizens) // 10))
        elif(len(self.citizens) < 1000):
             self.icon_symbol = "L"
        elif(len(self.citizens) < 10000):
             self.icon_symbol = "M"

        if(len(self.citizens) > self.max_population): # Overpopulation - DEATH!
            self.remove_citizen(None)

        self.size = 5 + int(len(self.citizens) // 10)
        if(self.world):
            if(self.world.is_overcrowded(self.x, self.y, 0)):
                for struc in self.world.get_tile_contents(self.x, self.y):
                    if(struc == self):
                        continue
                    if(struc.crumble(self.size)):
                        continue
        self.update_icon()

        if(city_output and not self.qdeling):
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
        citizen.try_equip()

    def remove_citizen(self, citizen_):
        if(citizen_):
            citizen_.qdel()
            del citizen_
        elif(len(self.citizens) > 0):
            citizen_ = random.choice(self.citizens)
            citizen_.qdel()
            del citizen_
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
        pos_cits = []
        for citizen in self.citizens:
            if(isinstance(citizen, Toddler)):
                continue
            if(citizen.actions_to_perform <= -citizen.max_actions_to_perform):
                continue
            pos_cits.append(citizen)
        for citizen in pos_cits:
            if(citizen.name == task["job"]):
                list_.append(citizen)
                pos_cits.remove(citizen)
        # It actually allows not just peasants, but everybody.
        if(task["allowed_peasants"]):
            for citizen in pos_cits:
                if(citizen.name == "Peasant"):
                    list_.append(citizen)
                    pos_cits.remove(citizen)
            for citizen in pos_cits:
                list_.append(citizen)
        return list_

    def get_icon(self):
        return {"symbol": self.icon_symbol, "color": self.faction.color if self.faction else self.icon_color, "font": self.icon_font}

    def get_task(self, city):
        if(city.faction != self.faction):
            relation = self.faction.get_relationship(city.faction)
            if(relation == "Unfriendly" or relation == "Neutral" or relation == "Friendly"):
                return {"priority" : 2, "job" : "Peasant", "task" : "gift", "res_required" : {random.choice(["food", "wood", "stone"]) : random.randint(10, 20)}, "target" : self, "allowed_peasants" : True}
            if(relation == "Hostile"):
                return {"priority" : 2, "job" : "Peasant", "task" : "kidnap", "target" : self, "allowed_peasants" : True}
        return super().get_task(city)

    def fire_act(self, severity):
        return_val = False
        for cit in range(severity):
            if(not len(self.citizens)):
                return False
            citizen = random.choice(self.citizens)
            if(not citizen.qdeling):
                citizen.fire_act(severity)
                return_val = True
        return return_val

    def electrocute_act(self, severity, source):
        Fire(self.loc, self.x, self.y)
        return False  # It does not actually conduct electricity.


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
                return {"priority" : 2, "job" : "Peasant", "task" : "claim", "target" : self, "allowed_peasants" : True}
        return super().get_task(city)

    def qdel(self):
        if(self.faction):
            self.faction.members.remove(self)
        self.faction = None
        super().qdel()

class Construction(Structure):
    icon_symbol = "c"
    name = "Construction"
    default_description = "When Construction will grow up, it will become a big Structure!."

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
                return {"priority" : 2, "job" : "Peasant", "task" : "claim", "target" : self, "allowed_peasants" : True}
        return {"priority" : 2, "job" : "Builder", "task" : "construct", "target" : self, "allowed_peasants" : False}

    def qdel(self):
        self.qdeling = True
        self.struc_type = None
        super().qdel()


class House(Structure):
    icon_symbol = "h"
    name = "House"
    default_description = "A place for Citizens to call home."
    work_required = 15

    def get_task(self, city):
        if(city.faction != self.faction):
            relation = city.faction.get_relationship(self.faction)
            if(relation == "Hostile"):
                return {"priority": 2, "job": "Peasant", "task": "claim", "target": self, "allowed_peasants": True}
        return {"priority": 1, "job": "Peasant", "task": "rest", "target": self, "allowed_peasants": True}

    def fire_act(self, severity):
        self.crumble(severity)
        return True

    def electrocute_act(self, severity, source):
        Fire(self.loc, self.x, self.y)
        return False  # It does not actually conduct electricity.


class Farm(Structure):
    icon_symbol = "w"
    name = "Farm"
    default_description = "A place to get food from."
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

    def electrocute_act(self, severity, source):
        Fire(self.loc, self.x, self.y)
        return False  # It does not actually conduct electricity.


class Mine(Structure):
    icon_symbol = "m"
    name = "Mine"
    default_description = "Diggy-diggy hole..."
    work_required = 20

    harvestable = True
    allow_peasants = False
    resource = "stone"
    job_to_harvest = "Miner"
    harv_priority = 5

    default_resource_multiplier = 1.3
    def_amount = 100


# Mobs.
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
        self.hunger_rate = random.uniform(0.7, 1.3)
        self.malnutrition = 0

        self.qdeling = False
        self.quality_modifier = random.uniform(0.7, 1.3)
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
        # self.world = None  # They don't have world var as of yet.
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
        target.construct(int(round(self.quality_modifier * self.loc.action_time)))
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
            target.faction.adjust_relationship(self.loc.faction, resources_required[res])
        self.actions_to_perform -= 1
        return True

    def claim(self, target):
        if(not target.faction):
            target.faction = self.loc.faction
            self.loc.faction.add_to_faction(target)
            target.update_icon()
        elif(not target.crumble(1)):  # By "capturing" it, we of course mean murdering it slightly.
            target.faction.adjust_relationship(self.faction, -30)  # I mean claiming other's territory is quite a threat.
            target.faction.members.remove(target)
            target.faction = None
            target.update_icon()
        self.actions_to_perform -= 1
        return True

    def break_tool(self, target):
        for material in target.materials:
            self.loc.resources[material] += target.materials[material]
        target.qdel()
        del target
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

    def required_strucs(self, strucs, food_required):
        requests = {"House" : 0,
                    "Farm" : 0,
                    "Mine" : 0}
        for struc in strucs:
            if(isinstance(struc, Farm)):
                requests["Farm"] = requests["Farm"] - 1
            if(isinstance(struc, Mine)):
                requests["Mine"] = requests["Mine"] - 1
            if(isinstance(struc, Rocky)):
                requests["Mine"] = requests["Mine"] + 1
        requests["Farm"] = requests["Farm"] + int(round(food_required / 3))
        requests["House"] = requests["House"] + int((self.loc.max_population - len(self.loc.citizens)) < 1)
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
                #if(self.accomplish_job_request(job.name)):  # Uncomment if do something better.
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
    max_actions_to_perform = 1

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

    def try_equip(self):
        if(prob(int(round((self.age / 8760) * abs(self.actions_to_perform))))):  # Too tired for breaking tools.
            return
        if(self.actions_to_perform <= -self.max_actions_to_perform):  # Absolutely tired.
            return
        for tool in self.loc.inventory:
            if(not isinstance(tool, Tool)):
                continue
            if(tool.quality > self.get_tool_quality(self.name)):
                if(self.tool):
                    self.loc.inventory.append(self.tool)
                if(prob(10)):  # Woopsy-daisy!
                    self.break_tool(tool)
                    return
                self.tool = tool
                self.loc.inventory.remove(self.tool)
                self.actions_to_perform -= 1

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
    default_description = "A bunch of people walking around and about."
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

        if(self.world):
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

    def remove_citizen(self, citizen_):
        if(citizen_):
            if(citizen_.tool):
                self.loc.inventory.tools.append(citizen_.tool)
                citizen_.tool = None
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
        self.resources["food"] = max([self.resources["food"] - (len(self.citizens) * self.action_time), 0])
        if(self.target):
            self.move_towards_to(self.world, target.x, target.y)
            return
        spot_x = self.x
        spot_y = self.y
        best_index = 0
        coords = self.world.get_region_coordinates(self.x, self.y, 3, 3)
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


#GUI.
class GUI:
    """A GUI class with all functions being abstract. Needed to contain variables, 
    and help Game_Window with processing these."""
    def __init__(self, parent, tag, x, y):
        self.parent = parent
        self.saved_x = x
        self.saved_y = y
        self.wind_wid = 0
        self.wind_hei = 0
        self.tag = tag

        self.qdeling = False
        self.inter_cycle = False

        self.wind = tkinter.Toplevel(parent.wind)
        self.wind.resizable(False, False)
        self.wind.geometry("+%d+%d" % (parent.wind.winfo_x() + self.saved_x, parent.wind.winfo_y() + self.saved_y))
        self.wind.attributes("-topmost", True)
        self.wind.protocol("WM_DELETE_WINDOW", self.on_close)

    def qdel(self):
        self.qdeling = True
        self.parent.child_windows.pop(self.tag)
        self.parent = None
        self.wind.destroy()
        del self

    def on_cycle(self):
        return

    def on_reopen(self, tag, x, y):
        return

    def on_close(self):
        self.qdel()


class Examine(GUI):

    def __init__(self, parent, tag, x, y):
        super().__init__(parent, tag, x, y)
        self.x_coord = int(round(x / self.parent.pixels_per_tile))
        self.y_coord = int(round(y / self.parent.pixels_per_tile))

        self.structures = sort_by_priority(copy.deepcopy(self.parent.cur_world.get_tile_contents(self.x_coord, self.y_coord)))

        self.wind.title(u'The Tile (%d, %d)' % (self.x_coord, self.y_coord))
        self.wind_wid = max([int(round(4 * self.parent.pixels_per_tile)), self.parent.max_coord_lenght])
        self.wind_hei = int(round(len(self.structures) * 5 * self.parent.pixels_per_tile))

        self.content = tkinter.Frame(self.wind, width=self.wind_hei, height=self.wind_hei, borderwidth=2, relief="solid")
        self.content.grid_propagate(0)

        self.coord_text = tkinter.Text(self.content, width=int(round(self.wind_wid / self.parent.pixels_per_tile)), height=1, fg="white", bg="dark blue", font='TkFixedFont')
        self.coord_text.insert(tkinter.END, x_y_to_coord(self.x_coord, self.y_coord))

        self.temp_map_field = tkinter.Canvas(self.content, width=self.wind_wid, height=self.wind_hei, bg='black')
        self.temp_map_field.bind("<ButtonPress-1>", self.on_click)
        self.temp_map_field.bind("<Shift-ButtonPress-1>", self.on_shift_click)
        self.structure_icons = []

        #self.coordinates = self.temp_map_field.create_text(int(round(self.wind_wid / 2)), self.wind_wid - self.parent.pixels_per_tile, text="Coords: (%s, %s)" % (self.x_coord, self.y_coord), font='TkiFixedFont', fill="green")

        self.content.pack(expand=False, padx=10, pady=10)

        self.coord_text.pack()
        self.temp_map_field.pack()

    def qdel(self):
        self.qdeling = True
        self.inter_cycle = True
        self.structures = None
        super().qdel()

    def on_click(self, event):
        """Try-hard hack to make these objects clickable."""
        # I do know of operator precedence. I do know that I subtract 1 and not pixels_per_tile...
        # But can you blame me if it works?
        y_ = int(round(event.y / self.parent.pixels_per_tile - 1))
        if(y_ >= 0 and y_ < len(self.structures)):
            atom = self.structures[y_]
            atom.Clicked(self.parent, atom.x, atom.y, mods=["shift"])  # Cheap hack to get at least some x and y to be passed.

    def on_shift_click(self, event):
        """Try-hard hack to make these objects clickable."""
        # I do know of operator precedence. I do know that I subtract 1 and not pixels_per_tile...
        # But can you blame me if it works?
        y_ = int(round(event.y / self.parent.pixels_per_tile - 1))
        if(y_ >= 0 and y_ < len(self.structures)):
            atom = self.structures[y_]
            atom.Clicked(self.parent, atom.x, atom.y, mods=["shift"])  # Cheap hack to get at least some x and y to be passed.

    def on_cycle(self):
        if(self.inter_cycle):
            return

        self.structures = sort_by_priority(copy.deepcopy(self.parent.cur_world.get_tile_contents(self.x_coord, self.y_coord)))

        self.wind_hei = int(round(len(self.structures) * 5 * self.parent.pixels_per_tile))
        self.content.configure(height=self.wind_hei)
        self.temp_map_field.configure(height=self.wind_hei)

        self.coord_text.delete('1.0', tkinter.END)
        self.coord_text.insert(tkinter.END, x_y_to_coord(self.x_coord, self.y_coord))

        for struc in self.structure_icons:
            if(self.inter_cycle):
                return
            self.temp_map_field.delete(struc)

        y = 0

        for structure in self.structures:
            if(self.inter_cycle):
                return
            icon = structure.get_icon()
            self.structure_icons.append(self.temp_map_field.create_text(int(round(self.wind_wid / 2)), int(round(y * self.parent.pixels_per_tile) + self.parent.pixels_per_tile), text="%s [%s]" % (icon["symbol"], structure.size), font=icon["font"], fill=icon["color"]))
            y += 1

    def on_reopen(self, tag, x, y):
        self.inter_cycle = True
        self.x_coord = int(round(x / self.parent.pixels_per_tile))
        self.y_coord = int(round(y / self.parent.pixels_per_tile))

        self.saved_x = x
        self.saved_y = y
        self.wind.geometry("+%d+%d" % (self.parent.wind.winfo_x() + self.saved_x, self.parent.wind.winfo_y() + self.saved_y))
        #self.temp_map_field.itemconfigure(self.coordinates, text="Coords: (%s, %s)" % (self.x_coord, self.y_coord))
        self.inter_cycle = False

class Game_Window:
    default_pixels_per_tile = 16.4
    cur_world = None

    def __init__(self, world):
        self.icon_updating = False  # True if icons are currently updating.
        self.icon_update = False
        self.qdeling = False
        self.wind = None
        self.child_windows = {}

        self.pixels_per_tile = self.default_pixels_per_tile

        self.cur_world = world
        self.cur_world.GUIs.append(self)
        self.wind_wid = int(round(self.cur_world.max_x * self.pixels_per_tile))
        self.wind_hei = int(round(self.cur_world.max_y * self.pixels_per_tile))

        self.wind = tkinter.Tk()
        self.wind.title(u'The Game')
        self.wind.resizable(False, False)
        self.wind.bind("<Configure>", self.move_me)
        self.wind.protocol("WM_DELETE_WINDOW", self.on_close)

        self.left = tkinter.Frame(self.wind, borderwidth=2, relief="solid")
        self.right = tkinter.Frame(self.wind, borderwidth=2, relief="solid")
        self.container = tkinter.Frame(self.left, borderwidth=2, relief="solid")
        self.box1 = tkinter.Frame(self.right, borderwidth=2, relief="solid")
        self.box2 = tkinter.Frame(self.right, borderwidth=2, relief="solid")

        def on_click(event):
            x_ = int(round(event.x / self.pixels_per_tile - 1))
            y_ = int(round(event.y / self.pixels_per_tile - 1))
            # TODO: Andrew I hope you know what is wrong v---- there.
            self.cur_world.Clicked(self, x_, y_, mods=["shift"])

        def on_shift_click(event):
            x_ = int(round(event.x / self.pixels_per_tile - 1))
            y_ = int(round(event.y / self.pixels_per_tile - 1))
            self.cur_world.Clicked(self, x_, y_, mods=["shift"])

        self.map_field = tkinter.Canvas(self.container, width=self.wind_wid + self.pixels_per_tile, height=self.wind_hei  + self.pixels_per_tile, bg='black')
        self.map_field.bind("<ButtonPress-1>", on_click)
        self.map_field.bind("<Shift-ButtonPress-1>", on_shift_click)
        self.map_field_overlays = {}

        #self.chatscrollbar = tkinter.Scrollbar(self.box1, orient=tkinter.VERTICAL)
        self.chatlog = tkinter.Canvas(self.box1, width=int(round(self.wind_wid / 2)), height=self.wind_hei, bg='dark blue')
        self.chat = self.chatlog.create_text(int(round(self.wind_wid / 4)), int(round(self.wind_hei / 2)), width = int(round(self.wind_wid / 2)), text=log, fill = 'white', font = 'TkFixedFont 12')
        # Since it uses TkFixedFont 12, we divide by 12. Almost makes sense.
        self.max_coord_lenght = int(round(((len(str(max([self.cur_world.max_x, self.cur_world.max_y]))) * 2) + 4) * self.pixels_per_tile))
        # self.chatlog.config(scrollregion=self.chatlog.bbox(tkinter.ALL), bd=0, yscrollcommand=self.chatscrollbar.set)
        # self.chatscrollbar.config(command=self.chatlog.yview)

        self.command_field = tkinter.Entry(self.left, width=int(round(self.wind_wid / 8)))
        self.command_field.focus_set()

        def action():
            global to_sleep_time
            global freeze_time
            global factions
            global city_output

            command = self.command_field.get()
            args = command.split()

            if(args[0] == "Spawn" and len(args) >= 4):
                if(args[1] in atoms_by_name and self.cur_world.coords_sanitized(int(args[2]), int(args[3]))):
                    if(len(args) > 4):
                        additional_args = []
                        for arg in args[4:len(args)]:
                            additional_args.append(arg)
                        text_to_path(args[1])(self.cur_world, int(args[2]), int(args[3]), *additional_args)
                    else:
                        text_to_path(args[1])(self.cur_world, int(args[2]), int(args[3]))

            elif(args[0] == "Show" and len(args) == 3):
                self.cur_world.show_turf(self, int(args[1]), int(args[2]))

            elif(args[0] == "Stop"):
                freeze_time = True

            elif(args[0] == "Faster"):
                if(not self.cur_world.processing):
                    freeze_time = False
                    to_sleep_time = 1000
                    return

                to_sleep_time = max([0, to_sleep_time - 100])

            elif(args[0] == "Slower"):
                if(to_sleep_time == 1000):
                    freeze_time = True
                    return

                to_sleep_time = min([1000, to_sleep_time + 100])

            elif(args[0] == "Output"):
                city_output = not city_output

            elif(args[0] == "Politics"):
                print("\n")
                for faction in factions:
                    print("~@---@~")
                    print("Faction " + faction.display_name + " relationships:")
                    for relationship in faction.relationships:
                        print("[" + faction.get_relationship(relationship) + "(" + str(faction.relationships[relationship]) + ")] with " + relationship.display_name)
                print("\n")

        self.act_button = tkinter.Button(self.left, text="Act", width=int(self.wind_wid // 80), command=action)
        self.current_time = tkinter.Label(self.box2, text="Current Time: " + time_to_date(self.cur_world.time))

        self.left.pack(side="left", fill="both")
        self.right.pack(side="right", fill="both")
        self.container.pack(expand=True, padx=5, pady=5)
        self.box1.pack(expand=True, padx=10, pady=10)
        self.box2.pack(expand=True, padx=10, pady=10)

        #self.chatscrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.map_field.pack()
        self.chatlog.pack()
        self.command_field.pack()
        self.act_button.pack()
        self.current_time.pack()

        def cycle():
            if(self.qdeling):
                if(not self.icon_updating):
                    self.cur_world.GUIs.remove(self)
                    self.wind.destroy()
            else:
                self.current_time.config(text="Current Time: " + time_to_date(self.cur_world.time))
                self.chatlog.itemconfigure(self.chat, text=log)

                for window_tag in self.child_windows:
                    if(self.child_windows[window_tag].inter_cycle):
                        continue
                    self.child_windows[window_tag].on_cycle()

            self.wind.after(1, cycle)

        def update_all_icons():
            self.icon_update = True
            self.cur_world.update_world_icons()

        threading.Thread(target=update_all_icons).start()

        cycle()

        self.wind.mainloop()

    def on_close(self):
        self.icon_update = False
        self.qdeling = True

    def open_window(self, win_type, tag, x, y):
        if((tag not in self.child_windows) or (not self.child_windows[tag])):
            self.child_windows[tag] = win_type(self, tag, x, y)
        else:
            self.child_windows[tag].on_reopen(tag, x, y)

    def close_window(self, tag):
        self.child_windows[tag].on_close()

    def move_me(self, event):
        """GUI func called, when the window moves."""
        for window_tag in self.child_windows:
            if(not self.child_windows[window_tag]):
                continue
            window = self.child_windows[window_tag]
            window.wind.geometry("+%d+%d" % (self.wind.winfo_x() + window.saved_x, self.wind.winfo_y() + window.saved_y))


    def update_icon_for(self, x, y, icons):
        if(not self.icon_update):
            return

        self.icon_updating = True
        coord = x_y_to_coord(x, y)

        if(not coord in self.map_field_overlays):
            self.map_field_overlays[coord] = []

        for icon in self.map_field_overlays[coord]:
            self.map_field.delete(icon)

        for icon in icons:
            self.map_field_overlays[coord].append(self.map_field.create_text(int(round(x * self.pixels_per_tile) + self.pixels_per_tile), int(round(y * self.pixels_per_tile) + self.pixels_per_tile), text=icon["symbol"], font=icon["font"], fill=icon["color"]))
        self.icon_updating = False

prepare_lists()

The_Map = World(1)  # World initiation on z = 1.

Tall_Grass(The_Map, 27, 24)
Tall_Grass(The_Map, 29, 25)
Tall_Grass(The_Map, 27, 24)
Tall_Grass(The_Map, 29, 25)
Tall_Grass(The_Map, 28, 26)
Tall_Grass(The_Map, 28, 26)
Forest(The_Map, 27, 24)
Forest(The_Map, 25, 24)
City(The_Map, 28, 25)
Mountain(The_Map, 29, 26)
Mountain(The_Map, 30, 26)
Iron_Deposit(The_Map, 29, 26)
Gold_Deposit(The_Map, 29, 26)

threading.Thread(target=master_controller).start()  # Controller start up.

GUI = Game_Window(The_Map)  # Opening the gui window.
