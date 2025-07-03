import sys
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import sounddevice as sd
import soundfile as sf

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QWidget, QSlider, QLabel
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class AudioEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Samplifast🎵")
        self.setGeometry(100, 100, 1000, 700)

        # ==== Переменные ====
        self.audio_data = None
        self.sample_rate = None
        self.original_audio_data = None
        self.original_sample_rate = None
        self.volume = 1.0
        self.playing = False
        self.stream = None
        self.trim_start_line = None
        self.trim_end_line = None
        self.dragging_line = None

        # ==== Стили ====
        button_style = (
            "QPushButton { background-color: black; color: white; "
            "padding: 8px; font-weight: bold; border: 1px solid white; }"
        )
        label_style = "color: white;"

        # ==== Основной лэйаут ====
        main_layout = QHBoxLayout()

        # ==== ГРОМКОСТЬ ====
        volume_layout = QVBoxLayout()
        volume_label = QLabel("Громкость")
        volume_label.setStyleSheet(label_style)
        self.volume_slider = QSlider(Qt.Vertical)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.update_volume)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        main_layout.addLayout(volume_layout)

        # ==== ПРАВАЯ ЧАСТЬ ====
        right_layout = QVBoxLayout()

        # Кнопки
        self.load_button = QPushButton("📁")
        self.load_button.setStyleSheet(button_style)
        self.load_button.clicked.connect(self.load_audio)

        self.play_pause_button = QPushButton("▶️")
        self.play_pause_button.setStyleSheet(button_style)
        self.play_pause_button.clicked.connect(self.play_pause_audio)

        self.trim_button = QPushButton("✂️")
        self.trim_button.setStyleSheet(button_style)
        self.trim_button.clicked.connect(self.trim_audio)

        for btn in [self.load_button, self.play_pause_button, self.trim_button]:
            right_layout.addWidget(btn)

        # ==== ГРАФИК ====
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: black;")
        right_layout.addWidget(self.canvas)

        main_layout.addLayout(right_layout)

        container = QWidget()
        container.setLayout(main_layout)
        container.setStyleSheet("background-color: black;")
        self.setCentralWidget(container)

    def update_volume(self, value):
        self.volume = value / 100.0

    def play_pause_audio(self):
        if self.playing:
            self.playing = False
            self.play_pause_button.setText("▶️")
            if self.stream is not None:
                self.stream.stop()
        else:
            if self.audio_data is None:
                print("Сначала загрузите аудио")
                return
            try:
                if np.issubdtype(self.audio_data.dtype, np.integer):
                    max_val = np.iinfo(self.audio_data.dtype).max
                    audio_normalized = self.audio_data.astype(np.float32) / max_val
                else:
                    audio_normalized = self.audio_data.astype(np.float32)

                self.audio_data = audio_normalized
                channels = self.audio_data.shape[1] if self.audio_data.ndim > 1 else 1

                self.stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=channels,
                    callback=self.play_callback,
                    blocksize=1024
                )
                self.stream.start()
                self.playing = True
                self.play_pause_button.setText("⏸️")

            except Exception as e:
                print(f"Ошибка при воспроизведении: {e}")

    def play_callback(self, outdata, frames, time, status):
        if self.audio_data is None:
            raise sd.CallbackAbort
        if self.playing:
            data = self.audio_data[:frames] * self.volume
            if data.ndim == 1:
                data = data.reshape(-1, 1)
            outdata[:len(data)] = data
            self.audio_data = self.audio_data[frames:]
        else:
            raise sd.CallbackAbort

    def load_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть аудио файл", "",
                                                   "Audio Files (*.wav *.mp3 *.flac)")
        if file_path:
            try:
                self.audio_data, self.sample_rate = sf.read(file_path)
                self.original_audio_data = self.audio_data.copy()
                self.original_sample_rate = self.sample_rate
                self.plot_audio()
            except Exception as e:
                print(f"Ошибка при загрузке аудио: {e}")

    def plot_audio(self):
        self.ax.clear()
        time = np.arange(len(self.audio_data)) / self.sample_rate
        self.ax.plot(time, self.audio_data, color='cyan')
        duration = len(self.audio_data) / self.sample_rate

        # Визуальные линии обрезки
        self.trim_start_line = self.ax.axvline(0, color='red', lw=2, picker=5)
        self.trim_end_line = self.ax.axvline(duration, color='red', lw=2, picker=5)

        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.canvas.mpl_connect("motion_notify_event", self.on_drag)
        self.canvas.mpl_connect("button_release_event", self.on_release)

        self.style_waveform()
        self.canvas.draw()

    def style_waveform(self):
        self.ax.set_facecolor("black")
        self.ax.set_title("Волновая форма аудио", color='white')
        self.ax.set_xlabel("Время (сек)", color='white')
        self.ax.set_ylabel("Амплитуда", color='white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')

    def on_click(self, event):
        if not event.inaxes:
            return
        if abs(event.xdata - self.trim_start_line.get_xdata()[0]) < 0.1:
            self.dragging_line = self.trim_start_line
        elif abs(event.xdata - self.trim_end_line.get_xdata()[0]) < 0.1:
            self.dragging_line = self.trim_end_line

    def on_drag(self, event):
        if not event.inaxes or self.dragging_line is None:
            return
        new_x = max(0, event.xdata)
        self.dragging_line.set_xdata([new_x])
        self.canvas.draw()

    def on_release(self, event):
        self.dragging_line = None

    def trim_audio(self):
        if self.audio_data is not None:
            try:
                start = self.trim_start_line.get_xdata()[0]
                end = self.trim_end_line.get_xdata()[0]
                if start >= end:
                    raise ValueError("Начало должно быть меньше конца")
                start_idx = int(start * self.sample_rate)
                end_idx = int(end * self.sample_rate)

                self.audio_data = self.original_audio_data[start_idx:end_idx]
                self.sample_rate = self.original_sample_rate
                self.plot_audio()

            except Exception as e:
                print(f"Ошибка при обрезке: {e}")
        else:
            print("Сначала загрузите аудио")


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = AudioEditor()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
