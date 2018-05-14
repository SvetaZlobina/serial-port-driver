import re
import time
import logging

from .physical_layer import handler

logger = logging.getLogger(__name__)
logger.addHandler(handler)


class DataLinkLayer:
    FD = b'\x7e'  # Начало, конец кадра
    FE = b'\xcd'  # Для бит стаффинга
    # тип кадра
    frame_types = {
        'INF':  b'\x01',  # информационный кадр
        'ACK':  b'\x98',  # положительная квитанция
        'NAK':  b'\xab',  # отрицательная квитанция
        'END':  b'\xb5',  # конец передачи
        'PSE':  b'\x5c',  # подавление источника (пауза)
    }
    # MAX_FDATA_LEN = 256     # максимальное количество данных в кадре
    MAX_FDATA_LEN = 40      # при цикл. кодировании получится в 2 раза больше
    # MAX_TRIES_NUM = 5       # максимальное количество попыток получения и передачи кадра
    MAX_TRIES_NUM = 10       # максимальное количество попыток получения и передачи кадра
    TIMEOUT_WAIT = 5.0      # время на получение первого кадра сообщения, когда он нам очень нужен
    TIMEOUT_LOOK = 0.25      # время на получение первого кадра сообещния, когда сообщения может и не быть

    def __init__(self, phys_layer):
        self.phys_layer = phys_layer
        self.status = 'Free'

    def check_received(self):
        """
        Проверяем, есть ли в физическом канале байты. Если да, то начинаем собирать кадр.
        В итоге в поле self.message может появиться принятое сообщение
        :return: Принятое сообщение
        """
        if self.status != 'Free':
            return None

        msg = None
        self.status = 'Receiving'
        # try:
        print('Checking received')
        msg = self.receive_msg(timeout=self.TIMEOUT_LOOK)

        self.status = 'Free'

        return msg

    def send_msg(self, msg):
        """
        Отправляет сообщение, полученное извне в физический канал.
        :param msg: Сообщение для отправки
        :return: Булевое значение. Успешно передано сообщение или нет
        """
        # try:
        self.status = 'Sending'
        data = msg

        max_f_l = self.MAX_FDATA_LEN
        # Если в кадре окажутся только данные с '~'==FD, то кол-во байтов в нём после байт-стаффинга увеличится вдвое
        half_f_l = max_f_l // 2 #40//2=20
        # Разбиваем данные по кадрам
        rem = len(data) % half_f_l #12%20=12
        frame_datas = [data[idx:idx + half_f_l] for idx in range(0, len(data) - rem, half_f_l)]
        if rem != 0:
            frame_datas.append(data[-rem:])
        # Байт-стаффим
        frame_datas = [self._byte_staff(f) for f in frame_datas]
        # Формируем кадры
        frames = [self._form_frame(self.frame_types['INF'], fd) for fd in frame_datas]
        # Добавляем конечный кадр и отправляем
        frames.append(self._form_frame(f_type=self.frame_types['END']))
        # отправка кадра
        self._send_frames(frames)
        self.status = 'Free'
        return True
        #except self.ConnectionError:  # Can't send a message
            #return False

    # def receive_msg_by_frame(self, timeout=None):
    #
    #     # frames = []
    #
    #     for n_try in range(self.MAX_TRIES_NUM):
    #         try:
    #             frame = None
    #             if len(frames) == 0:  # пытаемся получить первый кадр
    #                 frame = self._receive_frame(timeout=timeout)
    #             else:
    #                 frame = self._receive_frame(timeout=self.TIMEOUT_WAIT)
    #             frame_type = self._deform_frame(frame)[0]  # если кадр можно расформировать - значит он не битый
    #             print('got good frame at receive_msg')
    #             print('_good frame is {}'.format(frame))
    #             if frame_type in [self.frame_types['ACK'], self.frame_types['NAK']]:
    #                 print("Getting ack and nak. But we don't suppose to")
    #                 # пропускаем этот кадр, т.е. не отправляем ack и не добавляем его в сообщение
    #                 break
    #             self._send_ack()
    #             break
    #         except self.NoByteError as e:
    #             # если просто интересовались, есть ли сообщение в канале
    #             if len(frames) == 0 and n_try == 0 and timeout == self.TIMEOUT_LOOK:
    #                 self.status = 'Free'
    #                 return None
    #             print('NoByteError in receive_msg')
    #             self._send_nak()
    #         except self.BrokenFrameError as e:
    #             print('got broken frame in receive_msg')
    #             print('_broken frame is {}\n_particular error is {}'.format(
    #                 frame if frame else 'undefined', e.message))
    #             self._send_nak()
    #     else:
    #         print('Cant receive a frame in receive_msg_by_frame')
    #         self.status = 'Free'
    #         return None
    #     if self._deform_frame(frame)[0] not in [self.frame_types['ACK'], self.frame_types['NAK']]:
    #         frames.append(frame)

    def receive_msg(self, first_frame=None, timeout=None):
        """
        Запрос сообщения из канала.
        В отличие от check_received мы точно знаем, что сообщение должно придти. // Раньше так было
        После считывания, сообщение оказывается в поле self.message
        :param first_frame: Первый кадр сообщения. Мог быть считан в других функциях
        :return: Полученное сообщение
        """
        self.status = 'Receiving'

        frames = [first_frame] if first_frame else []

        while len(frames) == 0 or self._deform_frame(frames[-1])[0] != self.frame_types['END']:
            for n_try in range(self.MAX_TRIES_NUM):
                try:
                    frame = None
                    if len(frames) == 0:  # пытаемся получить первый кадр
                        frame = self._receive_frame(timeout=timeout)
                    else:
                        frame = self._receive_frame(timeout=self.TIMEOUT_WAIT)
                    frame_type = self._deform_frame(frame)[0]  # если кадр можно расформировать - значит он не битый
                    print('got good frame at receive_msg')
                    print('_good frame is {}'.format(frame))
                    if frame_type in [self.frame_types['ACK'], self.frame_types['NAK']]:
                        print("Getting ack and nak. But we don't suppose to")
                        # пропускаем этот кадр, т.е. не отправляем ack и не добавляем его в сообщение
                        break
                    self._send_ack()
                    break
                except self.NoByteError as e:
                    # если просто интересовались, есть ли сообщение в канале
                    if len(frames) == 0 and n_try == 0 and timeout == self.TIMEOUT_LOOK:
                        self.status = 'Free'
                        return None
                    print('NoByteError in receive_msg')
                    self._send_nak()
                except self.BrokenFrameError as e:
                    print('got broken frame in receive_msg')
                    print('_broken frame is {}\n_particular error is {}'.format(
                        frame if frame else 'undefined', e.message))
                    self._send_nak()
            else:
                print('Cant receive a frame in receive_msg')
                self.status = 'Free'
                return None
            if self._deform_frame(frame)[0] not in [self.frame_types['ACK'], self.frame_types['NAK']]:
                frames.append(frame)

        # Если получили лишний конечный кадр от пред. сообщения
        if self._deform_frame(frames[0])[0] == self.frame_types['END']:
            print('Got extra end frame')
            self.status = 'Free'
            return None
        frames = frames[:-1]  # Убирем кадр END
        if sum([self._deform_frame(f)[0] != self.frame_types['INF'] for f in frames]) > 0:
            raise ValueError('NonInformational frames in receive_msg function')

        frames = [self._debyte_staff(f) for f in frames]

        data = b''.join([self._deform_frame(f)[1] for f in frames])
        self.status = 'Free'
        return data

    def _send_frames(self, frames):
        """
        Отправка кадров на физический уровень.
        :param frames: список кадров для отправки
        :return:
        """
        self.status = 'Sending'
        for idx, frame in enumerate(frames):
            for n_try in range(self.MAX_TRIES_NUM):
                print('sending frame {}'.format(frame))
                self.phys_layer.send_bytes(frame)
                #print('sending frame {}'.format(frame))
                try:
                    print('waiting for ack')
                    ack_frame = self._receive_frame()
                    frame_type = self._deform_frame(ack_frame)[0]
                    if frame_type == self.frame_types['ACK']:
                        print('got ack')
                        break
                    elif frame_type == self.frame_types['NAK']:
                        print('got nak')
                        continue
                    else:
                        print("Expected ack/nak but got smt else. This is {}".format(ack_frame))
                        raise self.BrokenFrameError("Expected ack/nak but got smt else")
                except (self.BrokenFrameError, self.NoByteError) as e:
                    print("getting BrokenFrame or NoByte at all at send_file.\n_Particular error: {}".format(e.message))
                    continue
            else:
                self.status = 'Free'
                raise ConnectionError('Cant send a frame in {} times'.format(self.MAX_TRIES_NUM))
        self.status = 'Free'

    def _receive_frame(self, first_byte=None, timeout=TIMEOUT_WAIT):  # timeout=None):
        """
        Получение кадра из физического уровня
        :return: Словарь {'frame': кадр в виде строки байтов, 'broken': бинарное значение}
        """
        start_time = time.time()
        idx = 0
        while first_byte != self.FD:
            cur_time = time.time()
            time_delta = cur_time - start_time
            idx += 1
            if timeout and time_delta > timeout:
                raise self.NoByteError("Can't receive proper first frame")

            first_byte = self.phys_layer.receive_byte(timeout)

        frame, second_byte = first_byte, None

        second_byte = self.phys_layer.receive_byte()
        if second_byte is None:
            raise self.NoByteError("Can't get second_byte in _receive_frame")
        if second_byte != self.FD:  # Удостоверяемся, что смотрим на новый кадр, а не на конец предыдущего
            frame += second_byte
        else:
            second_byte = self.phys_layer.receive_byte()
            frame += second_byte  # Добавляем то, что на самом деле должно быть вторым байтом

        if second_byte == self.frame_types['INF']:
            frame += self.phys_layer.receive_bytes(2)
            data_len = self._decipher_byte(frame[-2:])[0]
            frame += self.phys_layer.receive_bytes(data_len*2+1)  # + последний кадр FD
        else:
            frame += self.phys_layer.receive_byte()

        return frame

    def _send_ack(self):
        """
        Отправление положительной квитанции
        :return:
        """
        print('sending ack')
        self.phys_layer.send_bytes(self._form_frame(self.frame_types['ACK']))

    def _send_nak(self):
        """
        Отправление отрицательной квитанции
        :return:
        """
        print('sending nak')
        self.phys_layer.send_bytes(self._form_frame(self.frame_types['NAK']))

    @classmethod
    def _form_frame(cls, f_type, data=None):
        """
        Формирование кадра
        :param f_type: Тип отправляемого кадра
        :param data: Данные в кадре. Максимальная длина = 256 байт
        :return: кадр в виде строки байтов
        """
        if f_type == cls.frame_types['INF']:
            data_l = len(data).to_bytes(1, 'big')
            ciphered_data_l = cls._cipher_byte(data_l)
            ciphered_data = b''.join([cls._cipher_byte(b) for b in data])
            return cls.FD + f_type + ciphered_data_l + ciphered_data + cls.FD
            # начало кадра+тип кадра+длина данных+данные в циклическом коде+конец кадра
        else:
            return cls.FD + f_type + cls.FD

    @classmethod
    def _deform_frame(cls, frame):
        """
        Расформирование кадров. Также проверяет кадр на наличие ошибок.
        :param frame: Кадр для расформировывания
        :return: кортеж ( тип_кадра, данные_в_кадре)
        """
        if len(frame) < 3:
            raise cls.BrokenFrameError('Too small frame: {}'.format(frame))
        f_type = frame[1:2]
        if f_type not in cls.frame_types.values():
            raise cls.BrokenFrameError('Unexpected f_type: {}'.format(frame))

        if f_type == cls.frame_types['INF']:
            data_l = int.from_bytes(cls._decipher_byte(frame[2:4]), 'big')
            data = b''.join([cls._decipher_byte(frame[idx:idx+2]) for idx in range(4, 4+data_l*2, 2)])
        else:
            data = None
        if frame[-1:] != cls.FD:
            raise cls.BrokenFrameError("Frame doesn't end with FD byte: {}".format(frame))
        return f_type, data

    @classmethod
    def _cipher_byte(cls, byte):
        # byte as integer in range 0-255
        if type(byte) is bytes:
            byte = byte[0]
        left, right = divmod(byte, 16)  # 16 == int('00010000', base=2)
        return b''.join(cls._hamming_cipher(x).to_bytes(1, 'big') for x in [left, right])

    @classmethod
    def _decipher_byte(cls, bytes_s):
        left, right = bytes_s[0], bytes_s[1]
        if left > 127 or right > 127 or \
                cls._reminder(left) != 0 or cls._reminder(right) != 0:
            raise cls.BrokenFrameError('One byte of data is corrupted')
        left, right = left // 8, right // 8  # 8 == int('0001000', 2)
        return (left*16+right).to_bytes(1, 'big')

    @classmethod
    def _decipher_bytes(cls, bytes_s):
        left, right = bytes_s[0], bytes_s[1]
        if left > 127 or right > 127 or \
                cls._detect_errors(left) != 0 or cls._detect_errors(right) != 0:
            raise cls.BrokenFrameError('One byte of data is corrupted')
        left, right = left // 8, right // 8  # 8 == int('0001000', 2)
        return (left * 16 + right).to_bytes(1, 'big')

    @classmethod
    def _detect_errors(cls, input_seq):
        c = dict([(7, 0), (6, 0), (5, 0), (4, 0), (3, 0), (2, 0), (1, 0)])
        mask = 0b0000001
        for i in range(1, 8):
            c[i] = input_seq & mask
            input_seq >>= 1
        h1 = c[1] ^ c[3] ^ c[5] ^ c[7]
        h2 = (c[2] ^ c[3] ^ c[6] ^ c[7]) << 1
        h3 = (c[4] ^ c[5] ^ c[6] ^ c[7]) << 2
        print("h1: " + "{0:b}".format(h1))
        print("h2: " + "{0:b}".format(h2))
        print("h3: " + "{0:b}".format(h3))
        print("h: " + "{0:b}".format(h1 + h2 + h3))
        #print("".join([str(i) + ": " + "{0:b}".format(c[i]) + "\n" for i in range(1, 8)]))
        return h1 + h2 + h3

    @classmethod
    def _hamming_cipher(cls, input_seq):
        """
        Функция кодирования кодом Хэмминга с длиной слова 4.
        :param input_seq: целое число в диапазоне от 0 до 15 включительно
        :return: целое число в диапазоне от 0 до 127 включительно
        """
        mask = 0b0001
        c = dict([(7, 0), (6, 0), (5, 0), (4, 0), (3, 0), (2, 0), (1, 0)])

        c[3] = input_seq & mask
        mask <<= 1
        c[5] = (input_seq & mask) >> 1
        mask <<= 1
        c[6] = (input_seq & mask) >> 2
        mask <<= 1
        c[7] = (input_seq & mask) >> 3

        c[1] = c[3] ^ c[5] ^ c[7]
        c[2] = (c[3] ^ c[6] ^ c[7]) << 1
        c[4] = (c[5] ^ c[6] ^ c[7]) << 3

        c[3] <<= 2
        c[5] <<= 4
        c[6] <<= 5
        c[7] <<= 6
        #print("".join([str(i) + ": " + "{0:b}".format(c[i]) + "\n" for i in range(1, 8)]))

        return c[7] + c[6] + c[5] + c[4] + c[3] + c[2] + c[1]

    @classmethod
    def _byte_staff(cls, x):
        """
        Процедура байт-стаффинга
        :param x: строка для обработки
        :return: изменённая строка
        """
        return re.sub(cls.FD, cls.FE+cls.FD, x) # регулятрное выражение: замена первого аргумента на второй
    @classmethod
    def _debyte_staff(cls, x):
        """
        Процедура, обратная байт-стаффингу
        :param x: строка для отменения байт-стаффинга
        :return: строка без байт-стаффа
        """
        return re.sub(cls.FE+cls.FD, cls.FD, x)

    @staticmethod
    def _int_to_bin(x, str_len):
        s = bin(x)[2:]
        return '0'*(str_len-len(s)) + s

    def set_connection(self, port_name):
        return self.phys_layer.set_connection(port_name)

    class NoByteError(Exception):
        def __init__(self, message):
            self.message = message

    class NoFrameError(Exception):
        def __init__(self, message):
            self.message = message

    class BrokenFrameError(Exception):
        def __init__(self, message):
            self.message = message
