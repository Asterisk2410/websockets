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
        
        if transcript:
            print('Transcript:', transcript)
        try:
            # Translate transcript to French
            translated_text = translator.translate_text(transcript, source_lang='EN', target_lang='FR')
            translated_text_str = translated_text.text
            # print('Transcript:', transcript)
            print('Translated Text:', translated_text_str)

            # Send the translated text back to the client    
            client_socket.sendall(translated_text_str.encode('utf-8'))
        except ValueError as e:
            logging.error('Error translating transcript: %s', e)
        except socket.error as e:
            logging.error('Error sending data: %s', e)
        
def audio_generator(client_socket):
    try:
        while True:
            data = client_socket.recv(CHUNK)
            if not data:
                break
            yield speech.StreamingRecognizeRequest(audio_content=data)
    except ConnectionAbortedError:
        logging.error("Connection aborted by the client")
    except Exception as e:
        logging.error("Error in audio generator: %s", e)
    finally:
        client_socket.close()

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



'''

import socket
import pyaudio
import threading

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Initialize pyaudio
audio = pyaudio.PyAudio()

# Open stream
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

# Socket connection parameters
host_ip = '127.0.0.1'
port = 4892
socket_address = (host_ip, port)

def receive_data(client_socket):
    buffer_size = 1024
    while True:
        try:
            translated_text = client_socket.recv(buffer_size).decode('utf-8')
            if translated_text:
                print('Translated Text:', translated_text)
        except socket.timeout:
            print('Socket timeout: No response from server')
        except socket.error as e:
            print('Socket error:', e)
            break
    client_socket.close()

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(socket_address)
    print('Client connected to {}:{}'.format(host_ip, port))
    
    client_socket.settimeout(10.0)  # Increase timeout if needed
    
    # Start a thread to receive data from the server
    receive_thread = threading.Thread(target=receive_data, args=(client_socket,))
    receive_thread.start()
    
    while True:
        data = stream.read(CHUNK)
        if not data:
            break
        
        try:
            client_socket.sendall(data)
        except socket.timeout:
            print('Socket timeout: No response from server')
        except socket.error as e:
            print('Socket error:', e)
            break

except socket.error as e:
    print('Socket error:', e)
finally:
    client_socket.close()
    stream.stop_stream()
    stream.close()
    audio.terminate()
    print('Client socket closed')


'''