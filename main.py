import sys
import cv2
import numpy as np
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, 
                            QHBoxLayout, QWidget, QLabel)
from worker1 import input_queue, result_queue, start_workers
import threading

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 初始化界面
        self.setWindowTitle("Dual Camera Monitor")
        self.setGeometry(100, 100, 1200, 600)

        # 创建双画面显示区域
        self.live_label = QLabel()
        self.live_label.setAlignment(Qt.AlignCenter)
        self.live_label.setText("实时摄像头画面")
        
        self.static_label = QLabel()
        self.static_label.setAlignment(Qt.AlignCenter)
        self.static_label.setText("检测到的静止画面")

        # 设置双画面布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout()
        layout.addWidget(self.live_label, 1)   # 左侧实时画面
        layout.addWidget(self.static_label, 1) # 右侧静止画面
        central_widget.setLayout(layout)

        # 摄像头初始化
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.live_label.setText("摄像头初始化失败")
            return

        # 定时器设置
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frames)
        self.timer.start(200)  # 0.2秒间隔

        # 帧处理参数
        self.prev_frame = None
        self.threshold = 1000000   # 差异阈值（可根据需要调整）
        self.static_count = 0

        # 启动工作线程
        start_workers()
        
        # 添加处理状态标志
        self.processing = False

    def process_frames(self):
        # 如果正在处理中，跳过新的帧
        if self.processing:
            return

        # 读取摄像头帧
        ret, frame = self.cap.read()
        if not ret:
            self.live_label.setText("获取画面失败")
            return

        # 显示实时画面（左侧）
        self.show_image(frame, self.live_label)

        # 转换为灰度图进行比较
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 首次运行初始化前一帧
        if self.prev_frame is None:
            self.prev_frame = gray.copy()
            return

        # 计算帧差异
        diff = cv2.absdiff(self.prev_frame, gray)
        diff_sum = np.sum(diff)

        # 检测静止画面
        if diff_sum < self.threshold:
            self.static_count += 1
            # 显示检测到的静止帧（右侧）
            self.show_image(frame, self.static_label)
            self.setWindowTitle(f"检测到静止画面（第{self.static_count}次）")
            
            # 发送图像到处理线程
            self.processing = True
            input_queue.put(frame)
            
            # 启动结果接收线程
            threading.Thread(target=self.get_result).start()
        else:
            self.prev_frame = gray.copy()

    def get_result(self):
        """接收处理结果的方法"""
        result = result_queue.get()  # 等待处理结果
        self.setWindowTitle(f"处理完成，PIN数量: {result}")
        self.processing = False  # 重置处理状态

    def show_image(self, frame, label):
        """通用方法：将OpenCV图像显示在指定QLabel上"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img).scaled(
            label.width(), label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.cap.release()
        self.timer.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())