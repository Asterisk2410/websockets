########### Working SOCKETS CLIENT ###########
'''import socket
import time

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error as e:
    print('Socket creation error:', e)

try:
    host_ip = '127.0.0.1'
    port = 4892
    socket_address = (host_ip, port)
    client_socket.connect(socket_address)
    print('Client connected to {}:{}'.format(host_ip, port))
    while True:
        try:
            client_socket.send(bytes('Test', 'utf-8'))
            print('Client sent: Test')
            response = client_socket.recv(4*1024)
            if response:
                print('Client received:', response.decode('utf-8'))
            time.sleep(3)
        except socket.error as e:
            print('Socket error:', e)
            break
except socket.error as e:
    print('Connection error:', e)
finally:
    client_socket.close()
    print('Client socket closed')'''

########### Working AUDIO CLIENT ###########
'''import socket
import pyaudio

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

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(socket_address)
    print('Client connected to {}:{}'.format(host_ip, port))
    
    while True:
        data = stream.read(CHUNK)
        client_socket.sendall(data)
        
        # # Receive translated text from server
        try:
            transcript = client_socket.recv(1024).decode('utf-8')
            translated_text = client_socket.recv(1024).decode('utf-8')
            if translated_text:
                print('Translated Text:', translated_text)
        except socket.error as e:
            print('Error receiving data:', e)
            break

except socket.error as e:
    print('Socket error:', e)
finally:
    client_socket.close()
    stream.stop_stream()
    stream.close()
    audio.terminate()
    print('Client socket closed')'''

import socket
import pyaudio

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

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(socket_address)
    print('Client connected to {}:{}'.format(host_ip, port))
    
    client_socket.settimeout(5.0)
    while True:
        data = stream.read(CHUNK)
        if not data:
            break
        
        try:
            client_socket.sendall(data)
            
            
            ''' The following code might be creating problems with the server'''
            
            # Receive translated text from server
            # translated_text = ''
            # while True:
            #     chunk = client_socket.recv(1024).decode('utf-8')
            #     if not chunk:
            #         break
            #     translated_text += chunk
            
            # if translated_text:
            #     print('Translated Text:', translated_text)
        
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