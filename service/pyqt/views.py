from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QProgressBar, QTextEdit, QMainWindow, QStackedWidget)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen


class HumidityCircle(QWidget):
    """습도 원그래프"""
    def __init__(self):
        super().__init__()
        self.value = 50
        self.setMinimumSize(200, 200)
    
    def set_value(self, val):
        self.value = val
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 배경 원
        rect = QRect(20, 20, 160, 160)
        painter.setPen(QPen(QColor("#0066cc"), 2))
        painter.setBrush(QBrush(QColor("#e8f0ff")))
        painter.drawEllipse(rect)
        
        # 진행 원
        painter.setPen(QPen(QColor("#0066cc"), 8))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        start_angle = 90 * 16
        span_angle = int((self.value / 100) * 360) * 16
        painter.drawArc(rect, start_angle, -span_angle)
        
        # 텍스트
        painter.setPen(QColor("#0066cc"))
        font = QFont("Arial", 20, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.value:.0f}%")


class HomePage(QWidget):
    """홈페이지"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
    
    def initUI(self):
        """UI 초기화"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # 상단: 센서 정보 (60% 높이)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(30)
        
        # 온도 카드
        temp_card = self.create_sensor_card("온도", "🌡️", "#1E88E5")
        self.temp_display = temp_card['value']
        top_layout.addWidget(temp_card['widget'], 1)
        
        # 습도 원그래프
        humidity_widget = self.create_humidity_circle()
        self.humidity_circle = humidity_widget['circle']
        self.humidity_display = humidity_widget['value']
        top_layout.addWidget(humidity_widget['widget'], 1)
        
        # 조도 카드
        illum_card = self.create_sensor_card_with_bar("조도", "☀️", "#42A5F5")
        self.illumination_display = illum_card['value']
        self.illumination_bar = illum_card['bar']
        top_layout.addWidget(illum_card['widget'], 1)
        
        # 이벤트 로그
        log_widget = self._create_log_widget()
        top_layout.addWidget(log_widget, 1)
        
        top_container = QWidget()
        top_container.setLayout(top_layout)
        main_layout.addWidget(top_container, 3)
        
        # 구분선
        separator = QWidget()
        separator.setStyleSheet("background-color: #cccccc;")
        separator.setMinimumHeight(2)
        main_layout.addWidget(separator)
        
        # 하단: 수동 제어 (40% 높이)
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # 가습기
        humidifier_layout = self.create_control_group("가습기", "💧")
        self.humidifier_status = humidifier_layout['status']
        self.humidifier_value = humidifier_layout['value']
        self.humidifier_on_btn = humidifier_layout['on_btn']
        self.humidifier_off_btn = humidifier_layout['off_btn']
        bottom_layout.addLayout(humidifier_layout['layout'], 1)
        
        # 에어컨
        ac_layout = self.create_control_group("에어컨", "❄️")
        self.ac_status = ac_layout['status']
        self.ac_value = ac_layout['value']
        self.ac_on_btn = ac_layout['on_btn']
        self.ac_off_btn = ac_layout['off_btn']
        bottom_layout.addLayout(ac_layout['layout'], 1)
        
        # 히터
        heater_layout = self.create_control_group("히터", "🔥")
        self.heater_status = heater_layout['status']
        self.heater_value = heater_layout['value']
        self.heater_on_btn = heater_layout['on_btn']
        self.heater_off_btn = heater_layout['off_btn']
        bottom_layout.addLayout(heater_layout['layout'], 1)
        
        # 커튼
        curtain_layout = self.create_control_group("커튼", "🪟")
        self.curtain_status = curtain_layout['status']
        self.curtain_value = curtain_layout['value']
        self.curtain_open_btn = curtain_layout['on_btn']
        self.curtain_open_btn.setText("개폐")
        self.curtain_close_btn = curtain_layout['off_btn']
        self.curtain_close_btn.setText("폐쇄")
        bottom_layout.addLayout(curtain_layout['layout'], 1)
        
        bottom_container = QWidget()
        bottom_container.setLayout(bottom_layout)
        main_layout.addWidget(bottom_container, 2)
        
        self.setLayout(main_layout)
    
    def _create_log_widget(self):
        """로그 위젯 생성"""
        log_widget = QWidget()
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(10)
        
        log_title = QLabel("📋 이벤트 로그")
        log_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        log_title.setStyleSheet("color: #0066cc;")
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                color: #0066cc;
                border: 2px solid #0066cc;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Courier New';
                font-size: 15px;
            }
        """)
        
        log_layout.addWidget(log_title)
        log_layout.addWidget(self.log_text)
        log_widget.setLayout(log_layout)
        return log_widget
    
    def create_humidity_circle(self):
        """습도 원그래프"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        title = QLabel("습도")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #333333;")
        
        circle = HumidityCircle()
        value_label = QLabel("50.0%")
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #0066cc;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(circle, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        widget.setLayout(layout)
        widget.setStyleSheet("""
            QWidget {
                background-color: #f0f4ff;
                border: 2px solid #0066cc;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        return {'widget': widget, 'circle': circle, 'value': value_label}
    
    def create_sensor_card(self, label, icon, color):
        """센서 카드 생성"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(20)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 40))
        
        info_layout = QVBoxLayout()
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        label_widget.setStyleSheet("color: #666666;")
        
        value_label = QLabel("0.0")
        value_label.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        
        info_layout.addWidget(label_widget)
        info_layout.addWidget(value_label)
        
        layout.addWidget(icon_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        
        widget.setLayout(layout)
        widget.setStyleSheet("""
            QWidget {
                background-color: #f0f4ff;
                border: 2px solid #0066cc;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        widget.setMinimumHeight(100)
        
        return {'widget': widget, 'value': value_label}
    
    def create_sensor_card_with_bar(self, label, icon, color):
        """프로그레스바가 있는 센서 카드"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        top_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 40))
        
        info_layout = QVBoxLayout()
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        label_widget.setStyleSheet("color: #666666;")
        value_label = QLabel("0 lux")
        value_label.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        info_layout.addWidget(label_widget)
        info_layout.addWidget(value_label)
        
        top_layout.addWidget(icon_label)
        top_layout.addLayout(info_layout)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        progress_bar = QProgressBar()
        progress_bar.setMaximum(10000)
        progress_bar.setValue(500)
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #e8e8e8;
                border: 2px solid {color};
                border-radius: 8px;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(progress_bar)
        
        widget.setLayout(layout)
        widget.setStyleSheet("""
            QWidget {
                background-color: #f0f4ff;
                border: 2px solid #0066cc;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        widget.setMinimumHeight(140)
        
        return {'widget': widget, 'value': value_label, 'bar': progress_bar}
    
    def create_control_group(self, label, icon):
        """제어 그룹 생성"""
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        left = QVBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 32))
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        label_widget.setStyleSheet("color: #333333;")
        status_label = QLabel("자동 제어")
        status_label.setFont(QFont("Arial", 10))
        status_label.setStyleSheet("color: #999999;")
        
        value_label = QLabel("OFF")
        value_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #ff3333;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        left.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        left.addWidget(label_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        left.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignCenter)
        left.addWidget(status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        on_btn = self.create_control_button("ON", "#00cc00")
        off_btn = self.create_control_button("OFF", "#ff3333")
        
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(on_btn)
        btn_layout.addWidget(off_btn)
        
        layout.addLayout(left, 1)
        layout.addLayout(btn_layout, 1)
        
        return {
            'layout': layout,
            'status': status_label,
            'value': value_label,
            'on_btn': on_btn,
            'off_btn': off_btn
        }
    
    def create_control_button(self, text, color):
        """제어 버튼"""
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        btn.setMinimumHeight(40)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """)
        return btn


class OutsidePage(QWidget):
    """실외 페이지 (엘리베이터 + 공동현관)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
    
    def initUI(self):
        """UI 초기화"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(40)
        
        # 왼쪽: 엘리베이터
        left_layout = self.create_elevator_panel()
        main_layout.addLayout(left_layout, 1)
        
        # 오른쪽: 공동현관
        right_layout = self.create_entry_panel()
        main_layout.addLayout(right_layout, 1)
        
        self.setLayout(main_layout)
    
    def create_elevator_panel(self):
        """엘리베이터 패널"""
        layout = QVBoxLayout()
        layout.setSpacing(30)
        
        title = QLabel("🛗 엘리베이터")
        title.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #0066cc;")
        layout.addWidget(title)
        
        status_box = QWidget()
        status_layout = QVBoxLayout()
        
        status_label = QLabel("상태: 대기중")
        status_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        status_label.setStyleSheet("color: #333333;")
        
        floor_label = QLabel("현재 층: 1층")
        floor_label.setFont(QFont("Arial", 18))
        floor_label.setStyleSheet("color: #666666;")
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(floor_label)
        status_box.setLayout(status_layout)
        status_box.setStyleSheet("""
            QWidget {
                background-color: #f0f4ff;
                border: 3px solid #0066cc;
                border-radius: 15px;
                padding: 30px;
            }
        """)
        self.elevator_status_label = status_label
        layout.addWidget(status_box)
        
        layout.addSpacing(40)
        
        call_btn = QPushButton("엘리베이터 호출\n(공동현관 층)")
        call_btn.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        call_btn.setMinimumHeight(120)
        call_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
            QPushButton:pressed {
                background-color: #003d7a;
            }
        """)
        self.call_elevator_btn = call_btn
        layout.addWidget(call_btn)
        
        layout.addStretch()
        return layout
    
    def create_entry_panel(self):
        """공동현관 패널"""
        layout = QVBoxLayout()
        layout.setSpacing(30)
        
        title = QLabel("🚪 공동현관")
        title.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #0066cc;")
        layout.addWidget(title)
        
        # 태그 정보
        tag_box = self._create_info_box("태그 인식", "미감지 ⏳", "#fff9f0", "#ff9900")
        self.tag_status_label = tag_box['status']
        layout.addWidget(tag_box['widget'])
        
        # 사용자 정보
        user_box = self._create_info_box("사용자 정보", "인증: 확인 대기중 ⏳", "#fff9f0", "#ff9900")
        self.user_status_label = user_box['status']
        layout.addWidget(user_box['widget'])
        
        # 문 상태
        door_box = self._create_info_box("현관문", "🔒 잠김", "#f0fff0", "#00aa00")
        self.door_status_label = door_box['status']
        layout.addWidget(door_box['widget'])
        
        layout.addStretch()
        return layout
    
    def _create_info_box(self, title, status_text, bg_color, border_color):
        """정보 박스 생성"""
        box = QWidget()
        box_layout = QVBoxLayout()
        box_layout.setSpacing(20)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333;")
        
        status_label = QLabel(f"상태: {status_text}")
        status_label.setFont(QFont("Arial", 14))
        status_label.setStyleSheet(f"color: {border_color};")
        
        box_layout.addWidget(title_label)
        box_layout.addWidget(status_label)
        
        box.setLayout(box_layout)
        box.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 10px;
                padding: 20px;
            }}
        """)
        
        return {'widget': box, 'status': status_label}


class MainWindow(QMainWindow):
    """메인 윈도우"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏠 스마트홈 시스템")
        self.setGeometry(100, 100, 1800, 800)
        self.setStyleSheet("background-color: #ffffff;")
        
        self.initUI()
    
    def initUI(self):
        """UI 초기화"""
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 왼쪽: 네비게이션 (세로)
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(15, 20, 15, 20)
        nav_layout.setSpacing(15)
        
        home_btn = self.create_nav_button("🏠 홈")
        outside_btn = self.create_nav_button("🚪 실외")
        
        home_btn.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        outside_btn.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        
        nav_layout.addWidget(home_btn)
        nav_layout.addWidget(outside_btn)
        nav_layout.addStretch()
        
        nav_widget = QWidget()
        nav_widget.setLayout(nav_layout)
        nav_widget.setStyleSheet("""
            QWidget {
                background-color: #0066cc;
            }
        """)
        nav_widget.setMinimumWidth(120)
        main_layout.addWidget(nav_widget)
        
        # 오른쪽: 페이지
        self.pages = QStackedWidget()
        
        self.home_page = HomePage()
        self.outside_page = OutsidePage()
        
        self.pages.addWidget(self.home_page)
        self.pages.addWidget(self.outside_page)
        
        main_layout.addWidget(self.pages, 1)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def create_nav_button(self, text):
        """네비게이션 버튼"""
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn.setMinimumHeight(50)
        btn.setMinimumWidth(100)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
        """)
        return btn