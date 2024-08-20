import sys
import os
import socket
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QVBoxLayout, QSlider, QLabel, QPushButton, QDial, QLineEdit, QGraphicsView, QGraphicsScene, QFrame, QDialog, QTextEdit, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
    
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
        self.initUI()
        self.socket = None
        self.signals = SocketSignals()
        

    def initUI(self):
        self.setWindowTitle('Skeleton Panel')
        self.setGeometry(100, 100, 1200, 800)

        # Set background image
        self.image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'doc/background.jpg'))
        self.background = QGraphicsView(self)
        self.scene = QGraphicsScene()
        self.background.setScene(self.scene)
        self.background.setStyleSheet("background: transparent; border: none;")
        self.background.setGeometry(0, 0, 1200, 800)
        self.bg_image = QPixmap(self.image_path).scaled(1200, 800, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.scene.addPixmap(self.bg_image)

        # Main layout
        layout = QGridLayout()
        self.setLayout(layout)

        # Frame for Server Messages
        message_frame = QFrame(self)
        message_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        message_frame.setLineWidth(2)
        message_layout = QGridLayout(message_frame)

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

        # Server Messages Label
        messages_label = QLabel('Server Messages', self)
        messages_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        messages_label.setStyleSheet("border: 2px solid black; color: black; font-weight: bold;")
        message_layout.addWidget(messages_label, 0, 0, 1, 2)
        
        # Text Edit for displaying server messages
        self.message_log = QTextEdit(self)
        self.message_log.setReadOnly(True)  # 읽기 전용으로 설정
        message_layout.addWidget(self.message_log, 1, 0, 1, 2)


        # Angle display for wheels
        self.wheel_labels = []
        self.wheel_value_labels = []
        self.wheel_sliders = []

    
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
        self.add_wheel_control(right_layout, 0, 0, 0, include_speed_buttons=False)  
        self.add_wheel_control(right_layout, 0, 1, 1, include_speed_buttons=False)  
        self.add_wheel_control(right_layout, 1, 0, 2, include_speed_buttons=False)  
        self.add_wheel_control(right_layout, 1, 1, 3, include_speed_buttons=False)  
        # Adjust spacing for wheel controls
        right_layout.setSpacing(20)  # 휠 간격 조정

        # Start and Stop buttons
        start_button = QPushButton('Start', self)
        stop_button = QPushButton('Stop', self)

        # Set button size (width x height)
        start_button.setFixedSize(100, 50) 
        stop_button.setFixedSize(100, 50)

        start_button.clicked.connect(self.start_robot)
        stop_button.clicked.connect(self.stop_robot)

        right_layout.addWidget(start_button, 2, 0, 1, 1)
        right_layout.addWidget(stop_button, 2, 1, 1, 1)

        # + Add acceleration, deceleration, and reset buttons
        accelerate_button = QPushButton('Accelerate', self)
        decelerate_button = QPushButton('Decelerate', self)
        
        # + Set button sizes
        accelerate_button.setFixedSize(100, 50)
        decelerate_button.setFixedSize(100, 50)
        
        # + Connect buttons to their respective methods
        accelerate_button.clicked.connect(self.accelerate)
        decelerate_button.clicked.connect(self.decelerate)
        right_layout.addWidget(accelerate_button, 3, 0, 1, 1)
        right_layout.addWidget(decelerate_button, 3, 1, 1, 1)

        
        # Set icons for speed control buttons
        increase_icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'doc/increase.PNG'))
        decrease_icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'doc/decrease.PNG'))


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

        right_layout.setSpacing(20)  # 휠 간격 조정


        # Add frames to the main layout
        layout.addWidget(message_frame, 0, 0)
        layout.addWidget(speed_angle_frame, 1, 0)
        layout.addWidget(right_frame, 0, 1, 3, 1)
        layout.setRowStretch(0, 2)  
        layout.setRowStretch(1, 1)
        


        self.show()

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
            print(f"Connected to {ip}:{port}")
            self.connect_button.setText("Connected")
            self.connect_button.setEnabled(False)
            threading.Thread(target=self.receive_data, daemon=True).start()
        except Exception as e:
            print(f"Connection failed: {e}")
            

    def receive_data(self):
        while True:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                message = data.decode()
                self.signals.receivedData.emit(message)
            except:
                break
        print("Disconnected from server")


    def send_command(self, command):
        if self.socket:
            try:
                self.socket.sendall(command.encode())
                print(f"Sent command: {command}")
            except:
                print("Failed to send command")
        else:
            print("Not connected to server")

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

    def toggle_auto(self):
        self.is_auto = not self.is_auto
        if self.is_auto:
            self.auto_button.setStyleSheet("background-color: green;")
        else:
            self.auto_button.setStyleSheet("background-color: red;")

    def update_wheel_angle(self, wheel_index, value):
        angle_label, angle_value_label = self.wheel_labels[wheel_index]
        angle_value_label.setText(str(value))

        if self.is_auto:
            # Send command to move the actual robot wheel
            command = f"{wheel_index} tmo {value}\n"
            self.send_command(command)

    def set_wheel_angle(self, wheel_index, input_field):
        try:
            value = int(input_field.text())
            if -200000 <= value <= 200000 and value % 50000 == 0:
                self.wheel_labels[wheel_index][1].setText(str(value))
                input_field.clear()

                # Send command to move the actual robot wheel
                command = f"{wheel_index} tmo {value}\n"
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
            command = f"{i} tmo {value}\n"
            self.send_command(command)

    def change_all_wheel_speeds(self, delta):
        speed_text = self.speed_label.text()
        if ": " in speed_text:
            try:
                current_speed = int(speed_text.split(": ")[1])
                new_speed = current_speed + delta
                self.speed_label.setText(f'Speed: {new_speed}')
            except ValueError:
                pass

    def set_speed(self, input_field):
        try:
            value = int(input_field.text())
            self.speed_label.setText(f'Speed: {value}')
            input_field.clear()
        except ValueError:
            input_field.setText("Error")

    def start_robot(self):
        self.speed_label.setText('Speed: 1500000')
        for angle_label, angle_value_label in self.wheel_labels:
            angle_value_label.setText('0')

    def stop_robot(self):
        self.speed_label.setText('Speed: 0')

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
            except Exception as e:
                print(f"Failed to send command: {e}")
        else:
            print("Not connected to server")
            
            
    def accelerate(self):
        self.current_speed += 5  # 가속화: 속도를 5 증가
        command = f"accel {self.current_speed}\n"  # 서버에 보낼 명령어
        self.send_command(command)  # 서버로 명령어 전송
        print(f"Accelerating... Current speed: {self.current_speed} km/h")

    def decelerate(self):
        if self.current_speed > 0:
            self.current_speed -= 5  # 감속화: 속도를 5 감소
            command = f"decel {self.current_speed}\n"  # 서버에 보낼 명령어
            self.send_command(command)  # 서버로 명령어 전송
        print(f"Decelerating... Current speed: {self.current_speed} km/h")   
        
        
    def log_message(self, message):
        """서버에서 받은 메시지를 QTextEdit에 추가합니다."""
        self.message_log.append(message)  # 메시지를 QTextEdit에 추가

    def send_command(self, command):
        """서버에 명령을 전송하고 응답을 수신하여 로그에 추가합니다."""
        if self.socket:
            try:
                if not command.endswith('\n'):
                    command += '\n'
                self.socket.sendall(command.encode('utf-8'))
                print(f"Sent command: {command.strip()}")

                # 서버 응답 수신
                response = self.socket.recv(1024).decode('utf-8')
                self.log_message(response)  # 서버 응답을 로그에 추가

            except Exception as e:
                print(f"Failed to send command: {e}")
                self.log_message(f"Error: {e}")  # 에러 메시지도 로그에 추가
        else:
            print("Not connected to server")
            self.log_message("Not connected to server")  # 연결되지 않았다는 메시지 로그 추가

    
    
    
    
    
    
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SkeletonPanel()
    sys.exit(app.exec_())