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