import random
import tkinter
import math
import threading
import time
import sys
import copy

# Defines go here.
# sys.stdout = open('log.txt', 'w') # Uncomment if you want to export to a log file.

log = ""
sqrt_2 = math.sqrt(2)
5
runtime = True
to_sleep_time = 0
freeze_time = False

city_output = False

atoms_by_name = {}

tools_by_job = {}

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


def get_vector(x1, x2):
    return sign(x2 - x1)


def text_to_path(text):
    return atoms_by_name[text]


def job_to_tool(job):
    if(job not in tools_by_job):
        return None
    return tools_by_job[job]


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
    tool_classes = get_all_subclasses(Tool)
    for tool in tool_classes:
        tools_by_job[tool.job] = tool


def master_controller():
    while(runtime):
        if(freeze_time):
            continue
        time.sleep(to_sleep_time / 1000)
        for world in worlds:
            if(world.initiated):
                if(world.processing):
                    continue
                world.processing = True

                for atom in world.process_atoms:
                    if(atom.last_action + atom.action_time < world.time):
                        atom.last_action = world.time + atom.action_time
                        atom.process()

                world.time += 1

                if(prob(1)):
                    if(prob(1)):
                        City(world.get_turf(random.randrange(0, world.max_x - 1), random.randrange(0, world.max_y - 1)))
                world.processing = False


# World stuff goes here.
class World:
    name = ""
    map_c = {}
    contents = []
    max_x = 50
    max_y = 34
    z = -1
    base_turf = "Plains"  # Default Turf.
    base_area = "Area"
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
        strucs = self.get_all_tile_contents(x_, y_)
        for struc in strucs:
            # If they override click, they issue their own code,
            # stop click handling from here.
            if(struc.overrideClick(GUI, x_, y_, mods)):
                return

        if("shift" in mods):
            self.show_turf(GUI, x_, y_)

    def show_turf(self, GUI, x_, y_):
        threading.Thread(target=GUI.open_window, args=[Examine, "examine", x_ * GUI.pixels_per_tile, y_ * GUI.pixels_per_tile]).start()

    def get_world(self):
        return self

    def coords_sanitized(self, x, y):
        return x >= 0 and y >= 0 and x < self.max_x and y < self.max_y

    def is_overcrowded(self, x, y, additional_size):
        """Additional_size argument is used by Citizens
        to determine if they can build something."""
        tile = self.get_turf(x, y)
        if(not tile):
            return False
        if(tile.current_load + additional_size > tile.size):
            return True
        return False

    def get_turf(self, x, y):
        """
        Returns the Turf at given coordinates, or
        None if such coordinates are not applicable.
        """
        if(self.coords_sanitized(x, y)):
            return self.map_c[x_y_to_coord(x, y)]["Turf"]
        return None

    def get_area(self, x, y):
        """
        Returns the Area at given coordinates, or
        None if such coordinates are not applicable.
        """
        if(self.coords_sanitized(x, y)):
            return self.map_c[x_y_to_coord(x, y)]["Area"]
        return None

    def get_tile_contents(self, x, y):
        """
        Returns contents of a Turf at given
        coordinates, or None if such turf
        doesn't exist.
        """
        turf = self.get_turf(x, y)
        if(turf):
            return turf.contents
        return None

    def get_all_tile_contents(self, x, y):
        """
        Returns Turf and Turf's contents.
        """
        turf = self.get_turf(x, y)
        return [turf] + turf.contents

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
                turf = self.map_c[x_y_to_coord(x_, y_)]["Turf"]
                contents += [turf] + turf.contents
        return contents

    def generate_world(self):
        for y in range(self.max_y):
            for x in range(self.max_x):
                # self.map_c[x_y_to_coord(x, y)] = {"Turf": text_to_path(self.base_turf)({"x": x, "y": y, "world": self}), "Area": text_to_path(self.base_area)({"x": x, "y": y, "world": self})}
                self.map_c[x_y_to_coord(x, y)] = {"Turf": text_to_path(self.base_turf)({"x": x, "y": y, "world": self})}
                self.generate_tile(text_to_path(pick_weighted(self.allowed_turfs)), x, y)

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

    def generate_tile(self, tile_type, x, y):
        new_turf = tile_type(self.get_turf(x, y))

        for content in new_turf.contents:
            content.qdel()
            del content

        if(len(new_turf.allowed_contents) == 0):
            return

        for N in range(self.struc_per_tile):
            if(prob(self.struc_chance_per_tile)):
                new_turf.generate_contents()(new_turf)

    def update_coord_icon(self, x, y):
        if(not self.initiated):
            return

        turf = self.get_turf(x, y)

        overlays = [turf]  # Turf is always visible.
        icons = []

        max_priority = turf.priority
        max_atom = turf

        for atom in turf.contents:
            if(atom.priority > max_priority):
                max_priority = atom.priority
                max_atom = atom
            if(atom.overlayable):
                overlays.append(atom)

        if(max_atom and max_atom not in overlays):
            overlays.append(max_atom)

        if(overlays):
            if(max_atom.block_overlays):
                icons.append(max_atom.icon)
            else:
                overlays = sort_by_priority(copy.deepcopy(overlays))
                for overlay in overlays:
                    icons.append(overlay.icon)

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
                        self.generate_tile(tile_type, x_, y_)
                    else:
                        tile = self.get_turf(x_, y_)
                        if(tile_type.name not in tile.allowed_contents):
                            continue
                        tile_type(self.get_turf(x_, y_))


# Datums.
class Faction:
    name = "" # I should really rename this to type, or use type instead.

    def __init__(self, creator):
        global factions
        self.qdeling = False
        self.display_name = random.choice(["Holy ", "Sacred ", "Eternal ", "Benevolent ", "Victorious ", "Glorious ", "Mighty "]) + random.choice(["Guild ", "Faction ", "Unity ", "Family ", "Dominion ", "Empire ", "Den "]) + random.choice(["of ", "for ", "with "]) + random.choice(["Citizens", "People", "Royalties", "Them", "Members", "Creations", "Knights", "Farmers", "Lands"])
        # Try to guess why there is no grey, green or black in the list below.
        self.color = random.choice(["red", "blue", "yellow", "magenta", "cyan", "white", "pale green", "royal blue", "orange", "coral", "maroon", "pink", "brown", "gray20"])
        self.members = [creator]
        self.relationships = {}

        for faction in factions:
            if(faction.qdeling):
                continue
            faction.relationships[self] = 0
            self.relationships[faction] = 0

        factions.append(self)  # So we don't set relationships to ourselves.

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
        if(value > 0 and self.color == faction.color):
            value *= 1.5
        self.relationships[faction] += value

    def qdel(self):
        if(not self.qdeling):
            self.qdeling = True
            self.Destroy()
        del self

    def Destroy(self):
        global factions
        
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
    icon = None  # A dict with lower qualities, or something else. Is set in set_icon(), updated in world using update_icon().
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

    def __init__(self, loc):
        self.processing = False
        self.qdeling = False

        self.x = -1
        self.y = -1
        self.loc = None
        self.world = None

        self.contents = []
        self.integrity = self.size
        self.set_icon()
        self.move_atom_to(loc)

        # Since "name" is more of a type, really.
        self.display_name = self.name
        self.description = self.default_description

        self.last_action = self.world.time
        if(self.needs_processing):
            self.processing = True
            self.world.process_atoms.append(self)

    def qdel(self):
        if(not self.qdeling):
            self.qdeling = True
            self.Destroy()
        del self

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
        if(isinstance(self.loc, World)):
            return self.loc
        else:
            return self.loc.get_world()

    def bump(self, bumped_with):
        # Bumped with is the thing that called the bump proc.
        return

    def bump_into(self, bumped_into):
        return

    def get_distance(self, to_dist):
        """
        Returns geometric distance from self to to_dist,
        if self in contents of to_dist returns -1.
        """
        if(self in to_dist.contents):
            return -1
        return abs(to_dist.x - self.x) + abs(to_dist.y - self.y)

    def move_atom_to(self, loc):
        if(loc.qdeling):
            return

        if(self.loc):
            self.loc.contents.remove(self)
            if(isinstance(self.loc, Turf)):
                self.loc.current_load -= self.size
            self.update_icon()

        if(isinstance(loc, Turf)):
            loc.current_load += self.size

            if(loc.current_load > loc.size):
                for struc in loc.contents:
                    struc.crumble(self.size)

        if(self.world != loc.world):
            self.world = loc.world

        self.loc = loc
        self.x = loc.x
        self.y = loc.y

        self.loc.contents.append(self)  # So we don't need to bump into ourselves in Turfs.

        self.update_icon()

    def move_towards_to(self, loc, dummy_moves=3):
        """
        Atom moving towards loc. If atom is in same
        turf as loc, it is moved into loc.
        """

        move_to_this = loc
        if(self.get_distance(loc) > 0):
            x_ = self.x + (((loc.x - self.x) > 0) - ((loc.x - self.x) < 0))
            y_ = self.y + (((loc.y - self.y) > 0) - ((loc.y - self.y) < 0))
            move_to_this = self.world.get_turf(x_, y_)

        while(dummy_moves):
            for struc in move_to_this.contents + [move_to_this]:
                if(struc.obstruction):
                    if(not self.world):
                        return False
                    break
            else:
                self.move_atom_to(move_to_this)
                return True
            x_t = self.x + random.randrange(-1, 1)
            y_t = self.y + random.randrange(-1, 1)
            move_to_this = self.world.get_turf(x_t, y_t)
            dummy_moves -= 1
        return False

    def process(self):
        return

    def crumble(self, severity):
        self.integrity -= severity
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

    def Destroy(self):
        if(self.processing):
            self.world.process_atoms.remove(self)

        self.loc.contents.remove(self)

        for content in self.contents:
            content.move_atom_to(self.world.get_turf(self.x, self.y))

        self.update_icon()

        self.loc = None
        self.world = None
        del self

    def update_icon(self):
        self.set_icon()
        self.world.update_coord_icon(self.x, self.y)

    def set_icon(self):
        self.icon = {"symbol": self.icon_symbol, "color": self.icon_color, "font": self.icon_font}


class Area(Atom):
    priority = 0
    obstruction = False

    def move_atom_to(self, loc):
        if(isinstance(loc, dict)):  # Cheap hacks.
            self.loc = loc["world"]
            self.loc.contents.append(self)
            self.world = self.loc
            self.x = loc["x"]
            self.y = loc["y"]
            return
        self.loc = loc.world
        self.loc.contents.append(self)
        self.world = self.loc
        self.x = loc.x
        self.y = loc.y

        old_area = self.world.get_area(self.x, self.y)
        if(old_area != self):
            self.world.map_c[x_y_to_coord(self.x, self.y)]["Area"] = self
            old_area.qdel()
            del old_area

    def Destroy(self):
        self_coord = x_y_to_coord(self.x, self.y)
        if(self.world.map_c[self_coord]["Area"] == self):
            base = text_to_path(self.world.base_area)
            self.world.map_c[self_coord]["Area"] == base(self)
        super().Destroy()
        del self


class Turf(Atom):
    overlayable = True
    priority = 1
    allowed_contents = []
    size = 20  # Turfs are really big.

    def __init__(self, loc):
        self.current_load = 0
        super().__init__(loc)

    def move_atom_to(self, loc):
        if(isinstance(loc, dict)):  # Cheap hacks.
            self.loc = loc["world"]
            self.loc.contents.append(self)
            self.world = self.loc
            self.x = loc["x"]
            self.y = loc["y"]
            return
        self.loc = loc.world
        self.loc.contents.append(self)
        self.world = self.loc
        self.x = loc.x
        self.y = loc.y

        old_turf = self.world.get_turf(self.x, self.y)
        if(old_turf != self):
            self.world.map_c[x_y_to_coord(self.x, self.y)]["Turf"] = self
            old_turf.qdel()
            del old_turf

        self.update_icon()

    def generate_contents(self):
        return text_to_path(pick_weighted(self.allowed_contents))

    def crumble(self, severity):
        return False

    def Destroy(self):
        self_coord = x_y_to_coord(self.x, self.y)
        if(self.world.map_c[self_coord]["Turf"] == self):
            base = text_to_path(self.world.base_turf)
            self.world.map_c[self_coord]["Turf"] == base(self)
        super().Destroy()
        del self

class Moveable(Atom):
    obstruction = False

class Object(Moveable):
    priority = 11

class Mob(Moveable):
    priority = 21

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

    def __init__(self, loc):
        super().__init__(loc)
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
            strucs = []
            if(self.x == x_ and self.y == y_):
                el_all_on_tile = True
                strucs = self.contents
            else:
                strucs = self.world.get_all_tile_contents(x_, y_)

            for struc in strucs:
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

    def __init__(self, loc):
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

    def __init__(self, loc, integrity=3):
        super().__init__(loc)
        self.integrity = int(integrity)

    def process(self):
        coords = self.world.get_region_coordinates(self.x, self.y, 1, 1)
        random.shuffle(coords)
        for coord in coords:
            coord = coord_to_list(coord)
            x_ = coord["x"]
            y_ = coord["y"]
            strucs = self.world.get_all_tile_contents(x_, y_)
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
        strucs = self.world.get_all_tile_contents(x, y)
        for struc in strucs:
            if(isinstance(struc, Water)):
                return
            if(isinstance(struc, Fire)):
                return
        Fire(self.world.get_turf(x, y), self.integrity)

    def get_task(self, city):
        return {"priority" : 1, "jobs" : ["Peasant"], "task" : "destroy", "target" : self, "allowed_peasants" : True, "dist_required": 0}

    def react_to_attack(self, attacker):
        if(prob(10)):
            attacker.fire_act(1)
            return True
        return False


class Lightning(Object):
    icon_symbol = "z"
    icon_color = "yellow"
    name = "Lightning"
    default_description = "It is before the Thunder."
    size = 1
    priority = 100  # Pretty "light".

    def __init__(self, loc, power=3):
        super().__init__(loc)
        power = int(power)
        strucs = self.world.get_all_tile_contents(self.x, self.y)
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

    def __init__(self, loc):
        super().__init__(loc)
        self.been_used = False
        self.resource_multiplier = random.uniform(0.7, 1.3) * self.default_resource_multiplier
        self.resourcefulness = self.get_max_resourcefulness()

    def get_max_resourcefulness(self):
        return int(round(self.def_amount * self.resource_multiplier * self.integrity))

    def get_task(self, city):
        if(self.harvestable):
            return {"priority" : self.harv_priority, "jobs" : [self.job_to_harvest], "task" : "harvest", "target" : self, "allowed_peasants" : self.allow_peasants, "dist_required": 0}

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
        if(prob(harvester.action_time)):
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
    priority = 3

    icon_symbol = "|"

    harvestable = True
    allow_peasants = True
    resource = "food"
    job_to_harvest = "Farmer"
    harv_priority = 1

    default_resource_multiplier = 1.3
    def_amount = 100

    def fire_act(self, severity):
        self.crumble(severity)
        return True

    def electrocute_act(self, severity, source):
        Fire(self.loc, severity)
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

    def_amount = 300

    def fire_act(self, severity):
        self.crumble(severity)
        return True

    def electrocute_act(self, severity, source):
        Fire(self.loc, severity)
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

    def_amount = 500


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

    def_amount = 30


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

    def_amount = 30


class Tool(Object):
    icon_color = "grey"
    icon_font = ("Courier", 5)
    icon_symbol = "t"  # We use lowercase of the first letter.

    overlayable = True
    priority = 2

    name = ""
    job = ""
    make_priority = 0
    jobs_to_make = []
    allowed_peasants = False
    # restype_ is a macro for using res_make_of
    res_to_make = {"restype_": 1, "wood": 1}

    res_make_of = None  # Chisel makes out of stone, etc.
    res_quality = 1.0  # Chisel should have higher quality, since it makes out of stone.

    def __init__(self, loc, materials={"wood" : 5}, quality_modifier=1):
        self.set_icon()
        self.qdeling = False
        self.loc = None
        self.move_atom_to(loc)
        self.display_name = self.name
        self.materials = materials
        self.quality = random.uniform(1.5, 2.5) * quality_modifier

    def crumble(self, severity):
        return False  # TODO: Tool breaking instead of structure breaking.

    def move_atom_to(self, loc):
        if(self.loc and not self.qdeling):
            self.loc.contents.remove(self)
        self.loc = loc
        self.x = loc.x
        self.y = loc.y
        self.loc.contents.append(self)

    def Destroy(self):
        self.loc.contents.remove(self)
        del self

    def get_task(self, city):
        return {"priority" : 1, "jobs" : ["Peasant"], "task" : "equip", "item" : self, "target": city, "allowed_peasants" : True, "dist_required": 0}


class Hoe(Tool):
    icon_symbol = "h"
    name = "Hoe"
    job = "Farmer"
    make_priority = 1
    jobs_to_make = ["Carpenter", "Stonecutter"]
    allowed_peasants = False
    res_to_make = {"restype_": 5}


class Hammer(Tool):
    icon_symbol = "h"
    name = "Hammer"
    job = "Builder"
    make_priority = 2
    jobs_to_make = ["Carpenter", "Stonecutter"]
    allowed_peasants = False
    res_to_make = {"restype_": 5}


class Axe(Tool):
    icon_symbol = "a"
    name = "Axe"
    job = "Lumberjack"
    make_priority = 3
    jobs_to_make = ["Stonecutter"]
    allowed_peasants = False
    res_to_make = {"restype_": 5}


class Sledgehammer(Tool):
    icon_symbol = "s"
    name = "Sledgehammer"
    job = "Blacksmith"
    make_priority = 4
    jobs_to_make = ["Stonecutter"]
    allowed_peasants = False
    res_to_make = {"restype_": 5}


class Sharphammer(Tool):
    icon_symbol = "s"
    name = "Sharphammer"
    job = "Weaponsmith"
    make_priority = 4
    jobs_to_make = ["Stonecutter"]
    allowed_peasants = False
    res_to_make = {"restype_": 5}


class Pickaxe(Tool):
    icon_symbol = "p"
    name = "Pickaxe"
    job = "Miner"
    make_priority = 3
    jobs_to_make = ["Stonecutter"]
    allowed_peasants = False
    res_to_make = {"restype_": 5}


class Chisel(Tool):
    icon_symbol = "c"
    name = "Chisel"
    job = "Stonecutter"
    make_priority = 3
    jobs_to_make = ["Peasant"]
    allowed_peasants = True
    res_to_make = {"stone": 5}

    res_make_of = "stone"
    res_quality = 1.5


class Saw(Tool):
    icon_symbol = "s"
    name = "Saw"
    job = "Carpenter"
    make_priority = 2
    jobs_to_make = ["Peasant"]
    allowed_peasants = True
    res_to_make = {"wood": 5}

    res_make_of = "wood"


class City(Object):
    icon_color = "grey"
    icon_symbol = "0"
    overlayable = True
    name = "City"
    default_description = ""  # Uses custom code.
    priority = 30  # Should actually be above mob layer.
    size = 5

    starting_citizens = 5

    needs_processing = True
    action_time = 24  # Once a day they get new tasks.

    def __init__(self, loc, faction=None):
        global log

        self.faction = faction
        if(faction):
            faction.add_to_faction(self)
        else:
            self.faction = Faction(self)

        super().__init__(loc)
        self.display_name = self.name + " " + str(random.randrange(1, 999))
        self.max_population = 10

        self.job_requests = {"Toddler": 0,
                             "Peasant": 0,
                             "Farmer": 0,
                             "Builder": 0,
                             "Carpenter": 0,
                             "Lumberjack": 0,
                             "Stonecutter": 0,
                             "Miner": 0,
                             "Blacksmith": 0,
                             "Weaponsmith": 0}
        self.tool_requests = {"Toddler": 0,
                              "Peasant": 0,
                              "Farmer": 0,
                              "Builder": 0,
                              "Carpenter": 0,
                              "Lumberjack": 0,
                              "Stonecutter": 0,
                              "Miner": 0,
                              "Blacksmith": 0,
                              "Weaponsmith": 0}
        self.structure_requests = {"Construction": 0,
                               "House": 0,
                               "Farm": 0,
                               "Mine": 0}
        self.generating_tasks = False

        self.citizens = []
        self.inventory = []

        self.tasks = []

        self.resources = {"food" : 100,
                          "wood" : 0,
                          "stone" : 0,
                          "iron" : 0,
                          "gold" : 0}

        for N in range(self.starting_citizens):
            citizen = Citizen(self, "Peasant", self)

        log += self.display_name + " has been settled in " + x_y_to_coord(self.x, self.y) + " at " + time_to_date(self.world.time) + "\n"

    def getExamineText(self):
        text = super().getExamineText()
        text += "It is a city of " + self.faction.display_name + " and it has " + str(len(self.citizens)) + " citizens in it!"
        return text

    def Destroy(self):
        global log

        log += self.display_name + " has been destroyed in " + x_y_to_coord(self.x, self.y) + " at " + time_to_date(self.world.time) + "\n"

        for cit in self.citizens:
            self.citizens.remove(cit)
            cit.target_task = None
            cit.city = None

        self.citizens = []
        self.inventory = []
        self.tasks = []
        self.faction.members.remove(self)
        self.faction = None

        super().Destroy()
        del self

    def process(self):
        food_required = 0
        for citizen in self.citizens:
            if(not citizen.qdeling):
                food_required += citizen.hunger_rate * self.action_time  # How much citizen eats per day.
                if(not citizen.find_a_job()):
                    citizen.find_tool()
                self.job_requests[citizen.job] -= 1

        actual_food_required = food_required

        self.job_requests = {"Toddler": 0,
                             "Peasant": 0,
                             "Farmer": 0,
                             "Builder": 1 + (len(self.citizens) // 10),
                             "Carpenter": 1 + (len(self.citizens) // 10),
                             "Lumberjack": 0,
                             "Stonecutter": 1 + (len(self.citizens) // 10),
                             "Miner": 0,
                             "Blacksmith": 0,
                             "Weaponsmith": 0}
        self.tool_requests = {"Toddler": 0,
                              "Peasant": 0,
                              "Farmer": 0,
                              "Builder": 0,
                              "Carpenter": 0,
                              "Lumberjack": 0,
                              "Stonecutter": 0,
                              "Miner": 0,
                              "Blacksmith": 0,
                              "Weaponsmith": 0}
        self.structure_requests = {"Construction": 0,
                               "House": int(self.max_population - len(self.citizens) <= 0),
                               "Farm": int(round((actual_food_required + (self.max_population - len(self.citizens)) * self.action_time) / Farm.default_resource_multiplier / 4)),  # Since a farm generally supplies three Citizens.
                               "Mine": 0}

        strucs = self.world.get_region_contents(self.x, self.y, 2, 2)
        random.shuffle(strucs)

        self.generating_tasks = True
        self.tasks = []

        houses_count = 0
        for struc in strucs:
            struc.been_used = False

            if(isinstance(struc, Citizen)):
                if(not struc.city):
                    struc.join_city(self)
                    continue

            task = struc.get_task(self)  # We pass ourselves as city argument.
            if(not task):  # This thing dindu tasking.
                continue

            if(isinstance(struc, City)):
                if(self.faction and struc.faction != self.faction):
                    self.faction.adjust_relationship(struc.faction, -3)

            elif(isinstance(struc, Resource)):
                if(struc.resource):
                    if(self.resources[struc.resource] >= 50 * self.action_time * len(self.citizens)):  # We have enough of this...
                        continue

                    if(isinstance(struc, Tall_Grass)):
                        if(food_required > 0):
                            food_required -= struc.resource_multiplier * struc.default_resource_multiplier * citizen.action_time

                    elif(isinstance(struc, Farm)):
                        if(food_required > 0):
                            food_required -= struc.resource_multiplier * struc.default_resource_multiplier * citizen.action_time * 3

                    elif(isinstance(struc, Forest)):
                        self.job_requests["Lumberjack"] += 1

                if(isinstance(struc, Structure)):
                    if(struc.name != "House" and struc.name != "City"):  # Houses are calculated as special snowflake case.
                        self.structure_requests[struc.name] -= 1
                    if(struc.job_to_harvest):
                        self.job_requests[struc.job_to_harvest] += 1
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

        for job_request in self.job_requests:
            self.tool_requests[job_request] = round(self.job_requests[job_request] * 1.5)

        self.max_population = 10 + houses_count * 2

        for tool in self.inventory:
            self.tool_requests[tool.job] -= 1
            if(isinstance(tool, Tool)):
                if(self.tool_requests[tool.job] <= 0):
                    self.tasks.append({"priority": 5, "jobs": ["Peasant"], "task": "break", "item": tool, "target": self, "allowed_peasants": True, "dist_required": -1})

        for tool_request in self.tool_requests:
            if(self.tool_requests[tool_request] <= 0):
                continue
            tool_type = job_to_tool(tool_request)
            if(not tool_type):
                continue
            for task_ in range(0, self.tool_requests[tool_request]):
                self.tasks.append({"priority": tool_type.make_priority, "jobs": tool_type.jobs_to_make, "task": "create", "item": tool_type, "target": self, "res_required": {"use_macro": 0}, "allowed_peasants": tool_type.allowed_peasants, "dist_required": -1})

        for structure_request in self.structure_requests:
            if(self.structure_requests[structure_request] <= 0):
                continue
            if(structure_request == "Farm"):
                for task in range(0, self.structure_requests[structure_request]):
                    self.tasks.append({"priority" : 1, "jobs" : ["Builder"], "task" : "build", "item" : Farm, "area": strucs, "target": None, "res_required" : {"wood" : 30}, "allowed_peasants" : False, "dist_required": 0})
            elif(structure_request == "Mine"):
                for task in range(0, self.structure_requests[structure_request]):
                    self.tasks.append({"priority" : 3, "jobs" : ["Builder"], "task" : "build", "item" : Mine, "area": strucs, "target": None, "res_required" : {"wood" : 30}, "allowed_peasants" : False, "dist_required": 0})
            elif(structure_request == "House"):
                for task in range(0, self.structure_requests[structure_request]):
                    self.tasks.append({"priority" : 3, "jobs" : ["Builder"], "task" : "build", "item" : House, "area": strucs, "target": None, "res_required" : {"wood" : 30, "stone" : 30}, "allowed_peasants" : False, "dist_required": 0})

        sorted_list = []
        to_sort = self.tasks.copy()
        task_priority = 1
        for task_priority in range(1, 11, 1):  # 1-10.
            for task in to_sort:
                if(task["priority"] == task_priority):
                    sorted_list.append(task)
                    to_sort.remove(task)
        self.tasks = sorted_list

        self.generating_tasks = False

        if(self.resources["food"] > 30 and (food_required <= 0) and (len(self.citizens) < self.max_population)):
            self.resources["food"] -= 30
            self.add_citizen(Toddler(self, "Toddler"))

        if(len(self.citizens) < 100):
            self.icon_symbol = str(int(len(self.citizens) // 10))
        elif(len(self.citizens) < 1000):
             self.icon_symbol = "L"
        elif(len(self.citizens) < 10000):
             self.icon_symbol = "M"

        if(len(self.citizens) > self.max_population): # Overpopulation - DEATH!
            cit = random.choice(self.citizens)
            self.remove_citizen(cit)
            cit.qdel()
            del cit

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
            print(len(self.inventory))
            l = ""
            for cit in self.citizens:
                l = l + cit.display_name + " "
            print(l + "[" + str(len(self.citizens)) + "]")

    def get_prioritized_task_for(self, citizen):
        """
        Returns a task that needs to be prioritized by
        citizen.
        """
        if(self.qdeling):
            return None
        for task in self.tasks:
            if(task == citizen.target_task):
                continue
            if(citizen.job in task["jobs"]):
                return task
            if(task["allowed_peasants"]):
                return task
        return None


    def add_citizen(self, citizen):
        self.citizens.append(citizen)

    def remove_citizen(self, citizen_):
        self.citizens.remove(citizen_)

        if(len(self.citizens) == 0):
            self.qdel()
            del self

    def set_icon(self):
        self.icon = {"symbol": self.icon_symbol, "color": self.faction.color if self.faction else self.icon_color, "font": self.icon_font}

    def get_task(self, city):
        if(city.faction != self.faction):
            relation = city.faction.get_relationship(self.faction)
            if(relation == "Unfriendly" or relation == "Neutral" or relation == "Friendly"):
                return {"priority" : 2, "jobs" : ["Peasant"], "task" : "put", "res_required" : {random.choice(["food", "wood", "stone"]) : random.randint(10, 20)}, "target" : self, "allowed_peasants" : True, "dist_required": -1}
            if(relation == "Hostile"):
                return {"priority" : 2, "jobs" : ["Peasant"], "task" : "kidnap", "target" : self, "allowed_peasants" : True, "dist_required": -1}
        return super().get_task(city)

    def fire_act(self, severity):
        self.crumble(severity)
        return True

    def electrocute_act(self, severity, source):
        Fire(self.loc)
        return False  # It does not actually conduct electricity.


class Structure(Resource):
    icon_color = "grey"
    overlayable = True
    size = 5
    priority = 12

    def __init__(self, loc, faction=None):
        self.faction = faction
        if(faction):
            faction.add_to_faction(self)
        super().__init__(loc)

    def set_icon(self):
        self.icon = {"symbol": self.icon_symbol, "color": self.faction.color if self.faction else self.icon_color, "font": self.icon_font}

    def get_task(self, city):
        if(city.faction != self.faction):
            relation = city.faction.get_relationship(self.faction)
            if(relation == "Hostile"):
                return {"priority" : 2, "jobs" : ["Peasant"], "task" : "claim", "target" : self, "allowed_peasants" : True, "dist_required": 0}
        return super().get_task(city)

    def Destroy(self):
        if(self.faction):
            self.faction.members.remove(self)
        self.faction = None
        super().Destroy()
        del self

class Construction(Structure):
    icon_symbol = "C"
    name = "Construction"
    default_description = "When Construction will grow up, it will become a big Structure!."

    def __init__(self, loc, to_construct, struc_type, faction=None):
        super().__init__(loc, faction)
        self.to_construct = to_construct
        self.struc_type = struc_type

    def construct(self, severity):
        self.to_construct = max(self.to_construct - severity, 0)
        if(self.to_construct <= 0 and not self.qdeling):
            self.struc_type(self.loc, self.faction)
            self.qdel()
            del self

    def get_task(self, city):
        if(city.faction != self.faction):
            relation = city.faction.get_relationship(self.faction)
            if(relation == "Hostile"):
                return {"priority" : 2, "jobs" : ["Peasant"], "task" : "claim", "target" : self, "allowed_peasants" : True, "dist_required": 0}
        return {"priority" : 1, "jobs" : ["Builder"], "task" : "construct", "target" : self, "allowed_peasants" : False, "dist_required": 0}


class House(Structure):
    icon_symbol = "H"
    name = "House"
    default_description = "A place for Citizens to call home."
    work_required = 20

    def fire_act(self, severity):
        self.crumble(severity)
        return True

    def electrocute_act(self, severity, source):
        Fire(self.loc)
        return False  # It does not actually conduct electricity.


class Farm(Structure):
    icon_symbol = "F"
    name = "Farm"
    default_description = "A place to get food from."
    work_required = 15

    harvestable = True
    allow_peasants = False
    resource = "food"
    job_to_harvest = "Farmer"
    harv_priority = 1

    default_resource_multiplier = 1.5
    def_amount = 500

    def fire_act(self, severity):
        self.crumble(severity)
        return True

    def electrocute_act(self, severity, source):
        Fire(self.loc)
        return False  # It does not actually conduct electricity.


class Mine(Structure):
    icon_symbol = "M"
    name = "Mine"
    default_description = "Diggy-diggy hole..."
    work_required = 25

    harvestable = True
    allow_peasants = False
    resource = "stone"
    job_to_harvest = "Miner"
    harv_priority = 5

    default_resource_multiplier = 1.3
    def_amount = 500


# Mobs.
class Citizen(Mob):
    icon_symbol = "o"
    icon_color = "grey"
    icon_font = ("Courier", 7)
    priority = 29  # Real high.
    overlayable = True
    size = 1

    max_actions_to_perform = 4
    max_work_per_action_time = 16  # Tasks take twice as much as walking.

    needs_processing = True
    action_time = 4

    def __init__(self, loc, job, city=None):
        self.city = None
        if(city):
            self.join_city(city)

        super().__init__(loc)
        self.resources = {"food" : 30,  # We give them some starting food.
                          "wood" : 0,
                          "stone" : 0,
                          "iron" : 0,
                          "gold" : 0}

        self.tasks = []
        self.personal_tasks = []
        self.target_task = None  # Task given by city.

        self.id = str(random.randrange(1, 999))
        self.actions_to_perform = self.max_actions_to_perform
        self.work_per_action_time = self.max_work_per_action_time

        self.max_health = random.randrange(2, 4)
        self.health = self.max_health
        self.age = 8760  # At least one year.

        self.max_saturation = random.randrange(50, 100)
        self.saturation = self.max_saturation
        self.hunger_rate = random.uniform(0.7, 1.3)
        self.malnutrition = 0

        self.qdeling = False
        self.quality_modifier = random.uniform(0.7, 1.3)
        self.job = None
        self.tool = None
        self.change_job(job)
        self.display_name = self.job + " " + self.id

    def join_city(self, city):
        if(self.city):
            self.leave_city()
        self.city = city
        if(self not in self.city.citizens):
            self.city.add_citizen(self)

    def leave_city(self):
        if(self in self.city.citizens):
            self.city.remove_citizen(self)
        self.city = None

    def process(self):
        self.work_per_action_time = self.max_work_per_action_time
        self.saturation = max(self.saturation - round(self.hunger_rate * self.action_time), 0)

        # Aging.
        if(prob(self.action_time)):  # Special actions ensue.
            self.quality_modifier += 0.1
        self.age += self.action_time  # Normal behavior.

        if(self.actions_to_perform <= 0):  # OVERWORKING: Citizens can work more than they should, but they will die quicker.
            if(prob(round(abs(self.actions_to_perform) * self.action_time))):
                if(self.crumble(abs(self.actions_to_perform))):
                    return False  # We dead.

        if(self.saturation == 0):
            self.malnutrition += self.action_time
            if(prob(self.malnutrition // 100)):
                if(self.crumble(self.malnutrition // 100)):
                    return False  # We dead.

        if(prob(self.age // 8760)):  # Sometimes they just die.
            if(self.crumble(self.age // 87600)):
                return False  # We dead.

        if(self.malnutrition > 0):
            self.malnutrition = max([self.malnutrition - round(self.saturation / (self.max_saturation) * self.action_time), 0])

        """
        Generates the most basic of
        Citizen's needs, and puts them
        in a list.

        Updates each tick!
        """
        self.personal_tasks = []
        if(self.resources["food"] <= 0 and self.city):  # If no food left in pockets, grab a full day worth of meals.
            # We append this to actual proper tasks, since we don't want this erased.
            self.personal_tasks.append({"task": "grab", "res_required": {"food": round(self.hunger_rate * self.action_time) * 5}, "target": self.city, "dist_required": -1})
        if(self.saturation < self.max_saturation):
            self.personal_tasks.append({"task": "eat", "res_required": {"food": self.max_saturation - self.saturation}})
        if(self.actions_to_perform <= 0):
            """

            This fragment is supposed to allow Citizens to rest more efficiently later.

            target = self.world.get_turf(self.x, self.y)
            for struc in self.world.get_region_contents(self.x, self.y, 1, 1):
                if(isinstance(struc, City)):
                    target = struc
                elif(isinstance(struc, House)):
                    target = struc
            """

            for i in range(0, self.max_actions_to_perform - self.actions_to_perform + 1):
                self.personal_tasks.append({"task": "rest", "target": self.loc, "dist_required": -1})

        for task in self.personal_tasks:
            if(self.work_per_action_time <= 0):
                break
            while(self.work_per_action_time > 0):
                result = self.perform_task(task)
                if(result == 3):  # We didn't even start the task, no work is done.
                    break
                if(result == 2):
                    self.work_per_action_time -= 2
                    # print(self.display_name + " performed " + str(task))
                    break
                elif(result == 1):
                    self.work_per_action_time -= 2
                    break  # No point in trying to accomplish a failed action.
                self.work_per_action_time -= 1

        perf_tasks = self.tasks.copy()

        for task in perf_tasks:
            if(self.work_per_action_time <= 0):
                break
            while(self.work_per_action_time > 0):
                result = self.perform_task(task)
                if(result == 3):  # We didn't even start the task, no work is done.
                    break
                if(result == 2):
                    self.work_per_action_time -= 2
                    # print(self.display_name + " performed " + str(task))
                    self.tasks.remove(task)
                    break
                elif(result == 1):
                    self.work_per_action_time -= 2
                    break
                self.work_per_action_time -= 1

        # Getting first task, to see if it's even worth it.
        self.target_task = None
        if(self.city and not self.city.generating_tasks):
            task = self.city.get_prioritized_task_for(self)
            if(task):
                self.target_task = task

        while(self.work_per_action_time > 0):
            # if(self.target_task in self.city.tasks):
            if(self.target_task):
                result = self.perform_task(self.target_task)
                if(result == 3):  # No path to task, help others.
                    if(self.city):
                        # Performance critical code. Copy-pasting and making in-line.
                        self.city.tasks.remove(self.target_task)
                        if(self.city.generating_tasks):  # Task is not ready.
                            break
                        task = self.city.get_prioritized_task_for(self)
                        if(not task):
                            break
                        self.target_task = task
                        continue

                    self.target_task = None

                elif(result == 2):
                    self.work_per_action_time -= 2

                    if(self.city):
                        self.city.tasks.remove(self.target_task)
                        if(self.city.generating_tasks):  # Task is not ready.
                            break
                        task = self.city.get_prioritized_task_for(self)
                        if(not task):
                            break
                        self.target_task = task
                        continue

                    self.target_task = None

                elif(result == 1):
                    self.work_per_action_time -= 2
                    if(self.city):
                        if(self.city.generating_tasks):  # Task is not ready.
                            break
                        task = self.city.get_prioritized_task_for(self)
                        if(not task):
                            break
                        self.target_task = task
                else:
                    self.work_per_action_time -= 1

            else:  # We didn't get any tasks, meh.
                break

        return True  # If it didn't die this iteration.

    def perform_task(self, task):
        """
        Attempts to perform the task given.
        Returns 0 if was walking towards task target.
        Returns 1 if failed task.
        Returns 2 if task accomplished.
        Returns 3 if can't reach.

        TODO: task unique ids.
        """
        if(("dist_required" in task) and task["target"]):
            if(self.get_distance(task["target"]) > task["dist_required"]):
                if(not self.move_towards_to(task["target"], 1)):
                    return 3  # Couldn't find a way to it.
                return 0

        if(task["task"] == "harvest"):
            return self.harvest(task["target"])

        elif(task["task"] == "create"):
            return self.create(task["res_required"], task["item"])

        elif(task["task"] == "construct"):
            return self.construct(task["target"])

        elif(task["task"] == "build"):
            look_for = []
            if(task["item"] == Farm):
                look_for = [Plains]
            if(task["item"] == Mine):
                look_for = [Rocky]
            if(task["item"] == House):
                look_for = [Plains, Hills]
            if(not task["target"]):
                for struc in task["area"]:
                    if(is_instance_in_list(struc, look_for)):
                        task["target"] = struc
                        return 0  # Well, we are kinda moving.
            return self.build(task["res_required"], task["item"], task["target"])

        elif(task["task"] == "rest"):
            return self.rest(task["target"])

        elif(task["task"] == "destroy"):
            return self.destroy(task["target"])

        elif(task["task"] == "kidnap"):
            return self.kidnap(task["target"])

        elif(task["task"] == "claim"):
            return self.claim(task["target"])

        elif(task["task"] == "break"):
            return self.break_tool(task["item"])

        if(task["task"] == "eat"):
            return self.eat(task["res_required"])

        elif(task["task"] == "grab"):
            return self.grab(task["res_required"], task["target"])

        elif(task["task"] == "put"):
            return self.put(task["res_required"], task["target"])

        elif(task["task"] == "equip"):
            return self.equip(task["item"], task["target"])

        elif(task["task"] == "put_tools"):
            return self.put_tools(task["target"])
        return 1

    def create(self, resources_required, item_type):
        if(self.actions_to_perform <= -self.max_actions_to_perform):
            return 1
        if("use_macro" in resources_required):
            resources_required = item_type.res_to_make
            if("restype_" in resources_required):
                resources_required[self.tool.res_make_of] = resources_required.pop("restype_")

        self.tasks.append({"task": "grab", "res_required": resources_required, "target": self.city, "dist_required": -1})

        for res in resources_required:
            if(self.resources[res] <= resources_required[res]):
                return 1

        for res in resources_required:
            self.resources[res] -= resources_required[res]

        modifier = self.quality_modifier

        if(self.tool):
            modifier = modifier * self.tool.res_quality

        item_type(self, resources_required, modifier)
        self.tasks.append({"task": "put_tools", "target": self.city, "dist_required": -1})
        self.actions_to_perform -= 1
        return 2

    def build(self, resources_required, struc_type, loc):
        if(self.actions_to_perform <= -self.max_actions_to_perform):
            return 1
        self.tasks.append({"task": "grab", "res_required": resources_required, "target": self.city, "dist_required": -1})
        if(self.loc.world.is_overcrowded(loc.x, loc.y, struc_type.size)):
            return 1
        for res in resources_required:
            if(self.resources[res] <= resources_required[res]):
                return 1
        for res in resources_required:
            self.resources[res] -= resources_required[res]
        self.actions_to_perform -= 1
        Construction(loc, struc_type.work_required, struc_type, self.city.faction)
        return 2

    def construct(self, target):
        if(self.actions_to_perform <= -self.max_actions_to_perform):
            return 1
        target.construct(int(round(self.quality_modifier * self.action_time)))
        self.actions_to_perform -= 1
        return 2

    def harvest(self, target):
        if(self.actions_to_perform <= -self.max_actions_to_perform):
            return 1
        if(not target.been_used):
            to_harvest = round(self.action_time * target.resource_multiplier * self.get_tool_quality(target.job_to_harvest))
            harvested = target.harvest(self, to_harvest)
            if(harvested > 0):
                self.resources[target.resource] += harvested
                self.actions_to_perform -= 1
                self.tasks.append({"task": "put", "res_required": {target.resource: harvested}, "target": self.city, "dist_required": -1})
                return 2
        return 1

    def rest(self, target):
        if(target.been_used):
            return 1
        self.actions_to_perform = min([self.max_actions_to_perform, self.actions_to_perform + 1])
        if(prob(self.health)):  # A healthy spirit in a healthy body.
            self.actions_to_perform = min([self.max_actions_to_perform, self.actions_to_perform + 1])
        self.health = min([self.health + 1, self.max_health])
        return 2

    def destroy(self, target):
        """
        Do not confuse with Destroy(!).
        This proc allows Citizens to destroy their targets.
        """
        if(self.actions_to_perform <= -self.max_actions_to_perform):
            return 1
        damage_to_do = int(round(((self.saturation / (self.max_saturation)) - (self.malnutrition / 100)) * self.action_time))
        if(damage_to_do >= 1):
            if(not target.react_to_attack(self)):  # If target reacted to attack, we failed.
                target.crumble(damage_to_do)
                self.actions_to_perform -= damage_to_do  # Hitting hard takes more effort.
                return 2
        return 1

    def react_to_attack(self, attacker):
        """
        This is basically the destroy() method.
        But it is used in coubnter attacking,
        we define it seperately to prevent recursions.
        """
        if(self.actions_to_perform <= -self.max_actions_to_perform):
            return False
        damage_to_do = int(round(((self.saturation / (self.max_saturation)) - (self.malnutrition / 100)) * self.action_time))
        if(damage_to_do >= 1):
            attacker.crumble(damage_to_do)
            self.actions_to_perform -= damage_to_do  # Hitting hard takes more effort.
            return True
        return False

    def kidnap(self, target):
        if(self.actions_to_perform <= -self.max_actions_to_perform):
            return 1
        if(len(target.citizens)):
            citizen = random.choice(target.citizens)
            citizen.join_city(self.city)
            self.actions_to_perform -= 1
            return 2
        return 1

    def claim(self, target):
        if(not target.faction):
            target.faction = self.city.faction
            self.city.faction.add_to_faction(target)
            target.update_icon()
        elif(self.destroy(target) and not target.qdeling):  # By "capturing" it, we of course mean murdering it slightly.
                target.faction.adjust_relationship(self.city.faction, -30)  # I mean claiming other's territory is quite a threat.
                target.faction.members.remove(target)
                target.faction = None
                target.update_icon()
        # self.actions_to_perform -= 1  # Action removal is handled in destroy().
        return 2

    def break_tool(self, target):
        to_put = {}
        for material in target.materials:
            if(prob(75 * self.quality_modifier)):  # Oh-ho-ho, it can break for good.
                self.resources[material] += target.materials[material]
                to_put[material] = target.materials[material]
        target.qdel()
        del target
        self.tasks.append({"task": "put", "res_required": to_put, "target": self.city, "dist_required": -1})
        return 2

    def grab(self, resources_required, target):
        """
        Grab all the resources_required from target's
        resources.
        """
        actual_grab_size = {}
        for res in resources_required:
            if(target.resources[res] >= resources_required[res]):
                actual_grab_size[res] = resources_required[res]
            else:
                actual_grab_size[res] = target.resources[res]
        for res in resources_required:
            target.resources[res] -= actual_grab_size[res]
            self.resources[res] += actual_grab_size[res]
        return 2  # Grabbing item is not an action.

    def put(self, resources_required, target):
        actual_put_size = {}
        for res in resources_required:
            if(self.resources[res] > resources_required[res]):
                actual_put_size[res] = resources_required[res]
            else:
                actual_put_size[res] = self.resources[res]
        for res in resources_required:
            self.resources[res] -= actual_put_size[res]
            target.resources[res] += actual_put_size[res]
        return 2  # Putting item is not an action.

    def eat(self, resources_required):
        """
        Eat as much as specified in res_required.
        Eat from target's resources.
        """
        actual_eat_size = {}
        for res in resources_required:
            if(self.resources[res] > resources_required[res]):
                actual_eat_size[res] = resources_required[res]
            else:
                actual_eat_size[res] = self.resources[res]
        eaten = 0
        for res in resources_required:
            self.resources[res] -= actual_eat_size[res]
            eaten += actual_eat_size[res]
        self.saturation = min([self.max_saturation, self.saturation + eaten])
        return 2  # Eating doesn't tak an action, come on.

    def put_tools(self, target):
        for tool in self.contents:
            if(isinstance(tool, Tool) and self.tool != tool):
                tool.move_atom_to(target)
                if("inventory" in vars(target).keys()):
                    target.inventory.append(tool)
        return 2

    def equip(self, tool, target):
        """
        Gets tool from target and equips it.
        We do return our old tool though.
        """
        if(self.tool):
            self.tool.move_atom_to(target)
        tool.move_atom_to(self)
        self.tool = tool
        return 2

    def crumble(self, severity):
        self.health = self.health - severity
        if(self.health <= 0):
            
            self.qdel()
            del self
            return True # Fully crumbled.
        return False

    def fire_act(self, severity):
        self.crumble(severity)
        return False  # I mean, you can't spread fire by just one Citizen.

    def electrocute_act(self, severity):
        self.crumble(seveirty)
        return False  # Do not conduct it further.

    def get_tool_quality(self, job_to_check="Toddler"):  # Toddler means any tool will do.
        if(self.tool and (self.tool.job == job_to_check or job_to_check == "Toddler")):
            return self.tool.quality
        return 1.0

    def find_a_job(self):
        """
        Returns True if we changed our job.
        Returns False if we didn't.
        """
        if(self.city.job_requests[self.job] >= 0):
            return False
        for job in ["Farmer", "Carpenter", "Builder", "Stonecutter", "Lumberjack", "Miner", "Blacksmith", "Weaponsmith"]:
            if(self.city.job_requests[job] > 0):
                if(self.become_job(job)):
                    return True
        return False

    def become_job(self, job):
        for tool in self.city.inventory:
            if(not isinstance(tool, Tool)):
                continue
            if(tool.job == job):
                self.change_job(job)
                return True
        return False

    def change_job(self, job, tool=None):
        if(self.job == job):
            return
        self.job = job
        self.icon_symbol = job[0].lower()  # Lifehack.
        self.display_name = self.job + " " + self.id
        self.find_tool()

    def find_tool(self):
        if(not self.city):
            return
        for tool in self.city.inventory:
            if(not isinstance(tool, Tool)):
                continue
            if(tool.job != self.job):
                continue
            if(tool.quality > self.get_tool_quality(self.job)):
                self.tasks.append({"priority": 1, "task": "equip", "item": tool, "target": self.city, "dist_required": -1})

    def set_icon(self):
        self.icon = {"symbol": self.icon_symbol, "color": self.city.faction.color if self.city and not self.city.qdeling else self.icon_color, "font": self.icon_font}

    def get_task(self, city):
        if(self.city and city.faction != self.city.faction):
            if(city.faction.get_relationship(self.city.faction) == "Hostile"):
                return {"priority" : 1, "jobs" : ["Peasant"], "task" : "destroy", "target" : self, "allowed_peasants" : True, "dist_required": 0}
        return None

    def Destroy(self):
        if(self.tool):
            if(self.city):
                self.city.inventory.append(self.tool)
                self.tool = None
            else:
                self.tool.qdel()
                del self.tool
        if(self.city):
            self.leave_city()
        super().Destroy()
        del self


class Toddler(Citizen):
    icon_symbol = "t"
    name = "Toddler"
    max_actions_to_perform = 1

    def __init__(self, loc, job):
        super().__init__(loc, "Toddler")  # No matter the job given, a Toddler is a Toddler.
        self.age = 0  # Since citizen is set to 8760.

        self.max_health = 1
        self.health = self.max_health

        self.max_saturation = random.randrange(10, 20)
        self.saturation = self.max_saturation
        self.hunger_rate = random.uniform(0.35, 0.65)

    def perform_task(self, task):
        if(("dist_required" in task) and task["target"]):
            if(self.get_distance(task["target"]) > task["dist_required"]):
                self.move_towards_to(task["target"], 1)
                return 0
        if(task["task"] == "eat"):
            return self.eat(task["res_required"])
        elif(task["task"] == "grab"):
            return self.grab(task["res_required"], task["target"])
        elif(task["task"] == "put"):
            return self.put(task["res_required"], task["target"])
        elif(task["task"] == "equip"):
            return self.equip(task["item"], task["target"])
        elif(task["task"] == "put_tools"):
            return self.put_tools(task["target"])
        return 1

    def find_a_job(self):
        # Toddlers don't really have jobs, but they use this to
        # break some tools.
        self.find_tool()
        return True  # We changed our job? I guess.

    def become_job(self, job):
        return False

    def process(self):
        if(not super().process()):
            return False

        if((self.age / 8760) >= 1):
            peasant = Citizen(self.loc, "Peasant", city=self.city)
            peasant.health = self.health
            peasant.age = self.age

            peasant.saturation = self.saturation
            peasant.malnutrition = self.malnutrition

            peasant.quality_modifier = self.quality_modifier
            self.qdel()
            del self
            return False  # Well, the Toddler did dissapear.
        return True


# GUI.
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
        self.inter_cycle = True  # Turn off when fully initiated.

        self.wind = tkinter.Toplevel(parent.wind)
        self.wind.resizable(False, False)
        self.wind.geometry("+%d+%d" % (parent.wind.winfo_x() + self.saved_x, parent.wind.winfo_y() + self.saved_y))
        self.wind.attributes("-topmost", True)
        self.wind.protocol("WM_DELETE_WINDOW", self.on_close)

    def qdel(self):
        if(not self.qdeling):
            self.qdeling = True
            self.Destroy()
        del self

    def Destroy(self):
        self.wind.destroy()
        self.parent.child_windows.pop(self.tag)
        self.parent = None
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

        self.structures = sort_by_priority(copy.deepcopy(self.parent.cur_world.get_all_tile_contents(self.x_coord, self.y_coord)))

        self.wind.title(u'The Tile (%d, %d)' % (self.x_coord, self.y_coord))
        self.wind_wid = max([int(round(4 * self.parent.pixels_per_tile)), self.parent.max_coord_lenght])
        self.wind_hei = int(round(len(self.structures) * 6 * self.parent.pixels_per_tile))

        self.content = tkinter.Frame(self.wind, width=self.wind_wid * 1.5, height=self.wind_hei * 2, borderwidth=2, relief="solid")

        self.coord_text = tkinter.Text(self.content, width=int(round(self.wind_wid / self.parent.pixels_per_tile)), height=1, fg="white", bg="dark blue", font='TkFixedFont')
        self.coord_text.insert(tkinter.END, x_y_to_coord(self.x_coord, self.y_coord))

        self.temp_map_field = tkinter.Canvas(self.content, width=self.wind_wid, height=self.wind_hei * 1.5, bg='black')
        self.temp_map_field.bind("<ButtonPress-1>", self.on_click)
        self.temp_map_field.bind("<Shift-Button-1>", self.on_shift_click)
        self.structure_icons = []

        #self.coordinates = self.temp_map_field.create_text(int(round(self.wind_wid / 2)), self.wind_wid - self.parent.pixels_per_tile, text="Coords: (%s, %s)" % (self.x_coord, self.y_coord), font='TkiFixedFont', fill="green")

        self.content.pack(expand=False, padx=10, pady=10)

        self.coord_text.pack()
        self.temp_map_field.pack()

        self.inter_cycle = False

    def Destroy(self):
        self.parent.wind.focus_force()
        self.inter_cycle = True
        self.structures = None
        super().Destroy()
        del self

    def on_click(self, event):
        """Try-hard hack to make these objects clickable."""
        # I do know of operator precedence. I do know that I subtract 1 and not pixels_per_tile...
        # But can you blame me if it works?
        y_ = int(round(event.y / self.parent.pixels_per_tile - 1))
        if(y_ >= 0 and y_ < len(self.structures)):
            atom = self.structures[y_]
            atom.Clicked(self.parent, atom.x, atom.y)  # Cheap hack to get at least some x and y to be passed.

    def on_shift_click(self, event):
        y_ = int(round(event.y / self.parent.pixels_per_tile - 1))
        if(y_ >= 0 and y_ < len(self.structures)):
            atom = self.structures[y_]
            atom.Clicked(self.parent, atom.x, atom.y, mods=["shift"])

    def on_cycle(self):
        if(self.inter_cycle):
            return

        self.structures = sort_by_priority(copy.deepcopy(self.parent.cur_world.get_all_tile_contents(self.x_coord, self.y_coord)))

        self.wind_hei = int(round(len(self.structures) * 6 * self.parent.pixels_per_tile))
        self.content.configure(height=self.wind_hei * 2)
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
            icon = structure.icon
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
        self.wind.focus_force()

        self.left = tkinter.Frame(self.wind, borderwidth=2, relief="solid")
        self.right = tkinter.Frame(self.wind, borderwidth=2, relief="solid")
        self.container = tkinter.Frame(self.left, borderwidth=2, relief="solid")
        self.box1 = tkinter.Frame(self.right, borderwidth=2, relief="solid")
        self.box2 = tkinter.Frame(self.right, borderwidth=2, relief="solid")

        self.map_field = tkinter.Canvas(self.container, width=self.wind_wid + self.pixels_per_tile, height=self.wind_hei  + self.pixels_per_tile, bg='black')
        self.map_field.bind("<ButtonPress-1>", self.on_click)
        self.map_field.bind('<Shift-Button-1>', self.on_shift_click)
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

            if(not len(args)):
                return

            if(args[0] == "Spawn" and len(args) >= 4):
                if(args[1] in atoms_by_name and self.cur_world.coords_sanitized(int(args[2]), int(args[3]))):
                    if(len(args) > 4):
                        additional_args = []
                        for arg in args[4:len(args)]:
                            additional_args.append(arg)
                        text_to_path(args[1])(self.cur_world.get_turf(int(args[2]), int(args[3])), *additional_args)
                    else:
                        text_to_path(args[1])(self.cur_world.get_turf(int(args[2]), int(args[3])))

            elif(args[0] == "Show" and len(args) == 3):
                if(self.cur_world.coords_sanitized(int(args[1]), int(args[2]))):
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
                if(not self.icon_update and not self.icon_updating):
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

    def on_click(self, event):
        x_ = int(round(event.x / self.pixels_per_tile - 1))
        y_ = int(round(event.y / self.pixels_per_tile - 1))
        self.cur_world.Clicked(self, x_, y_, mods=["from_world"])

    def on_shift_click(self, event):
        x_ = int(round(event.x / self.pixels_per_tile - 1))
        y_ = int(round(event.y / self.pixels_per_tile - 1))
        self.cur_world.Clicked(self, x_, y_, mods=["from_world","shift"])

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

threading.Thread(target=master_controller).start()  # Controller start up.

GUI = Game_Window(The_Map)  # Opening the gui window.
