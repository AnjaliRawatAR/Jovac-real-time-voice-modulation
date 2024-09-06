import numpy as np
import sounddevice as sd
from scipy import signal
from cryptography.fernet import Fernet

CHUNK = 1024
CHANNELS = 1
RATE = 44100

class VoiceModulator:
    def __init__(self):
        self.stream = sd.Stream(
            samplerate=RATE,
            blocksize=CHUNK,
            channels=CHANNELS,
            dtype=np.float32,
            callback=self.audio_callback
        )
        self.pitch_shift = 1.0
        self.reverb = 0.0
        self.distortion = 0.0
        self.voice_type = "normal"
        self.is_running = False
        self.is_encrypted = False
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)

    def pitch_shift_effect(self, data, shift):
        indices = np.round(np.arange(0, len(data), shift)).astype(int)
        indices = indices[indices < len(data)]
        return data[indices]

    def reverb_effect(self, data, amount):
        reverb_data = np.zeros_like(data)
        for i in range(5):
            delay = int(RATE * 0.1 * i)
            if delay < len(data):
                reverb_data[delay:] += data[:len(data)-delay] * (amount ** (i+1))
        return data + reverb_data

    def distortion_effect(self, data, amount):
        return np.tanh(amount * data) / np.tanh(amount)

    def robot_voice(self, data):
        t = np.arange(len(data)) / RATE
        carrier = np.sin(2 * np.pi * 100 * t)
        return data * carrier

    def male_to_female(self, data):
        shifted = self.pitch_shift_effect(data, 1.2)
        return signal.lfilter([1.0, -0.85], [1.0], shifted)

    def encrypt_data(self, data):
        return self.cipher_suite.encrypt(data.tobytes())

    def decrypt_data(self, encrypted_data):
        return np.frombuffer(self.cipher_suite.decrypt(encrypted_data), dtype=np.float32)

    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            print(status)

        data = indata[:, 0]

        if self.is_encrypted:
            data = self.encrypt_data(data)
            outdata[:] = np.frombuffer(data, dtype=np.float32).reshape(-1, 1)[:frames]
            return

        if self.voice_type == "robot":
            data = self.robot_voice(data)
        elif self.voice_type == "female":
            data = self.male_to_female(data)

        data = self.pitch_shift_effect(data, self.pitch_shift)
        data = self.reverb_effect(data, self.reverb)
        data = self.distortion_effect(data, self.distortion)

        out = np.zeros((frames, CHANNELS), dtype=np.float32)
        out[:len(data), 0] = data[:frames]
        outdata[:] = out

    def start(self):
        self.is_running = True
        self.stream.start()

    def stop(self):
        self.is_running = False
        self.stream.stop()
