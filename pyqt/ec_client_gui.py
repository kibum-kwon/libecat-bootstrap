# -*- coding: utf-8 -*-

import sys
import os
import socket
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QVBoxLayout, QLabel, QPushButton, QDial, QLineEdit, QGraphicsView, QGraphicsScene, QFrame, QDialog, QTextEdit
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Connection")
        layout = QVBoxLayout()

        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText("IP Address")
        layout.addWidget(self.ip_input)

        self.port_input = QLineEdit(self)
        self.port_input.setPlaceholderText("Port")
        layout.addWidget(self.port_input)

        connect_button = QPushButton("Connect", self)
        connect_button.clicked.connect(self.accept)
        layout.addWidget(connect_button)

        self.setLayout(layout)

    def get_connection_info(self):
        return self.ip_input.text(), self.port_input.text()

class SocketSignals(QObject):
    receivedData = pyqtSignal(str)

class SkeletonPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.is_auto = False
        self.current_speed = 0  
        self.angle_change_cmd = "tmo"
        self.speed_change_cmd = "twv"
        self.direction_change_cmd = "wro"
        self.direction_params = "1"  
        self.initUI()
        self.socket = None
        self.signals = SocketSignals()
        self.signals.receivedData.connect(self.log_message)

    def initUI(self):
        self.window_width = 1200
        self.window_height = 800
        self.setGeometry(100, 100, self.window_width, self.window_height)
        self.setWindowTitle('Skeleton Panel')

        # Set background image
        self.image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'doc/background.jpg'))
        self.background = QGraphicsView(self)
        self.scene = QGraphicsScene()
        self.background.setScene(self.scene)
        self.background.setStyleSheet("background: transparent; border: none;")
        self.background.setGeometry(0, 0, self.window_width, self.window_height)
        self.bg_image = QPixmap(self.image_path).scaled(self.window_width, self.window_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.scene.addPixmap(self.bg_image)

        # Main layout
        layout = QGridLayout()
        self.setLayout(layout)

        # Frame for Robot Camera View
        self.camera_frame = QFrame(self)
        self.camera_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.camera_frame.setLineWidth(2)
        self.camera_frame.setMinimumSize(int(self.window_width * 0.45), int(self.window_height * 0.45))
        camera_layout = QVBoxLayout(self.camera_frame)

        screen_label = QLabel('Message', self)
        screen_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        screen_label.setStyleSheet("border: 2px solid black; color: black; font-weight: bold;")
        camera_layout.addWidget(screen_label)

        self.message_display = QTextEdit(self)
        self.message_display.setReadOnly(True)
        self.message_display.setMinimumSize(int(self.window_width * 0.4), int(self.window_height * 0.4))
        camera_layout.addWidget(self.message_display)

        # Frame for Speed/Angle display
        speed_angle_frame = QFrame(self)
        speed_angle_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        speed_angle_frame.setLineWidth(2)
        speed_angle_layout = QGridLayout(speed_angle_frame)

        # Frame for Wheel controls (right side)
        right_frame = QFrame(self)
        right_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        right_frame.setLineWidth(2)
        right_layout = QGridLayout(right_frame)

        # Speed display label
        self.speed_label = QLabel('Speed: 0', self)
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.speed_label.setStyleSheet("color: black; font-weight: bold; font-size: 24px;")
        speed_angle_layout.addWidget(self.speed_label, 0, 0, 1, 2)

        # Angle display for wheels
        self.wheel_labels = []
        self.wheel_value_labels = []
        for i in range(1, 5):
            angle_label = QLabel(f'Wheel {i} Angle:', self)
            angle_label.setAlignment(Qt.AlignCenter)
            angle_label.setStyleSheet("color: black; font-weight: bold; font-size: 24px;")

            angle_value_label = QLabel('0', self)
            angle_value_label.setAlignment(Qt.AlignCenter)
            angle_value_label.setStyleSheet("color: black; font-weight: bold; font-size: 20px;")

            vbox = QVBoxLayout()
            vbox.addWidget(angle_label)
            vbox.addWidget(angle_value_label)

            if i % 2 == 1:
                row = 1 + (i - 1) // 2
                col = 0
            else:
                row = 1 + (i - 1) // 2
                col = 1
            speed_angle_layout.addLayout(vbox, row, col)

            self.wheel_labels.append((angle_label, angle_value_label))
            self.wheel_value_labels.append(angle_value_label)

        # Wheel controls
        self.add_wheel_control(right_layout, 1, 0, 0, include_speed_buttons=False)  
        self.add_wheel_control(right_layout, 1, 1, 1, include_speed_buttons=False)  
        self.add_wheel_control(right_layout, 2, 0, 2, include_speed_buttons=False)  
        self.add_wheel_control(right_layout, 2, 1, 3, include_speed_buttons=False)  

        # Start and Stop buttons
        start_button = QPushButton('Start', self)
        stop_button = QPushButton('Stop', self)

        # Set button size (width x height)
        start_button.setFixedSize(100, 50) 
        stop_button.setFixedSize(100, 50)

        start_button.clicked.connect(self.start_robot)
        stop_button.clicked.connect(self.stop_robot)

        right_layout.addWidget(start_button, 0, 0, 1, 1)
        right_layout.addWidget(stop_button, 0, 1, 1, 1)

        # Speed control buttons and input field
        button_layout = QGridLayout()
        button_layout.setSpacing(0)
        button_layout.setContentsMargins(0, 0, 0, 0)

        acceleration_button = QPushButton(self)
        deceleration_button = QPushButton(self)



        # Set icons for speed control buttons
        acceleration_icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'doc/increase.PNG'))
        deceleration_icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'doc/decrease.PNG'))
        
        acceleration_button.setIcon(QIcon(acceleration_icon_path))
        deceleration_button.setIcon(QIcon(deceleration_icon_path))

        # Configure button size and style
        icon_size = QSize(50, 50)
        acceleration_button.setIconSize(icon_size)
        deceleration_button.setIconSize(icon_size)
        acceleration_button.setFixedSize(50, 50)
        acceleration_button.setStyleSheet("border: none; margin: 0px; padding: 0px;")
        deceleration_button.setFixedSize(50, 50)
        deceleration_button.setStyleSheet("border: none; margin: 0px; padding: 0px;")

        # Input field for speed value
        speed_input = QLineEdit(self)
        speed_input.setFixedSize(120, 30)
        speed_input.setStyleSheet("font-size: 16px;")
        speed_input.setAlignment(Qt.AlignCenter)
        speed_input.setPlaceholderText("Speed")
        speed_input.returnPressed.connect(lambda: self.set_speed(speed_input))

        # Link buttons to speed control
        acceleration_button.clicked.connect(lambda: self.change_all_wheel_speeds(500000))
        deceleration_button.clicked.connect(lambda: self.change_all_wheel_speeds(-500000))

        button_layout.addWidget(acceleration_button, 0, 0)
        button_layout.addWidget(deceleration_button, 0, 1)
        button_layout.addWidget(speed_input, 0, 2)

        right_layout.addLayout(button_layout, 3, 0, 1, 2)

        # Connection button
        self.connect_button = QPushButton("Connection", self)
        self.connect_button.clicked.connect(self.show_connection_dialog)
        self.connect_button.setFixedHeight(50)
        right_layout.addWidget(self.connect_button, 4, 0, 1, 2)
        
        # Add Auto button
        self.auto_button = QPushButton("Auto", self)
        self.auto_button.clicked.connect(self.toggle_auto)
        self.auto_button.setStyleSheet("background-color: red;")
        self.auto_button.setFixedHeight(50)
        right_layout.addWidget(self.auto_button, 5, 0, 1, 1)

        # Add Send All Wheel Positions button
        self.send_button = QPushButton("Send All Wheel Angle", self)
        self.send_button.clicked.connect(self.send_all_wheel_positions)
        self.send_button.setFixedSize(200, 50)
        right_layout.addWidget(self.send_button, 5, 1, 1, 1)

        # Add frames to the main layout
        layout.addWidget(self.camera_frame, 0, 0, 2, 1)  
        layout.addWidget(speed_angle_frame, 2, 0)
        layout.addWidget(right_frame, 0, 1, 3, 1)
        layout.setRowStretch(0, 4)  
        layout.setRowStretch(1, 4)
        layout.setRowStretch(2, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        
        
#-----------------------------------------------------------후진 버튼 추가
        self.reverse_button = QPushButton("후진", self)
        self.reverse_button.setFixedHeight(50)  # 버튼 크기 설정
        self.reverse_button.clicked.connect(self.reverse_robot)  # 후진 메서드 연결
        right_layout.addWidget(self.reverse_button, 6, 0, 1, 2)  # 레이아웃에 추가

        self.show()
        
#------------------------------------------------------후진 버튼 추가
    def reverse_robot(self):
        # 후진 동작을 위한 로직을 구현합니다.
        self.current_speed = -500000  # 후진 속도 설정 (예: -500000)
        self.change_all_wheel_speeds(self.current_speed)  # 모든 바퀴 속도 조정
        self.update_speed_label()  # 속도 레이블 업데이트
        
    def update_speed_label(self):
        self.speed_label.setText(f'Speed: {self.current_speed}')  # 현재 속도를 레이블에 표시


# /*********************************angle angle angle angle *****************************************************************/ 


    def show_connection_dialog(self):
        dialog = ConnectionDialog(self)
        if dialog.exec_():
            ip, port = dialog.get_connection_info()
            self.connect_to_server(ip, port)

    def connect_to_server(self, ip, port):
        try:
            port = int(port)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, port))
            print(f"Connected to {ip} {port}")
            self.log_message(f"Connected to {ip} {port}")
            self.connect_button.setText("Connected")
            self.connect_button.setEnabled(False)
            threading.Thread(target=self.receive_data, daemon=True).start()
        except Exception as e:
            print(f"Connection failed: {e}")

    def receive_data(self):
        while self.socket:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                message = data.decode()
                self.signals.receivedData.emit(message)
            except Exception as e:
                self.log_message(f"Error receiving data: {e}")
                break
        self.log_message("Disconnected from server")
        self.socket = None
        self.connect_button.setText("Connection")
        self.connect_button.setEnabled(True)

    def toggle_auto(self):
        self.is_auto = not self.is_auto
        if self.is_auto:
            self.auto_button.setStyleSheet("background-color: green;")
        else:
            self.auto_button.setStyleSheet("background-color: red;")

    def add_wheel_control(self, layout, row, col, wheel_index, include_speed_buttons=True):
        dial = QDial(self)
        dial.setNotchesVisible(True)
        dial.setWrapping(False)  # Disable 360-degree rotation
        dial.setMinimum(-4)  # -200000 / 50000 = -4
        dial.setMaximum(4)   # 200000 / 50000 = 4
        dial.setSingleStep(1)
        dial.setPageStep(1)

        # Connect the dial's value change to update the angle display
        dial.valueChanged.connect(lambda value, idx=wheel_index: self.update_wheel_angle(idx, value * 50000))
        
        # Input field for entering the angle value manually
        angle_input = QLineEdit(self)
        angle_input.setFixedSize(80, 30)
        angle_input.setStyleSheet("font-size: 16px;")
        angle_input.setAlignment(Qt.AlignCenter)
        angle_input.setPlaceholderText("Angle")
        angle_input.returnPressed.connect(lambda idx=wheel_index, input=angle_input: self.set_wheel_angle(idx, input))

        # Layout to hold the dial and the input field
        wheel_layout = QGridLayout()
        wheel_layout.addWidget(dial, 0, 0, Qt.AlignCenter)
        wheel_layout.addWidget(angle_input, 1, 0, Qt.AlignCenter)

        # Add the wheel control layout to the specified position in the main layout
        layout.addLayout(wheel_layout, row, col, Qt.AlignCenter)

    def update_wheel_angle(self, wheel_index, value):
        angle_label, angle_value_label = self.wheel_labels[wheel_index]
        angle_value_label.setText(str(value))

        if self.is_auto:
            # Send command to move the actual robot wheel
            command = f"{wheel_index} {self.angle_change_cmd} {value}\n"
            self.send_command(command)

    def set_wheel_angle(self, wheel_index, input_field):
        try:
            value = int(input_field.text())
            if -200000 <= value <= 200000 and value % 50000 == 0:
                self.wheel_labels[wheel_index][1].setText(str(value))
                input_field.clear()

                # Send command to move the actual robot wheel
                command = f"{wheel_index} {self.angle_change_cmd} {value}\n"
                self.send_command(command)

                # Update dial position
                dial = self.findChild(QDial, f"dial_{wheel_index}")
                if dial:
                    dial.setValue(value // 50000)
            else:
                input_field.setText("Invalid")
        except ValueError:
            input_field.setText("Error")

    def send_all_wheel_positions(self):
        for i in range(4):
            value = int(self.wheel_labels[i][1].text())
            command = f"{i} {self.angle_change_cmd} {value}"
            self.send_command(command)

# /*********************************controooooooooooool angle *****************************************************************/ 

    def keyPressEvent(self, event):
        if self.is_auto:
            if event.key() == Qt.Key_A:
                self.rotate_wheels(-50000, -50000)
            elif event.key() == Qt.Key_D:
                self.rotate_wheels(50000, 50000)
            elif event.key() == Qt.Key_S:
                self.reset_wheels()
            elif event.key() == Qt.Key_L:
                self.set_speed_hex(0x2BB0)
            elif event.key() == Qt.Key_K:
                self.set_speed_hex(0)
            elif event.key() == Qt.Key_J:
                self.toggle_direction()

    def reset_wheels(self):
        self.rotate_wheels(0, 0)
        self.log_message("Wheels reset to (0, 0)\n")    

    def rotate_wheels(self, angle0, angle1):
        commands = [
            f"0 {self.angle_change_cmd} {angle0}\n",
            f"1 {self.angle_change_cmd} {angle1}\n"
        ]
        for command in commands:
            self.send_command(command)

# /*********************************controooooooooooool wheel *****************************************************************/ 

    def toggle_direction(self):
        self.direction_params = "0" if self.direction_params == "1" else "1"
        direction_text = "frontward" if self.direction_params == "1" else "backward"
        self.log_message(f"###################################")
        self.log_message(f"direction setting: {direction_text}")
        self.log_message(f"###################################\n")
        for i in range(4):
            command = f"{i} {self.direction_change_cmd} {self.direction_params}"
            self.send_command(command)

    def set_speed_hex(self, speed_hex):
        self.current_speed = speed_hex
        self.speed_label.setText(f'Speed: {self.current_speed}')
        hex_speed = f"0x{self.current_speed:X}"
        for i in range(4):
            command = f"{i} {self.speed_change_cmd} {hex_speed}"
            self.send_command(command)
        self.log_message(f"Speed set to: {hex_speed}\n")

# /*********************************speed speed speed speed *****************************************************************/ 

    def accelerate(self):
        self.change_all_wheel_speeds(0x2BB0) # 2 rpm

    def decelerate(self):
        self.change_all_wheel_speeds(0x2BB0)

    def change_all_wheel_speeds(self, delta):
        self.current_speed += delta
        self.current_speed = max(0, self.current_speed)  
        self.speed_label.setText(f'Speed: {self.current_speed}')
        
        hex_speed = f"0x{self.current_speed:X}"
        for i in range(4):  
            command = f"{i} {self.speed_change_cmd} {hex_speed}"
            self.send_command(command)

    def set_speed(self, input_field):
        try:
            value = int(input_field.text())
            self.current_speed = value
            self.speed_label.setText(f'Speed: {self.current_speed}')
            input_field.clear()
            
            hex_speed = f"0x{self.current_speed:X}"  #
            for i in range(4):
                command = f"{i} {self.speed_change_cmd} {hex_speed}"
                self.send_command(command)
        except ValueError:
            input_field.setText("Error")

    def start_robot(self):
        self.current_speed = 0000
        self.speed_label.setText(f'Speed: {self.current_speed}')
        hex_speed = f"0x{self.current_speed:X}" 
        for i in range(4):
            command = f"{i} {self.speed_change_cmd} {hex_speed}"
            self.send_command(command)
        for angle_label, angle_value_label in self.wheel_labels:
            angle_value_label.setText('0')

    def stop_robot(self):
        self.current_speed = 0
        self.speed_label.setText('Speed: 0')
        hex_speed = f"0x{self.current_speed:X}"  
        for i in range(4):
            command = f"{i} {self.speed_change_cmd} {hex_speed}"
            self.send_command(command)

    def resizeEvent(self, event):
        self.background.setGeometry(0, 0, self.width(), self.height())
        self.bg_image = QPixmap(self.image_path).scaled(self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.scene.clear()
        self.scene.addPixmap(self.bg_image)
        super().resizeEvent(event)

    def send_command(self, command):
        if self.socket:
            try:
                
                if not command.endswith('\n'):
                    command += '\n'
                self.socket.sendall(command.encode('utf-8'))
                print(f"Sent command: {command.strip()}")
                self.log_message(f"Sent command: {command.strip()}")
            except Exception as e:
                print(f"Failed to send command: {e}")
                self.log_message(f"Failed to send command: {e}")
        else:
            print("Not connected to server")
            self.log_message("Not connected to server")       

    def log_message(self, message):
        self.message_display.append(message)
        self.message_display.verticalScrollBar().setValue(
            self.message_display.verticalScrollBar().maximum()
        )
        QApplication.processEvents()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SkeletonPanel()
    sys.exit(app.exec_())