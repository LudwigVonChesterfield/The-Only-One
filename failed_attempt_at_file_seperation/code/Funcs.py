import code.Globals

import random
import copy

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

def sort_by_priority(to_sort: list):
    if(not to_sort):  # Safety measures.
        return []  # Safety measures.
    atom_list = copy.deepcopy(to_sort)
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

def text_to_path(text):
    return Globals.atoms_by_name[text]
