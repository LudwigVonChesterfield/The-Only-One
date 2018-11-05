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

        self.structures = sort_by_priority(self.parent.cur_world.get_tile_contents(self.x_coord, self.y_coord))

        self.wind.title(u'The Tile')
        self.wind_wid = int(round(4 * self.parent.pixels_per_tile))
        self.wind_hei = int(round(len(self.structures) * 5 * self.parent.pixels_per_tile))

        self.temp_map_field = tkinter.Canvas(self.wind, width=self.wind_wid, height=self.wind_hei, bg='black')
        self.temp_map_field.bind("<ButtonPress-1>", self.on_click)
        self.structure_icons = []

        #self.coordinates = self.temp_map_field.create_text(int(round(self.wind_wid / 2)), self.wind_wid - self.parent.pixels_per_tile, text="Coords: (%s, %s)" % (self.x_coord, self.y_coord), font='TkiFixedFont', fill="green")

        self.temp_map_field.pack()

    def qdel(self):
        self.structures = None
        super().qdel()

    def on_click(self, event):
            """Try-hard hack to make these objects clickable."""
            # I do know of operator precedence. I do know that I subtract 1 and not pixels_per_tile...
            # But can you blame me if it works?
            y_ = int(round(event.y / self.parent.pixels_per_tile - 1))
            if(y_ >= 0 and y_ < len(self.structures)):
                atom = self.structures[y_]
                atom.ClickedOn(self.parent, atom.x, atom.y)  # Cheap hack to get at least some x and y to be passed.

    def on_cycle(self):
        self.structures = sort_by_priority(self.parent.cur_world.get_tile_contents(self.x_coord, self.y_coord))

        for struc in self.structure_icons:
            self.temp_map_field.delete(struc)

        y = 0

        for structure in self.structures:
            icon = structure.get_icon()
            self.structure_icons.append(self.temp_map_field.create_text(int(round(self.wind_wid / 2)), int(round(y * self.parent.pixels_per_tile) + self.parent.pixels_per_tile), text="%s [%s]" % (icon["symbol"], structure.priority), font=icon["font"], fill=icon["color"]))
            y += 1

    def on_reopen(self, tag, x, y):
        self.x_coord = int(round(x / self.parent.pixels_per_tile))
        self.y_coord = int(round(y / self.parent.pixels_per_tile))

        self.saved_x = x
        self.saved_y = y
        self.wind.geometry("+%d+%d" % (self.parent.wind.winfo_x() + self.saved_x, self.parent.wind.winfo_y() + self.saved_y))
        #self.temp_map_field.itemconfigure(self.coordinates, text="Coords: (%s, %s)" % (self.x_coord, self.y_coord))

class Game_Window:
    default_pixels_per_tile = 16.4
    cur_world = None

    def __init__(self, world):
        self.icon_update = False
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

        self.left = tkinter.Frame(self.wind, borderwidth=2, relief="solid")
        self.right = tkinter.Frame(self.wind, borderwidth=2, relief="solid")
        self.container = tkinter.Frame(self.left, borderwidth=2, relief="solid")
        self.box1 = tkinter.Frame(self.right, borderwidth=2, relief="solid")
        self.box2 = tkinter.Frame(self.right, borderwidth=2, relief="solid")

        def on_click(event):
            x_ = int(round(event.x / self.pixels_per_tile - 1))
            y_ = int(round(event.y / self.pixels_per_tile - 1))
            self.cur_world.ClickedOn(self, x_, y_)

        self.map_field = tkinter.Canvas(self.container, width=self.wind_wid + self.pixels_per_tile, height=self.wind_hei  + self.pixels_per_tile, bg='black')
        self.map_field.bind("<ButtonPress-1>", on_click)
        self.map_field_overlays = {}
        self.icon_update = True

        self.cur_world.update_world_icons()

        self.chatlog = tkinter.Canvas(self.box1, width=int(round(self.wind_wid / 2)), height=self.wind_hei, bg = 'dark blue')
        self.chat = self.chatlog.create_text(int(round(self.wind_wid / 4)), int(round(self.wind_hei / 2)), width = int(round(self.wind_wid / 2)), text=log, fill = 'white', font = 'TkFixedFont 12')
        # Since it uses TkFixedFont 12, we divide by 12. Almost makes sense.
        self.chat_lenght = int(round(self.wind_wid / 48))

        self.command_field = tkinter.Entry(self.left, width=int(round(self.wind_wid / 8)))
        self.command_field.focus_set()

        def action():
            global to_sleep_time
            global freeze_time
            command = self.command_field.get()
            args = command.split()

            if(args[0] == "Spawn" and len(args) >= 4):
                if(args[1] in atoms_by_name):
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
                    to_sleep_time = 100
                    return

                to_sleep_time = max([0, to_sleep_time - 10])

            elif(args[0] == "Slower"):
                if(to_sleep_time == 100):
                    freeze_time = True
                    return

                to_sleep_time = min([100, to_sleep_time + 10])


        self.act_button = tkinter.Button(self.left, text="Act", width=int(self.wind_wid // 80), command=action)
        self.current_time = tkinter.Label(self.box2, text="Current Time: " + time_to_date(self.cur_world.time))

        self.left.pack(side="left", fill="both")
        self.right.pack(side="right", fill="both")
        self.container.pack(expand=True, padx=5, pady=5)
        self.box1.pack(expand=True, padx=10, pady=10)
        self.box2.pack(expand=True, padx=10, pady=10)

        self.map_field.pack()
        self.chatlog.pack()
        self.command_field.pack()
        self.act_button.pack()
        self.current_time.pack()

        def cycle():
            self.current_time.config(text="Current Time: " + time_to_date(self.cur_world.time))
            self.chatlog.itemconfigure(self.chat, text=log)

            for window_tag in self.child_windows:
                if(self.child_windows[window_tag].qdeling):
                    continue
                self.child_windows[window_tag].on_cycle()

            self.wind.after(1, cycle)

        cycle()

        self.wind.mainloop()

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

        coord = x_y_to_coord(x, y)

        if(not coord in self.map_field_overlays):
            self.map_field_overlays[coord] = []

        for icon in self.map_field_overlays[coord]:
            self.map_field.delete(icon)
        for icon in icons:
            self.map_field_overlays[coord].append(self.map_field.create_text(int(round(x * self.pixels_per_tile) + self.pixels_per_tile), int(round(y * self.pixels_per_tile) + self.pixels_per_tile), text=icon["symbol"], font=icon["font"], fill=icon["color"]))
