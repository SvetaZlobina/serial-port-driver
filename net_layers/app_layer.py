import os
import time


class AppLayer:
    msg_types = {'FILE': b'f',
                 'MSG': b'm',
                 'FILE_END': b'l',
                 'FILE_PROPOSE': b'p',
                 'FILE_ACK': b'a',
                 'FILE_NAK': b'n'}
    MSG_TYPE_LEN = 1    # Длина поля типа сообщения в байтах
    MSG_SIZE_LEN = 1    # Длина поля размера сообщения в байтах
    FNAME_SIZE_LEN = 1  # Длина поля размера названия файла в байтах
    DATA_SIZE_LEN = 4   # Длина поля размера данных в сообщении в байтах

    def __init__(self, datalink_layer):
        self.dl_layer = datalink_layer
        self.save_dir_name = '.'
        self.text_buffer = ''
        self.status = 'Free'

    def check_received(self):
        """
        Проверка, было ли получено какое-либо сообщение на канальном уровне.
        :return: само сообщениие в utf-8
        """
        if self.status != 'Free':
            return None
        bytes_str = self.dl_layer.check_received()
        if bytes_str is None:
            return None

        msg_type = self._deform_message(bytes_str)['msg_type']
        if msg_type not in self.msg_types.values():
            raise ValueError("Received unknown message type. It's {}".format(msg_type))

        if msg_type == self.msg_types['MSG']:
            return self.receive_msg(bytes_str)
        elif msg_type == self.msg_types['FILE_PROPOSE']:
            return self.receive_file_proposal(bytes_str)
        elif msg_type == self.msg_types['FILE']:
            return self.receive_file(bytes_str)
        elif msg_type == self.msg_types['FILE_END']:
            return self.receive_file_completely(bytes_str)
        elif msg_type == self.msg_types['FILE_ACK'] or msg_type == self.msg_types['FILE_NAK']:
            return self.send_file(bytes_str)
        else:
            raise ValueError("Don't know how to process {} at app_layer.check_received".format(msg_type))

    def send_file_propose(self, fname):
        """
        Отправление сообщения с предложением принять файл.
        :param fname: абсолютное имя файла
        :return:
        """
        self._send_message(self.msg_types['FILE_PROPOSE'], fname=fname)

    def receive_file_proposal(self, bytes_str):
        """
        Получение и обработка предложения принять файл.
        С помощью исключения FileProposal сообщение "Принять файл или отказаться" передаётся в интерфейс приложения
        :param bytes_str: Строка с предложением
        :return:
        """
        fname = self._deform_message(bytes_str)['fname']
        raise self.FileProposal(fname)

    def send_file_ack(self, fname, save_dir_name):
        """
        Передача сообщения с согласием принять файл.
        :param fname: Абсолютное имя файла
        :param save_dir_name: Имя папки для сохранения полученного файла
        :return:
        """
        self.save_dir_name = save_dir_name
        self._send_message(self.msg_types['FILE_ACK'], fname=fname)

    def send_file_nak(self, fname):
        """
        Передача сообщения с отказом принять файл
        :param fname: Абсолютное имя файла
        :return:
        """

        self._send_message(self.msg_types['FILE_NAK'], fname=fname)

    def send_msg(self, msg):
        """
        Передача "сообщения", в смысле сообщения в чате
        :param msg: текст "сообщения"
        :return:
        """
        self._send_message(self.msg_types['MSG'], data=msg)

    def receive_msg(self, bytes_str):
        """
        Получение "сообщения", в смысле сообщения в чате
        :param bytes_str: данные из канального уровня
        :return: кортеж (отправитель, текст сообщения)
        """
        self.status = 'Receiving message'
        msg = self._deform_message(bytes_str)['msg']
        self.status = 'Free'
        return msg

    def send_file(self, bytes_str):
        """
        Отправка файла через сеть.
        :param bytes_str: строка с согласием или отказом принять файл от другого пользователя
        :return: сообщение об отправке файла
        """
        msg_type, fname = [self._deform_message(bytes_str)[x] for x in ['msg_type', 'fname']]
        if msg_type == self.msg_types['FILE_NAK']:
            raise self.FileNotAcknowledged(fname)
        try:
            with open(fname, 'rb') as f:
                for line in f:
                    if self.dl_layer.is_paused:
                        # curr_position = f.tell()
                        while self.dl_layer.is_paused:
                            print('sending is paused')
                            msg  = self.dl_layer.check_received()
                            time.sleep(1)
                    print('line to send:', line.decode('utf-8'))
                    self._send_message(self.msg_types['FILE'], fname=self.short_fname(fname), data=line)
        except Exception as e:
            print("Error trying to read file before sending.\n_Particular error is {}".format(e.args))
            raise self.FailedSend(e.args)

        self._send_message(self.msg_types['FILE_END'], fname=self.short_fname(fname))

        return_str = '### Файл {} успешно отправлен ###'.format(self.short_fname(fname))
        return bytes(return_str, 'utf-8')

    def pause_receiving_file(self):
        '''
        Приостановка получения файла
        :return:
        '''

        self.dl_layer.is_paused = True

    def resume_receiving_file(self):
        '''
        Продолжение получения файла
        :return:
        '''

        self.dl_layer.is_paused = False
        self.dl_layer.send_rsm()

    def receive_file(self, bytes_str):
        """
        Получение файла из сети.
        :param bytes_str: Строка из канального уровня.
        :return: кортеж (отправитель "В", сообщение о получении файла)
        """
        self.status = 'Receiving file'

        print('bytes before deroming:', bytes_str)

        fname, data = [self._deform_message(bytes_str)[x] for x in ['fname', 'data']]

        print('fname after deforming:', fname)
        print('data after deforming:', data)
        # print('data in receive_file:', data.decode('utf-8'))
        if os.path.exists(os.path.join(self.save_dir_name, fname)):
            with open(os.path.join(self.save_dir_name, fname), 'ab') as f:
                f.write(data)
        else:
            with open(os.path.join(self.save_dir_name, fname), 'wb') as f:
                f.write(data)

        self.status = 'Free'

        if self.dl_layer.is_paused:
            self.text_buffer = data
            return None
        else:
            if self.text_buffer != '':
                data = self.text_buffer + data
                self.text_buffer = ''
                return data
            else:
                return data

    def receive_file_completely(self, bytes_str):
        '''
        Получение сообщения о конце файла
        :param bytes_str:
        :return:
        '''

        self.status = 'Receiving file'

        fname = self._deform_message(bytes_str)['fname']
        self.status = 'Free'

        return_str = '\n### Файл {} полностью принят и сохранён ###\n'.format(fname)
        return bytes(return_str, 'utf-8')

    def set_connection(self, port_name):
        """
        Установка соединения с заданным портом
        :param port_name: имя порта для подключения
        :return: результат подключения. None - если всё хорошо
        """
        return self.dl_layer.set_connection(port_name)

    @staticmethod
    def short_fname(fname):
        """
        Генерация "короткого" относительного пути файла
        :param fname: абсолютный путь к файлу
        :return: относительный путь к файлу
        """
        return fname.split('/')[-1]

    def _send_message(self, msg_type, fname=None, data=None):
        """
        Общий алгоритм для отправки сообщения через сеть.
        :param msg_type: тип сообщения
        :param fname: абсолютный путь к файлу, если требуется
        :param data: данные для передачи, если требуются
        :return:
        """
        self.status = 'Sending {}'.format(filter(lambda k: self.msg_types[k] == msg_type, self.msg_types))
        if data:
            print('data before forming:', data)
        bytes_str = self._form_message(msg_type, fname=fname, data=data)
        print('bytes after forming:', bytes_str)
        # print('bytes after forming decoded:', bytes_str.decode('utf-8'))
        try:
            self.dl_layer.send_msg(bytes_str)
        except ConnectionError as e:
            self.status = 'Free'
            raise self.FailedSend(e.args)
        self.status = 'Free'

    def _form_message(self, msg_type, data=None, fname=None):
        """
        Обобщённое формирование сообщения на основе его типа и содержания
        :param msg_type: тип сообщения
        :param data: данные сообщения, если требуется
        :param fname: абсолютное имя файла, если требуется
        :return: сформированное сообщение для отправки через сеть
        """
        def form(data, bytes_size_len, to_encode=True):
            if data is None:
                raise ValueError('No data passed to form function in form_message')
            data_bytes = data.encode() if to_encode else data
            if len(data_bytes) > 256**bytes_size_len:
                raise OverflowError('Too large data to put its len into {} bytes'.format(bytes_size_len))
            data_bytes_len = len(data_bytes)
            return data_bytes_len.to_bytes(bytes_size_len, 'big') + data_bytes

        if msg_type == self.msg_types['FILE']:
            return msg_type + form(fname, self.FNAME_SIZE_LEN) + form(data, self.DATA_SIZE_LEN, to_encode=False)
        elif msg_type in [self.msg_types[x] for x in ['FILE_PROPOSE', 'FILE_ACK', 'FILE_NAK', 'FILE_END']]:
            return msg_type + form(fname, self.FNAME_SIZE_LEN)
        elif msg_type == self.msg_types['MSG']:
            return msg_type + form(data, self.MSG_SIZE_LEN)
        else:
            raise ValueError('Unknown message format. at app_layer.form_message')

    def _deform_message(self, message):
        """
        Извлечение полезной информации из сообщения
        :param message: исходное сообщение, полученное процедурой _form_message
        :return: словарь с полями:  msg_type - тип сообщения
                                    fname - название файла              (опционально)
                                    data - данные файла                 (опционально)
                                    msg - содержимое сообщения из чата  (опционально)
        """
        msg_type = message[0:self.MSG_TYPE_LEN]

        def parse(data, bytes_size_len, to_decode=True):
            if not data:
                raise ValueError("No data in parse function. Message is {}".format(message))
            data_len = int.from_bytes(data[0:bytes_size_len], 'big')
            parsed_data = data[bytes_size_len:data_len+bytes_size_len]
            parsed_data = parsed_data.decode() if to_decode else parsed_data
            return data_len+bytes_size_len, parsed_data

        result = {'msg_type': msg_type}
        if msg_type == self.msg_types['FILE']:
            fname_size, fname = parse(message[self.MSG_TYPE_LEN:], self.FNAME_SIZE_LEN)
            result['fname'] = fname
            result['data'] = parse(message[self.MSG_TYPE_LEN+fname_size:], self.DATA_SIZE_LEN, to_decode=False)[1]
        elif msg_type in [self.msg_types[x] for x in ['FILE_PROPOSE', 'FILE_ACK', 'FILE_NAK', 'FILE_END']]:
            result['fname'] = parse(message[self.MSG_TYPE_LEN:], self.FNAME_SIZE_LEN)[1]
        elif msg_type == self.msg_types['MSG']:
            result['msg'] = parse(message[self.MSG_TYPE_LEN:], self.MSG_SIZE_LEN)[1]
        else:

            raise ValueError('Unknown message type at app_layer.deform_message - {}\n'
                             'message is {}'.format(msg_type, message))
        return result

    class FileNotAcknowledged(Exception):
        """
        Особое исключение, если собеседник из чата отказывается принимать файл.
        Используется для передачи этой информации в интерфейс программы.
        """
        def __init__(self, message):
            self.message = message

    class FileProposal(Exception):
        """
        Особое исключение, если собеседник из чата предлагает получить файл.
        Используется для передачи этой информации в интерфейс программы.
        """
        def __init__(self, message):
            self.message = message

    class FailedSend(Exception):
        def __init__(self, message):
            self.message = message
