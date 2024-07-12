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

########### Working AUDIO TRANSCRIPTION-TRANSLATION SERVER ###########
import os
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
    print('GOT A CONNECTION FROM:', addr)
    time.sleep(3)
    handle_client(client_socket)   
