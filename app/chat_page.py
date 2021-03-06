import tkinter as tk
from tkinter import messagebox, filedialog


class ChatPage(tk.Frame):
    RELOAD_RATE = 2000
    MSG_LIMIT = 50
    COLOR_BACK = '#e1b4d3'
    COLOR_BUTTON = '#ba7ea7'
    BUTTON_WIDTH = 20
    BUTTON_HEIGHT = 2
    BUTTON_FONT = 'arial 14'

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, background=self.COLOR_BACK)
        self.controller = controller
        self.msg_entry_str = tk.StringVar()

        label = tk.Label(self, text='Содержимое получаемого файла',background=self.COLOR_BACK, font=controller.title_font)
        text = tk.Text(self, name='!text', height=35, width=85)
        scrbar = tk.Scrollbar(self, command=text.yview)
        # entry = tk.Entry(self, textvariable=self.msg_entry_str)
        # msg_btn = tk.Button(self, text="Отправить сообщение", command=self.send_msg, name='!button')
        file_btn = tk.Button(self, text="Отправить файл", width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT,
                             font=self.BUTTON_FONT,  background=self.COLOR_BUTTON, command=self.send_file, name='!button2')
        clean_btn = tk.Button(self, text="Очистить экран", width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT,  background=self.COLOR_BUTTON,
                              font=self.BUTTON_FONT, command=self.clear_text, name='!clean_btn')
        pause_btn = tk.Button(self, text="Пауза", width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, background=self.COLOR_BUTTON,
                              font=self.BUTTON_FONT, command=self.make_pause, name='!pause_btn')

        label.grid(row=0, column=0, sticky='n', pady=2)
        text.grid(row=1, column=0, padx=10)
        scrbar.grid(row=1, column=1, sticky='nsew', padx=2)
        file_btn.grid(row=1, column=2, padx=5, sticky='s')
        clean_btn.grid(row=1, column=2, padx=5, sticky='n')
        pause_btn.grid(row=1, column=2, padx=5)

        # self.init_text()

        self.check_received()

    def send_file(self):
        fname = filedialog.askopenfilename(title='Файл для отправки')
        if not fname:
            return
        try:
            self.disable_send()
            self.controller.app_layer.send_file_propose(fname)
        except self.controller.app_layer.FailedSend as e:
            messagebox.showwarning('Ошибка', "Не удалось отправить предложение об отправке файла.")
            self.activate_buttons()
            return

    def check_received(self):
        try:
            message = self.controller.app_layer.check_received()
            if message:
                self.show_msg(message)
                self.activate_buttons()
        except self.controller.app_layer.FileNotAcknowledged as e:
            messagebox.showinfo('Отправка файла', 'В принятии файла {} отказано'
                                .format(self.controller.app_layer.short_fname(e.message)))
            self.activate_buttons()
        except self.controller.app_layer.FileProposal as e:
            fname = e.message
            if messagebox.askyesno('Получение файла', 'Принять файл {}?'.format(
                    self.controller.app_layer.short_fname(fname))):
                save_dir_name = filedialog.askdirectory(title='Выберите папку для сохранения файла')
                self.disable_send()
                self.controller.app_layer.send_file_ack(fname, save_dir_name)
            else:
                self.controller.app_layer.send_file_nak(fname)
                messagebox.showinfo('Получение файла', "Вы отказались принять файл {}".format(
                    self.controller.app_layer.short_fname(fname)))
                self.activate_buttons()
        except self.controller.app_layer.FailedSend as e:
            messagebox.showinfo('Внимание', "Не удалось отправить файл.")
            self.activate_buttons()
        self.after(self.RELOAD_RATE, self.check_received)

    def show_msg(self, msg):
        if msg:
            self.print_msg(msg)

    def print_msg(self, txt):
        text_field = self.children['!text']
        text_field.config(state=tk.NORMAL)
        print('bytes to print: ', txt)
        try:
            text_field.insert(tk.INSERT,  '{}'.format(txt.decode('utf-8')))
        except Exception as e:  # если вдруг случилась какая-то ошибка с декодированием
            print('Decoding exception:', e.args)
            pass
        text_field.config(state=tk.DISABLED)

    def make_pause(self):
        pause_btn = self.children['!pause_btn']
        if pause_btn['text'] == 'Пауза':  # если передач а сообщения активна
            pause_btn.config(text='Продолжить')
            self.controller.app_layer.pause_receiving_file()
        else:  # если была пауза в передаче
            pause_btn.config(text='Пауза')
            self.controller.app_layer.resume_receiving_file()

    def disable_send(self):
        # self.children['!button'].config(state="disabled")
        self.children['!button2'].config(state="disabled")

    def activate_buttons(self):
        # self.children['!button'].config(state="active")
        self.children['!button2'].config(state="active")

    # def disable_pause(self):
    #     self.children['!clean_btn'].config(state="active")

    def clear_text(self):
        pass
        text_field = self.children['!text']
        text_field.config(state=tk.NORMAL)
        text_field.delete('1.0', tk.END)
        text_field.config(state=tk.DISABLED)


