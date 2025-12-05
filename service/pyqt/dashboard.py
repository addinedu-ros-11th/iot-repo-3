"""IoT 시스템 대시보드 UI (그래프 포함)"""

import sys
import threading
import time
import requests
from collections import deque
from PyQt6 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class GraphCanvas(FigureCanvas):
    """그래프를 그리는 캔버스 클래스"""
    
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
        """그래프 초기 설정"""
        self.ax1.clear()
        self.ax2.clear()
        
        self.ax1.tick_params(axis='y', labelcolor='red')
        self.ax1.set_ylim(15, 35)
        self.ax1.grid(True, alpha=0.3)
        
        self.ax2.tick_params(axis='y', labelcolor='blue')
        self.ax2.set_ylim(0, 100)
        
        self.ax1.set_xticks([])
        
        self.fig.tight_layout()
    
    def update_graph(self, temperature, humidity):
        """그래프 업데이트"""
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


class DisplayManager:
    """데이터 파서 및 디스플레이 매니저"""
    
    def __init__(self, lcd_temp, lcd_hum, graph_canvas):
        self.lcd_temp = lcd_temp
        self.lcd_hum = lcd_hum
        self.graph_canvas = graph_canvas
        self.latest_temp = None
        self.latest_hum = None
    
    def update_display(self, data):
        """시리얼 데이터를 파싱하여 LCD와 그래프 업데이트"""
        try:
            print("[DEBUG] update_display: " + data)
            if data.startswith("SEN"):
                parts = data.split(',')
                if len(parts) >= 3:
                    if parts[1] == "TEM":
                        self.latest_temp = int(parts[2])
                        self.lcd_temp.display(self.latest_temp)
                    elif parts[1] == "HUM":
                        self.latest_hum = int(parts[2])
                        self.lcd_hum.display(self.latest_hum)

                # 그래프는 temp와 hum 둘 다 있으면 업데이트
                if self.latest_temp is not None and self.latest_hum is not None:
                    self.graph_canvas.update_graph(self.latest_temp, self.latest_hum)
        except Exception as e:
            print(f"[ERROR] update_display: {e}")

class Ui_Dialog(object):
    """대시보드 UI 클래스"""

    def __init__(self):
        self.api_url = "http://localhost:5000"
        self.polling_interval = 0.05
        self.polling_thread = None
        self.running = True
        
        # 홈 제어 상태
        self.air_state = 0
        self.heat_state = 0
        self.hum_state = 0

    def setupUi(self, dialog):
        dialog.setObjectName("dialog")
        dialog.resize(1039, 639)
        self.groupBox_e = QtWidgets.QGroupBox(parent=dialog)
        self.groupBox_e.setGeometry(QtCore.QRect(40, 20, 341, 161))
        self.groupBox_e.setObjectName("groupBox_e")
        self.le_e_id = QtWidgets.QLineEdit(parent=self.groupBox_e)
        self.le_e_id.setGeometry(QtCore.QRect(20, 50, 221, 41))
        self.le_e_id.setReadOnly(True)
        self.le_e_id.setObjectName("le_e_id")
        self.label_e_id = QtWidgets.QLabel(parent=self.groupBox_e)
        self.label_e_id.setGeometry(QtCore.QRect(20, 30, 66, 18))
        self.label_e_id.setObjectName("label_e_id")
        self.label_e_approv = QtWidgets.QLabel(parent=self.groupBox_e)
        self.label_e_approv.setGeometry(QtCore.QRect(260, 50, 61, 41))
        self.label_e_approv.setObjectName("label_e_approv")
        self.pushButton_e = QtWidgets.QPushButton(parent=self.groupBox_e)
        self.pushButton_e.setGeometry(QtCore.QRect(20, 110, 151, 30))
        self.pushButton_e.setObjectName("pushButton_e")
        self.label_e_open = QtWidgets.QLabel(parent=self.groupBox_e)
        self.label_e_open.setGeometry(QtCore.QRect(180, 120, 131, 18))
        self.label_e_open.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_e_open.setObjectName("label_e_open")
        self.groupBox_ele = QtWidgets.QGroupBox(parent=dialog)
        self.groupBox_ele.setGeometry(QtCore.QRect(40, 190, 341, 291))
        self.groupBox_ele.setObjectName("groupBox_ele")
        self.lcdNumber_floor = QtWidgets.QLCDNumber(parent=self.groupBox_ele)
        self.lcdNumber_floor.setGeometry(QtCore.QRect(-60, 100, 181, 91))
        self.lcdNumber_floor.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.lcdNumber_floor.setLineWidth(-1)
        self.lcdNumber_floor.setObjectName("lcdNumber_floor")
        self.label = QtWidgets.QLabel(parent=self.groupBox_ele)
        self.label.setGeometry(QtCore.QRect(60, 80, 66, 18))
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.pushButton_1f = QtWidgets.QPushButton(parent=self.groupBox_ele)
        self.pushButton_1f.setGeometry(QtCore.QRect(210, 200, 88, 26))
        self.pushButton_1f.setObjectName("pushButton_1f")
        self.pushButton_2f = QtWidgets.QPushButton(parent=self.groupBox_ele)
        self.pushButton_2f.setGeometry(QtCore.QRect(210, 140, 88, 26))
        self.pushButton_2f.setObjectName("pushButton_2f")
        self.pushButton_3f = QtWidgets.QPushButton(parent=self.groupBox_ele)
        self.pushButton_3f.setGeometry(QtCore.QRect(210, 80, 88, 26))
        self.pushButton_3f.setObjectName("pushButton_3f")
        self.label_ele_3f = QtWidgets.QLabel(parent=self.groupBox_ele)
        self.label_ele_3f.setGeometry(QtCore.QRect(190, 80, 16, 18))
        self.label_ele_3f.setObjectName("label_ele_3f")
        self.label_ele_2f = QtWidgets.QLabel(parent=self.groupBox_ele)
        self.label_ele_2f.setGeometry(QtCore.QRect(190, 140, 16, 18))
        self.label_ele_2f.setObjectName("label_ele_2f")
        self.label_ele_1f = QtWidgets.QLabel(parent=self.groupBox_ele)
        self.label_ele_1f.setGeometry(QtCore.QRect(190, 200, 16, 18))
        self.label_ele_1f.setObjectName("label_ele_1f")
        self.line = QtWidgets.QFrame(parent=self.groupBox_ele)
        self.line.setGeometry(QtCore.QRect(150, 40, 20, 211))
        self.line.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.label_6 = QtWidgets.QLabel(parent=self.groupBox_ele)
        self.label_6.setGeometry(QtCore.QRect(220, 40, 66, 18))
        self.label_6.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_6.setObjectName("label_6")
        self.groupBox_home = QtWidgets.QGroupBox(parent=dialog)
        self.groupBox_home.setGeometry(QtCore.QRect(440, 20, 581, 601))
        self.groupBox_home.setObjectName("groupBox_home")
        self.widget_graph = QtWidgets.QWidget(parent=self.groupBox_home)
        self.widget_graph.setGeometry(QtCore.QRect(30, 150, 521, 201))
        self.widget_graph.setObjectName("widget_graph")
        self.lcdNumber_temp = QtWidgets.QLCDNumber(parent=self.groupBox_home)
        self.lcdNumber_temp.setGeometry(QtCore.QRect(10, 50, 101, 51))
        self.lcdNumber_temp.setObjectName("lcdNumber_temp")
        self.lcdNumber_hu = QtWidgets.QLCDNumber(parent=self.groupBox_home)
        self.lcdNumber_hu.setGeometry(QtCore.QRect(150, 50, 101, 51))
        self.lcdNumber_hu.setObjectName("lcdNumber_hu")
        self.label_2 = QtWidgets.QLabel(parent=self.groupBox_home)
        self.label_2.setGeometry(QtCore.QRect(10, 30, 66, 18))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(parent=self.groupBox_home)
        self.label_3.setGeometry(QtCore.QRect(150, 30, 66, 18))
        self.label_3.setObjectName("label_3")
        self.lcdNumber_lux = QtWidgets.QLCDNumber(parent=self.groupBox_home)
        self.lcdNumber_lux.setGeometry(QtCore.QRect(20, 440, 101, 51))
        self.lcdNumber_lux.setObjectName("lcdNumber_lux")
        self.label_4 = QtWidgets.QLabel(parent=self.groupBox_home)
        self.label_4.setGeometry(QtCore.QRect(20, 410, 101, 18))
        self.label_4.setObjectName("label_4")
        self.pushButton_curOpen = QtWidgets.QPushButton(parent=self.groupBox_home)
        self.pushButton_curOpen.setGeometry(QtCore.QRect(20, 530, 121, 26))
        self.pushButton_curOpen.setObjectName("pushButton_curOpen")
        self.pushButton_curClose = QtWidgets.QPushButton(parent=self.groupBox_home)
        self.pushButton_curClose.setGeometry(QtCore.QRect(160, 530, 121, 26))
        self.pushButton_curClose.setObjectName("pushButton_curClose")
        self.pushButton_curStop = QtWidgets.QPushButton(parent=self.groupBox_home)
        self.pushButton_curStop.setGeometry(QtCore.QRect(290, 530, 121, 26))
        self.pushButton_curStop.setObjectName("pushButton_curStop")
        self.progressBar_cur = QtWidgets.QProgressBar(parent=self.groupBox_home)
        self.progressBar_cur.setGeometry(QtCore.QRect(160, 450, 241, 41))
        self.progressBar_cur.setProperty("value", 24)
        self.progressBar_cur.setObjectName("progressBar_cur")
        self.label_5 = QtWidgets.QLabel(parent=self.groupBox_home)
        self.label_5.setGeometry(QtCore.QRect(160, 410, 101, 18))
        self.label_5.setObjectName("label_5")
        self.label_airState = QtWidgets.QLabel(parent=self.groupBox_home)
        self.label_airState.setGeometry(QtCore.QRect(420, 40, 151, 18))
        self.label_airState.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_airState.setObjectName("label_airState")
        self.label_heatState = QtWidgets.QLabel(parent=self.groupBox_home)
        self.label_heatState.setGeometry(QtCore.QRect(420, 80, 151, 18))
        self.label_heatState.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_heatState.setObjectName("label_heatState")
        self.label_humiState = QtWidgets.QLabel(parent=self.groupBox_home)
        self.label_humiState.setGeometry(QtCore.QRect(420, 120, 151, 18))
        self.label_humiState.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_humiState.setObjectName("label_humiState")
        self.pushButton_curAuto = QtWidgets.QPushButton(parent=self.groupBox_home)
        self.pushButton_curAuto.setGeometry(QtCore.QRect(430, 530, 121, 26))
        self.pushButton_curAuto.setObjectName("pushButton_curAuto")
        self.label_curState = QtWidgets.QLabel(parent=self.groupBox_home)
        self.label_curState.setGeometry(QtCore.QRect(160, 410, 300, 20))
        self.label_curState.setText("")
        self.label_curState.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_curState.setObjectName("label_curState")
        self.pushButton_heat = QtWidgets.QPushButton(parent=self.groupBox_home)
        self.pushButton_heat.setGeometry(QtCore.QRect(290, 70, 151, 30))
        self.pushButton_heat.setObjectName("pushButton_heat")
        self.pushButton_air = QtWidgets.QPushButton(parent=self.groupBox_home)
        self.pushButton_air.setGeometry(QtCore.QRect(290, 30, 151, 30))
        self.pushButton_air.setObjectName("pushButton_air")
        self.pushButton_humi = QtWidgets.QPushButton(parent=self.groupBox_home)
        self.pushButton_humi.setGeometry(QtCore.QRect(290, 110, 151, 30))
        self.pushButton_humi.setObjectName("pushButton_humi")

        self.retranslateUi(dialog)
        QtCore.QMetaObject.connectSlotsByName(dialog)

        # 그래프 캔버스 생성 및 추가
        self.graph_canvas = GraphCanvas()
        layout = QtWidgets.QVBoxLayout(self.widget_graph)
        layout.addWidget(self.graph_canvas)
        self.widget_graph.setLayout(layout)
        
        # 디스플레이 매니저 생성
        self.display_manager = DisplayManager(
            self.lcdNumber_temp,
            self.lcdNumber_hu,
            self.graph_canvas
        )

        # 버튼 클릭 이벤트 연결
        self.pushButton_1f.clicked.connect(self.elevator_1f_call)
        self.pushButton_2f.clicked.connect(self.elevator_2f_call)
        self.pushButton_3f.clicked.connect(self.elevator_3f_call)
        self.pushButton_e.clicked.connect(self.entrance_open)
        self.pushButton_air.clicked.connect(self.control_air)
        self.pushButton_heat.clicked.connect(self.control_heat)
        self.pushButton_humi.clicked.connect(self.control_hum)
        self.pushButton_curOpen.clicked.connect(self.curtain_open)
        self.pushButton_curClose.clicked.connect(self.curtain_close)
        self.pushButton_curStop.clicked.connect(self.curtain_stop)
        self.pushButton_curAuto.clicked.connect(self.curtain_enable_auto)
        self.progressBar_cur.setRange(0, 100)

        # 커튼 상태 관리
        self.curtain_max_steps = int(1.3 * 2048)
        self.curtain_auto_mode = True
        self.curtain_motion_state = "정지"
        self.curtain_status_message = ""

        # 초기 상태: 모든 체크 아이콘 숨김
        self.label_ele_1f.setText("")
        self.label_ele_2f.setText("")
        self.label_ele_3f.setText("")

    def retranslateUi(self, dialog):
        """UI 텍스트 설정"""
        _translate = QtCore.QCoreApplication.translate
        dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.groupBox_e.setTitle(_translate("Dialog", "공동현관"))
        self.label_e_id.setText(_translate("Dialog", "ID"))
        self.label_e_approv.setText(_translate("Dialog", ""))
        self.pushButton_e.setText(_translate("Dialog", "공동현관 열기"))
        self.label_e_open.setText(_translate("Dialog", " "))
        self.groupBox_ele.setTitle(_translate("Dialog", "엘리베이터"))
        self.label.setText(_translate("Dialog", "층"))
        self.pushButton_1f.setText(_translate("Dialog", "1층"))
        self.pushButton_2f.setText(_translate("Dialog", "2층"))
        self.pushButton_3f.setText(_translate("Dialog", "3층"))
        self.groupBox_home.setTitle(_translate("Dialog", "Home"))
        self.label_2.setText(_translate("Dialog", "온도(C)"))
        self.label_3.setText(_translate("Dialog", "습도(%)"))
        self.label_4.setText(_translate("Dialog", "외부조도(LUX)"))
        self.label_airState.setText(_translate("Dialog", "Auto"))
        self.label_heatState.setText(_translate("Dialog", "Auto"))
        self.label_humiState.setText(_translate("Dialog", "Auto"))
        self.pushButton_heat.setText(_translate("Dialog", "히터 ON/OFF/Auto"))
        self.pushButton_air.setText(_translate("Dialog", "에어컨 ON/OFF/Auto"))
        self.pushButton_humi.setText(_translate("Dialog", "가습기 ON/OFF/Auto"))
        self.pushButton_curOpen.setText(_translate("Dialog", "커튼 OPEN"))
        self.pushButton_curClose.setText(_translate("Dialog", "커튼 CLOSE"))
        self.pushButton_curStop.setText(_translate("Dialog", "커튼 STOP"))
        self.pushButton_curAuto.setText(_translate("Dialog", "커튼 Auto 복귀"))
        self.label_5.setText(_translate("Dialog", "커튼 열림 정도"))
        self.label_curState.setText(_translate("Dialog", " "))

    def entrance_open(self):
        """출입문 열기"""
        try:
            response = requests.post(
                f"{self.api_url}/api/command",
                json={
                    'device_id': 'ent_001',
                    'metric_name': 'MOTOR',
                    'value': '1'
                },
                timeout=5
            )

            if response.json().get('success'):
                self.label_e_approv.setText("✅")
            else:
                print(f"[ERROR] {response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[ERROR] 명령 전송 실패: {e}")

    def elevator_1f_call(self):
        """엘리베이터 1층 호출"""
        try:
            response = requests.post(
                f"{self.api_url}/api/command",
                json={
                    'device_id': 'ele_001',
                    'metric_name': 'FLOOR',
                    'value': '1'
                },
                timeout=5
            )

            if response.json().get('success'):
                self.label_ele_1f.setText("✅")
            else:
                print(f"[ERROR] {response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[ERROR] 명령 전송 실패: {e}")

    def elevator_2f_call(self):
        """엘리베이터 2층 호출"""
        try:
            response = requests.post(
                f"{self.api_url}/api/command",
                json={
                    'device_id': 'ele_001',
                    'metric_name': 'FLOOR',
                    'value': '2'
                },
                timeout=5
            )

            if response.json().get('success'):
                self.label_ele_2f.setText("✅")
            else:
                print(f"[ERROR] {response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[ERROR] 명령 전송 실패: {e}")

    def elevator_3f_call(self):
        """엘리베이터 3층 호출"""
        try:
            response = requests.post(
                f"{self.api_url}/api/command",
                json={
                    'device_id': 'ele_001',
                    'metric_name': 'FLOOR',
                    'value': '3'
                },
                timeout=5
            )

            if response.json().get('success'):
                self.label_ele_3f.setText("✅")
            else:
                print(f"[ERROR] {response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[ERROR] 명령 전송 실패: {e}")

    def control_air(self):
        """에어컨 제어 (ON/OFF/Auto)"""
        try:
            if self.air_state == 0:
                value = '1'
                self.air_state = 1
                self.label_airState.setText("ON")

            elif self.air_state == 1:
                value = '0'
                self.air_state = 2
                self.label_airState.setText("OFF")
            else:
                value = '-1'
                self.air_state = 0
                self.label_airState.setText("Auto")
            
            response = requests.post(
                f"{self.api_url}/api/command",
                json={
                    'device_id': 'dht_001',
                    'metric_name': 'AIR',
                    'value': value
                },
                timeout=5
            )

            if not response.json().get('success'):
                print(f"[ERROR] {response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[ERROR] 명령 전송 실패: {e}")

    def control_heat(self):
        """히터 제어 (ON/OFF/Auto)"""
        try:
            if self.heat_state == 0:
                value = '1'
                self.heat_state = 1
                self.label_heatState.setText("ON")
            elif self.heat_state == 1:
                value = '0'
                self.heat_state = 2
                self.label_heatState.setText("OFF")
            else:
                value = '-1'
                self.heat_state = 0
                self.label_heatState.setText("Auto")
            
            response = requests.post(
                f"{self.api_url}/api/command",
                json={
                    'device_id': 'dht_001',
                    'metric_name': 'HEAT',
                    'value': value
                },
                timeout=5
            )

            if not response.json().get('success'):
                print(f"[ERROR] {response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[ERROR] 명령 전송 실패: {e}")

    def control_hum(self):
        """가습기 제어 (ON/OFF/Auto)"""
        try:
            if self.hum_state == 0:
                value = '1'
                self.hum_state = 1
                self.label_humiState.setText("ON")
            elif self.hum_state == 1:
                value = '0'
                self.hum_state = 2
                self.label_humiState.setText("OFF")
            else:
                value = '-1'
                self.hum_state = 0
                self.label_humiState.setText("Auto")
            
            response = requests.post(
                f"{self.api_url}/api/command",
                json={
                    'device_id': 'dht_001',
                    'metric_name': 'HUMI',
                    'value': value
                },
                timeout=5
            )

            if not response.json().get('success'):
                print(f"[ERROR] {response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[ERROR] 명령 전송 실패: {e}")

    def curtain_open(self):
        """커튼 열기"""
        try:
            response = requests.post(
                f"{self.api_url}/api/command",
                json={
                    'device_id': 'cur_001',
                    'metric_name': 'MOTOR',
                    'value': 'OPEN'
                },
                timeout=5
            )

            if response.json().get('success'):
                self._mark_manual_mode_requested()
                self._set_curtain_status_message("요청:OPEN")
            else:
                print(f"[ERROR] {response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[ERROR] 명령 전송 실패: {e}")

    def curtain_close(self):
        """커튼 닫기"""
        try:
            response = requests.post(
                f"{self.api_url}/api/command",
                json={
                    'device_id': 'cur_001',
                    'metric_name': 'MOTOR',
                    'value': 'CLOSE'
                },
                timeout=5
            )

            if response.json().get('success'):
                self._mark_manual_mode_requested()
                self._set_curtain_status_message("요청:CLOSE")
            else:
                print(f"[ERROR] {response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[ERROR] 명령 전송 실패: {e}")

    def curtain_stop(self):
        """커튼 정지"""
        try:
            response = requests.post(
                f"{self.api_url}/api/command",
                json={
                    'device_id': 'cur_001',
                    'metric_name': 'MOTOR',
                    'value': 'STOP'
                },
                timeout=5
            )

            if response.json().get('success'):
                self._mark_manual_mode_requested()
                self._set_curtain_status_message("요청:STOP")
            else:
                print(f"[ERROR] {response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[ERROR] 명령 전송 실패: {e}")

    def curtain_enable_auto(self):
        """커튼 AUTO 모드 활성화"""
        try:
            response = requests.post(
                f"{self.api_url}/api/command",
                json={
                    'device_id': 'cur_001',
                    'metric_name': 'MODE',
                    'value': 'AUTO'
                },
                timeout=5
            )

            if response.json().get('success'):
                self._set_curtain_status_message("요청:AUTO")
            else:
                print(f"[ERROR] {response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[ERROR] 명령 전송 실패: {e}")

    def _handle_curtain_direction(self, value):
        """커튼 방향 처리"""
        try:
            direction = int(float(value))
            if direction > 0:
                motion_text = "열림 중"
            elif direction < 0:
                motion_text = "닫힘 중"
            else:
                motion_text = "정지"
            
            self._set_curtain_motion_state(motion_text)
        except (ValueError, TypeError):
            print(f"[ERROR] 잘못된 커튼 방향값: {value}")

    def _update_curtain_progress(self, step_value):
        """커튼 진행률 업데이트"""
        try:
            steps = float(step_value)
            
            if self.curtain_max_steps <= 0:
                return
            
            percentage = max(0, min(100, int((steps / self.curtain_max_steps) * 100)))
            self.progressBar_cur.setValue(percentage)
        except (ValueError, TypeError):
            print(f"[ERROR] 잘못된 커튼 스텝값: {step_value}")

    def _set_curtain_motion_state(self, text):
        """커튼 모션 상태 설정"""
        self.curtain_motion_state = text
        self.curtain_status_message = ""
        self._refresh_curtain_status_label()

    def _set_curtain_status_message(self, text):
        """커튼 상태 메시지 설정"""
        self.curtain_status_message = text
        self._refresh_curtain_status_label()

    def _refresh_curtain_status_label(self):
        """커튼 상태 라벨 새로고침"""
        mode_text = "AUTO" if self.curtain_auto_mode else "MANUAL"
        parts = [f"모드: {mode_text}", f"상태: {self.curtain_motion_state}"]
        if self.curtain_status_message:
            parts.append(self.curtain_status_message)
        self.label_curState.setText('  |  '.join(filter(None, parts)))

    def _mark_manual_mode_requested(self):
        """수동 모드 요청 표시"""
        if self.curtain_auto_mode:
            self.curtain_auto_mode = False

    def handle_serial_data(self, state: dict):
        """상태에 따라 UI 업데이트"""
        if not state:
            return
        device_id = state.get('device_id')
        data_type = state.get('data_type', '')
        metric_name = state.get('metric_name', '')
        value = state.get('value', '')
        
        # 그래프와 LCD 업데이트용 데이터 생성
        if data_type == "SEN":
            if device_id[:3] == "dht":
                if metric_name == 'HUM':
                    serial_data = f"SEN,{metric_name},{value}"
                    self.display_manager.update_display(serial_data)
                
                elif metric_name == 'TEM':
                    serial_data = f"SEN,{metric_name},{value}"
                    self.display_manager.update_display(serial_data)

            if device_id[:3] == "ent":
                if metric_name == 'RFID_ACCESS':
                    self.le_e_id.setText(str(value))
                    self.label_e_approv.setText("✅")
                    
                elif metric_name == 'RFID_DENY':
                    self.le_e_id.setText(str(value))
                    self.label_e_approv.setText("❌")
            
                elif metric_name == 'MOTOR':                
                    print("[DEBUG] device_name: " + device_id[:3] + " metric_name: " + metric_name + " value: " + value)
                    if value == "-1":
                        self.label_e_open.setText(" ")
                        self.le_e_id.clear()
                        self.label_e_approv.setText(" ")

                    elif value == "1":
                        self.label_e_open.setText("공동현관 열림")

            elif device_id[:3] == "ele":
                if metric_name == 'FLOOR':
                    floor_num = int(value)
                    self.lcdNumber_floor.display(floor_num)
                    self.label_ele_3f

            elif device_id[:3] == "cur":
                if metric_name == "LIGHT":
                    self.lcdNumber_lux.display(float(value))

                elif metric_name == "CUR_STEP":
                    self._update_curtain_progress(value)

                elif metric_name == "MOTOR_DIR":
                    self._handle_curtain_direction(value)

        if data_type == "ACK":
            if device_id[:3] == "ele":
                if metric_name == "FLOOR" or metric_name == "CANCEL":
                    if value == "1":
                        self.label_ele_1f.setText(" ")
                    elif value == "2":
                        self.label_ele_2f.setText(" ")
                    elif value == "3":
                        self.label_ele_3f.setText(" ")

    def start_polling(self):
        """상태 폴링 시작"""
        self.polling_thread = threading.Thread(
            target=self._poll_state,
            daemon=True
        )
        self.polling_thread.start()

    def stop_polling(self):
        """상태 폴링 중지"""
        self.running = False
        if self.polling_thread:
            self.polling_thread.join(timeout=2)

    def _poll_state(self):
        """주기적으로 서버에서 상태 조회"""
        while self.running:
            try:
                response = requests.get(
                    f"{self.api_url}/api/state",
                    timeout=2
                )
                state = response.json()

                # UI 업데이트
                self.handle_serial_data(state)

            except requests.RequestException as e:
                print(f"[ERROR] 상태 조회 실패: {e}")

            time.sleep(self.polling_interval)


def main():
    """메인 함수"""
    app = QtWidgets.QApplication(sys.argv)
    dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(dialog)
    ui.start_polling()
    dialog.show()

    try:
        sys.exit(app.exec())
    finally:
        ui.stop_polling()


if __name__ == "__main__":
    main()