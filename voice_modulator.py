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
        # Simple pitch shifting using resampling
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
        carrier = np.sin(2 * np.pi * 100 * t)  # 100 Hz carrier
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
        
        # Ensure the output data matches the expected shape
        out = np.zeros((frames, CHANNELS), dtype=np.float32)
        out[:len(data), 0] = data[:frames]
        outdata[:] = out

    def start(self):
        self.is_running = True
        self.stream.start()

    def stop(self):
        self.is_running = False
        self.stream.stop()

try:
    import tkinter as tk

    class GUI:
        def __init__(self, modulator):
            self.modulator = modulator
            self.root = tk.Tk()
            self.root.title("Advanced Voice Modulator")

            self.create_widgets()

        def create_widgets(self):
            self.create_slider("Pitch Shift", 0.5, 2.0, self.update_pitch)
            self.create_slider("Reverb", 0.0, 1.0, self.update_reverb)
            self.create_slider("Distortion", 0.0, 10.0, self.update_distortion)
            
            tk.Label(self.root, text="Voice Type").pack()
            self.voice_type_var = tk.StringVar(value="normal")
            voice_types = ["normal", "robot", "female"]
            for voice in voice_types:
                tk.Radiobutton(self.root, text=voice, variable=self.voice_type_var, value=voice, command=self.update_voice_type).pack()

            self.encrypt_var = tk.BooleanVar()
            self.encrypt_checkbox = tk.Checkbutton(self.root, text="Encrypt/Decrypt", variable=self.encrypt_var, command=self.toggle_encryption)
            self.encrypt_checkbox.pack()

            self.start_button = tk.Button(self.root, text="Start", command=self.start_modulation)
            self.start_button.pack()

            self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_modulation, state=tk.DISABLED)
            self.stop_button.pack()

        def create_slider(self, label, from_, to, command):
            tk.Label(self.root, text=label).pack()
            slider = tk.Scale(self.root, from_=from_, to=to, resolution=0.1, orient=tk.HORIZONTAL, command=command)
            slider.set((from_ + to) / 2)
            slider.pack()

        def update_pitch(self, value):
            self.modulator.pitch_shift = float(value)

        def update_reverb(self, value):
            self.modulator.reverb = float(value)

        def update_distortion(self, value):
            self.modulator.distortion = float(value)

        def update_voice_type(self):
            self.modulator.voice_type = self.voice_type_var.get()

        def toggle_encryption(self):
            self.modulator.is_encrypted = self.encrypt_var.get()

        def start_modulation(self):
            self.modulator.start()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

        def stop_modulation(self):
            self.modulator.stop()
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

        def run(self):
            self.root.mainloop()

except ImportError:
    print("tkinter is not available. Running in command-line mode.")
    
    class CLI:
        def __init__(self, modulator):
            self.modulator = modulator
        
        def run(self):
            print("Voice Modulator CLI")
            print("Commands: start, stop, pitch <value>, reverb <value>, distortion <value>, voice <type>, encrypt <on/off>, quit")
            
            while True:
                command = input("> ").split()
                if not command:
                    continue
                
                if command[0] == "start":
                    self.modulator.start()
                elif command[0] == "stop":
                    self.modulator.stop()
                elif command[0] == "pitch" and len(command) > 1:
                    self.modulator.pitch_shift = float(command[1])
                elif command[0] == "reverb" and len(command) > 1:
                    self.modulator.reverb = float(command[1])
                elif command[0] == "distortion" and len(command) > 1:
                    self.modulator.distortion = float(command[1])
                elif command[0] == "voice" and len(command) > 1:
                    self.modulator.voice_type = command[1]
                elif command[0] == "encrypt" and len(command) > 1:
                    self.modulator.is_encrypted = (command[1].lower() == "on")
                elif command[0] == "quit":
                    break
                else:
                    print("Invalid command")

if __name__ == "__main__":
    modulator = VoiceModulator()
