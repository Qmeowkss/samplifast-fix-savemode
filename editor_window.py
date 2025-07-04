from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QSlider, QLabel, QFileDialog
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import audio_functions as af


class AudioEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Samplifast🎵")
        self.setGeometry(100, 100, 1200, 800)

        self.tracks = [
            {"audio_data": None, "original_audio_data": None, "sample_rate": None,
             "original_sample_rate": None, "volume": 1.0, "playing": False,
             "stream": None, "trim_start_line": None, "trim_end_line": None,
             "canvas": None, "ax": None, "play_button": None},
            {"audio_data": None, "original_audio_data": None, "sample_rate": None,
             "original_sample_rate": None, "volume": 1.0, "playing": False,
             "stream": None, "trim_start_line": None, "trim_end_line": None,
             "canvas": None, "ax": None, "play_button": None}
        ]

        self.init_ui()

    def init_ui(self):
        button_style = (
            "QPushButton { background-color: black; color: white; "
            "padding: 8px; font-weight: bold; border: 1px solid white; }"
        )
        label_style = "color: white;"

        main_layout = QVBoxLayout()
        waveform_layout = QHBoxLayout()
        control_layout = QHBoxLayout()

        for i in range(2):
            v_layout = QVBoxLayout()

            load_btn = QPushButton(f"Загрузить {i + 1}")
            load_btn.setStyleSheet(button_style)
            load_btn.clicked.connect(lambda _, x=i: af.load_audio(self, x))

            play_btn = QPushButton(f"▶️ {i + 1}")
            play_btn.setStyleSheet(button_style)
            play_btn.clicked.connect(lambda _, x=i: af.play_pause_audio(self, x))
            self.tracks[i]["play_button"] = play_btn

            trim_btn = QPushButton(f"✂️ {i + 1}")
            trim_btn.setStyleSheet(button_style)
            trim_btn.clicked.connect(lambda _, x=i: af.trim_audio(self, x))

            vol_slider = QSlider(Qt.Vertical)
            vol_slider.setMinimum(0)
            vol_slider.setMaximum(100)
            vol_slider.setValue(100)
            vol_slider.valueChanged.connect(lambda value, x=i: af.update_volume(self, x, value))

            vol_label = QLabel("Громкость")
            vol_label.setStyleSheet(label_style)

            v_layout.addWidget(load_btn)
            v_layout.addWidget(play_btn)
            v_layout.addWidget(trim_btn)
            v_layout.addWidget(vol_label)
            v_layout.addWidget(vol_slider)

            fig, ax = plt.subplots()
            canvas = FigureCanvas(fig)
            canvas.setStyleSheet("background-color: black;")
            waveform_layout.addWidget(canvas)

            self.tracks[i]["canvas"] = canvas
            self.tracks[i]["ax"] = ax

            control_layout.addLayout(v_layout)

        self.play_all_button = QPushButton("▶️ Воспроизвести всё")
        self.play_all_button.setStyleSheet(button_style)
        self.play_all_button.clicked.connect(lambda: af.play_all_tracks(self))
        control_layout.addWidget(self.play_all_button)

        main_layout.addLayout(waveform_layout)
        main_layout.addLayout(control_layout)

        container = QWidget()
        container.setLayout(main_layout)
        container.setStyleSheet("background-color: black;")
        self.setCentralWidget(container)
