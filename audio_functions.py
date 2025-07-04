from PyQt5.QtWidgets import QFileDialog
import soundfile as sf
import sounddevice as sd
import numpy as np


def update_volume(self, track_index, value):
    self.tracks[track_index]["volume"] = value / 100.0


def load_audio(self, track_index):
    file_path, _ = QFileDialog.getOpenFileName(self, "Открыть аудио файл", "",
                                               "Audio Files (*.wav *.mp3 *.flac)")
    if file_path:
        try:
            data, rate = sf.read(file_path)
            self.tracks[track_index]["audio_data"] = data
            self.tracks[track_index]["original_audio_data"] = data.copy()
            self.tracks[track_index]["sample_rate"] = rate
            self.tracks[track_index]["original_sample_rate"] = rate
            plot_audio(self, track_index)
        except Exception as e:
            print(f"Ошибка при загрузке аудио дорожки {track_index + 1}: {e}")


def plot_audio(self, track_index):
    ax = self.tracks[track_index]["ax"]
    canvas = self.tracks[track_index]["canvas"]
    audio_data = self.tracks[track_index]["audio_data"]
    rate = self.tracks[track_index]["sample_rate"]

    ax.clear()
    time = np.arange(len(audio_data)) / rate
    ax.plot(time, audio_data, color='cyan')

    self.tracks[track_index]["trim_start_line"] = ax.axvline(0, color='red', lw=2, picker=5)
    self.tracks[track_index]["trim_end_line"] = ax.axvline(len(audio_data) / rate, color='red', lw=2, picker=5)

    ax.set_facecolor("black")
    ax.set_title("Волновая форма аудио", color='white')
    ax.set_xlabel("Время (сек)", color='white')
    ax.set_ylabel("Амплитуда", color='white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    canvas.mpl_connect("button_press_event", lambda event: on_click(self, event, track_index))
    canvas.mpl_connect("motion_notify_event", lambda event: on_drag(self, event, track_index))
    canvas.mpl_connect("button_release_event", lambda event: on_release(self, event, track_index))

    canvas.draw()


def on_click(self, event, track_index):
    if not event.inaxes:
        return
    trim_start = self.tracks[track_index]["trim_start_line"]
    trim_end = self.tracks[track_index]["trim_end_line"]

    if abs(event.xdata - trim_start.get_xdata()[0]) < 0.1:
        self.tracks[track_index]["dragging_line"] = trim_start
    elif abs(event.xdata - trim_end.get_xdata()[0]) < 0.1:
        self.tracks[track_index]["dragging_line"] = trim_end


def on_drag(self, event, track_index):
    if not event.inaxes or self.tracks[track_index].get("dragging_line") is None:
        return
    new_x = max(0, event.xdata)
    self.tracks[track_index]["dragging_line"].set_xdata([new_x])
    self.tracks[track_index]["canvas"].draw()


def on_release(self, event, track_index):
    self.tracks[track_index]["dragging_line"] = None


def trim_audio(self, track_index):
    try:
        start = self.tracks[track_index]["trim_start_line"].get_xdata()[0]
        end = self.tracks[track_index]["trim_end_line"].get_xdata()[0]
        if start >= end:
            raise ValueError("Начало должно быть меньше конца")
        start_idx = int(start * self.tracks[track_index]["sample_rate"])
        end_idx = int(end * self.tracks[track_index]["sample_rate"])

        trimmed = self.tracks[track_index]["original_audio_data"][start_idx:end_idx]
        self.tracks[track_index]["audio_data"] = trimmed
        self.tracks[track_index]["sample_rate"] = self.tracks[track_index]["original_sample_rate"]

        plot_audio(self, track_index)

    except Exception as e:
        print(f"Ошибка при обрезке дорожки {track_index + 1}: {e}")


def play_pause_audio(self, track_index):
    try:
        track = self.tracks[track_index]
        if track["playing"]:
            track["playing"] = False
            if track["stream"]:
                track["stream"].stop()
            if track["play_button"]:
                track["play_button"].setText(f"▶️ {track_index + 1}")
        else:
            audio_data = track["audio_data"]
            if np.issubdtype(audio_data.dtype, np.integer):
                max_val = np.iinfo(audio_data.dtype).max
                audio_data = audio_data.astype(np.float32) / max_val

            channels = audio_data.shape[1] if audio_data.ndim > 1 else 1

            def callback(outdata, frames, time, status):
                if track["playing"]:
                    data = track["audio_data"][:frames] * track["volume"]
                    if data.ndim == 1:
                        data = data.reshape(-1, 1)
                    outdata[:len(data)] = data
                    track["audio_data"] = track["audio_data"][frames:]
                else:
                    raise sd.CallbackAbort

            track["audio_data"] = audio_data
            stream = sd.OutputStream(
                samplerate=track["sample_rate"],
                channels=channels,
                callback=callback,
                blocksize=1024
            )
            track["stream"] = stream
            stream.start()
            track["playing"] = True
            if track["play_button"]:
                track["play_button"].setText(f"⏸️ {track_index + 1}")
    except Exception as e:
        print(f"Ошибка при воспроизведении дорожки {track_index + 1}: {e}")


def play_all_tracks(self):
    for i in range(len(self.tracks)):
        play_pause_audio(self, i)
