import sys
import numpy as np
import matplotlib.pyplot as plt
import pyaudio
import wave
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, QByteArray
from PyQt5.QtGui import QPixmap, QFont
from scipy.fft import rfft, rfftfreq
import os
from io import BytesIO

class AudioWorker(QThread):
    finished = pyqtSignal()
    peakFrequencyDetected = pyqtSignal(float, str)  # Signal to emit peak frequency
    rawAudioData = pyqtSignal(np.ndarray)  # Emit raw audio data
    animalSoundSpectrogram = pyqtSignal(np.ndarray)

    def __init__(self, frames, pyaudio_instance):
        super().__init__()
        self.frames = frames
        self.pyaudio_instance = pyaudio_instance
        self.playing = True  # Flag to control playback
    
    def animal_sound(self, animal_name):
        """
        Plays the sound of the specified animal.
        """
        filename = os.path.join('sound_sample', animal_name + '.wav')
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return

        # Open the wave file
        wf = wave.open(filename, 'rb')

        # Open a stream to play the audio
        stream = self.pyaudio_instance.open(format=self.pyaudio_instance.get_format_from_width(wf.getsampwidth()),
                                            channels=wf.getnchannels(),
                                            rate=wf.getframerate(),
                                            output=True)

        # Read and play the audio file
        chunk_size = 128  # Smaller chunk size for more responsive playback
        data = wf.readframes(chunk_size)
        while self.playing:
            while len(data) > 0 and self.playing:
                stream.write(data)
                data = wf.readframes(chunk_size)
            
            # Rewind the file for looping
            wf.rewind()
            data = wf.readframes(chunk_size)

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        wf.close()
    
    def stop_playback(self):
        self.playing = False

    def run(self):
        # Combine frames
        data = b''.join(self.frames)
        audio_data = np.frombuffer(data, dtype=np.int16)
        self.rawAudioData.emit(audio_data)  # Emit raw audio data for plotting in main thread

        # FFT
        N = len(audio_data)
        yf = rfft(audio_data)
        xf = rfftfreq(N, 1 / 44100)

        # Mask out frequencies below 300Hz
        mask = xf > 300
        yf = yf[mask]
        xf = xf[mask]

        # Find peak frequency
        idx_peak = np.argmax(np.abs(yf))
        peak_freq = xf[idx_peak]
        
        # Decide which animal sound to play and calculate its spectrogram
        animal_file = self.get_animal_sound_file(peak_freq)
        self.emitSpectrogramFromFile(animal_file)
        
        self.peakFrequencyDetected.emit(peak_freq, animal_file)  # Emit the peak frequency

        # Start playback
        self.animal_sound(animal_file)

        self.finished.emit()
        
    def get_animal_sound_file(self, peak_freq):
        if peak_freq <= 550:
            return "elephant"
        elif peak_freq <= 875:
            return "whale"
        elif peak_freq <= 1300:
            return "lemur"
        else:
            return "dolphin"
        
    def emitSpectrogramFromFile(self, animal_name):
        filename = os.path.join('sound_sample', animal_name + '.wav')
        if not os.path.exists(filename):
            return

        with wave.open(filename, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio_data = np.frombuffer(frames, dtype=np.int16)
            self.animalSoundSpectrogram.emit(audio_data)

class AudioAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize PyAudio
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.state = "idle"  # States: "idle", "recording", "playing"
        self.freq_label = QLabel('Input Peak Frequency: --- Hz, Output: ---------', self)
        self.spectrogramLabel = QLabel(self)
        self.outputSpectrogramLabel = QLabel(self)

        # Setup GUI
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Audio Analyzer")
        self.setGeometry(0, 0, 600, 300)  # Adjust size to accommodate both plots

        mainLayout = QVBoxLayout()
        spectrogramLayout = QHBoxLayout()  # Create a horizontal layout

        self.main_button = QPushButton('Start Recording', self)
        self.main_button.clicked.connect(self.toggleAudio)
        mainLayout.addWidget(self.main_button)
        mainLayout.addWidget(self.freq_label)

        # Add spectrogram labels to the horizontal layout
        spectrogramLayout.addWidget(self.spectrogramLabel)
        spectrogramLayout.addWidget(self.outputSpectrogramLabel)
        mainLayout.addLayout(spectrogramLayout)  # Add the horizontal layout to the main layout

        central_widget = QWidget()
        central_widget.setLayout(mainLayout)
        self.setCentralWidget(central_widget)

    def toggleAudio(self):
        if self.state == "idle":
            self.startRecording()
        elif self.state == "recording":
            self.stopRecording()
        elif self.state == "playing":
            self.stopPlayback()

    def startRecording(self):
        self.frames = []
        self.stream = self.pyaudio_instance.open(format=pyaudio.paInt16, channels=1,
                                                rate=44100, input=True,
                                                frames_per_buffer=1024,
                                                stream_callback=self.callback)
        self.main_button.setText('Stop Recording')
        self.state = "recording"

    def stopRecording(self):
        self.stream.stop_stream()
        self.stream.close()
        self.state = "playing"
        self.audioWorker = AudioWorker(self.frames, self.pyaudio_instance)
        self.audioWorker.peakFrequencyDetected.connect(self.updateFrequencyDisplay)
        self.audioWorker.rawAudioData.connect(self.updateSpectrogramDisplay)
        self.audioWorker.animalSoundSpectrogram.connect(self.updateAnimalSoundSpectrogram)
        self.audioWorker.finished.connect(self.onPlaybackFinished)
        self.audioWorker.start()
        self.main_button.setText('Stop Playing')

    def onPlaybackFinished(self):
        self.stopPlayback()

    def stopPlayback(self):
        if hasattr(self, 'audioWorker'):
            self.audioWorker.stop_playback()
        self.main_button.setText('Start Recording')
        self.state = "idle"
        
    def updateFrequencyDisplay(self, frequency, animal_file):
        name = {'dolphin': 'Indo-Pacific humpback dolphin', 'lemur': 'Sifaka Lemur', 'whale': 'Blue Whale', 'elephant': 'Asian Elephant'}
        self.freq_label.setText(f'Input Peak Frequency: {frequency:.2f} Hz, Output: {name[animal_file]}')

    def updateSpectrogramDisplay(self, audio_data):
        # Generate and display the spectrogram using matplotlib
        plt.specgram(audio_data, NFFT=8820, Fs=44100, noverlap=4410, cmap='viridis')
        plt.ylim(0, 8000)
        plt.xlabel('Time')
        plt.ylabel('Frequency')
        plt.title("Input")

        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(buf.getvalue()), 'PNG')
        self.spectrogramLabel.setPixmap(pixmap)

        plt.close()

    def updateAnimalSoundSpectrogram(self, audio_data):
        # Generate and display the spectrogram using matplotlib
        plt.specgram(audio_data, NFFT=8820, Fs=44100*2, noverlap=4410, cmap='plasma')
        plt.ylim(0, 8000)
        print(audio_data[0])
        plt.xlabel('Time')
        plt.ylabel('Frequency')
        plt.title("Output")

        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(buf.getvalue()), 'PNG')
        self.outputSpectrogramLabel.setPixmap(pixmap)  # Use a different label

        plt.close()

    def callback(self, in_data, frame_count, time_info, status):
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set font for the entire application
    font = QFont()
    font.setPointSize(48)  # Setting font size
    app.setFont(font)
    
    ex = AudioAnalyzer()
    ex.show()
    sys.exit(app.exec_())
    
