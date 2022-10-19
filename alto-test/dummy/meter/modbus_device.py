from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import *
from pymodbus.transaction import *
from pymodbus.constants import Endian
import psutil
import logging
from threading import Thread
import time
'''
import needed modules to create dummy for ModbusTCP device and create dummy modbus server to generate data.
'''
_log = logging.getLogger(__name__)


def get_cpu_usage():
    '''
    Some attemp to find dummy data. Coming up with something easy to get from system
    '''
    builder = BinaryPayloadBuilder()
    for register in psutil.cpu_percent(interval=1,percpu=True):
        builder.add_32bit_float(register)
    return builder.to_registers()


class ModDummySlave:
    def __init__(self, host='127.0.0.1', port=502, slaveId=1):
        '''
        Initilize TCP Client. If for some reason your slave support something with non standard framer (Modbus RTU over TCP)
        add framer parameter in the ModbusTCPClient class also. example below:
        '''
        self.client = ModbusTcpClient(host=host, port=port)
        self.slaveId = slaveId


    def run(self):
        sampling = 300
        self.client.connect()
        while self.client.connect():
            self.client.write_registers(0,get_cpu_usage(),unit=self.slaveId)
            time.sleep(sampling/1000)

if __name__ == '__main__':
    ModDummySlave().run()
