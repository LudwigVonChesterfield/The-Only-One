import math


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
