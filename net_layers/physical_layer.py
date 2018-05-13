import serial
import random
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
# handler = logging.FileHandler('run.log')
handler = logging.FileHandler('run1.log')
handler.setLevel(logging.WARNING)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)


class PhysicalLayer:
    READ_TIMEOUT = 1  # секунд. если 0 - то неблокирующий режим
    WRITE_TIMEOUT = 1

    def __init__(self, port_name=None):
        self.port = self.open_port(port_name)


    def send_bytes(self, bytes_s):
        """
        Запись байтов строки bytes_s в порт
        """
        def corrupt(bytes_s, p=0.001):
            new_bytes_s = b''
            for idx, byte in enumerate(bytes_s):
                orig_byte = bin(byte)[2:]
                new_byte = ''.join([str(int(bit) ^ (1-int(random.random() > p))) for bit in orig_byte])
                new_bytes_s += int(new_byte, 2).to_bytes(1, 'big')
            return new_bytes_s
        bytes_s = corrupt(bytes_s)

        try:
            self.port.write(bytes_s)
        except serial.SerialTimeoutException as e:
            raise ConnectionError(e.args)

    def receive_byte(self, timeout=None):
        """
        Чтение одного байта из порта
        :param timeout:время ожидания байта в секундах
        :return:возвращение None, если байт не был считан
        """
        return self.receive_bytes(1, timeout)

    def receive_bytes(self, amount, timeout=None):
        """
        Чтение amount байт из порта
        :param amount: количество байт из порта
        :param timeout: время ожидания байта в секундах
        :return: возвращение None, если байты не были считаны
        """
        if not self.port.is_open:
            return None
        self.port.timeout = timeout if timeout and timeout < 1.0 else 1.0
        bytes_s = self.port.read(amount)
        return bytes_s if len(bytes_s) > 0 else None

    def close_port(self):
        """
        закрытие порта
        """
        self.port.close()

    def open_port(self, port_name):
        """
        открытие порта
        :param port_name: нозвание порта
        :return: объект класса serial.Serial
        """
        return serial.Serial(port_name, timeout=self.READ_TIMEOUT, write_timeout=self.WRITE_TIMEOUT)

    def set_connection(self, port_name):
        """
        Установка соединения
        :param port_name: номер порта для соединения
        :return: None, Ошибка
        """
        if self.port.name == port_name:
            return None
        try:
            self.port = self.open_port(port_name)
            return None
        except serial.SerialException as e:
            return 'Такого номер порта не существует.'
