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
from matplotlib.backends.backend_qt5agg import FigureCanvas


class AudioEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        # ======================== НАСТРОЙКА ОКНА ========================
        self.setWindowTitle("Samplitude Python Clone")
        self.setGeometry(100, 100, 1000, 700)

        # ======================== СТИЛИ ========================
        button_style = (
            "QPushButton { background-color: black; color: white; padding: 12px; "
            "font-weight: bold; border: 1px solid white; }"
            "QPushButton:pressed { background-color: #333333; }"
        )
        label_style = "color: white;"
        slider_style = "QSlider {background-color: black;}"

        # ======================== ЛЕВАЯ ПАНЕЛЬ (ГРОМКОСТЬ) ========================
        volume_layout = QVBoxLayout()
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(5)

        volume_label = QLabel("Громкость")
        volume_label.setStyleSheet(label_style)

        self.volume_slider = QSlider(Qt.Vertical)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100)
        self.volume_slider.setStyleSheet(slider_style)
        self.volume_slider.valueChanged.connect(self.update_volume)

        volume_layout.addWidget(volume_label, alignment=Qt.AlignHCenter)
        volume_layout.addWidget(self.volume_slider)

        # ======================== ПРАВАЯ ПАНЕЛЬ ========================
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # ==== СЛАЙДЕРЫ ОБРЕЗКИ ====
        self.trim_start_slider = QSlider(Qt.Horizontal)
        self.trim_end_slider = QSlider(Qt.Horizontal)
        for slider in (self.trim_start_slider, self.trim_end_slider):
            slider.setMinimum(0)
            slider.setStyleSheet(slider_style)
            slider.valueChanged.connect(self.update_trim_overlay)

        trim_label = QLabel("Диапазон обрезки (сек):")
        trim_label.setStyleSheet(label_style)

        right_layout.addWidget(trim_label)
        right_layout.addWidget(self.trim_start_slider)
        right_layout.addWidget(self.trim_end_slider)

        # ==== КНОПКИ ====
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)

        self.load_button = QPushButton("📁")
        self.play_pause_button = QPushButton("▶️")
        self.trim_button = QPushButton("✂️")
        for btn, slot in [
            (self.load_button, self.load_audio),
            (self.play_pause_button, self.play_pause_audio),
            (self.trim_button, self.trim_audio),
        ]:
            btn.setStyleSheet(button_style)
            btn.setFixedHeight(40)
            btn.clicked.connect(slot)
            buttons_layout.addWidget(btn)

        right_layout.addLayout(buttons_layout)

        # ==== ГРАФИК ====
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: black;")
        right_layout.addWidget(self.canvas)

        # ==== ОСНОВНОЙ ЛЭЙАУТ ====
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        main_layout.addLayout(volume_layout)
        main_layout.addLayout(right_layout)

        container = QWidget()
        container.setLayout(main_layout)
        container.setStyleSheet("background-color: black;")
        self.setCentralWidget(container)

        # ======================== ПЕРЕМЕННЫЕ ========================
        self.audio_data = None
        self.original_audio_data = None
        self.sample_rate = None
        self.original_sample_rate = None
        self.volume = 1.0
        self.playing = False
        self.stream = None
        self.playback_position = 0

    # ======================== ОБРАБОТЧИК ГРОМКОСТИ ========================
    def update_volume(self, value):
        self.volume = value / 100.0

    # ======================== ОБРАБОТЧИК ЗАГРУЗКИ АУДИО ========================
    def load_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть аудио файл", "", "Audio Files (*.wav *.mp3 *.flac)"
        )
        if file_path:
            try:
                self.audio_data, self.sample_rate = sf.read(file_path)
                self.original_audio_data = self.audio_data.copy()
                self.original_sample_rate = self.sample_rate
                self.playback_position = 0

                duration = len(self.audio_data) / self.sample_rate
                self.trim_start_slider.setMaximum(int(duration))
                self.trim_end_slider.setMaximum(int(duration))
                self.trim_start_slider.setValue(0)
                self.trim_end_slider.setValue(int(duration))

                self.plot_audio()
            except Exception as e:
                print(f"Ошибка при загрузке аудио: {e}")

    # ======================== ОБРАБОТЧИК ПРОИГРЫВАНИЯ ========================
    def play_pause_audio(self):
        if self.audio_data is None:
            print("Сначала загрузите аудио")
            return

        if self.playing:
            self.playing = False
            self.play_pause_button.setText("▶️")
            if self.stream:
                self.stream.stop()
        else:
            try:
                self.audio_data = self.audio_data.astype(np.float32)
                if np.max(np.abs(self.audio_data)) > 1.0:
                    self.audio_data /= np.max(np.abs(self.audio_data))  # нормализация

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

    # ======================== CALLBACK ПРОИГРЫВАНИЯ ========================
    def play_callback(self, outdata, frames, time, status):
        if self.audio_data is None or not self.playing:
            raise sd.CallbackAbort

        start = self.playback_position
        end = start + frames
        if end > len(self.audio_data):
            self.playing = False
            self.play_pause_button.setText("▶️")
            raise sd.CallbackStop

        data = self.audio_data[start:end] * self.volume
        if data.ndim == 1:
            data = data.reshape(-1, 1)

        outdata[:len(data)] = data
        self.playback_position = end

    # ======================== ОБРАБОТКА ОБРЕЗКИ ========================
    def trim_audio(self):
        if self.audio_data is None:
            print("Сначала загрузите аудио")
            return

        try:
            start = self.trim_start_slider.value()
            end = self.trim_end_slider.value()
            if start >= end:
                raise ValueError("Начало должно быть меньше конца")

            start_idx = int(start * self.sample_rate)
            end_idx = int(end * self.sample_rate)
            self.audio_data = self.original_audio_data[start_idx:end_idx]
            self.sample_rate = self.original_sample_rate
            self.playback_position = 0

            self.plot_audio()
        except Exception as e:
            print(f"Ошибка при обрезке: {e}")

    # ======================== ОБНОВЛЕНИЕ ОБЛАСТЕЙ ОБРЕЗКИ ========================
    def update_trim_overlay(self):
        if self.audio_data is None:
            return
        start_sec = self.trim_start_slider.value()
        end_sec = self.trim_end_slider.value()
        if start_sec >= end_sec:
            return

        duration = len(self.audio_data) / self.sample_rate
        self.ax.clear()
        time = np.arange(len(self.audio_data)) / self.sample_rate
        self.ax.plot(time, self.audio_data, color='cyan')
        self.ax.axvspan(0, start_sec, color='red', alpha=0.3)
        self.ax.axvspan(end_sec, duration, color='red', alpha=0.3)
        self.style_waveform()
        self.canvas.draw()

    # ======================== ПОСТРОЕНИЕ ГРАФИКА ========================
    def plot_audio(self):
        self.ax.clear()
        time = np.arange(len(self.audio_data)) / self.sample_rate
        self.ax.plot(time, self.audio_data, color='cyan')
        self.style_waveform()
        self.canvas.draw()

    # ======================== СТИЛИЗАЦИЯ ГРАФИКА ========================
    def style_waveform(self):
        self.ax.set_facecolor("black")
        self.figure.patch.set_facecolor("black")
        self.ax.set_title("Волновая форма аудио", color='white')
        self.ax.set_xlabel("Время (сек)", color='white')
        self.ax.set_ylabel("Амплитуда", color='white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')


# ======================== ТОЧКА ВХОДА ========================
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = AudioEditor()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
