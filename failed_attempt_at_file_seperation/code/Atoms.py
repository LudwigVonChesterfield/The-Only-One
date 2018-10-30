from code.Funcs import *
from code.Coords import *
from code.Globals import *

class Atom:
    symbol = ""
    priority = 0

    name = ""
    default_description = "I am an Atom."

    obstruction = False
    size = 0

    needs_processing = False

    action_time = 0

    def __init__(self, loc, x, y):
        self.x = - 1
        self.y = -1
        self.loc = None
        self.world = loc.get_world()
        self.contents = []
        self.move_atom_to(loc, x, y)
        self.last_action = self.world.time
        self.description = self.default_description
        self.display_name = self.name  # Since "name" is more of a type, really.
        self.integrity = self.size
        self.qdeling = False
        atoms.append(self)
        if(self.needs_processing):
            self.world.process_atoms.append(self)

    def overrideClick(self, GUI, x_, y_):
        if(self.canClickOn(GUI, x_, y_)):
            return self.ClickedOn(GUI, x_, y_)
        return False

    def canClickOn(self, GUI, x_, y_):  # Change this in case of special behavior.
        return False

    def ClickedOn(self, GUI, x_, y_):
        self.Examinated(GUI)  # Default behavior of clicking on it, is just this.

    def Examinated(self, GUI):
        global log
        log = log + self.getExamineText() + "\n"

    def getExamineText(self):
        return str(self.symbol) + " [" + self.display_name + "] " + self.default_description

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
                    if(struc.crumble(self.size)):
                        continue
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
        if(get_distance(self.x, self.y, x, y) > sqrt_2):  # sqrt_2 = math.sqrt(2), because diagonal tiles?
           return False
        self.move_atom_to(world, x, y)
        return True

    def move_towards_to(self, world, x, y):
        dummy_moves = 3  # Set this to something higher if you want some wacky shit.
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

    def get_task(self, city):
        return None  # If this returns None, consider skipping trying to get task from this.

    def react_to_attack(self, attacker):
        """Returns True if attack was parried, False otherwise."""
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

class Moveable(Atom):
    obstruction = False