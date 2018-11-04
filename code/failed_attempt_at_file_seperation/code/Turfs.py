from code.Atoms import *
from code.Funcs import *

class Turf(Atom):
    priority = 1
    allowed_contents = []
    size = 20 # Turfs are really big.

    def generate_contents(self):
        return text_to_path(pick_weighted(self.allowed_contents))

    def crumble(self, severity):
        return False

class Plains(Turf):
    symbol = "_"
    name = "Plains"
    default_description = "A plain sight, not much to see."
    allowed_contents = {"Nothing" : 100, "Tall_Grass" : 30, "Forest" : 5}

class Hills(Turf):
    symbol = "-"
    name = "Hills"
    default_description = "Hilly terrain. Up and down..."
    allowed_contents = {"Nothing" : 100, "Forest" : 1}

class Rocky(Turf):
    symbol = "="
    name = "Rocky"
    default_description = "Hills, but with a slight chance of rocks being around."
    allowed_contents = {"Nothing" : 100, "Mountain" : 10, "Iron_Deposit" : 3, "Gold_Deposit" : 1, "Forest" : 1}

class Water(Turf):
    symbol = "~"
    name = "Water"
    default_description = "Wet. Moist. Is a fluid."
    obstruction = True
