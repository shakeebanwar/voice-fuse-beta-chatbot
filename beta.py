import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import asyncio
import websockets
import uvicorn
import base64
import json
import uuid
import requests
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Connect
from twilio.rest import Client
from starlette.middleware.sessions import SessionMiddleware
# from logger_config import setup_logger
from __config__ import ACCOUNT_SID, AUTH_TOKEN, TWILIO_NUM, WEBSOCKET_SUBDOMAIN, SECRET_KEY, DEEPGRAM_URI, HEADERS

# logger = setup_logger("my_app_logger", level=logging.INFO)

call_sids = {}

# def reset_for_next_call():
#     logger.info("Session variables have been reset...")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

call_count : int = 0

KEEP_ALIVE_INTERVAL = 10

async def send_keep_alive(deepgram_ws):
    while True:
        try:
            await deepgram_ws.send("keep-alive")
        except websockets.exceptions.ConnectionClosed:
            break
        await asyncio.sleep(KEEP_ALIVE_INTERVAL)

def llmquery(userquery,session_id):
    print("session_id===>",session_id)
    url = "https://llm.voicefuse.xyz/chats/"
    payload = json.dumps({"query": userquery, "session_id":session_id})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload).json()
    return response



def analyze_behavior(session_id):
    url = f"https://llm.voicefuse.xyz/session/{session_id}"
    response = requests.request("GET", url).json()
    is_interested = response["prediction"]
    print("is_interested==>",is_interested)
    if is_interested.lower() == "yes":
        print("email is sending...")
        send_email("shakeebanwar250@gmail.com")
        # send_email("adilinbox4@gmail.com")
        # send_email("syedaffan.dev@gmail.com")
        # send_email("waqqasqaziqazi@gmail.com")
        return True
    
    print("customer is not interested")
    return False

def send_email(email):
    sender_email = "hnhtechsolution02@gmail.com"
    receiver_email = [email]
    password = "mqjyxutpycjisnnz"
    for emailSend in receiver_email:
        message = MIMEMultipart("alternative")
        message["Subject"] = "Share the ❤️ Friend! Refer & EARN NOW 😊"
        message["From"] = sender_email
        message["To"] = emailSend

        # Create the plain-text and HTML version of your message
        html = """
            <h1>Interested User</h1>
        """
        # Turn these into plain/html MIMEText objects
        part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        message.attach(part2)

        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, emailSend, message.as_string()
            )


    print("email is sent to ",email)


# send_email("shakeebanwar250@gmail.com")


@app.websocket("/audiostream/{call_sid}")
async def audio_stream(websocket: WebSocket, call_sid: str):
    await websocket.accept()

    if call_sid is None:
        await websocket.send_text(json.dumps({"error": "Call SID not found in session"}))
        return
    
    async with websockets.connect(uri=DEEPGRAM_URI, extra_headers=HEADERS) as deepgram_ws:
        async def receive_deepgram_transcripts():
            try:
                while True:
                    message = await deepgram_ws.recv()
                    if message is None:
                        continue
                    
                    data = json.loads(message)
                    if data.get("type") == "Results" and data.get("is_final"):
                        if data["channel"]["alternatives"][0]["confidence"] > 0.7:
                            transcript = data["channel"]["alternatives"][0]["transcript"]
                            print(f"Transcribed input: {transcript}")
                            print("===========================================================")
                            session_id = call_sids[call_sid]["twillo-sid"]
                            userquery = llmquery(transcript,session_id)
                            twml = VoiceResponse()
                            twml.say(userquery["answer"]["answer"])
                            connect = Connect()
                            connect.stream(url=f"wss://{WEBSOCKET_SUBDOMAIN}/audiostream/{call_sid}")
                            twml.append(connect)
                            await send_response_to_twilio(call_sid, twml.to_xml())
                            if userquery["answer"]["conversation_stage"] == "close" and userquery["conversation_stage"] == "close":
                                print("calling end....")
                                await end_call(call_sid)
                                #analyze user behaviour
                                session_id = userquery["session_id"]
                                analyze_behavior(session_id)
                                break
                        else:
                            print(f"Confidence score of {data['channel']['alternatives'][0]['confidence']} is too low...")

            except websockets.exceptions.ConnectionClosed as e:
                print(f"receive_deepgram_transcripts Connection to Deepgram WebSocket closed: {e.code} - {e.reason}")
            # except Exception as e:
            #     print(f"Error receiving Deepgram transcripts: {e}")
            #     await end_call(call_sid)


        async def forward_audio_to_deepgram():
            try:
                while True:
                    message = await websocket.receive_text()
                    if message is None:
                        continue
                    data = json.loads(message)
                    event = data['event']
                    if event == 'media':
                        chunk = base64.b64decode(data['media']['payload'])
                        await deepgram_ws.send(chunk)
                    elif event == 'stop':
                        break

            except websockets.exceptions.ConnectionClosed as e:
                print(f"forward_audio_to_deepgram Connection to WebSocket closed: {e.code} - {e.reason}")
            except Exception as e:
                print(f"Error forwarding request: {e}")


        await asyncio.gather(
            receive_deepgram_transcripts(),
            forward_audio_to_deepgram()
            # send_keep_alive(deepgram_ws)
        )


    print("Resetting for next call...")

@app.post("/make-call")
async def make_call(call_request:dict):
    try:
        phone_number = call_request["phone_number"]
        interested_caller_id = call_request["interested_caller_id"]
        call_sid = str(uuid.uuid4())
        websocket_url = f"wss://{WEBSOCKET_SUBDOMAIN}/audiostream/{call_sid}"
        twml = VoiceResponse()
        twml.say("Hello! I hope you're doing well today. I'm reaching out from SpeedStream. Are you currently satisfied with your internet connectivity, or are you looking to explore options for a better service?")
        connect = Connect()
        connect.stream(url=websocket_url)
        twml.append(connect)
        start_xml = str(twml.to_xml())
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        call = client.calls.create(
            twiml=start_xml,
            to=phone_number,
            from_=TWILIO_NUM
        )
        call_sids[call_sid] = {"twillo-sid":call.sid,"interested_caller_id":interested_caller_id}
        print(call_sids)
        return JSONResponse(content={"call_sid": call.sid})
    except Exception as e:
        logger.error(f"Error in make_call: {e}")
        return JSONResponse(content={"message": "Failed to initiate call"}, status_code=500)

async def send_response_to_twilio(call_sid, response_twiml):
    try:
        twilio_call_sid = call_sids.get(call_sid)
        if not twilio_call_sid:
            raise ValueError("Twilio call SID not found for the provided call_sid")

        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        call = client.calls(twilio_call_sid["twillo-sid"]).update(twiml=response_twiml)
        print(f"Sent response to Twilio: {response_twiml}")
    except Exception as e:
        print(f"Failed to send response to Twilio: {e}")

async def end_call(call_sid):
    try:
        twilio_call_sid = call_sids.get(call_sid)
        if not twilio_call_sid:
            raise ValueError("Twilio call SID not found for the provided call_sid")

        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        call = client.calls(twilio_call_sid["twillo-sid"]).update(status="completed")
        print(f"Ended call with SID: {twilio_call_sid['twillo-sid']}")
    except Exception as e:
        print(f"Failed to end the call: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6080)













