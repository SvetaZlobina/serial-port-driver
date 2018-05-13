import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk


class ChatPage(tk.Frame):
    RELOAD_RATE = 5000
    MSG_LIMIT = 50
    # USER_A_NAME = 'YOU      '
    # USER_B_NAME = 'COLLEAGUE'
    COLOR_BACK = '#FDF6F6'
    COLOR_BUTTON = '#E9AFCE'
    BUTTON_WIDTH = 20
    BUTTON_HEIGHT = 2
    BUTTON_FONT = 'arial 14'


    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, background=self.COLOR_BACK)
        self.controller = controller
        self.msg_entry_str = tk.StringVar()

        label = tk.Label(self, text='Содержимое получаемого файла', font=controller.title_font, background=self.COLOR_BACK)
        text = tk.Text(self, name='!text', height=30, width=90)
        scrbar = tk.Scrollbar(self, command=text.yview)
        # entry = tk.Entry(self, textvariable=self.msg_entry_str)
        # msg_btn = tk.Button(self, text="Отправить сообщение", command=self.send_msg, name='!button')
        #self.img = Image.open("exit.png")
        #eimg = ImageTk.PhotoImage(self.img)
        file_btn = tk.Button(self, width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, font=self.BUTTON_FONT,
                             text="Отправить файл", command=self.send_file, name='!button2', background=self.COLOR_BUTTON)
        clean_btn = tk.Button(self, width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, font=self.BUTTON_FONT,
                              text="Очистить экран", name='!clean_btn', background=self.COLOR_BUTTON)
        pause_btn = tk.Button(self, width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, font=self.BUTTON_FONT,
                              text="Пауза", name='!pause_btn', background=self.COLOR_BUTTON)

        label.grid(row=0, column=0, sticky='n', pady=2)
        text.grid(row=1, column=0, padx=10)
        scrbar.grid(row=1, column=1, sticky='nsew', padx=2)
        file_btn.grid(row=1, column=2, padx=5, sticky='s')
        clean_btn.grid(row=1, column=2, padx=5, sticky='n')
        pause_btn.grid(row=1, column=2, padx=5)

        # self.init_text()

        self.check_received()

    # def init_text(self):
    #     text = self.children['!text']
    #     # text.insert(tk.INSERT, 'YOU      : Hello World\n')
    #     # text.insert(tk.INSERT, 'COLLEAGUE: Hello you too\n')
    #     text.config(state=tk.DISABLED)
    #     # text.tag_configure('tag_left', justify='left')
    #     # text.tag_configure('tag_right', justify='right')
    #     sb = self.children['!scrollbar']
    #     text['yscrollcommand'] = sb.set

    # def send_msg(self):
    #     msg = self.msg_entry_str.get()
    #     if not msg:
    #         return
    #     self.disable_buttons()
    #     if len(msg) > self.MSG_LIMIT:
    #         messagebox.showwarning('Внимание!', 'Длина сообщения ({}) должна быть меньше {} символов'.format(
    #             len(msg), self.MSG_LIMIT))
    #         self.activate_buttons()
    #         return
    #     try:
    #         self.controller.app_layer.send_msg(msg)
    #     except self.controller.app_layer.FailedSend as e:
    #         messagebox.showwarning('Ошибка', "Не удалось отправить сообщение.")
    #         self.activate_buttons()
    #         return
    #     self.show_applayer_msg('A', msg)
    #     self.msg_entry_str.set('')
    #     self.activate_buttons()
    #     return

    def send_file(self):
        fname = filedialog.askopenfilename(title='Файл для отправки')
        if not fname:
            return
        try:
            self.disable_buttons()
            self.controller.app_layer.send_file_propose(fname)
        except self.controller.app_layer.FailedSend as e:
            messagebox.showwarning('Ошибка', "Не удалось отправить запрос на передачу файла.")
            self.activate_buttons()
            return

    def check_received(self):
        try:
            sender, message = self.controller.app_layer.check_received()
            if message:
                self.show_applayer_msg(sender, message)
                self.activate_buttons()
        except self.controller.app_layer.FileNotAcknowledged as e:
            messagebox.showinfo('Передача файла', '{} отказал в получении файла {}'.format(
                self.USER_B_NAME, self.controller.app_layer.short_fname(e.message)))
            self.activate_buttons()
        except self.controller.app_layer.FileProposal as e:
            fname = e.message
            if messagebox.askyesno('Получение файла', 'Принять файл {}?'.format(
                    self.controller.app_layer.short_fname(fname))):
                save_dir_name = filedialog.askdirectory(title='Выберите папку для сохранения файла')
                self.disable_buttons()
                self.controller.app_layer.send_file_ack(fname)
            else:
                self.controller.app_layer.send_file_nak(fname)
                messagebox.showinfo('Получение файла', "Вы отказались принять файл {}".format(
                    self.controller.app_layer.short_fname(fname)))
                self.activate_buttons()
        except self.controller.app_layer.FailedSend as e:
            messagebox.showinfo('Внимание', "Не удалось отправить файл.")
            self.activate_buttons()
        self.after(self.RELOAD_RATE, self.check_received)

    def show_applayer_msg(self, sender, msg):
        sender_mapping = {'A': self.USER_A_NAME, 'B': self.USER_B_NAME}
        sender = sender_mapping[sender]
        if msg:
            self.print_msg(sender, msg)

    def print_msg(self, sender, txt):
        text_field = self.children['!text']
        text_field.config(state=tk.NORMAL)
        text_field.insert(tk.INSERT,  '{}: {}\n'.format(sender, txt))
        text_field.config(state=tk.DISABLED)

    def disable_buttons(self):
        # self.children['!button'].config(state="disabled")
        self.children['!button2'].config(state="disabled")

    def activate_buttons(self):
        # self.children['!button'].config(state="active")
        self.children['!button2'].config(state="active")
