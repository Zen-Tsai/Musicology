import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
import pyaudio
import threading
from pydub import AudioSegment
import pyaudio
import numpy as np

class AugmentedAudioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.pyaudio_instance = pyaudio.PyAudio()
        self.setupAudioStreams()
    
    def initUI(self):
        # Create buttons
        self.recordButton = QPushButton('Record', self)
        self.mixButton = QPushButton('Mix', self)
        self.playButton = QPushButton('Play', self)

        # Layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.recordButton)
        vbox.addWidget(self.mixButton)
        vbox.addWidget(self.playButton)

        self.setLayout(vbox)
        self.setWindowTitle('Audio Mixer')
        self.setGeometry(300, 300, 300, 150)

        # Connect buttons to functions
        self.recordButton.clicked.connect(self.recordAudio)
        self.mixButton.clicked.connect(self.mixAudio)
        self.playButton.clicked.connect(self.playAudio)
    
    def setupAudioStreams(self):
        # Audio stream parameters
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.frames_per_buffer = 1024
        
        # Check and adjust the number of channels for recording if necessary
        # input_device_info = self.pyaudio_instance.get_default_input_device_info()
        # input_channels = min(input_device_info['maxInputChannels'], self.channels)
        # print(input_channels)

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

        
        
    def recordAudio(self):
        try:
            data = self.record_stream.read(self.frames_per_buffer, exception_on_overflow=False)
            # Process your data
        except IOError as e:
            if e.errno == pyaudio.paInputOverflowed:
                # Handle overflow here (e.g., discard data, log error, etc.)
                data = '\x00' * self.frames_per_buffer  # return a silent frame
            else:
                raise  # For other exceptions, raise them
        return data
#     def recordAudio(self):
#         # Read data from the recording stream
#         data = self.record_stream.read(self.frames_per_buffer)
#         # Convert data to numpy array or process it as needed
#         audio_data = np.frombuffer(data, dtype=np.int16)

#         # ... [process audio_data as required] ...

#         return audio_data

    def playAudio(self, audio_data):
        """
        Play audio data through the playback stream.

        :param audio_data: The audio data to be played.
        """
        # Ensure the audio data is in the correct format
        # Here, it's assumed that audio_data is a numpy array. 
        # You might need to convert it to bytes or another format depending on your setup
        formatted_audio_data = audio_data.tobytes()

        # Write the audio data to the playback stream
        self.playback_stream.write(formatted_audio_data)
        
    def mixAudio(self, live_audio_data, file_path):
        """
        Mixes live audio data with an audio file.

        :param live_audio_data: A numpy array containing live recorded audio.
        :param file_path: Path to the pre-existing audio file to mix with.
        :return: Mixed audio as a numpy array.
        """

        # Load the audio file using pydub
        audio_file = AudioSegment.from_file(file_path)

        # Convert the pydub audio to the same sample rate and channels as live audio
        audio_file = audio_file.set_frame_rate(self.rate).set_channels(self.channels)

        # Convert pydub audio to numpy array
        file_data = np.array(audio_file.get_array_of_samples())

        # If the live audio data is shorter than the file data, we need to match their lengths
        min_length = min(len(live_audio_data), len(file_data))
        live_audio_data = live_audio_data[:min_length]
        file_data = file_data[:min_length]

        # Mix the live audio data with the file data
        mixed_audio = live_audio_data + file_data

        # Normalize mixed_audio if necessary to prevent clipping

        return mixed_audio

    def startAugmentedAudio(self):
        # Start threads for recording and playback
        self.record_thread = threading.Thread(target=self.recordAudio)
        self.playback_thread = threading.Thread(target=self.playbackAudio)
        self.record_thread.start()
        self.playback_thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AugmentedAudioApp()
    ex.show()
    sys.exit(app.exec_())
