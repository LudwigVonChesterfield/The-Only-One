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


class Faction:
    name = ""  # I should really rename this to type, or use type instead.

    def __init__(self, creator):
        self.display_name = random.choice(["Holy ", "Sacred ", "Eternal ", "Benevolent ", "Victorious ", "Glorious ", "Mighty "]) + random.choice(["Guild ", "Faction ", "Unity ", "Family ", "Dominion ", "Empire ", "Den "]) + random.choice(["of ", "for ", "with "]) + random.choice(["Citizens", "People", "Royalties", "Them", "Members", "Creations", "Knights", "Farmers", "Lands"])
        # Try to guess why there is no grey, green or black in the list below.
        self.color = random.choice(["red", "blue", "yellow", "magenta", "cyan", "white", "pale green", "royal blue", "orange", "coral", "maroon", "pink", "brown", "gray20"])
        Globals.factions.append(self)
        self.members = [creator]
        self.relationships = {}

        for faction in Globals.factions:
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
        self.qdeling = True
        for member in self.members:
            member.faction = None
        self.members = []
        for relationship in self.relationships:
            relationship.relationships.pop(self)
        self.relationships = {}
        Globals.factions.remove(self)
        del self
