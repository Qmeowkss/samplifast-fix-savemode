import sounddevice as sd
import numpy as np

def play_pause_track(self, track_index):
    track = self.tracks[track_index]
    if track["data"] is None:
        return

    if track.get("playing", False):
        # Остановить воспроизведение
        if track["stream"] is not None:
            track["stream"].stop()
            track["stream"].close()
            track["stream"] = None
        track["playing"] = False
    else:
        # Начать воспроизведение
        track["playing"] = True
        track["play_pointer"] = 0

        def callback(outdata, frames, time, status):
            data = track["data"]
            start = track["play_pointer"]
            end = start + frames
            chunk = data[start:end]
            if len(chunk) < frames:
                chunk = np.pad(chunk, (0, frames - len(chunk)), 'constant')
                track["playing"] = False
                raise sd.CallbackStop()

            chunk = chunk * track["volume"]
            if chunk.ndim == 1:
                chunk = chunk.reshape(-1, 1)

            outdata[:len(chunk)] = chunk
            track["play_pointer"] += frames

        track["stream"] = sd.OutputStream(
            samplerate=track["sample_rate"],
            channels=1 if track["data"].ndim == 1 else track["data"].shape[1],
            callback=callback
        )
        track["stream"].start()

def play_pause_all(self):
    any_playing = any(track.get("playing", False) for track in self.tracks)
    if any_playing:
        # Остановить все
        for track in self.tracks:
            if track["stream"] is not None:
                track["stream"].stop()
                track["stream"].close()
                track["stream"] = None
            track["playing"] = False
    else:
        # Запустить все дорожки
        for i in range(len(self.tracks)):
            play_pause_track(self, i)

def update_volume(self, track_index, value):
    self.tracks[track_index]["volume"] = value / 100.0
