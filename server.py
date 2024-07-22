########### Working SOCKETS SERVER ###########
'''import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '127.0.0.1'
port = 4892
backlog = 5
socket_address = (host_ip, port)
print('Socket server listening on {}:{}'.format(host_ip, port))
server_socket.bind(socket_address)
server_socket.listen(backlog)

while True:
    client_socket, addr = server_socket.accept()
    print('GOT A CONNECTION FROM:', addr)
    if client_socket:
        try:
            while True:
                data = client_socket.recv(4*1024)
                if not data or data.decode('utf-8') == 'END':
                    print('Client disconnected or sent END')
                    break
                print('GOT FROM CLIENT:', data.decode('utf-8'))
                try:
                    client_socket.sendall(bytes('Test', 'utf-8'))
                    print('Sent "Test" to client')
                except Exception as e:
                    print('Error sending data:', e)
        except Exception as e:
            print('Error receiving data:', e)
        finally:
            client_socket.close()
            print('Client socket closed')'''

########### Working AUDIO SERVER ###########
'''import socket
import pyaudio

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Initialize pyaudio
audio = pyaudio.PyAudio()

# Open stream
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, output=True,
                    frames_per_buffer=CHUNK)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '127.0.0.1'
port = 4892
backlog = 5
socket_address = (host_ip, port)

server_socket.bind(socket_address)
server_socket.listen(backlog)
print('Socket server listening on {}:{}'.format(host_ip, port))

while True:
    client_socket, addr = server_socket.accept()
    print('GOT A CONNECTION FROM:', addr)
    
    try:
        while True:
            data = client_socket.recv(CHUNK)
            if not data:
                break
            stream.write(data)
    except socket.error as e:
        print('Socket error:', e)
    finally:
        client_socket.close()
        print('Client socket closed')

stream.stop_stream()
stream.close()
audio.terminate()'''

########### Working AUDIO TRANSCRIPTION-TRANSLATION SERVER ---FREE TRANSLATOR ###########
'''import os
import socket
import pyaudio
from google.cloud import speech
from google.oauth2 import service_account
from googletrans import Translator
import time


# Set the environment variable for Google Cloud credentials
# client_file = 'speech_to_text_cred.json'
# credentials = service_account.Credentials.from_service_account_file(client_file)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'speech_to_text_cred.json'

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
STREAMING_LIMIT = 300  # Streaming limit in seconds

# Initialize pyaudio
audio = pyaudio.PyAudio()

# Initialize Google Cloud Speech client
client = speech.SpeechClient()

# Initialize Google Cloud Translate client
translate = Translator()

def transcribe_streaming(responses, client_socket):
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        
        ### Translate transcript to French
        translated_text = translate.translate(transcript, src='en', dest='fr').text
        print('Transcript:', transcript)
        print('Translated Text:', translated_text)
        
        # Send the translated text back to the client
        try:
            client_socket.sendall(translated_text.encode('utf-8'))
        except socket.error as e:
            print('Error sending data:', e)

def handle_client(client_socket):
    try:
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="en-US",
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True
        )

        requests = (speech.StreamingRecognizeRequest(audio_content=chunk)
                        for chunk in iter(lambda: client_socket.recv(CHUNK), b''))

        responses = client.streaming_recognize(streaming_config, requests)
        transcribe_streaming(responses, client_socket)

    except socket.error as e:
        print('Socket error:', e)
    finally:
        client_socket.close()
        print('Client socket closed')

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '127.0.0.1'
port = 4892
backlog = 5
socket_address = (host_ip, port)

server_socket.bind(socket_address)
server_socket.listen(backlog)
print('Socket server listening on {}:{}'.format(host_ip, port))

while True:
    client_socket, addr = server_socket.accept()
    print('Waiting for connection...')
    if client_socket:
        print('GOT A CONNECTION FROM:', addr)
        time.sleep(2)
        handle_client(client_socket)
'''

########### Working AUDIO TRANSCRIPTION-TRANSLATION SERVER ---GOOGLE CLOUD TRANSLATOR ###########
'''import os
import socket
import pyaudio
import webrtcvad
from google.cloud import speech
from google.cloud import translate_v2 as translator
# from googletrans import Translator
from google.api_core import exceptions
import logging

# Set the environment variable for Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'speech_to_text_cred.json'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Audio parameters
CHUNK = 1024  # Must be a multiple of 320 for 20ms frames at 16kHz
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Initialize pyaudio
audio = pyaudio.PyAudio()

# Initialize Google Cloud Speech client
client = speech.SpeechClient()

# Initialize Google Translate client
translate = translator.Client()

# Initialize VAD
vad = webrtcvad.Vad()
vad.set_mode(1)  # Set aggressiveness level (0-3). Higher value means more aggressive.

def is_speech(data):
    """ Use VAD to check if the audio data contains speech. """
    return vad.is_speech(data, RATE)

def transcribe_streaming(responses, client_socket):
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        
        # Translate transcript to French
        translated_text = translate.translate(transcript, src='en', dest='fr').text
        logging.info('Transcript: %s', transcript)
        print('Transcript:', transcript)
        print('Translated Text:', translated_text)
        logging.info('Translated Text: %s', translated_text)
        
        # Send the translated text back to the client
        # try:
        #     client_socket.sendall(translated_text.encode('utf-8'))
        # except socket.error as e:
        #     logging.error('Error sending data: %s', e)

def handle_client(client_socket):
    try:
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="en-US",
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True
        )

        def generate_requests():
            buffer = b''
            while True:
                try:
                    data = client_socket.recv(CHUNK)
                    if not data:
                        logging.info("No data received, breaking loop.")
                        break
                    buffer += data
                    while len(buffer) >= 320:  # Process frames of 20ms (320 bytes)
                        frame = buffer[:320]
                        buffer = buffer[320:]
                        if is_speech(frame):
                            yield speech.StreamingRecognizeRequest(audio_content=frame)
                        else:
                            logging.info("Silence detected, waiting for speech...")
                except ConnectionAbortedError as e:
                    logging.error('Connection aborted: %s', e)
                    break
                except socket.error as e:
                    logging.error('Socket error during recv: %s', e)
                    break
                except Exception as e:
                    logging.error('Unexpected error during data recv: %s', e)
                    break

        responses = client.streaming_recognize(streaming_config, generate_requests())
        transcribe_streaming(responses, client_socket)

    except socket.error as e:
        logging.error('Socket error: %s', e)
    except exceptions.OutOfRange as e:
        logging.error('Audio Timeout Error: %s', e)
    except exceptions.Unknown as e:
        logging.error('Unknown error: %s', e)
    finally:
        client_socket.close()
        logging.info('Client socket closed')

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '127.0.0.1'
port = 4892
backlog = 5
socket_address = (host_ip, port)

server_socket.bind(socket_address)
server_socket.listen(backlog)
logging.info('Socket server listening on %s:%s', host_ip, port)

while True:
    client_socket, addr = server_socket.accept()
    if client_socket:
        logging.info('GOT A CONNECTION FROM: %s', addr)
        handle_client(client_socket)
'''

########### Working AUDIO TRANSCRIPTION-TRANSLATION SERVER ---DEEPL TRANSLATOR ###########
'''import os
import time
import socket
import pyaudio
import deepl  ## library for speech translation
from google.cloud import speech
from google.api_core import exceptions
from dotenv import load_dotenv
import logging

# Set the environment variable for Google Cloud credentials
load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'speech_to_text_cred.json'
deep_api_key = os.getenv('DEEPL_API_KEY') 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Audio parameters
CHUNK = 1024  # Must be a multiple of 320 for 20ms frames at 16kHz
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Initialize pyaudio
audio = pyaudio.PyAudio()

# Initialize Google Cloud Speech client
client = speech.SpeechClient()

# Initialize Google Translate client
translate = deepl.Translator(deep_api_key)  ## deepl translate

def transcribe_streaming(responses, client_socket):
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        
        # Translate transcript to French
        translated_text = translate.translate_text(transcript, source_lang='en', target_lang='fr').text
        logging.info('Transcript: %s', transcript)
        print('Transcript:', transcript)
        print('Translated Text:', translated_text)
        logging.info('Translated Text: %s', translated_text)
        
        # Send the translated text back to the client
        try:
            client_socket.sendall(translated_text.encode('utf-8'))
        except socket.error as e:
            logging.error('Error sending data: %s', e)

def handle_client(client_socket):
    try:
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="en-US",
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True
        )
        
        while True:
            try:
                data = client_socket.recv(CHUNK)
                if not data:
                    logging.info("No data received, breaking loop.")
                    time.sleep(1)
                requests = (speech.StreamingRecognizeRequest(audio_content=data))        
            except ConnectionAbortedError as e:
                logging.error('Connection aborted: %s', e)
                break
        responses = client.streaming_recognize(streaming_config, requests)
        transcribe_streaming(responses, client_socket)

    except socket.error as e:
        logging.error('Socket error: %s', e)
    except exceptions.OutOfRange as e:
        logging.error('Audio Timeout Error: %s', e)
    except exceptions.Unknown as e:
        logging.error('Unknown error: %s', e)
    finally:
        client_socket.close()
        logging.info('Client socket closed')

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '127.0.0.1'
port = 4892
backlog = 5
socket_address = (host_ip, port)

server_socket.bind(socket_address)
server_socket.listen(backlog)
logging.info('Socket server listening on %s:%s', host_ip, port)

while True:
    client_socket, addr = server_socket.accept()
    if client_socket:
        logging.info('GOT A CONNECTION FROM: %s', addr)
        handle_client(client_socket)'''
        
import os
import time
import socket
import pyaudio
import deepl  # Library for translation
from google.cloud import speech
from google.api_core import exceptions
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'speech_to_text_cred.json'
deep_api_key = os.getenv('DEEPL_API_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Initialize pyaudio
audio = pyaudio.PyAudio()

# Initialize Google Cloud Speech client
client = speech.SpeechClient()

# Initialize DeepL Translate client
translator = deepl.Translator(deep_api_key)

def transcribe_streaming(responses, client_socket):
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        
        # Translate transcript to French
        translated_text = translator.translate_text(transcript, source_lang='EN', target_lang='FR')
        translated_text_str = translated_text.text
        print('Transcript:', transcript)
        print('Translated Text:', translated_text_str)
        
        # Send the translated text back to the client
        try:
            client_socket.sendall(translated_text_str.encode('utf-8'))
        except socket.error as e:
            logging.error('Error sending data: %s', e)

def audio_generator(client_socket):
    while True:
        data = client_socket.recv(CHUNK)
        if not data:
            break
        yield speech.StreamingRecognizeRequest(audio_content=data)

def handle_client(client_socket):
    try:
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="en-US",
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True
        )
        
        requests = audio_generator(client_socket)
        responses = client.streaming_recognize(streaming_config, requests)
        
        transcribe_streaming(responses, client_socket)

    except socket.error as e:
        logging.error('Socket error: %s', e)
    except exceptions.OutOfRange as e:
        logging.error('Audio Timeout Error: %s', e)
    except exceptions.Unknown as e:
        logging.error('Unknown error: %s', e)
    finally:
        client_socket.close()
        logging.info('Client socket closed')

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '127.0.0.1'
port = 4892
backlog = 5
socket_address = (host_ip, port)

server_socket.bind(socket_address)
server_socket.listen(backlog)
logging.info('Socket server listening on %s:%s', host_ip, port)

while True:
    client_socket, addr = server_socket.accept()
    if client_socket:
        logging.info('GOT A CONNECTION FROM: %s', addr)
        handle_client(client_socket)
