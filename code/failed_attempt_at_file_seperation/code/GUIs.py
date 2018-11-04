import code.Globals
from code.Funcs import *
from code.Time import *

import tkinter

class Game_Window:
    default_pixels_per_tile = 16.4
    wind = None
    cur_world = None

    def __init__(self, world):
        self.showing_turf = None  # Is set to the showing turf window upon showing the turf.
        self.showing_turf_content = None
        self.showing_turf_strucs = []
        self.showing_turf_rel_x = 0
        self.showing_turf_rel_y = 0

        self.pixels_per_tile = self.default_pixels_per_tile

        self.cur_world = world
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
            x_ = int(round(event.x // self.pixels_per_tile))
            y_ = int(round(event.y // self.pixels_per_tile))
            self.cur_world.ClickedOn(self, x_, y_)

        self.map_field = tkinter.Canvas(self.container, width=self.wind_wid, height=self.wind_hei, bg='black')
        self.map_field.bind("<ButtonPress-1>", on_click)
        self.map_bg = self.map_field.create_text(int(round(self.wind_wid / 2)), int(round(self.wind_hei / 2)), text=self.cur_world.world_to_string(), fill = 'green', font = 'TkFixedFont')
        self.chatlog = tkinter.Canvas(self.box1, width=int(round(self.wind_wid / 2)), height=self.wind_hei, bg = 'dark blue')
        self.chat = self.chatlog.create_text(int(round(self.wind_wid / 4)), int(round(self.wind_hei / 2)), width = int(round(self.wind_wid / 2)), text=log, fill = 'white', font = 'TkFixedFont 12')
        # Since it uses TkFixedFont 12, we divide by 12. Almost makes sense.
        self.chat_lenght = int(round(self.wind_wid / 48))

        self.command_field = tkinter.Entry(self.left, width=int(round(self.wind_wid / 8)))
        self.command_field.focus_set()

        def action():
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
                    to_sleep_chance = 100
                    return

                to_sleep_chance = max([1, to_sleep_chance - 10])

            elif(args[0] == "Slower"):
                if(to_sleep_chance == 100):
                    freeze_time = True
                    return

                to_sleep_chance = min([100, to_sleep_chance + 10])


        self.act_button = tkinter.Button(self.left, text="Act", width=int(self.wind_wid // 80), command=action)
        self.current_time = tkinter.Label(self.box2, text="Current Time: " + time_to_date(self.cur_world.time))

        self.left.pack(side="left", expand=True, fill="both")
        self.right.pack(side="right", expand=True, fill="both")
        self.container.pack(expand=True, fill="both", padx=5, pady=5)
        self.box1.pack(expand=True, fill="both", padx=10, pady=10)
        self.box2.pack(expand=True, fill="both", padx=10, pady=10)

        self.map_field.pack()
        self.chatlog.pack()
        self.command_field.pack()
        self.act_button.pack()
        self.current_time.pack()

        def cycle():
            self.current_time.config(text="Current Time: " + time_to_date(self.cur_world.time))
            self.map_field.itemconfigure(self.map_bg, text=self.cur_world.world_to_string())
            self.chatlog.itemconfigure(self.chat, text=self.get_log())
            self.wind.after(1, cycle)

        cycle()

        self.wind.mainloop()

    def move_me(self, event):
        """GUI func called, when the window moves."""
        if(self.showing_turf != None):
            x_temp = self.wind.winfo_x() + self.showing_turf_rel_x
            y_temp = self.wind.winfo_y() + self.showing_turf_rel_y
            self.showing_turf.master.geometry("+%d+%d" % (x_temp, y_temp))

    def get_log(self):
        global log
        print(log)
        return log
