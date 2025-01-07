import json
import multiprocessing
import time
import platform
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging


from websockets.sync.server import serve
from flask import Flask, send_from_directory, render_template, request, jsonify

import tracemalloc

tracemalloc.start()

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    SpeakWSOptions,
    SpeakWebSocketEvents,
)


# Flask App
app = Flask(__name__, static_folder="./public", static_url_path="/public")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

def hello(websocket):
    # Deepgram TTS WS connection
    connected = False
    deepgram = DeepgramClient()
    dg_connection = deepgram.speak.websocket.v("1")

    global last_time
    last_time = time.time() - 5

    def on_open(self, open, **kwargs):
        print(f"\n\n{open}\n\n")

    def on_flush(self, flushed, **kwargs):
        print(f"\n\n{flushed}\n\n")
        flushed_str = str(flushed)
        websocket.send(flushed_str)
        # sending of flushed str

    def on_binary_data(self, data, **kwargs):
        print("Received binary data")

        global last_time
        if time.time() - last_time > 3:
            print("------------ [Binary Data] Attach header.\n")

            # Add a wav audio container header to the file if you want to play the audio
            # using the AudioContext or media player like VLC, Media Player, or Apple Music
            # Without this header in the Chrome browser case, the audio will not play.
            header = bytes(
                [
                    0x52,
                    0x49,
                    0x46,
                    0x46,  # "RIFF"
                    0x00,
                    0x00,
                    0x00,
                    0x00,  # Placeholder for file size
                    0x57,
                    0x41,
                    0x56,
                    0x45,  # "WAVE"
                    0x66,
                    0x6D,
                    0x74,
                    0x20,  # "fmt "
                    0x10,
                    0x00,
                    0x00,
                    0x00,  # Chunk size (16)
                    0x01,
                    0x00,  # Audio format (1 for PCM)
                    0x01,
                    0x00,  # Number of channels (1)
                    0x80,
                    0xBB,
                    0x00,
                    0x00,  # Sample rate (48000)
                    0x00,
                    0xEE,
                    0x02,
                    0x00,  # Byte rate (48000 * 2)
                    0x02,
                    0x00,  # Block align (2)
                    0x10,
                    0x00,  # Bits per sample (16)
                    0x64,
                    0x61,
                    0x74,
                    0x61,  # "data"
                    0x00,
                    0x00,
                    0x00,
                    0x00,  # Placeholder for data size
                ]
            )
            websocket.send(header)
            last_time = time.time()

        # I assume this is where the data is sent
        websocket.send(data)

    def on_close(self, close, **kwargs):
        print(f"\n\n{close}\n\n")

    dg_connection.on(SpeakWebSocketEvents.Open, on_open)
    dg_connection.on(SpeakWebSocketEvents.AudioData, on_binary_data)
    dg_connection.on(SpeakWebSocketEvents.Flushed, on_flush)
    dg_connection.on(SpeakWebSocketEvents.Close, on_close)

    try:
        while True:
            # This is likely where the message is received
            message = websocket.recv()
            print(f"message from UI: {message}")

            data = json.loads(message)
            # This is the text to be sent
            text = data.get("text")
            model = data.get("model")

            if not text:
                if app.debug:
                    app.logger.debug("You must supply text to synthesize.")
                continue

            if not model:
                model = "aura-asteria-en"

            # Are we connected to the Deepgram TTS WS?
            if connected is False:
                options: SpeakWSOptions = SpeakWSOptions(
                    model=model,
                    encoding="linear16",
                    sample_rate=48000,
                )

                if dg_connection.start(options) is False:
                    if app.debug:
                        app.logger.debug(
                            "Unable to start Deepgram TTS WebSocket connection"
                        )
                    raise Exception("Unable to start Deepgram TTS WebSocket connection")
                connected = True

            # Flushing right upon sending the text to turn to speech
            dg_connection.send_text(text)
            dg_connection.flush()

    except Exception as e:
        dg_connection.finish()


@app.route("/<path:filename>")
def serve_others(filename):
    return send_from_directory(app.static_folder, filename)

import os
from llmmodel import agent_executor
from llmmodel import config
from langchain_core.messages import ToolMessage
os.system("")  # enables ansi escape characters in terminal

COLOR = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "ENDC": "\033[0m",
}
async def run(usermsg):
    returned_output = []
    async for event in agent_executor.astream_events({"messages": [{"role": "user", "content": usermsg}]}, config=config, version="v2"):
        # kind = event["event"]
        # if kind == "on_chat_model_stream":
        #     print(event, end="|", flush=True)
        print(event)  # Log all events to inspect their structure

        toolmsg_example = ToolMessage(content='42', tool_call_id='asdfvbhgf')

        if event["event"] == "on_chat_model_stream":
            # print(event.get("data", {}).get("chunk", {}).get("content", ""), end="|", flush=True)
            print(COLOR["HEADER"], event["data"]["chunk"].content, COLOR["ENDC"], end="|", flush=True)
            socketio.emit('chat_model_stream', {'message': event["data"]["chunk"].content})
            returned_output.append(['chat_model_stream', {'message': event["data"]["chunk"].content}])

        elif event["event"] == "on_tool_start":  
            print(COLOR["BLUE"], "tool is being called", COLOR["ENDC"])
            socketio.emit('tool_start', {'message': 'tool to assist in ordering has been called'})
            returned_output.append(['tool_start', {'message': 'tool to assist in ordering has been called'}])

        elif event["event"] == "on_tool_end":  # Relax filter for debugging
            print(COLOR["BLUE"], "tool calling has ended", COLOR["ENDC"])
            socketio.emit('tool_end', {'message': 'tool to assist in ordering has been called'})
            returned_output.append(['tool_end', {'message': 'tool to assist in ordering has been called'}])
    
        elif event["event"] == "on_chat_model_end":
            # socketio.emit('on_chat_model_end', {'message': event["data"]["output"].content})
            pass
        elif event["event"] == "on_chain_end":
            if len(event["data"]['output']['messages']) > 1 and isinstance(event["data"]['output']['messages'][-2], toolmsg_example):
                socketio.emit('tool_msg', {'message': event["data"]['output']['messages'][-2].content})

    

    # Return the final output from the task
    final_result = {'status': 'done', 'message': 'Task is complete!', 'history': returned_output}
    
    # Emit the final result after processing
    socketio.emit('task_complete', final_result)
    return returned_output


@app.route("/api/model-text", methods=['POST'])
async def model_text():
    # from llmmodel import run
    try:
        data = request.get_json()
        logging.info(f"Received data: {data}")

        if not data:
            return jsonify({"error": "Invalid JSON or no data provided"}), 400
        output = await run(data["text"])
        # socketio.start_background_task(run_with_await, data["text"])
        logging.info(f"Run output: {output}")

        # socketio.start_background_task(asyncio.create_task, run_with_await(data["text"]))

        return jsonify({"message": "Data received successfully!", "data": output}), 200
    except Exception as e:
        # Handle errors and send a meaningful response
        logging.error(f"Error in model_text: {e}")

        return jsonify({"error": str(e)}), 500


@app.route("/assets/<path:filename>")
def serve_image(filename):
    return send_from_directory(app.static_folder, "assets/" + filename)


@app.route("/", methods=["GET"])
def serve_index():
    # return app.send_static_file("index.html")
    return render_template("index.html")

@app.route("/home", methods=["GET"])
def home():
    return render_template("home.html")


def run_ui():
    # app.run(debug=True, use_reloader=False)
    socketio.run(app, debug=True, use_reloader=False)
    # app.run(debug=True)

# From what i understand i assume this websocket is served for as long as the server runs
def run_ws():
    with serve(hello, "localhost", 3001) as server:
        server.serve_forever()


if __name__ == "__main__":
    if platform.system() == "Darwin":
        multiprocessing.set_start_method("fork")

    p_flask = multiprocessing.Process(target=run_ui)
    p_ws = multiprocessing.Process(target=run_ws)

    p_flask.start()
    p_ws.start()

    p_flask.join()
    p_ws.join()
