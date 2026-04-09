import serial as pyserial
from serial.tools.list_ports import comports
import time
from datetime import datetime
import struct




def get_devices_list():
    """ Get the devices connected to COM ports and their serial number.
    
    Returns
    -------
    devices_COM : dict of serial number > COM port
    devices_serials : list of str
    """

    ports = [port[0] for port in comports()]
    devices = []
    devices_serials = []
    for port in ports:
        try:
            ser = get_serial(port)
            devices.append(port)
            devices_serials.append(ser)
        except Exception as e:
            # print(e)
            pass
    devices_COM = {devices_serials[i]:devices[i] for i in range(len(devices))}
    return(devices_COM, devices_serials)

def checksum(data):
    CS = 0
    for i in range(0, len(data)):
        CS = (CS + ord(data[i]))
    CS = (CS ^ 0xFF)
    CS = (CS + 1)
    return CS

def get_serial(port, timeout=500):
    ser = pyserial.Serial()
    ser.baudrate = 9600
    ser.port = port
    ser.open()
    ser.flushInput()
    ser.flushOutput()

    msg = chr(0x4B) + chr(0x4E) + chr(0x00)
    msg += chr(checksum(msg)) + chr(0x0D)
    ser.write(msg.encode('utf-8'))

    start = time.time()
    timed_out = False
    while ser.inWaiting() < 7 and (not timed_out):
        time.sleep(0.01)
        timed_out = time.time() > start+timeout/1000
    if timed_out:
        raise RuntimeError("Read timed out.")

    rec = ser.read(ser.inWaiting())
    ser.close()

    if not rec[0] == 0x4B:
        raise RuntimeError("Getting serial number failed.")

    serialno = struct.unpack('i', rec[1:5])[0]
    return str(serialno)



class WikaController:

    def __init__(self):

        self.serial = None
        self.units = "bar"

    def open_communication(self, port):

        self.serial = pyserial.Serial()
        self.serial.baudrate = 9600
        self.serial.port = port
        self.serial.open()
        self.serial.flushInput()
        self.serial.flushOutput()

        self.start_time = time.time()


        # if not self.devices:
        #     raise RuntimeError("Tried to open but no devices found.")
        # if serial is None:
        #     port = self.devices[idx]
        #     self.opened_device = self.device_names[idx]
        # else:
            # port = self.devices[self.device_names.index(serial)]
            # self.opened_device = self.device_names.index(serial)

    def close_communication(self):
        if self.serial is not None:
            self.serial.close()

    @property
    def online(self):
        if self.serial is None:
            return False
        return self.serial.isOpen()

    def grab_pressure(self, waiting_time=1, timeout=500):
        if not self.online:
            raise RuntimeError("Tried to grab pressure but not online.")
        msg = chr(0x50) + chr(0x5A) + chr(0x00)
        msg += chr(checksum(msg)) + chr(0x0D)
        self.serial.write(msg.encode('utf-8'))

        start = time.time()
        timed_out = False
        while self.serial.inWaiting() < 8 and (not timed_out):
            time.sleep(0.01)
            timed_out = time.time() > start+timeout/1000
        if timed_out:
            raise RuntimeError("Read timed out.")

        rec = self.serial.read(self.serial.inWaiting())

        if not rec[0] == 0x50:
            raise RuntimeError("Pressure grab failed.")

        pressure = struct.unpack('f', rec[1:5])[0]
        if rec[5] == 0xFE:
            # gauge pressure, bar
            pressure += 1
        elif rec[5] == 0xFF:
            # absolute pressure, bar
            pass
        else:
            raise RuntimeError("Pressure unit not set to bar!")


        time.sleep(waiting_time)
        # return pres, params
        return pressure, time.time()-self.start_time


if __name__ == "__main__":
    devices, device_names = get_devices_list()

    controller = WikaController()
    controller.open(devices[0])
    print(controller.online)
    print(controller.grab())
    controller.close()


    # print(device_names)
    # print(devices)