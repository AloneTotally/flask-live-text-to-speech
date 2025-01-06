// import Alpine from 'alpinejs'
 
// window.Alpine = Alpine
 
// Alpine.start()

const PLAY_STATES = {
    NO_AUDIO: "no_audio",
    LOADING: "loading",
    PLAYING: "playing",
};

let playState = PLAY_STATES.NO_AUDIO;
let audioPlayer;
const textArea = document.getElementById("text-input");
const llmTextArea = document.getElementById("text-input-model");
const submit = document.getElementById('send-text')
submit.addEventListener('click', sendDataModel)

const errorMessage = document.querySelector("#error-message");
let audioChunks = []; // Array to buffer incoming audio data chunks
let socket;

// Function to update the play button based on the current state
function updatePlayButton() {
    const playButton = document.getElementById("play-button");
    const icon = playButton.querySelector(".button-icon");

    switch (playState) {
        case PLAY_STATES.NO_AUDIO:
            icon.className = "button-icon fa-solid fa-play";
            break;
        case PLAY_STATES.LOADING:
            icon.className = "button-icon fa-solid fa-circle-notch";
            break;
        case PLAY_STATES.PLAYING:
            icon.className = "button-icon fa-solid fa-stop";
            break;
        default:
            break;
    }
}

// Function to stop audio
function stopAudio() {
    audioPlayer = document.getElementById("audio-player");
    if (audioPlayer) {
        playState = PLAY_STATES.PLAYING;
        updatePlayButton();
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        audioPlayer = null;
    }
}

// Function to handle the click event on the play button
function playButtonClick() {
    switch (playState) {
        case PLAY_STATES.NO_AUDIO:
            sendData(document.getElementById("text-input").value);
            break;
        case PLAY_STATES.PLAYING:
            stopAudio();
            playState = PLAY_STATES.NO_AUDIO;
            updatePlayButton();
            break;
        default:
            break;
    }
}

// Remove error message when the text area has a value
textArea.addEventListener("input", () => {
    errorMessage.innerHTML = "";
});

function sendDataModel() {
    const textInput = document.getElementById("text-input-model").value;
    console.log("got the textinput value");
    Alpine.store('chat').messages.push({type: 'human', data: textInput})
    llmTextArea.value = ''
    
    fetch("http://127.0.0.1:5000/api/model-text", {
        method: "POST", // Use POST for sending data
        headers: {
          "Content-Type": "application/json" // Set the content type to JSON
        },
        body: JSON.stringify({text: textInput}) // Convert the JavaScript object to JSON
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json(); // Parse the JSON response from the server
        })
        .then(result => {
          console.log("Server response:", result);
        })
        .catch(error => {
          console.error("Error sending data:", error);
        });
}


// Connect to the Socket.IO server
const socketio = io();

// Listen for "chat_model_stream" events and update the HTML element
socketio.on('chat_model_stream', (data) => {
    console.log("Received chat_model_stream:", data);
    // const chatElement = document.getElementById('chatModelStream');
    lastIndex = Alpine.store('chat').messages.length - 1
    if (Alpine.store('chat').messages[lastIndex].type == 'chat_model_stream') {
        Alpine.store('chat').messages[lastIndex].data = Alpine.store('chat').messages[lastIndex].data.concat(data.message)
    } else {
        Alpine.store('chat').messages.push({data: data.message, type: 'chat_model_stream'})
    }
});

// Listen for "tool_start" events and update the HTML element
socketio.on('tool_start', (data) => {
    console.log("Received tool_start:", data);
    const chatElement = document.getElementById('chatModelStream');  // Ensure you're updating the right element
    Alpine.store('chat').messages.push({data: data.message, type: 'tool_start'})

});


// Listen for "tool_end" events and update the HTML element
socketio.on('tool_end', (data) => {
    console.log("Received tool_end:", data);
    const chatElement = document.getElementById('chatModelStream');  // Ensure you're updating the right element
    Alpine.store('chat').messages.push({data: data.message, type: 'tool_end'})

});

// Optional: Handle connection errors
socketio.on('connect_error', (error) => {
    console.error("Connection error:", error);
});

socketio.on('disconnect', () => {
    console.log("Disconnected from server.");
});

    // Listen for "task_complete" event, which contains the final result
socketio.on('on_chat_model_end', (data) => {
    console.log("Task completed:", data);
    // const chatElement = document.getElementById('chatModelStream');
    sendData(data.message)
    // chatElement.textContent = chatElement.textContent + "\n" + data.message;
});


// Function to send data to backend via WebSocket
function sendData(textInput) {
    // const modelSelect = document.getElementById("models");
    // const selectedModel = modelSelect.options[modelSelect.selectedIndex].value;
    // const textInput = document.getElementById("text-input").value;
    if (!textInput) {
        errorMessage.innerHTML = "ERROR: Please add text!";
    } else {
        playState = PLAY_STATES.LOADING;
        updatePlayButton();

        // we want to simulate holding a connection open like you would for a websocket
        // that's the reason why we only initialize once
        if (!socket) {
            // create a new WebSocket connection
            socket = new WebSocket(`ws://localhost:3001`);

            // disable the model select
            // modelSelect.disabled = true;

            socket.addEventListener("open", () => {
                const data = {
                    text: textInput,
                };
                socket.send(JSON.stringify(data));
                // Things are sent thru the websocket here
            });

            socket.addEventListener("message", (event) => {
                // console.log("Incoming event:", event);

                if (typeof event.data === "string") {
                    console.log("Incoming text data:", event.data);

                    let msg = JSON.parse(event.data);

                    if (msg.type === "Open") {
                        console.log("WebSocket opened 2");
                    } else if (msg.type === "Error") {
                        console.error("WebSocket error:", error);
                        playState = PLAY_STATES.NO_AUDIO;
                        updatePlayButton();
                    } else if (msg.type === "Close") {
                        console.log("WebSocket closed");
                        playState = PLAY_STATES.NO_AUDIO;
                        updatePlayButton();
                    } else if (msg.type === "Flushed") {
                        console.log("Flushed received");

                        // All data received, now combine chunks and play audio
                        const blob = new Blob(audioChunks, { type: "audio/wav" });

                        if (window.MediaSource) {
                            console.log('MP4 audio is supported');
                            const audioContext = new AudioContext();
                    
                            const reader = new FileReader();
                            reader.onload = function () {
                                const arrayBuffer = this.result;
                    
                                audioContext.decodeAudioData(arrayBuffer, (buffer) => {
                                    const source = audioContext.createBufferSource();
                                    source.buffer = buffer;
                                    source.connect(audioContext.destination);
                                    source.start();
                    
                                    playState = PLAY_STATES.PLAYING;
                                    updatePlayButton();
                    
                                    source.onended = () => {
                                        // Clear the buffer
                                        audioChunks = [];
                                        playState = PLAY_STATES.NO_AUDIO;
                                        updatePlayButton();
                                    };
                                });
                            };
                            reader.readAsArrayBuffer(blob);
                        } else {
                            console.error('MP4 audio is NOT supported');
                        }
            
                        // Clear the buffer
                        audioChunks = [];
                    }
                }

                if (event.data instanceof Blob) {
                    // Incoming audio blob data
                    const blob = event.data;
                    console.log("Incoming blob data:", blob);

                    // Push each blob into the array
                    audioChunks.push(blob);
                }
            });
            
            socket.addEventListener("close", () => {
                console.log("Close received");
                playState = PLAY_STATES.NO_AUDIO;
                updatePlayButton();
            });

            socket.addEventListener("error", (error) => {
                console.error("WebSocket error:", error);
                playState = PLAY_STATES.NO_AUDIO;
                updatePlayButton();
            });
        } else {
            const data = {
                text: textInput,
            };
            socket.send(JSON.stringify(data));
        }
    }
}

// Event listener for the click event on the play button
document
    .getElementById("play-button")
    .addEventListener("click", playButtonClick);
