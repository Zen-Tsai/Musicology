import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog
from PyQt5.QtCore import QTimer
import pyaudio
from pydub import AudioSegment
import numpy as np
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
import pygame

class AudioProcessor:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.frames_per_buffer = 1024

        self.stream = self.p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer
        )

    def get_audio_data(self):
        return np.frombuffer(self.stream.read(self.frames_per_buffer), dtype=np.int16)

    def plot_fft(self, audio_data):
        n = len(audio_data)
        frequencies = fftfreq(n, d=1/self.rate)
        fft_values = fft(audio_data)
        magnitude = np.abs(fft_values)

        plt.plot(frequencies[:n//2], magnitude[:n//2])
        plt.title('FFT of Audio Signal')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Magnitude')
        plt.show()

    def get_peak_frequency(self, audio_data):
        n = len(audio_data)
        frequencies = fftfreq(n, d=1/self.rate)
        fft_values = fft(audio_data)
        magnitude = np.abs(fft_values)

        # Find the index of the maximum magnitude
        max_index = np.argmax(magnitude[:n//2])

        # Corresponding frequency
        peak_frequency = frequencies[max_index]

        return peak_frequency

    def process_audio(self):
        try:
            audio_data = self.get_audio_data()
            self.plot_fft(audio_data)
            peak_frequency = self.get_peak_frequency(audio_data)
            print(f'Highest Frequency: {peak_frequency} Hz')
        except Exception as e:
            print(f'Error processing audio: {e}')

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

class AugmentedAudioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.pyaudio_instance = pyaudio.PyAudio()
        self.setupAudioStreams()
        self.live_audio_data = b''  # Buffer for live audio data

    def initUI(self):
        # Create buttons
        self.recordButton = QPushButton('Record', self)
        self.stopButton = QPushButton('Stop', self)
        self.playButton = QPushButton('Analyze', self)

        # Layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.recordButton)
        vbox.addWidget(self.stopButton)
        vbox.addWidget(self.playButton)

        self.setLayout(vbox)
        self.setWindowTitle('System')
        self.setGeometry(300, 300, 300, 150)

        # Connect buttons to functions
        self.recordButton.clicked.connect(self.startRecording)
        self.stopButton.clicked.connect(self.stopRecording)
        self.playButton.clicked.connect(self.playAudio)
        
        # Timer for updating the GUI and processing audio data
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateLiveAudio)
        self.timer.start(500)  # Update every 100 milliseconds

    def setupAudioStreams(self):
        # Audio stream parameters
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.frames_per_buffer = 1024

        # Open recording stream
        self.record_stream = self.pyaudio_instance.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer
        )

        # Open playback stream
        self.playback_stream = self.pyaudio_instance.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            output=True,
            frames_per_buffer=self.frames_per_buffer
        )

    def startRecording(self):
        # Set the flag to False before starting recording
        self.stopRecording = False
        print("Start recording...")

    def stopRecording(self):
        # Set the flag to True to stop recording
        self.stopRecording = True
        print("Finish recording...")

    def updateLiveAudio(self):
        if not self.stopRecording:
            try:
                data = self.record_stream.read(self.frames_per_buffer, exception_on_overflow=False)
                self.live_audio_data += data  # Update live audio data
            except IOError as e:
                if e.errno == pyaudio.paInputOverflowed:
                    data = b'\x00' * self.frames_per_buffer  # Silent frame
                    self.live_audio_data += data  # Update live audio data
                    print("exception reached...")

    def play_audio(self, file_path):
        try: 
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            pygame.event.wait()
        except Exception as e:
            print(f"Error in playAudio: {e}")

    def animal_sound(self, animal):
        if animal == "elephant":
            self.play_audio("./sound_sample/elephant.wav")
        elif animal == "whale":
            self.play_audio("./sound_sample/whale.wav")
        elif animal == "lemur":
            self.play_audio("./sound_sample/lemur.wav")
        else:
            self.play_audio("./sound_sample/dolphin.wav")

    def playAudio(self):
        # Ensure the live audio data is in the correct format
        print("Playing back audio...")
        
        # Convert binary data to array of integers
        formatted_audio_data = np.frombuffer(self.live_audio_data, dtype=np.int16)
        
        # Plot FFT
        n = len(formatted_audio_data)
        frequencies = fftfreq(n, d=1/self.rate)
        fft_values = fft(formatted_audio_data)
        magnitude = np.abs(fft_values)

        plt.plot(frequencies[:n//2], magnitude[:n//2])
        plt.title('FFT of Audio Signal')
        plt.xlabel('Frequency (Hz)')
        plt.xlim(20, 3000)
        plt.ylabel('Magnitude')
        plt.show()

        # Find peak frequency
        max_index = np.argmax(magnitude[:n//2])
        peak_frequency = frequencies[max_index]
        print("#####   Maxmimum Frequency:", peak_frequency, "   #####")
        # Write the audio data to the playback stream
        self.playback_stream.write(self.live_audio_data)
        if peak_frequency <= 550:
            self.animal_sound("elephant")
        elif peak_frequency > 550 and peak_frequency <= 875:
            self.animal_sound("whale")
        elif peak_frequency > 875 and peak_frequency <= 1300:
            self.animal_sound("lemur")
        else:
            self.animal_sound("dolphin")

        print("Finish playing back audio...")

    def closeEvent(self, event):
        # Stop the timer and close the audio streams when the application is closed
        self.timer.stop()
        self.record_stream.stop_stream()
        self.playback_stream.stop_stream()
        self.record_stream.close()
        self.playback_stream.close()
        self.pyaudio_instance.terminate()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AugmentedAudioApp()
    ex.show()
    sys.exit(app.exec_())
