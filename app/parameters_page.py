import tkinter as tk


class ParametersPage(tk.Frame):
    COLOR_BACK = '#e1b4d3'
    COLOR_BUTTON = '#ba7ea7'
    BUTTON_WIDTH = 25
    BUTTON_HEIGHT = 2

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, background=self.COLOR_BACK)
        self.controller = controller
        label = tk.Label(self, text="Параметры соединения", font=controller.title_font, background=self.COLOR_BACK)
        label.pack(side="top", fill="x", pady=10)

        self.port_name_string = tk.StringVar()
        self.port_name_string.set('')
        self.status_string = tk.StringVar()

        l1 = tk.Label(self, text="Подключаемый порт", font='arial 12', background=self.COLOR_BACK)
        w1 = tk.Entry(self, bd=5, width=45, textvariable=self.port_name_string)
        l3 = tk.Label(self, background=self.COLOR_BACK)
        b1 = tk.Button(self, text='Подключение', bg=self.COLOR_BUTTON,
                       width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, font='arial 18', command=self.set_connection)
        l2 = tk.Label(self, text="Состояние: введите название порта", textvariable=self.status_string, background=self.COLOR_BACK)

        '''for elem, coord in [(label,    (0, 0)),
                            (l1,     (1, 0)),
                            (w1,   (2, 0)),
                            (b1,    (3, 0))]:
            elem.grid(row=coord[0], column=coord[1], sticky="nsew", padx=2, pady=2)'''
        l1.pack()
        w1.pack()
        l3.pack()
        b1.pack()
        l2.pack()

    def set_connection(self):
        print('port_name_string:', self.port_name_string.get())
        res = self.controller.app_layer.set_connection(self.port_name_string.get())
        if res is None:
            self.status_string.set('Установлено соединение с портом {}'.format(self.port_name_string.get()))
            self.controller.frames["ChatPage"].activate_buttons()
            print('Установлено соединение с портом {}'.format(self.port_name_string.get()))
            self.controller.frames['ChatPage'].tkraise()
        if res is not None:
            self.status_string.set(res)
            self.controller.frames["ChatPage"].disable_buttons()
            print(res)
