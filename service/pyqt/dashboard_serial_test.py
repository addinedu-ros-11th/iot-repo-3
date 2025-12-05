import serial
import threading
import time
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from collections import deque

from_class = uic.loadUiType("service/pyqt/dashboard.ui")[0]

# Define serial port configurations
SERIAL_PORTS = {
    'ele_00': '/dev/ttyACM0',
    'ent_00': '/dev/ttyACM1',
    'cur_00': '/dev/ttyACM2',
    'dht_00': '/dev/ttyACM3',
}

class GraphCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 6))
        super().__init__(self.fig)
        self.setParent(parent)
        
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()
        
        self.max_points = 50
        self.temp_data = deque(maxlen=self.max_points)
        self.hum_data = deque(maxlen=self.max_points)
        self.index_data = deque(maxlen=self.max_points)
        self.current_index = 0
        
        self.setup_plot()
        
    def setup_plot(self):
        self.ax1.clear()
        self.ax2.clear()
        
        self.ax1.tick_params(axis='y', labelcolor='red')
        self.ax1.set_ylim(0, 35)
        self.ax1.grid(True, alpha=0.3)
        
        self.ax2.tick_params(axis='y', labelcolor='blue')
        self.ax2.set_ylim(0, 100)
        
        self.ax1.set_xticks([])
        
        self.fig.tight_layout()
        
    def update_graph(self, temperature, humidity):
        self.index_data.append(self.current_index)
        self.temp_data.append(temperature)
        self.hum_data.append(humidity)
        self.current_index += 1
        
        self.ax1.clear()
        self.ax2.clear()
        
        line1 = self.ax1.plot(list(self.index_data), list(self.temp_data), 
                             'r-o', linewidth=2, markersize=4, label='Temperature')
        self.ax1.tick_params(axis='y', labelcolor='red')
        self.ax1.set_ylim(0, 35)
        self.ax1.grid(True, alpha=0.3)
        
        line2 = self.ax2.plot(list(self.index_data), list(self.hum_data), 
                             'b-o', linewidth=2, markersize=4, label='Humidity')
        self.ax2.tick_params(axis='y', labelcolor='blue')
        self.ax2.set_ylim(0, 100)
        
        self.ax1.set_xticks([])
                
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        self.ax1.legend(lines, labels, loc='upper left', fontsize=9)
        
        self.fig.tight_layout()
        self.draw()


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
                    data = self.ser.readline().decode('utf-8', errors='ignore').strip()
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

        self._initialize_state()
        self._setup_ui_components()
        self._connect_signals()

        self.serial_threads = {}
        self.init_serial_ports()

    def _initialize_state(self):
        """Initializes all state variables."""
        self.air_state = 0
        self.heat_state = 0
        self.hum_state = 0
        
        # Curtain state variables
        self.curtain_auto_mode = False
        self.curtain_max_steps = 1000  # Default value, might be updated from device
        self.curtain_motion_state = "정지"
        self.curtain_status_message = ""

    def _setup_ui_components(self):
        """Sets up UI elements like graphs and initial label texts."""
        # Graph Canvas
        self.graph_canvas = GraphCanvas()
        layout = QVBoxLayout(self.widget_graph)
        layout.addWidget(self.graph_canvas)
        self.widget_graph.setLayout(layout)

        # Initial labels
        self.label_ele_1f.setText("")
        self.label_ele_2f.setText("")
        self.label_ele_3f.setText("")
        self._refresh_curtain_status_label()

    def _connect_signals(self):
        """Connects all UI element signals to their slots."""
        # Elevator buttons
        self.pushButton_1f.clicked.connect(self.elevator_1f_call)
        self.pushButton_2f.clicked.connect(self.elevator_2f_call)
        self.pushButton_3f.clicked.connect(self.elevator_3f_call)

        # Entrance button
        self.pushButton_e.clicked.connect(self.entrance_open)

        # DHT control buttons
        self.pushButton_air.clicked.connect(self.control_air)
        self.pushButton_heat.clicked.connect(self.control_heat)
        self.pushButton_humi.clicked.connect(self.control_hum)

        # Curtain control buttons
        self.pushButton_curOpen.clicked.connect(self.curtain_open)
        self.pushButton_curClose.clicked.connect(self.curtain_close)
        self.pushButton_curStop.clicked.connect(self.curtain_stop)
        self.pushButton_curAuto.clicked.connect(self.curtain_auto)

    def init_serial_ports(self):
        for name, port in SERIAL_PORTS.items():
            thread = SerialThread(serial_port=port, baud_rate=9600)
            thread.received_data.connect(self.handle_serial_data)
            thread.start()
            self.serial_threads[name] = thread
            print(f"Started serial thread for {name} on {port}")

    # --- Device Control Methods ---
    def _send_command(self, device, command):
        """Safely sends a command to a specified device."""
        if device in self.serial_threads:
            self.serial_threads[device].write(command)
        else:
            print(f"Device '{device}' not connected.")

    def entrance_open(self):
        self._send_command('ent_00', "CMO,MOTOR,1\n")
        self.label_e_approv.setText("✅")

    def elevator_1f_call(self):
        if self.label_ele_1f.text() == "✅":
            self._send_command('ele_00', "CMO,CANCEL,1\n")
            self.label_ele_1f.setText("")

        else:
            self._send_command('ele_00', "CMO,FLOOR,1\n")
            self.label_ele_1f.setText("✅")

    def elevator_2f_call(self):
        if self.label_ele_2f.text() == "✅":
            self._send_command('ele_00', "CMO,CANCEL,2\n")
            self.label_ele_2f.setText("")
        else:
            self._send_command('ele_00', "CMO,FLOOR,2\n")
            self.label_ele_2f.setText("✅")

    def elevator_3f_call(self):
        if self.label_ele_3f.text() == "✅":
            self._send_command('ele_00', "CMO,CANCEL,3\n")
            self.label_ele_3f.setText("")
        else:
            self._send_command('ele_00', "CMO,FLOOR,3\n")
            self.label_ele_3f.setText("✅")

    def control_air(self):
        states = [(0, "A", "ON", 1), (1, "B", "AUTO", 2), (2, "G", "OFF", 0)]
        current_state_index = self.air_state
        command, text, next_state = states[current_state_index][1:]
        self.air_state = next_state
        self.label_airState.setText(text)
        self._send_command('dht_00', command)

    def control_heat(self):
        states = [(0, "C", "ON", 1), (1, "D", "AUTO", 2), (2, "H", "OFF", 0)]
        current_state_index = self.heat_state
        command, text, next_state = states[current_state_index][1:]
        self.heat_state = next_state
        self.label_heatState.setText(text)
        self._send_command('dht_00', command)

    def control_hum(self):
        states = [(0, "E", "ON", 1), (1, "F", "AUTO", 2), (2, "I", "OFF", 0)]
        current_state_index = self.hum_state
        command, text, next_state = states[current_state_index][1:]
        self.hum_state = next_state
        self.label_humiState.setText(text)
        self._send_command('dht_00', command)

    def curtain_open(self):
        self._send_command('cur_00', "CMO,MOTOR,OPEN\n")
        self._mark_manual_mode_requested()
        self._set_curtain_status_message("요청:OPEN")

    def curtain_close(self):
        self._send_command('cur_00', "CMO,MOTOR,CLOSE\n")
        self._mark_manual_mode_requested()
        self._set_curtain_status_message("요청:CLOSE")

    def curtain_stop(self):
        self._send_command('cur_00', "CMO,MOTOR,STOP\n")
        self._mark_manual_mode_requested()
        self._set_curtain_status_message("요청:STOP")

    def curtain_auto(self):
        self._send_command('cur_00', "CMO,MODE,AUTO\n")
        self._set_curtain_status_message("요청:AUTO")

    # --- Serial Data Handling ---
    def handle_serial_data(self, port, data):
        device_name = None
        for name, p in SERIAL_PORTS.items():
            if p == port:
                device_name = name
                break
        
        if not device_name:
            print(f"Data from unknown port {port}: {data}")
            return

        handlers = {
            'ele_00': self._handle_ele_00_data,
            'ent_00': self._handle_ent_00_data,
            'dht_00': self._handle_dht_00_data,
            'cur_00': self._handle_cur_00_data,
        }
        
        handler = handlers.get(device_name)
        if handler:
            handler(data)
        else:
            print(f"No handler for device {device_name}")

    def _handle_ele_00_data(self, data):
        if data.startswith("ACK,FLOOR,") or data.startswith("ACK,CANCEL,"):
            try:
                floor = int(data.split(',')[2])
                if floor == 1:
                    self.label_ele_1f.setText("")
                elif floor == 2:
                    self.label_ele_2f.setText("")
                elif floor == 3:
                    self.label_ele_3f.setText("")
            except (ValueError, IndexError) as e:
                print(f"Error parsing elevator ACK from data '{data}': {e}")
        elif data.startswith("SEN,FLOOR,"):
            try:
                floor_number = int(data.split(',')[2])
                self.lcdNumber_floor.display(floor_number)
            except (ValueError, IndexError) as e:
                print(f"Error parsing elevator floor number from data '{data}': {e}")

    def _handle_ent_00_data(self, data):
        parts = data.split(',')
        if len(parts) != 3:
            print(f"[ERROR] invalid entrance data: {data!r}")
            return
        
        data_type, metric_name, value = parts
        if data_type == "SEN":
            if metric_name == "RFID_ACCESS":
                self.le_e_id.setText(str(value))
                self.label_e_approv.setText("✅")
            elif metric_name == "RFID_DENY":
                self.le_e_id.setText(str(value))
                self.label_e_approv.setText("❌")
            elif metric_name == "MOTOR" and value == "-1":
                self.le_e_id.clear()
                self.label_e_approv.setText("")

    def _handle_dht_00_data(self, data):
        try:
            if "SEN,TEM" in data and "HUM" in data:
                parts = data.split(',')
                temperature = float(parts[2])
                humidity = int(parts[4])
                
                self.lcdNumber_temp.display(temperature)
                self.lcdNumber_hu.display(humidity)
                
                self.graph_canvas.update_graph(temperature, humidity)
        except Exception as e:
            print(f"Error in dht_00 data handling from data '{data}': {e}")
    
    def _handle_cur_00_data(self, data):
        data = data.strip()
        if not data:
            return

        parts = data.split(',')
        if len(parts) != 3:
            print(f"[ERROR] invalid frame for cur_00: {data!r}")
            return

        data_type, metric_name, value = parts

        if data_type == "ACK":
            if metric_name == "MOTOR":
                if self.curtain_auto_mode:
                    self.curtain_auto_mode = False
                    self._refresh_curtain_controls()
                self._set_curtain_status_message(f"ACK:{value}")
            elif metric_name == "MODE":
                self.curtain_auto_mode = value.upper() == "AUTO"
                self._refresh_curtain_controls()
                self._set_curtain_status_message(f"MODE:{value}")
            elif metric_name == "ERROR":
                self._set_curtain_status_message(f"ERROR:{value}")
        elif data_type == "SEN":
            if metric_name == "LIGHT":
                try:
                    self.lcdNumber_lux.display(float(value))
                except ValueError:
                    print(f"[ERROR] invalid light value: {value!r}")
            elif metric_name == "CUR_STEP":
                self._update_curtain_progress(value)
            elif metric_name == "MOTOR_DIR":
                self._handle_curtain_direction(value)
        else:
            print(f"[WARN] unsupported frame type for cur_00: {data_type!r}")

    # --- Curtain Helper Methods ---
    def _handle_curtain_direction(self, value):
        try:
            direction = int(float(value))
            if direction > 0:
                motion_text = "열림 중"
            elif direction < 0:
                motion_text = "닫힘 중"
            else:
                motion_text = "정지"
            self._set_curtain_motion_state(motion_text)
        except ValueError:
            print(f"[ERROR] invalid motor direction: {value!r}")

    def _update_curtain_progress(self, step_value):
        try:
            steps = float(step_value)
            if self.curtain_max_steps > 0:
                percentage = max(0, min(100, int((steps / self.curtain_max_steps) * 100)))
                self.progressBar_cur.setValue(percentage)
        except ValueError:
            print(f"[ERROR] invalid curtain step value: {step_value!r}")

    def _refresh_curtain_controls(self):
        self.pushButton_curAuto.setText("커튼 Auto 복귀")
        self._refresh_curtain_status_label()

    def _set_curtain_motion_state(self, text):
        self.curtain_motion_state = text
        self.curtain_status_message = ""
        self._refresh_curtain_status_label()

    def _set_curtain_status_message(self, text):
        self.curtain_status_message = text
        self._refresh_curtain_status_label()

    def _refresh_curtain_status_label(self):
        mode_text = "AUTO" if self.curtain_auto_mode else "MANUAL"
        parts = [f"모드: {mode_text}", f"상태: {self.curtain_motion_state}"]
        if self.curtain_status_message:
            parts.append(self.curtain_status_message)
        self.label_curState.setText('  |  '.join(parts))

    def _mark_manual_mode_requested(self):
        if self.curtain_auto_mode:
            self.curtain_auto_mode = False
            self._refresh_curtain_controls()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    sys.exit(app.exec())
