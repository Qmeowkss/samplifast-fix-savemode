import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QSlider
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import music_control as mc
import track1_control as t1
import track2_control as t2


class AudioEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Samplifast🎵")
        self.setGeometry(100, 100, 1200, 700)

        self.tracks = [
            {"data": None, "sample_rate": None, "original_data": None, "volume": 1.0, "playing": False, "stream": None, "play_pointer": 0},
            {"data": None, "sample_rate": None, "original_data": None, "volume": 1.0, "playing": False, "stream": None, "play_pointer": 0}
        ]

        self.track_axes = []
        self.track_canvases = []

        button_style = (
            "QPushButton { background-color: black; color: white; "
            "padding: 8px; font-weight: bold; border: 1px solid white; }"
        )

        main_layout = QHBoxLayout()
        control_layout = QVBoxLayout()

        for i in range(2):
            load_btn = QPushButton(f"Загрузить {i+1}")
            load_btn.setStyleSheet(button_style)
            load_btn.clicked.connect(lambda _, x=i: t1.load_audio(self, x) if x == 0 else t2.load_audio(self, x))
            control_layout.addWidget(load_btn)

            play_btn = QPushButton(f"Воспроизвести {i+1}")
            play_btn.setStyleSheet(button_style)
            play_btn.clicked.connect(lambda _, x=i: mc.play_pause_track(self, x))
            control_layout.addWidget(play_btn)

            volume_slider = QSlider(Qt.Horizontal)
            volume_slider.setMinimum(0)
            volume_slider.setMaximum(100)
            volume_slider.setValue(100)
            volume_slider.valueChanged.connect(lambda value, x=i: mc.update_volume(self, x, value))
            control_layout.addWidget(volume_slider)

        play_all_btn = QPushButton("▶️ Все дорожки")
        play_all_btn.setStyleSheet(button_style)
        play_all_btn.clicked.connect(lambda: mc.play_pause_all(self))
        self.play_all_button = play_all_btn
        control_layout.addWidget(play_all_btn)

        zoom_in_button = QPushButton("Увеличить")
        zoom_in_button.setStyleSheet(button_style)
        zoom_in_button.clicked.connect(self.zoom_in)
        control_layout.addWidget(zoom_in_button)

        zoom_out_button = QPushButton("Уменьшить")
        zoom_out_button.setStyleSheet(button_style)
        zoom_out_button.clicked.connect(self.zoom_out)
        control_layout.addWidget(zoom_out_button)

        main_layout.addLayout(control_layout)

        plot_layout = QVBoxLayout()
        for i in range(2):
            fig, ax = plt.subplots()
            canvas = FigureCanvas(fig)
            canvas.setStyleSheet("background-color: black;")
            plot_layout.addWidget(canvas)
            self.track_axes.append(ax)
            self.track_canvases.append(canvas)

        main_layout.addLayout(plot_layout)

        container = QWidget()
        container.setLayout(main_layout)
        container.setStyleSheet("background-color: black;")
        self.setCentralWidget(container)

    def plot_track(self, index):
        if self.tracks[index]["data"] is None:
            return

        ax = self.track_axes[index]
        canvas = self.track_canvases[index]

        ax.clear()
        data = self.tracks[index]["data"]
        sr = self.tracks[index]["sample_rate"]
        time = np.arange(len(data)) / sr
        ax.plot(time, data, color='cyan')
        ax.set_facecolor("black")
        ax.set_title(f"Дорожка {index + 1}", color='white')
        ax.set_xlabel("Время (сек)", color='white')
        ax.set_ylabel("Амплитуда", color='white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        canvas.draw()

    def zoom_in(self):
        for ax, canvas in zip(self.track_axes, self.track_canvases):
            xlim = ax.get_xlim()
            center = sum(xlim) / 2
            span = (xlim[1] - xlim[0]) / 4
            ax.set_xlim(center - span, center + span)
            canvas.draw()

    def zoom_out(self):
        for ax, canvas in zip(self.track_axes, self.track_canvases):
            xlim = ax.get_xlim()
            center = sum(xlim) / 2
            span = (xlim[1] - xlim[0])
            ax.set_xlim(center - span, center + span)
            canvas.draw()
