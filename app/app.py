import tkinter as tk
from tkinter import font as tkfont

from .parameters_page import ParametersPage
from .chat_page import ChatPage


class App(tk.Tk):
    def __init__(self, app_layer):
        tk.Tk.__init__(self)
        self.app_layer = app_layer

        self.title_font = tkfont.Font(family='Arial', size=24, weight="bold")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (ParametersPage, ChatPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.frames["ChatPage"].disable_send()

        menu_bar = tk.Menu(self)
        menu_bar.add_command(label='Параметры порта', command=lambda: self.show_frame("ParametersPage"))
        menu_bar.add_command(label='Обмен файлами', command=lambda: self.show_frame("ChatPage"))
        # menu_bar.add_separator()
        # menu_bar.add_command(label='Выход', command=self.quit)
        self.config(menu=menu_bar)

        self.show_frame("ParametersPage")

    def show_frame(self, page_name):
        # print('showing off', page_name)
        frame = self.frames[page_name]
        frame.tkraise()


