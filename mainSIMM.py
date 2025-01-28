import sys
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, 
                            QWidget, QLabel, QHBoxLayout, QSizePolicy)

class StableCameraViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 初始化界面
        self.setWindowTitle("稳定画面检测器")
        self.setFixedSize(1200, 600)  # 固定窗口尺寸
        
        # 创建双画面容器
        container = QWidget()
        self.setCentralWidget(container)
        layout = QHBoxLayout(container)
        
        # 实时画面区域
        self.live_view = QLabel()
        self.live_view.setAlignment(Qt.AlignCenter)
        self.live_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.live_view.setMinimumSize(600, 400)  # 设置最小尺寸
        
        # 结果画面区域
        self.result_view = QLabel()
        self.result_view.setAlignment(Qt.AlignCenter)
        self.result_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result_view.setMinimumSize(600, 400)
        
        layout.addWidget(self.live_view)
        layout.addWidget(self.result_view)
        
        # 摄像头初始化
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.live_view.setText("摄像头初始化失败")
            return
        
        # 处理参数
        self.prev_frame = None
        self.similarity_threshold = 0.9
        self.static_frame = None
        
        # 定时器设置
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(200)  # 200ms检测间隔

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # 显示实时画面（固定尺寸）
        self.show_fixed_image(frame, self.live_view, 600, 400)
        
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.prev_frame is not None:
            # 计算SSIM相似度
            score, _ = ssim(self.prev_frame, gray, full=True)
            if score > self.similarity_threshold:
                self.static_frame = frame.copy()
                self.show_fixed_image(self.static_frame, self.result_view, 600, 400)
        
        self.prev_frame = gray.copy()

    def show_fixed_image(self, frame, label, max_w, max_h):
        """固定最大显示尺寸的显示方法"""
        h, w = frame.shape[:2]
        scale = min(max_w/w, max_h/h)  # 计算缩放比例
        
        # 等比例缩放
        resized = cv2.resize(frame, (int(w*scale), int(h*scale)))
        
        # 转换为QPixmap
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.cap.release()
        self.timer.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StableCameraViewer()
    window.show()
    sys.exit(app.exec_())