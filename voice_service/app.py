import asyncio
import base64
import json
import os

import aiohttp
from aiohttp import web
from twilio.twiml.voice_response import VoiceResponse, Connect
import websockets

# In-memory store for call information
# In a production environment, you'd want to use a more persistent store like Redis
call_info = {}

# OpenAI Realtime API config
OPENAI_SESSIONS_URL = "https://api.openai.com/v1/realtime/sessions"
REALTIME_WEBSOCKET_URL = "wss://api.openai.com/v1/realtime/sessions"

async def handle_call(request):
    """Handle incoming Twilio call."""
    response = VoiceResponse()
    response.say(
        "Thank you for calling the dental office. Please wait a moment while I connect you to our AI assistant, Echo."
    )
    response.pause(length=1)
    connect = Connect()
    # The 'wss' scheme is crucial for secure WebSockets.
    # aiohttp will handle the upgrade from http -> ws automatically.
    # We use request.host to dynamically get the ngrok URL.
    stream_url = f"wss://{request.host}/media"
    connect.stream(url=stream_url)
    response.append(connect)

    # Twilio sends data as form-urlencoded, so we need to read the post body
    data = await request.post()
    call_sid = data.get('CallSid')
    from_number = data.get('From')

    if call_sid:
        call_info[call_sid] = {"conversation_log": []}
        print(f"Incoming call from {from_number} (SID: {call_sid})")

    return web.Response(text=str(response), content_type="text/xml")

async def handle_media(request):
    """Handle the bidirectional media stream."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    stream_sid = None
    call_sid = None

    async def twilio_receiver(ws):
        """Receives audio from Twilio and sends it to OpenAI."""
        nonlocal stream_sid, call_sid
        try:
            while not ws.closed:
                message = await ws.receive()
                if message.type == web.WSMsgType.TEXT:
                    data = json.loads(message.data)
                    if data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        call_sid = data['start']['callSid']
                        # Store the stream_sid to be used when sending audio back
                        if call_sid in call_info:
                            call_info[call_sid]['stream_sid'] = stream_sid
                        print(f"Media stream started for call {call_sid} (Stream SID: {stream_sid})")
                        # Start the OpenAI processing in a separate task
                        call_info[call_sid]['openai_task'] = asyncio.create_task(openai_processor(ws, call_sid))

                    elif data['event'] == 'media':
                        if call_sid and 'twilio_queue' in call_info[call_sid]:
                            chunk = base64.b64decode(data['media']['payload'])
                            call_info[call_sid]['twilio_queue'].put_nowait(chunk)

                    elif data['event'] == 'stop':
                        print(f"Media stream stopped for call {call_sid}")
                        if call_sid and call_sid in call_info:
                             # Signal the OpenAI processor to stop
                            if 'twilio_queue' in call_info[call_sid]:
                                await call_info[call_sid]['twilio_queue'].put(None)
                            
                            # Wait for the processor to finish and get the log
                            if 'openai_task' in call_info[call_sid]:
                                log = await call_info[call_sid]['openai_task']
                                if log:
                                    print(f"Triggering summary for call {call_sid}...")
                                    try:
                                        async with aiohttp.ClientSession() as session:
                                            summary_url = "http://summary_service:5003/summarize"
                                            await session.post(summary_url, json={"conversation_log": log})
                                    except Exception as summary_e:
                                        print(f"Failed to trigger summary for call {call_sid}: {summary_e}")
                                
                                # Clean up call info from memory
                                if call_sid in call_info:
                                    del call_info[call_sid]
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in twilio_receiver: {e}")

    await twilio_receiver(ws)
    return ws

async def openai_processor(twilio_ws, call_sid):
    """Connects to OpenAI and processes the audio stream."""
    import websockets

    # The model is now a query param, so we can extract it from the config
    model = "gpt-4o-realtime-preview-2024-10-01"
    session_config = {
        "instructions": "You are Echo, a friendly and professional AI assistant for a dental office. Your primary goal is to guide a patient through a natural conversation to gather comprehensive clinical notes for their upcoming appointment. Strive for an empathetic and unhurried conversational flow. Avoid asking a long list of questions at once; instead, let the conversation guide your next question.\n\n1.  **Greet and Confirm Identity:** Start by asking for the caller's full name.\n2.  **Establish Patient History:** Ask if they are a new or existing patient. This is important context.\n3.  **Initial Inquiry:** Ask for the reason for their upcoming appointment.\n4.  **Investigative Dialogue:** Based on their reason, engage them in a diagnostic conversation. Your goal is to fill out a clinical note, so you must be thorough.\n    *   **If they report pain or a specific problem:** You MUST gather details on the following points. Ask questions one by one until you have the information. Do not move on until you have a clear answer for each.\n        *   **Location:** 'I'm sorry to hear that. Could you tell me exactly which tooth or area is bothering you?'\n        *   **History of the Issue:** 'Is this a new problem, or have you had issues with this tooth before?'\n        *   **Timeline:** 'How long has this been going on?'\n        *   **Pain/Sensation:** 'Can you describe the feeling? Is it a sharp, dull, throbbing, or sensitive feeling?'\n        *   **Severity:** 'I need to note the severity. On a scale of 1 to 10, with 10 being the worst pain imaginable, how would you rate it?'\n        *   **Triggers & Relievers:** 'Is there anything specific that makes it better or worse, like hot or cold temperatures, sweet foods, or pressure from chewing?'\n    *   **If they report a routine check-up:** Frame your questions as being thorough. For example: 'That's great! Just to be thorough for your chart, have you noticed any new sensitivity or discomfort anywhere in your mouth?' If they say yes, you must follow the 'pain or specific problem' path above.\n5.  **Conclude:** Thank the caller for the detailed information and assure them it has been logged for their visit.",
        "voice": "alloy",
        "turn_detection": {
            "type": "server_vad",
            "silence_duration_ms": 700,
            "prefix_padding_ms": 300
        },
        "response": {
            "end_of_turn_detection": {
                "type": "relaxed"
            }
        },
        "output_interruption": {
            "enabled": True
        },
        "input_audio_transcription": {
            "model": "gpt-4o-transcribe",
            "language": "en",
            "prompt": "The user is calling a dental office to describe their symptoms before an appointment. Expect dental terms like toothache, cavity, root canal, crown, gums, pain, sensitivity, cleaning, check-up, filling."
        },
        "modalities": ["audio", "text"],
        "input_audio_format": "g711_ulaw",
        "output_audio_format": "g711_ulaw"
    }

    try:
        websocket_url = f"wss://api.openai.com/v1/realtime?model={model}"
        headers = {
            "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}",
            "OpenAI-Beta": "realtime=v1"
        }

        async with websockets.connect(
            websocket_url,
            additional_headers=headers
        ) as openai_ws:
            # Send the session configuration
            session_update_message = {
                "type": "session.update",
                "session": session_config
            }
            await openai_ws.send(json.dumps(session_update_message))

            # Create queues for bidirectional audio
            call_info[call_sid]['twilio_queue'] = asyncio.Queue()

            async def openai_sender():
                """Sends audio from Twilio to OpenAI."""
                while True:
                    chunk = await call_info[call_sid]['twilio_queue'].get()
                    if chunk is None:
                        # Use a more specific end-of-stream event
                        await openai_ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
                        # After committing, we gracefully close the connection from our side.
                        await openai_ws.close()
                        break
                    
                    audio_append = {
                        "type": "input_audio_buffer.append",
                        "audio": base64.b64encode(chunk).decode('utf-8')
                    }
                    await openai_ws.send(json.dumps(audio_append))


            async def openai_receiver():
                """Receives responses from OpenAI and forwards them to Twilio."""
                while True:
                    try:
                        message = await openai_ws.recv()
                        response = json.loads(message)

                        if response.get("type") == 'response.audio.delta' and 'delta' in response:
                            audio_chunk = base64.b64decode(response['delta'])
                            media_response = {
                                "event": "media",
                                "streamSid": call_info[call_sid].get('stream_sid'),
                                "media": {"payload": base64.b64encode(audio_chunk).decode('utf-8')}
                            }
                            await twilio_ws.send_str(json.dumps(media_response))
                        
                        elif response.get("type") == "conversation.item.input_audio_transcription.completed":
                            transcript = response.get("transcript", "")
                            if transcript and transcript.strip():
                                print(f"OpenAI Transcript for {call_sid}: {transcript}")
                                # We assume the user is speaking, so role is 'user'
                                call_info[call_sid]['conversation_log'].append({"role": "user", "content": transcript})
                        
                        elif response.get("type") == "conversation.item.assistant_response.completed":
                            # Capturing assistant's final response if needed for the log
                            assistant_response = response.get("transcript", "")
                            if assistant_response and assistant_response.strip():
                                call_info[call_sid]['conversation_log'].append({"role": "assistant", "content": assistant_response})

                    except websockets.exceptions.ConnectionClosed:
                        print("OpenAI WebSocket connection closed.")
                        break

            sender_task = asyncio.create_task(openai_sender())
            receiver_task = asyncio.create_task(openai_receiver())

            await asyncio.gather(sender_task, receiver_task)

    except Exception as e:
        print(f"Error in openai_processor: {e}")
    finally:
        print(f"OpenAI processor for {call_sid} finished.")
    
    # Return the log for summary generation
    if call_sid in call_info:
        return call_info[call_sid].get("conversation_log", [])
    return []


app = web.Application()
app.router.add_post("/call", handle_call)
app.router.add_get("/media", handle_media)

if __name__ == "__main__":
    web.run_app(app, port=8080)
