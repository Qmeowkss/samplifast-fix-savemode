from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget,
    QSlider, QLabel, QDoubleSpinBox, QHBoxLayout, QGroupBox, QStyleFactory
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor
import sys
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas
import soundfile as sf
import sounddevice as sd


class AudioEditor(QMainWindow):
    def __init__(self):
        #первый раз в жизни делаю стили
        button_style = """
            QPushButton {
                background-color: black;
                color: white;
                border: 1px solid #555;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #333;
            }
            QPushButton:pressed {
                background-color: #111;
            }
        """

        spinbox_style = """
            QDoubleSpinBox {
                background-color: black;
                color: white;
                border: 1px solid #777;
                border-radius: 4px;
                padding: 2px 4px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background-color: #222;
                subcontrol-origin: border;
                width: 16px;
                border: 1px solid #444;
            }
            QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {
                width: 7px;
                height: 7px;
            }
        """

            
        super().__init__()
        self.setWindowTitle("🎵 Samplifast__artyxyz__")
        self.setGeometry(100, 100, 900, 700)

        # Шрифт
        font = QFont("Segoe UI", 10)
        self.setFont(font)

        # Палитра цветов
        self.setStyle(QStyleFactory.create("Fusion"))
        palette = QPalette()
        palette.setColor(QPalette.Window, Qt.black)
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Button, Qt.white)
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.Base, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        self.setPalette(palette)

        layout = QVBoxLayout()

        # Группа кнопок
        button_group = QGroupBox("Управление")
        button_layout = QHBoxLayout()

        self.load_button = QPushButton("📂 Загрузить")
        self.load_button.clicked.connect(self.load_audio)
        button_layout.addWidget(self.load_button)

        self.play_button = QPushButton("▶️ Воспроизвести")
        self.play_button.clicked.connect(self.play_audio)
        button_layout.addWidget(self.play_button)

        self.pause_button = QPushButton("⏸️ Пауза")
        self.pause_button.clicked.connect(self.pause_audio)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)

        button_group.setLayout(button_layout)
        layout.addWidget(button_group)

        # === Ползунок громкости ===
        volume_group = QGroupBox("Громкость")
        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.update_volume)
        volume_layout.addWidget(QLabel("0%"))
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(QLabel("100%"))
        volume_group.setLayout(volume_layout)
        layout.addWidget(volume_group)

        # === Обрезка ===
        trim_group = QGroupBox("Обрезка аудио")
        trim_layout = QHBoxLayout()

        self.start_time = QDoubleSpinBox()
        self.start_time.setSuffix(" сек")
        self.start_time.setRange(0, 10000)
        trim_layout.addWidget(QLabel("Старт:"))
        trim_layout.addWidget(self.start_time)
        self.start_time.setStyleSheet(spinbox_style)

        self.end_time = QDoubleSpinBox()
        self.end_time.setSuffix(" сек")
        self.end_time.setRange(0, 10000)
        trim_layout.addWidget(QLabel("Конец:"))
        trim_layout.addWidget(self.end_time)
        self.end_time.setStyleSheet(spinbox_style)

        self.trim_button = QPushButton("✂️ Обрезать")
        self.trim_button.clicked.connect(self.trim_audio)
        trim_layout.addWidget(self.trim_button)
        self.trim_button.setStyleSheet(button_style)


        trim_group.setLayout(trim_layout)
        layout.addWidget(trim_group)
        self.load_button.setStyleSheet(button_style)
        self.play_button.setStyleSheet(button_style)
        self.pause_button.setStyleSheet(button_style)


        # График
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: black;")
        layout.addWidget(self.canvas)
        # Установка чёрного фона
        self.figure.patch.set_facecolor('black')       # фон всей области
        self.ax.set_facecolor('black')                 # фон области графика

        # Цвет линий и текста
        self.ax.tick_params(colors='white')            # оси
        self.ax.spines['bottom'].set_color('white')    # нижняя ось
        self.ax.spines['top'].set_color('white')       # верхняя ось
        self.ax.spines['left'].set_color('white')      # левая ось
        self.ax.spines['right'].set_color('white')     # правая ось
        self.ax.title.set_color('white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')


        # основной виджет
        container = QWidget() 
        container.setLayout(layout)
        container.setStyleSheet("background-color: black;")
        self.setCentralWidget(container)

        # Переменные
        self.audio_data = None
        self.original_audio_data = None
        self.sample_rate = None
        self.original_sample_rate = None
        self.volume = 1.0
        self.playing = False
        self.stream = None

    def update_volume(self, value):
        self.volume = value / 100.0

    def play_audio(self):
        if self.audio_data is not None:
            try:
                if np.issubdtype(self.audio_data.dtype, np.integer):
                    max_val = np.iinfo(self.audio_data.dtype).max
                    audio_normalized = self.audio_data.astype(np.float32) / max_val
                else:
                    audio_normalized = self.audio_data.astype(np.float32)

                self.stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=audio_normalized.shape[1] if audio_normalized.ndim > 1 else 1,
                    callback=self.play_callback,
                    blocksize=1024
                )
                self.stream.start()
                self.playing = True
                self.play_button.setEnabled(False)
                self.pause_button.setEnabled(True)

            except Exception as e:
                print(f"Ошибка воспроизведения: {e}")
        else:
            print("Сначала загрузите аудио")

    def play_callback(self, outdata, frames, time, status):
        if self.audio_data is None:
            raise sd.CallbackAbort
        if self.playing:
            data = self.audio_data[:frames] * self.volume
            outdata[:len(data)] = data
            self.audio_data = self.audio_data[frames:]
        else:
            raise sd.CallbackAbort
        

    def pause_audio(self):
        if self.playing:
            self.playing = False
            self.pause_button.setText("▶️ Возобновить")
            self.stream.stop()
        else:
            if self.audio_data is not None:
                self.playing = True
                self.pause_button.setText("⏸️ Пауза")
                self.stream.start()


    def load_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть аудиофайл", "", 
                                                   "Аудиофайлы (*.wav *.mp3 *.flac)")
        if file_path:
            try:
                self.audio_data, self.sample_rate = sf.read(file_path)
                self.original_audio_data = self.audio_data.copy()
                self.original_sample_rate = self.sample_rate

                duration = len(self.audio_data) / self.sample_rate
                self.start_time.setMaximum(duration)
                self.end_time.setMaximum(duration)

                self.ax.clear()
                time = np.arange(len(self.audio_data)) / self.sample_rate
                self.ax.plot(time, self.audio_data)
                self.ax.set_title("Волновая форма")
                self.ax.set_xlabel("Время (сек)")
                self.ax.set_ylabel("Амплитуда")
    
                self.canvas.draw()
            except Exception as e:
                print(f"Ошибка загрузки: {e}")


    def trim_audio(self):
        if self.audio_data is not None:
            try:
                start = self.start_time.value()
                end = self.end_time.value()

                if start >= end:
                    raise ValueError("Начало должно быть меньше конца")

                start_idx = int(start * self.sample_rate)
                end_idx = int(end * self.sample_rate)

                self.audio_data = self.original_audio_data[start_idx:end_idx]
                self.sample_rate = self.original_sample_rate

                self.ax.clear()
                time = np.arange(len(self.audio_data)) / self.sample_rate
                self.ax.plot(time, self.audio_data)
                self.ax.set_title("Обрезанная волновая форма")
                self.ax.set_xlabel("Время (сек)")
                self.ax.set_ylabel("Амплитуда")

                self.canvas.draw()

            except Exception as e:
                print(f"Ошибка обрезки: {e}")
        else:
            print("Сначала загрузите аудио")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = AudioEditor()
    editor.show()
    sys.exit(app.exec_())
