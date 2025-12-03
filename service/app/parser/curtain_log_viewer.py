import os
import sys
from datetime import datetime, timedelta

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

import pymysql


COLUMNS = [
    "id",
    "device_id",
    "created_at",
    "light_value",
    "motor_direction",
    "current_step",
    "max_steps",
]


class CurtainLogTableModel(QAbstractTableModel):
    def __init__(self, rows=None, parent=None):
        super().__init__(parent)
        self._rows = rows or []

    def rowCount(self, parent=QModelIndex()):  # type: ignore[override]
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):  # type: ignore[override]
        return len(COLUMNS)

    def data(self, index, role=Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self._rows[index.row()]
        col_name = COLUMNS[index.column()]
        value = row.get(col_name)
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value) if value is not None else ""

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # type: ignore[override]
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return COLUMNS[section]
        return str(section + 1)

    def setRows(self, rows):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()


class CurtainLogViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Curtain Log Viewer")
        self.resize(1000, 600)

        self.connection = None

        # Top filter area
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)

        self.device_edit = QLineEdit()
        self.device_edit.setPlaceholderText("device_id (빈칸이면 전체)")

        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(1, 24 * 60)
        self.minutes_spin.setValue(60)

        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 10000)
        self.limit_spin.setValue(200)

        refresh_button = QPushButton("최근 데이터 갱신")
        refresh_button.clicked.connect(self.refresh_data)

        filter_layout.addWidget(QLabel("device_id:"))
        filter_layout.addWidget(self.device_edit)
        filter_layout.addWidget(QLabel("최근 분:"))
        filter_layout.addWidget(self.minutes_spin)
        filter_layout.addWidget(QLabel("최대 행 수:"))
        filter_layout.addWidget(self.limit_spin)
        filter_layout.addWidget(refresh_button)

        # Table
        self.table = QTableView()
        self.model = CurtainLogTableModel([])
        self.table.setModel(self.model)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)

        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.addWidget(filter_widget)
        main_layout.addWidget(self.table)
        self.setCentralWidget(central)

        # Open DB and initial load
        try:
            self.connection = self.create_connection()
        except Exception as e:  # pragma: no cover - UI dialog
            QMessageBox.critical(self, "DB 연결 오류", str(e))
            sys.exit(1)

        # 초기 1회 조회 후, 5초마다 자동 새로고침
        self.refresh_data()

        self.timer = QTimer(self)
        self.timer.setInterval(5000)  # 5초
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start()

    def create_connection(self):
        # 1) tools/.env 파일이 있으면 먼저 읽어서 os.environ에 채운다.
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" not in line:
                            continue
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip("'\"")
                        if key and key not in os.environ:
                            os.environ[key] = value
            except Exception:
                # env 파일 읽기 실패 시에는 조용히 무시하고, 기존 환경변수만 사용
                pass

        host = os.getenv("CURTAIN_DB_HOST")
        port = int(os.getenv("CURTAIN_DB_PORT", "3306"))
        user = os.getenv("CURTAIN_DB_USER")
        password = os.getenv("CURTAIN_DB_PASSWORD")
        db_name = os.getenv("CURTAIN_DB_NAME", "ioclean")

        missing = [
            name
            for name, value in [
                ("CURTAIN_DB_HOST", host),
                ("CURTAIN_DB_USER", user),
                ("CURTAIN_DB_PASSWORD", password),
            ]
            if not value
        ]
        if missing:
            raise RuntimeError(
                "환경변수 설정 필요: " + ", ".join(missing)
            )

        return pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

    def refresh_data(self):
        print("refresh_data called", datetime.now())

        if self.connection is None:
            return

        device_id = self.device_edit.text().strip()
        minutes = self.minutes_spin.value()
        limit = self.limit_spin.value()

        since_time = datetime.utcnow() - timedelta(minutes=minutes)

        sql = "SELECT id, device_id, created_at, light_value, motor_direction, current_step, max_steps " \
              "FROM curtain_log WHERE created_at >= %s"
        params = [since_time]

        if device_id:
            sql += " AND device_id = %s"
            params.append(device_id)

        sql += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
        except Exception as e:  # pragma: no cover - UI dialog
            QMessageBox.critical(self, "조회 오류", str(e))
            return

        self.model.setRows(rows)


def main():
    app = QApplication(sys.argv)
    viewer = CurtainLogViewer()
    viewer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
