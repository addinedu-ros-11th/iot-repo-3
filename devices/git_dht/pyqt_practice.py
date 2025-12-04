import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import *
import serial
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from collections import deque
from datetime import datetime

# Receiver는 시리얼 데이터를 읽어오는 백그라운드 스레드입니다.
class Receiver(QThread):
    # 시리얼 데이터를 메인 스레드로 전달할 신호
    SerialMonitor = pyqtSignal(str)

    def __init__(self, conn, parent=None):
        super(Receiver, self).__init__(parent)
        self.is_running = True
        self.conn = conn
        print("Receiver initialized")

    def run(self):
        while self.is_running:
            if self.conn.in_waiting > 0:
                data = self.conn.readline()
                try:
                    data = data.decode('utf-8', errors='ignore').strip()
                except UnicodeDecodeError:
                    print("Decoding error occurred, skipping line.")
                    continue
                if data:
                    print(data)
                    self.SerialMonitor.emit(data) 


# 그래프를 그리는 캔버스 클래스
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


# 디바이스 컨트롤러 클래스
class DeviceController(QObject):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.air_state = 0
        self.heat_state = 0
        self.hum_state = 0
    
    def control_air(self):
        if self.air_state == 0:
            print("CMO,AIR,1")
            if self.conn.is_open:
                self.conn.write(b'A')
            self.air_state = 1
        elif self.air_state == 1:
            print("CMO,AIR,0")
            if self.conn.is_open:
                self.conn.write(b'B')
            self.air_state = 2
        else:
            print("CMO,AIR,-1")
            if self.conn.is_open:
                self.conn.write(b'G')
            self.air_state = 0
    
    def control_heat(self):
        if self.heat_state == 0:
            print("CMO,HEAT,1")
            if self.conn.is_open:
                self.conn.write(b'C')
            self.heat_state = 1
        elif self.heat_state == 1:
            print("CMO,HEAT,0")
            if self.conn.is_open:
                self.conn.write(b'D')
            self.heat_state = 2
        else:
            print("CMO,HEAT,-1")
            if self.conn.is_open:
                self.conn.write(b'H')
            self.heat_state = 0
    
    def control_hum(self):
        if self.hum_state == 0:
            print("CMO,HUMI,1")
            if self.conn.is_open:
                self.conn.write(b'E')
            self.hum_state = 1
        elif self.hum_state == 1:
            print("CMO,HUMI,0")
            if self.conn.is_open:
                self.conn.write(b'F')
            self.hum_state = 2
        else:
            print("CMO,HUMI,-1")
            if self.conn.is_open:
                self.conn.write(b'I')
            self.hum_state = 0


# 데이터 파서 및 디스플레이 매니저 클래스
class DisplayManager(QObject):
    def __init__(self, lcd1, lcd2, graph_canvas):
        super().__init__()
        self.lcd1 = lcd1
        self.lcd2 = lcd2
        self.graph_canvas = graph_canvas
    
    def update_display(self, data):
        """시리얼 데이터를 파싱하여 LCD와 그래프 업데이트"""
        try:
            if "SEN,TEM" in data and "HUM" in data:
                parts = data.split(',')
                temperature = float(parts[2])
                humidity = int(parts[4])
                
                # LCD 업데이트
                self.lcd1.display(temperature)
                self.lcd2.display(humidity)
                
                # 그래프 업데이트
                self.graph_canvas.update_graph(temperature, humidity)
        except Exception as e:
            print(f"Error in update_display: {e}")


# UI를 로드하고 기본 윈도우 클래스를 설정합니다.
from_class = uic.loadUiType("project.ui")[0]

class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 시리얼 연결
        self.conn = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=1)

        # 그래프 캔버스 생성 및 추가
        self.graph_canvas = GraphCanvas()
        layout = QVBoxLayout(self.widget_graph)
        layout.addWidget(self.graph_canvas)
        self.widget_graph.setLayout(layout)
        
        # 디바이스 컨트롤러 생성
        self.device_controller = DeviceController(self.conn)
        
        # 디스플레이 매니저 생성
        self.display_manager = DisplayManager(self.LCD_1, self.LCD_2, self.graph_canvas)
        
        # 버튼 연결
        self.pbnAir.clicked.connect(self.device_controller.control_air)
        self.pbnHeat.clicked.connect(self.device_controller.control_heat)
        self.pbnHum.clicked.connect(self.device_controller.control_hum)
        
        # Receiver 생성 및 시작
        self.recv = Receiver(self.conn)
        self.recv.SerialMonitor.connect(self.display_manager.update_display)
        self.recv.start()

    def closeEvent(self, event):
        self.recv.is_running = False
        self.recv.wait()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()
    sys.exit(app.exec())