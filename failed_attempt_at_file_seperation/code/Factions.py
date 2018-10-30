from code.Globals import *

import random

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
