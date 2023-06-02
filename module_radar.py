import time
import serial
from datetime import datetime
from utils import create_csv, register_in_csv

class ModuleError(Exception):
    """
    One of the error bits was set in the module
    """
    
class ModuleCommunication:
    """
    Simple class to communicate with the module software
    """
    def __init__(self, port, rtscts):
        self._port = serial.Serial(port, 115200, rtscts=rtscts,
                                   exclusive=True, timeout=2)

    def read_packet_type(self, packet_type):
        """
        Read any packet of packet_type. Any packages received with
        another type is discarded.
        """
        while True:
            header, payload = self._read_packet()
            if header[3] == packet_type:
                break
        return header, payload

    def _read_packet(self):
        header = self._port.read(4)
        length = int.from_bytes(header[1:3], byteorder='little')

        data = self._port.read(length + 1)
        assert data[-1] == 0xCD
        payload = data[:-1]
        return header, payload

    def register_write(self, addr, value):
        """
        Write a register
        """
        data = bytearray()
        data.extend(b'\xcc\x05\x00\xf9')
        data.append(addr)
        data.extend(value.to_bytes(4, byteorder='little', signed=False))
        data.append(0xcd)
        self._port.write(data)
        _header, payload = self.read_packet_type(0xF5)
        assert payload[0] == addr

    def register_read(self, addr):
        """
        Read a register
        """
        data = bytearray()
        data.extend(b'\xcc\x01\x00\xf8')
        data.append(addr)
        data.append(0xcd)
        self._port.write(data)
        _header, payload = self.read_packet_type(0xF6)
        assert payload[0] == addr
        return int.from_bytes(payload[1:5], byteorder='little', signed=False)

    def buffer_read(self, offset):
        """
        Read the buffer
        """
        data = bytearray()
        data.extend(b'\xcc\x03\x00\xfa\xe8')
        data.extend(offset.to_bytes(2, byteorder='little', signed=False))
        data.append(0xcd)
        self._port.write(data)

        _header, payload = self.read_packet_type(0xF7)
        assert payload[0] == 0xE8
        return payload[1:]

    def read_stream(self):
        """
        Read a stream of data
        """
        _header, payload = self.read_packet_type(0xFE)
        return payload

    @staticmethod
    def _check_error(status):
        ERROR_MASK = 0xFFFF0000
        if status & ERROR_MASK != 0:
            ModuleError(f"Error in module, status: 0x{status:08X}")

    @staticmethod
    def _check_timeout(start, max_time):
        if (time.monotonic() - start) > max_time:
            raise TimeoutError()

    def _wait_status_set(self, wanted_bits, max_time):
        """
        Wait for wanted_bits bits to be set in status register
        """
        start = time.monotonic()

        while True:
            status = self.register_read(0x6)
            self._check_timeout(start, max_time)
            self._check_error(status)

            if status & wanted_bits == wanted_bits:
                return
            time.sleep(0.1)

    def wait_start(self):
        """
        Poll status register until created and activated
        """
        ACTIVATED_AND_CREATED = 0x3
        self._wait_status_set(ACTIVATED_AND_CREATED, 3)

    def wait_for_data(self, max_time):
        """
        Poll status register until data is ready
        """
        DATA_READY = 0x00000100
        self._wait_status_set(DATA_READY, max_time)


class ModuleDistanceDetector:
    
    def __init__(self, port = "/dev/ttyS0"):
        self.port = port
        #self.connect()

    def connect(self):
        try:
            # Rasberry Mini Uart PORT
            #port = '/dev/ttyS0'
            # XM132 is true
            flowcontrol = True
            self.com = ModuleCommunication(self.port, flowcontrol)
            # Make sure that module is stopped
            self.com.register_write(0x03, 0)
            # Give some time to stop (status register could be polled too)
            time.sleep(0.5)
            # Clear any errors and status
            self.com.register_write(0x3, 4)
            # Read product ID
            product_identification =  self.com.register_read(0x10)
            print(f'product_identification=0x{product_identification:08X}')

            version = self.com.buffer_read(0)
            print(f'Software version: {version}')
            # Set Mode read distance
            mode = 'distance'
            self.com.register_write(0x2, 0x200)
            #range_min = 2200
            #range_max = 2700
            self.com.register_write(0x20, 2200)
            self.com.register_write(0x21, 2700)
            # Update rate 1Hz
            self.com.register_write(0x23, 2000)
            self.com.register_write(0x24, 200)
            self.com.register_write(0x29, 4)

            # Disable UART streaming mode
            self.com.register_write(5, 0)

            # Activate and start
            self.com.register_write(3,3)
            return True
        except Exception as err:
            print(f"Error {err=}, {type(err)=}")
            return False

    def close(self):
        self.com.register_write(0x03, 0)

    def start(self):
        # Wait for it to start
        self.com.wait_start()
        print('Sensor activated')

        # Read out distance start
        dist_start = self.com.register_read(0x81)
        print(f'dist_start={dist_start / 1000} m')

        dist_length = self.com.register_read(0x82)
        print(f'dist_length={dist_length / 1000} m')
        duration = 100
        start = time.monotonic()

    def read(self):
        self.com.register_write(3, 4)
        # Wait for data read
        self.com.wait_for_data(2)
        dist_count = self.com.register_read(0xB0)
        print('                                               ', end='\r')
        print(f'Detected {dist_count} peaks:', end='')

        distances, amplitudes = self.read_peaks(dist_count)
        num_dist = len(distances)
        mean_distance = 0
        if num_dist > 0:
            mean_distance = sum(distances) / num_dist
        return mean_distance
    
    def read_data(self):
        self.com.register_write(3, 4)
        # Wait for data read
        self.com.wait_for_data(2)
        dist_count = self.com.register_read(0xB0)
        distances, amplitudes = self.read_peaks(dist_count)
        return distances, amplitudes

    def read_peaks(self, dist_count):
        distances = []
        amplitudes = []
        for count in range(dist_count):
            dist_distance = self.com.register_read(0xB1 + 2 * count)
            dist_amplitude = self.com.register_read(0xB2 + 2 * count)
            print(f' dist_{count}_distance={dist_distance / 1000} m', end='')
            print(f' dist_{count}_amplitude={dist_amplitude}', end='')
            distances.append(dist_distance / 1000)
            amplitudes.append(dist_amplitude)
        return distances, amplitudes

if __name__ == "__main__":
    distanceDetector = ModuleDistanceDetector()
     ## Connect Module Radar
    success_xm132 = distanceDetector.connect()
    
    req_fields = ["distance","amplitude", "time"]
    delay = 0.5
    name_file = create_csv(name_base = f"xm132_{str(delay)}fps_", req_fields = req_fields)
    
    if success_xm132:
        distanceDetector.start()
        print("XM132 conectado exitosamente")
        while True:
            distances, amplitudes = distanceDetector.read_data()
            #print("Distancia: ", distance)
            time = datetime.now()
            for d, a in zip(distances, amplitudes):
                data = {"distance": d, "amplitude": a, "time": time}
                register_in_csv(name_file, data)
            time.sleep(delay)
    else:
        print("XM132 no se puedo conectar")