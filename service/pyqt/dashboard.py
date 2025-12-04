import serial
import threading
import time
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import *

from_class = uic.loadUiType("./dashboard.ui")[0]

# Define serial port configurations
# Adjust the COM port based on your environment
SERIAL_PORTS = {
    'elevator': 'COM3',
    'entrance': 'COM4',
    'curtain': 'COM5',
}

class SerialThread(QThread):
    received_data = pyqtSignal(str, str)  # port_name, data

    def __init__(self, serial_port, baud_rate):
        super().__init__()
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.ser = None
        self.running = False

    def run(self):
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            self.running = True
            while self.running:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8').strip()
                    if data:
                        self.received_data.emit(self.serial_port, data)
                time.sleep(0.01)
        except serial.SerialException as e:
            print(f"Serial Error on {self.serial_port}: {e}")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

    def stop(self):
        self.running = False
        self.wait()

    def write(self, data):
        if self.ser and self.ser.is_open:
            self.ser.write(data.encode('utf-8'))

class WindowClass(QMainWindow, from_class) :
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.serial_threads = {}
        self.init_serial_ports()

        # Connect buttons to slots
        self.pushButton_1f.clicked.connect(self.elevator_1f_call)
        self.pushButton_2f.clicked.connect(self.elevator_2f_call)
        self.pushButton_3f.clicked.connect(self.elevator_3f_call)
        
        self.pushButton_e.clicked.connect(self.entrance_open)

        # Initially hide all check icons
        self.label_ele_1f.setText("")
        self.label_ele_2f.setText("")
        self.label_ele_3f.setText("")

    def init_serial_ports(self):
        for name, port in SERIAL_PORTS.items():
            thread = SerialThread(serial_port=port, baud_rate=9600)
            thread.received_data.connect(self.handle_serial_data)
            thread.start()
            self.serial_threads[name] = thread
            print(f"Started serial thread for {name} on {port}")

    def elevator_1f_call(self):
        command = "CMO,FLOOR,1\n"
        if 'elevator' in self.serial_threads:
            self.serial_threads['elevator'].write(command)
            self.label_ele_1f.setText("✅")

    def elevator_2f_call(self):
        command = "CMO,FLOOR,2\n"
        if 'elevator' in self.serial_threads:
            self.serial_threads['elevator'].write(command)
            self.label_ele_2f.setText("✅")

    def elevator_3f_call(self):
        command = "CMO,FLOOR,3\n"
        if 'elevator' in self.serial_threads:
            self.serial_threads['elevator'].write(command)
            self.label_ele_3f.setText("✅")

    def handle_serial_data(self, port, data):
        # Find which device this data is from
        device_name = None
        for name, p in SERIAL_PORTS.items():
            if p == port:
                device_name = name
                break
        
        if not device_name:
            print(f"Data from unknown port {port}: {data}")
            return

        if device_name == 'elevator':
            if data == "ACK,FLOOR,1":
                self.label_ele_1f.setText("")
            elif data == "ACK,FLOOR,2":
                self.label_ele_2f.setText("")
            elif data == "ACK,FLOOR,3":
                self.label_ele_3f.setText("")
            elif data.startswith("SEN,FLOOR,"):
                try:
                    floor_number = int(data.split(',')[2])
                    self.lcdNumber_floor.display(floor_number)
                except (ValueError, IndexError) as e:
                    print(f"Error parsing elevator floor number: {e}")
        
        elif device_name == 'entrance':
            # Add logic for entrance device here
            print(f"Entrance data: {data}")
            pass
        
        elif device_name == 'curtain':
            # Add logic for curtain device here
            print(f"Curtain data: {data}")
            pass


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    Dialog = WindowClass()
    Dialog.show()
    sys.exit(app.exec())
