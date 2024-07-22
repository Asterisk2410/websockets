import os
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from google.cloud import speech
from googletrans import Translator
from google.api_core.exceptions import OutOfRange
import torch

# Set the environment variable for Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'speech_to_text_cred.json'

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('audio_data')
def handle_audio_data(data):
    if data:
        try:
            # Initialize Google Cloud clients
            print('Received audio data')
            speech_client = speech.SpeechClient()
            translator = Translator()

            # Configure recognition config
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code="en-US",
            )
            streaming_config = speech.StreamingRecognitionConfig(
                config=config,
                interim_results=True
            )
            print('here')
            # Create a generator to stream audio chunks
            requests = (speech.StreamingRecognizeRequest(audio_content=data),)
            print('here2')
            # Perform streaming recognition
            responses = speech_client.streaming_recognize(streaming_config, requests)
            print('here3')
            if responses:
                for response in responses:
                    for result in response.results:
                        if not result.alternatives:
                            continue
                        transcript = result.alternatives[0].transcript
                        logging.info('Transcript: %s', transcript)

                        # Translate the transcript
                        translation = translator.translate(transcript, dest='fr')
                        translated_text = translation.text
                        print('Translation:', translated_text)
                        logging.info('Translation: %s', translated_text)
                        print('sending')
                        # Send translated text back to the client
                        socketio.emit('translated_text', translated_text)
            else:
                print("No audio data received.")
                socketio.emit('error', {'message': 'No audio data received.'})

        except OutOfRange as e:
            logging.error("Streaming limit exceeded: %s", e)
            socketio.emit('error', {'message': 'Streaming limit exceeded, please refresh the page.'})
        except Exception as e:
            logging.error("Error during streaming recognition: %s", e)
            socketio.emit('error', {'message': 'An error occurred during transcription.'})

    else:
        print("No audio data received.")
        socketio.emit('error', {'message': 'No audio data received.'})
        
    
if __name__ == '__main__':
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print('Using GPU')
    else:
        device = torch.device('cpu')
        print('Using CPU')
    socketio.run(app, host='0.0.0.0', port=5000)
    print('Server running on port 5000')
    logging.basicConfig(level=logging.INFO)



'''

import os
import time
import socket
import asyncio
import websockets
import pyaudio
import deepl  # Library for translation
from google.cloud import speech
from google.api_core import exceptions
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/to/your/speech_to_text_cred.json'
deep_api_key = os.getenv('DEEPL_API_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Initialize Google Cloud Speech client
client = speech.SpeechClient()

# Initialize DeepL Translate client
translator = deepl.Translator(deep_api_key)

async def transcribe_streaming(websocket, path):
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )

    requests = (speech.StreamingRecognizeRequest(audio_content=chunk) async for chunk in websocket)

    try:
        responses = client.streaming_recognize(streaming_config, requests)

        async for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript
            
            # Translate transcript to French
            translated_text = translator.translate_text(transcript, source_lang='EN', target_lang='FR').text
            logging.info('Transcript: %s', transcript)
            logging.info('Translated Text: %s', translated_text)
            
            # Send the translated text back to the client
            await websocket.send(translated_text)
    except exceptions.GoogleAPIError as e:
        logging.error('Google API error: %s', e)
    except socket.error as e:
        logging.error('Socket error: %s', e)

start_server = websockets.serve(transcribe_streaming, '127.0.0.1', 4892)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_server)
    logging.info('WebSocket server listening on ws://127.0.0.1:4892')
    asyncio.get_event_loop().run_forever()


'''