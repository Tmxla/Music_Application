import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QLineEdit, QMessageBox
)
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, QSize, QCoreApplication
import requests
import sounddevice as sd
from scipy.io.wavfile import write

QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

class DeepTuneApp(QWidget):
    def __init__(self):
        super().__init__()

        self.backend_url = "http://127.0.0.1:5000"  # Flask 서버 주소

        self.setWindowTitle("DeepTune 시뮬레이터")
        self.setFixedSize(375, 812)

        self.selected_image_path = None
        self.selected_audio_path = None

        self.bg = QLabel(self)
        if os.path.exists("assets/background.png"):
            bg_pixmap = QPixmap("assets/background.png")
            self.bg.setPixmap(bg_pixmap)
            self.bg.setGeometry(0, 0, 375, 812)
            self.bg.lower()
        else:
            self.bg.setStyleSheet("background-color: #1D2671;")

        # 상단 안내 텍스트
        self.header = QLabel("음악을 찾아보세요", self)
        self.header.setFont(QFont("Helvetica", 16, QFont.Bold))
        self.header.setStyleSheet("color: white;")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setGeometry(0, 30, 375, 40)

        # 마이크 버튼 - 좌측 상단 안내문구 좌측
        self.mic_btn = QPushButton(self)
        self.mic_btn.setIcon(QIcon("assets/mic2.png"))
        self.mic_btn.setIconSize(QSize(30, 30))
        self.mic_btn.setGeometry(20, 35, 30, 30)
        self.mic_btn.setStyleSheet("border: none;")
        self.mic_btn.clicked.connect(self.select_audio)

        # 마이크 버튼 아래 라벨
        self.mic_label = QLabel("음성", self)
        self.mic_label.setFont(QFont("Helvetica", 10))
        self.mic_label.setStyleSheet("color: white;")
        self.mic_label.setAlignment(Qt.AlignCenter)
        self.mic_label.setGeometry(10, 70, 50, 20)

        # 이미지 버튼 - 우측 상단 안내문구 우측
        self.img_btn = QPushButton(self)
        self.img_btn.setIcon(QIcon("assets/photo.png"))
        self.img_btn.setIconSize(QSize(30, 30))
        self.img_btn.setGeometry(325, 35, 30, 30)
        self.img_btn.setStyleSheet("border: none;")
        self.img_btn.clicked.connect(self.select_image)

        # 이미지 버튼 아래 라벨
        self.img_label = QLabel("사진", self)
        self.img_label.setFont(QFont("Helvetica", 10))
        self.img_label.setStyleSheet("color: white;")
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setGeometry(315, 70, 50, 20)

        # 앨범 이미지
        self.album = QLabel(self)
        self.album.setPixmap(QPixmap())  # 초기엔 비움
        self.album.setGeometry(107, 256, 160, 160)
        self.album.setStyleSheet("background-color: rgba(255, 255, 255, 30); border-radius: 12px;")

        # 노래 제목
        self.song_title = QLabel("노래 제목", self)
        self.song_title.setFont(QFont("Helvetica", 14, QFont.Bold))
        self.song_title.setStyleSheet("color: white;")
        self.song_title.setAlignment(Qt.AlignCenter)
        self.song_title.setGeometry(0, 430, 375, 30)

        # 아티스트
        self.artist = QLabel("아티스트", self)
        self.artist.setFont(QFont("Helvetica", 11))
        self.artist.setStyleSheet("color: #DADADA;")
        self.artist.setAlignment(Qt.AlignCenter)
        self.artist.setGeometry(0, 460, 375, 25)

        # 텍스트 입력창 - 가장 아래
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("장면 설명을 입력하세요")
        self.input.setStyleSheet("""
            padding: 8px;
            font-size: 13px;
            border-radius: 20px;
            background-color: rgba(255, 255, 255, 180);
        """)
        self.input.setGeometry(60, 740, 255, 50)
        self.input.returnPressed.connect(self.analyze_text)

        
    #백엔드로 입력 데이터 전송
    def analyze_text(self):
        text = self.input.text()
        if text:
            self.send_text_to_backend(text)
        else:
            QMessageBox.warning(self, "입력 오류", "장면 설명을 입력해주세요.")

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "파일 선택", "", "Images (*.png)")
        if path:
            self.selected_image_path = path
            self.send_image_to_backend(path)

    def select_audio(self):
        self.send_audio_to_backend()

    def update_result(self, data):
        self.song_title.setText(data.get("title", "제목 없음"))
        self.artist.setText(data.get("artist", "아티스트 없음"))

        cover = data.get("cover", "")
        pixmap = QPixmap()

        if cover.startswith("assets/") and os.path.exists(cover):
            #내부 파일 경로인 경우
            pixmap = QPixmap(cover)
        elif cover.startswith("http"):
            #웹 이미지 URL인 경우
            from urllib.request import urlopen
            from io import BytesIO
            image_data = urlopen(cover).read()
            pixmap.loadFromData(image_data)
        elif cover.startswith("data:image"):
            #base64 인코딩일 경우
            import base64
            header, encoded = cover.split(",", 1)
            image_data = base64.b64decode(encoded)
            pixmap.loadFromData(image_data)

        self.album.setPixmap(pixmap.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def send_text_to_backend(self, text):
        try:
            #flask 주소 추후에 첨부 예정
            response = requests.post(f"{self.backend_url}/analyze_text", json = {"text": text})
            result = response.json()
            if "title" in result and "artist" in result and "cover" in result:
                self.update_result(result)
            else:
                QMessageBox.warning(self, "서버 응답 오류", "예상한 데이터 형식이 아닙니다.")

        except Exception as e:
            QMessageBox.warning(self, "서버 오류", str(e))

    def send_image_to_backend(self, path):
        try:
            with open(path, "rb") as f:
                files = {"image": f}
                response = requests.post(f"{self.backend_url}/analyze_image", files = files)
                result = response.json()
                if "title" in result and "artist" in result and "cover" in result:
                    self.update_result(result)
                else:
                    QMessageBox.warning(self, "서버 응답 오류", "예상한 데이터 형식이 아닙니다.")

        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))

    def record_audio(self, duration=5, output_file="temp_audio.wav"):
        fs = 44100  # 샘플링 주파수
        QMessageBox.information(self, "녹음 중", f"{duration}초간 녹음합니다. 소리를 들려주세요.")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()  # 녹음 완료 대기
        write(output_file, fs, recording)
        return output_file


    def send_audio_to_backend(self):
        try:
            path = self.record_audio(duration=5)  # 5초 녹음
            with open(path, "rb") as f:
                files = {"audio": f}
                response = requests.post(f"{self.backend_url}/analyze_audio", files=files)
                result = response.json()
                if "title" in result and "artist" in result and "cover" in result:
                    self.update_result(result)
                else:
                    QMessageBox.warning(self, "서버 응답 오류", "예상한 데이터 형식이 아닙니다.")
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DeepTuneApp()
    window.show()
    sys.exit(app.exec_())
