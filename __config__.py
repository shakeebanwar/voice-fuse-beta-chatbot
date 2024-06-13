NGROK_HTTPS_URL = "https://llmapi.voicefuse.xyz"
WEBSOCKET_SUBDOMAIN = NGROK_HTTPS_URL.replace("https://", "")
TWILIO_NUM = "+18773555998"
ACCOUNT_SID=  "AC4a092d7a6e1c689241b05d6bd45f72ad"
AUTH_TOKEN= "2fe2377370fdabe4339d62637009649b"
DEEPGRAM_API_KEY= "779048e3a1366cc3531c53bfb611943f61c534e9"
HEADERS = {'Authorization': f'Token {DEEPGRAM_API_KEY}'}
DEEPGRAM_ENDPOINT = "https://api.deepgram.com/v1/listen"

VERSION : str = "latest"
LANGUAGE : str = "en-US"
PUNCTUATE : str = "true"
INTERIM_RESULTS : str = "true"
ENDPOINTING : str = "true"
UTTERANCE_END_MS : str = "1000"
VAD_EVENTS : str = "true"
ENCODING : str = "mulaw"
SAMPLE_RATE: int = 8000
DEEPGRAM_MODEL:str = "nova-2-phonecall"
DEEPGRAM_URI: str = f"wss://api.deepgram.com/v1/listen?model={DEEPGRAM_MODEL}&language={LANGUAGE}&version={VERSION}&punctuate={PUNCTUATE}&interim_results={INTERIM_RESULTS}&endpointing={ENDPOINTING}&utterance_end_ms={UTTERANCE_END_MS}&sample_rate={SAMPLE_RATE}&encoding={ENCODING}&vad_events={VAD_EVENTS}"
DEFAULT_MESSAGE : str = "Sorry, can you repeat that again?" # This will the default transcription output

SECRET_KEY : str = "secret!"
