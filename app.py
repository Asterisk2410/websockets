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
