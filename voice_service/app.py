import asyncio
import base64
import json
import os
import websockets

from flask import Flask, request
from flask_sock import Sock
from twilio.twiml.voice_response import VoiceResponse, Connect
from twilio.rest import Client

app = Flask(__name__)
sock = Sock(app)

# Load environment variables
# Ensure you have OPENAI_API_KEY, TWILIO_ACCOUNT_SID, and TWILIO_AUTH_TOKEN set
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
twilio_client = Client()

# OpenAI Realtime API config
OPENAI_SAMPLE_RATE = 24000  # OpenAI's recommended sample rate
OPENAI_ENDPOINT = "wss://api.openai.com/v1/realtime" # Placeholder

# In-memory store for call information
# In a production environment, you'd want to use a more persistent store like Redis
call_info = {}

async def openai_realtime_stream(call_sid):
    """Generator function to stream audio to and from OpenAI's Realtime API."""
    uri = f"{OPENAI_ENDPOINT}?model=gpt-4o&sample_rate={OPENAI_SAMPLE_RATE}"
    
    async with websockets.connect(uri, extra_headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}) as openai_ws:
        print(f"Connected to OpenAI Realtime API for call {call_sid}")
        
        async def openai_sender(ws):
            """Sends audio from Twilio to OpenAI."""
            try:
                while True:
                    chunk = await call_info[call_sid]['twilio_queue'].get()
                    if chunk is None: break
                    await ws.send(chunk)
            except Exception as e:
                print(f"Error in openai_sender: {e}")

        async def openai_receiver(ws):
            """Receives audio and text from OpenAI."""
            try:
                while True:
                    message = await ws.recv()
                    # Here you would process audio and text responses from OpenAI
                    response = json.loads(message)
                    if 'text' in response:
                        transcript = response['text']
                        print(f"OpenAI Transcript for {call_sid}: {transcript}")
                        call_info[call_sid]['conversation_log'].append(transcript)
                    
                    if 'audio' in response:
                        # This is a placeholder for where you'd handle audio from OpenAI
                        # The audio would need to be in the correct format for Twilio (e.g., mulaw)
                        audio_chunk = base64.b64decode(response['audio'])
                        await call_info[call_sid]['openai_queue'].put(audio_chunk)

            except Exception as e:
                print(f"Error in openai_receiver: {e}")

        # Create queues for bidirectional audio
        call_info[call_sid]['twilio_queue'] = asyncio.Queue()
        call_info[call_sid]['openai_queue'] = asyncio.Queue()

        sender_task = asyncio.create_task(openai_sender(openai_ws))
        receiver_task = asyncio.create_task(openai_receiver(openai_ws))

        await asyncio.gather(sender_task, receiver_task)

@app.route("/voice", methods=["POST"])
def voice():
    """Accept incoming calls and connect them to a media stream."""
    response = VoiceResponse()
    connect = Connect()
    # The 'wss' scheme is crucial for secure WebSockets. Use your public URL/IP here.
    # For local testing, you might use a tool like ngrok.
    connect.stream(url=f"wss://{request.host}/media")
    response.append(connect)
    
    call_sid = request.form['CallSid']
    call_info[call_sid] = {"conversation_log": []}
    
    print(f"Incoming call from {request.form['From']} (SID: {call_sid})")
    return str(response)

@sock.route("/media")
async def media(ws):
    """Handle the bidirectional media stream between Twilio and our app."""
    stream_sid = None
    call_sid = None

    async def twilio_sender(ws):
        """Sends audio from our app (from OpenAI) to Twilio."""
        try:
            while True:
                chunk = await call_info[call_sid]['openai_queue'].get()
                if chunk is None: break

                media_response = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {"payload": base64.b64encode(chunk).decode('utf-8')}
                }
                await ws.send(json.dumps(media_response))
        except Exception as e:
            print(f"Error in twilio_sender: {e}")

    async def twilio_receiver(ws):
        """Receives audio from Twilio and sends it to OpenAI."""
        nonlocal stream_sid, call_sid
        try:
            while True:
                message = await ws.receive()
                data = json.loads(message)
                if data['event'] == 'start':
                    stream_sid = data['start']['streamSid']
                    call_sid = data['start']['callSid']
                    print(f"Media stream started for call {call_sid} (Stream SID: {stream_sid})")
                    # Start the OpenAI stream processing
                    asyncio.create_task(openai_realtime_stream(call_sid))
                
                elif data['event'] == 'media':
                    # This assumes mu-law format from Twilio
                    chunk = base64.b64decode(data['media']['payload'])
                    if call_sid and call_sid in call_info:
                         await call_info[call_sid]['twilio_queue'].put(chunk)

                elif data['event'] == 'stop':
                    print(f"Media stream stopped for call {call_sid}")
                    if call_sid and call_sid in call_info:
                        await call_info[call_sid]['twilio_queue'].put(None) # Signal sender to stop
                        await call_info[call_sid]['openai_queue'].put(None) # Signal sender to stop
                        # Potentially trigger summary service here
                    break
        except Exception as e:
            print(f"Error in twilio_receiver: {e}")

    sender_task = asyncio.create_task(twilio_sender(ws))
    receiver_task = asyncio.create_task(twilio_receiver(ws))
    await asyncio.gather(sender_task, receiver_task)
    
if __name__ == '__main__':
    # Note: This local server is for development and testing.
    # For production, use a more robust server like gunicorn.
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    
    server = pywsgi.WSGIServer(('', 8080), app, handler_class=WebSocketHandler)
    print("Server listening on port 8080")
    server.serve_forever()
