// script.js

const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const translatedTextElement = document.getElementById('translatedText');

let mediaRecorder;
let socket;
let audioChunks = [];

startButton.addEventListener('click', startRecording);
stopButton.addEventListener('click', stopRecording);

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start(250); // Sending audio chunks every 250ms

            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(event.data);
                }
            });

            socket = new WebSocket('ws://127.0.0.1:4892'); // WebSocket connection to the server

            socket.addEventListener('open', () => {
                console.log('WebSocket connection established');
            });

            socket.addEventListener('message', event => {
                const translatedText = event.data;
                translatedTextElement.textContent = translatedText;
            });

            socket.addEventListener('close', () => {
                console.log('WebSocket connection closed');
            });

            socket.addEventListener('error', error => {
                console.error('WebSocket error:', error);
            });

            startButton.disabled = true;
            stopButton.disabled = false;
        })
        .catch(error => {
            console.error('Error accessing audio stream:', error);
        });
}

function stopRecording() {
    mediaRecorder.stop();
    socket.close();

    startButton.disabled = false;
    stopButton.disabled = true;
}
