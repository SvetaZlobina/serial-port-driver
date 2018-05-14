from net_layers.physical_layer import PhysicalLayer
from net_layers.data_link_layer import DataLinkLayer
from net_layers.app_layer import AppLayer
from app.app import App
from app.parameters_page import ParametersPage
from app.chat_page import ChatPage

import serial

if __name__ == "__main__":
    ph_layer = PhysicalLayer()
    dl_layer = DataLinkLayer(ph_layer)
    ap_layer = AppLayer(dl_layer)

    app = App(ap_layer)
    app.geometry(newGeometry="%dx%d%+d%+d" % (900, 600, 300, 10))
    app.resizable(False, False)
    app.title('Курсовая работа по сетям: Злобина, Заровная, Кучаева')
    app.mainloop()

    # port1 = serial.Serial('/dev/ttyS20')
    # print('Подключение к порту:', port1.name)
    #
    # port2 = serial.Serial('/dev/ttyS21')
    # print('Подключение к порту:', port2.name)
    #
    # port1.write(b'Hello')
    # line = port2.read(5)
    # print(line)


    # with open('example.txt', 'rb') as f:
    #     for line in f:
    #         print(line.decode('utf-8'))
    # for i in range(len(data)//21 + 1):
    #     print(data[i * 21:(i + 1) * 21])
    #     print(data[i*21:(i+1)*21].decode('utf-8'))
                # self._send_message(self.msg_types['FILE'], fname=self.short_fname(fname), data=data)
    # except Exception as e:
    #     print("Error trying to read file before sending.\n_Particular error is {}".format(e.args))
    #     raise self.FailedSend(e.args)

