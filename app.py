import azure.cognitiveservices.speech as speechsdk
import base64
import datetime
import html
import json
import numpy as np
import os
import pytz
import random
import re
import requests
import threading
import time
import torch
import traceback
import uuid
from flask import Flask, Response, render_template, request
from flask_socketio import SocketIO, join_room
from azure.identity import DefaultAzureCredential
from vad_iterator import VADIterator, int2float
from DirectLineClient import DirectLineClient


app = Flask(__name__, template_folder='.')

socketio = SocketIO(app)


speech_region = os.environ.get('SPEECH_REGION')
speech_key = os.environ.get('SPEECH_KEY')


enable_websockets = True 
enable_vad = False 
enable_token_auth_for_speech = False
default_tts_voice = 'en-US-Andrew2:DragonHDLatestNeural'
sentence_level_punctuations = [ '.', '?', '!', ':', ';', '。', '？', '！', '：', '；' ] # Punctuations that indicate the end of a sentence
enable_quick_reply = True 
quick_replies = [ "Uhm, Let me take a look. I'm looking into it.", "Uhm, let me check that for you. I need to check our knowledge base"]
oyd_doc_regex = re.compile(r'\[doc(\d+)\]')


client_contexts = {}
speech_token = None
ice_token = None


vad_iterator = None
if enable_vad and enable_websockets:
    vad_model, _ = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad')
    vad_iterator = VADIterator(model=vad_model, threshold=0.5, sampling_rate=16000, min_silence_duration_ms=150, speech_pad_ms=100)


@app.route("/")
def index():
    return render_template("chat.html", methods=["GET"], client_id=initializeClient(), enable_websockets=enable_websockets)



@app.route("/chat")
def chatView():
    return render_template("chat.html", methods=["GET"], client_id=initializeClient(), enable_websockets=enable_websockets)


@app.route("/api/getSpeechToken", methods=["GET"])
def getSpeechToken() -> Response:
    global speech_token
    response = Response(speech_token, status=200)
    response.headers['SpeechRegion'] = speech_region
    return response


@app.route("/api/getIceToken", methods=["GET"])
def getIceToken() -> Response:
    return Response(ice_token, status=200)


@app.route("/api/connectAvatar", methods=["POST"])
def connectAvatar() -> Response:
    global client_contexts
    client_id = uuid.UUID(request.headers.get('ClientId'))

    disconnectAvatarInternal(client_id)
    client_context = client_contexts[client_id]

    client_context['tts_voice'] = request.headers.get('TtsVoice') if request.headers.get('TtsVoice') else default_tts_voice
    client_context['personal_voice_speaker_profile_id'] = request.headers.get('PersonalVoiceSpeakerProfileId')

    try:
        if enable_token_auth_for_speech:
            while not speech_token:
                time.sleep(0.2)
            speech_config = speechsdk.SpeechConfig(endpoint=f'wss://{speech_region}.tts.speech.microsoft.com/cognitiveservices/websocket/v1?enableTalkingAvatar=true')
            speech_config.authorization_token = speech_token
        else:
            speech_config = speechsdk.SpeechConfig(subscription=speech_key, endpoint=f'wss://{speech_region}.tts.speech.microsoft.com/cognitiveservices/websocket/v1?enableTalkingAvatar=true')


        client_context['speech_synthesizer'] = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        speech_synthesizer = client_context['speech_synthesizer']
        
        ice_token_obj = json.loads(ice_token)
        
        local_sdp = request.data.decode('utf-8')
        avatar_character = request.headers.get('AvatarCharacter')
        avatar_style = request.headers.get('AvatarStyle')
        background_color = '#FFFFFFFF' if request.headers.get('BackgroundColor') is None else request.headers.get('BackgroundColor')
        background_image_url = request.headers.get('BackgroundImageUrl')
        is_custom_avatar = request.headers.get('IsCustomAvatar')
        transparent_background = 'false' if request.headers.get('TransparentBackground') is None else request.headers.get('TransparentBackground')
        video_crop = 'false' if request.headers.get('VideoCrop') is None else request.headers.get('VideoCrop')
        avatar_config = {
            'synthesis': {
                'video': {
                    'protocol': {
                        'name': "WebRTC",
                        'webrtcConfig': {
                            'clientDescription': local_sdp,
                            'iceServers': [{
                                'urls': [ ice_token_obj['Urls'][0] ],
                                'username': ice_token_obj['Username'],
                                'credential': ice_token_obj['Password']
                            }]
                        },
                    },
                    'format':{
                        'crop':{
                            'topLeft':{
                                'x': 600 if video_crop.lower() == 'true' else 0,
                                'y': 0
                            },
                            'bottomRight':{
                                'x': 1320 if video_crop.lower() == 'true' else 1920,
                                'y': 1080
                            }
                        },
                        'bitrate': 1000000
                    },
                    'talkingAvatar': {
                        'customized': is_custom_avatar.lower() == 'true',
                        'character': avatar_character,
                        'style': avatar_style,
                        'background': {
                            'color': '#00FF00FF' if transparent_background.lower() == 'true' else background_color,
                            'image': {
                                'url': background_image_url
                            }
                        }
                    }
                }
            }
        }
        
        connection = speechsdk.Connection.from_speech_synthesizer(speech_synthesizer)
        connection.connected.connect(lambda evt: print(f'TTS Avatar service connected.'))
        def tts_disconnected_cb(evt):
            print(f'TTS Avatar service disconnected.')
            client_context['speech_synthesizer_connection'] = None
        connection.disconnected.connect(tts_disconnected_cb)
        connection.set_message_property('speech.config', 'context', json.dumps(avatar_config))
        client_context['speech_synthesizer_connection'] = connection

        speech_sythesis_result = speech_synthesizer.speak_text_async('').get()
        print(f'Result id for avatar connection: {speech_sythesis_result.result_id}')
        if speech_sythesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_sythesis_result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")
                raise Exception(cancellation_details.error_details)
        turn_start_message = speech_synthesizer.properties.get_property_by_name('SpeechSDKInternal-ExtraTurnStartMessage')
        remoteSdp = json.loads(turn_start_message)['webrtc']['connectionString']

        return Response(remoteSdp, status=200)

    except Exception as e:
        return Response(f"Result ID: {speech_sythesis_result.result_id}. Error message: {e}", status=400)


@app.route("/api/connectSTT", methods=["POST"])
def connectSTT() -> Response:
    global client_contexts
    client_id = uuid.UUID(request.headers.get('ClientId'))
   
    disconnectSttInternal(client_id)
    system_prompt = request.headers.get('SystemPrompt')
    client_context = client_contexts[client_id]
    try:
        if enable_token_auth_for_speech:
            while not speech_token:
                time.sleep(0.2)
            speech_config = speechsdk.SpeechConfig(endpoint=f'wss://{speech_region}.stt.speech.microsoft.com/speech/universal/v2')
            speech_config.authorization_token = speech_token
        else:
            speech_config = speechsdk.SpeechConfig(subscription=speech_key, endpoint=f'wss://{speech_region}.stt.speech.microsoft.com/speech/universal/v2')

        audio_input_stream = speechsdk.audio.PushAudioInputStream()
        client_context['audio_input_stream'] = audio_input_stream

        audio_config = speechsdk.audio.AudioConfig(stream=audio_input_stream)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        client_context['speech_recognizer'] = speech_recognizer

        speech_recognizer.session_started.connect(lambda evt: print(f'STT session started - session id: {evt.session_id}'))
        speech_recognizer.session_stopped.connect(lambda evt: print(f'STT session stopped.'))

        speech_recognition_start_time = datetime.datetime.now(pytz.UTC)

        def stt_recognized_cb(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                try:
                    user_query = evt.result.text.strip()
                    if user_query == '':
                        return

                    socketio.emit("response", { 'path': 'api.chat', 'chatResponse': '\n\nUser: ' + user_query + '\n\n' }, room=client_id)
                    recognition_result_received_time = datetime.datetime.now(pytz.UTC)
                    speech_finished_offset = (evt.result.offset + evt.result.duration) / 10000
                    stt_latency = round((recognition_result_received_time - speech_recognition_start_time).total_seconds() * 1000 - speech_finished_offset)
                    print(f'STT latency: {stt_latency}ms')
                    socketio.emit("response", { 'path': 'api.chat', 'chatResponse': f"<STTL>{stt_latency}</STTL>" }, room=client_id)
                    chat_initiated = client_context['chat_initiated']
                    if not chat_initiated:
                        initializeChatContext(system_prompt, client_id)
                        client_context['chat_initiated'] = True
                    first_response_chunk = True
                    for chat_response in handleUserQuery(user_query, client_id):
                        if first_response_chunk:
                            socketio.emit("response", { 'path': 'api.chat', 'chatResponse': 'Assistant: ' }, room=client_id)
                            first_response_chunk = False
                        socketio.emit("response", { 'path': 'api.chat', 'chatResponse': chat_response }, room=client_id)
                except Exception as e:
                    print(f"Error in handling user query: {e}")
        speech_recognizer.recognized.connect(stt_recognized_cb)

        def stt_recognizing_cb(evt):
            if not vad_iterator:
                stopSpeakingInternal(client_id)
        speech_recognizer.recognizing.connect(stt_recognizing_cb)

        def stt_canceled_cb(evt):
            cancellation_details = speechsdk.CancellationDetails(evt.result)
            print(f'STT connection canceled. Error message: {cancellation_details.error_details}')
        speech_recognizer.canceled.connect(stt_canceled_cb)

        speech_recognizer.start_continuous_recognition()
        return Response(status=200)

    except Exception as e:
        return Response(f"STT connection failed. Error message: {e}", status=400)


@app.route("/api/disconnectSTT", methods=["POST"])
def disconnectSTT() -> Response:
    client_id = uuid.UUID(request.headers.get('ClientId'))
    try:
        disconnectSttInternal(client_id)
        return Response('STT Disconnected.', status=200)
    except Exception as e:
        return Response(f"STT disconnection failed. Error message: {e}", status=400)


@app.route("/api/speak", methods=["POST"])
def speak() -> Response:
    client_id = uuid.UUID(request.headers.get('ClientId'))
    try:
        ssml = request.data.decode('utf-8')
        result_id = speakSsml(ssml, client_id, True)
        return Response(result_id, status=200)
    except Exception as e:
        return Response(f"Speak failed. Error message: {e}", status=400)


@app.route("/api/stopSpeaking", methods=["POST"])
def stopSpeaking() -> Response:
    global client_contexts
    client_id = uuid.UUID(request.headers.get('ClientId'))
    stopSpeakingInternal(client_id)
    return Response('Speaking stopped.', status=200)


@app.route("/api/chat", methods=["POST"])
def chat() -> Response:
    global client_contexts
    client_id = uuid.UUID(request.headers.get('ClientId'))
    client_context = client_contexts[client_id]
    chat_initiated = client_context['chat_initiated']
    if not chat_initiated:
        initializeChatContext(request.headers.get('SystemPrompt'), client_id)
        client_context['chat_initiated'] = True
    user_query = request.data.decode('utf-8')
    return Response(handleUserQuery(user_query, client_id), mimetype='text/plain', status=200)


@app.route("/api/chat/clearHistory", methods=["POST"])
def clearChatHistory() -> Response:
    client_id = uuid.UUID(request.headers.get('ClientId'))
    client_context = client_contexts[client_id]
    initializeChatContext(request.headers.get('SystemPrompt'), client_id)
    client_context['chat_initiated'] = True
    return Response('Chat history cleared.', status=200)


@app.route("/api/disconnectAvatar", methods=["POST"])
def disconnectAvatar() -> Response:
    client_id = uuid.UUID(request.headers.get('ClientId'))
    try:
        disconnectAvatarInternal(client_id)
        return Response('Disconnected avatar', status=200)
    except:
        return Response(traceback.format_exc(), status=400)


@app.route("/api/releaseClient", methods=["POST"])
def releaseClient() -> Response:
    global client_contexts
    client_id = uuid.UUID(json.loads(request.data)['clientId'])
    try:
        disconnectAvatarInternal(client_id)
        disconnectSttInternal(client_id)
        time.sleep(2) 
        client_contexts.pop(client_id)
        print(f"Client context released for client {client_id}.")
        return Response('Client context released.', status=200)
    except Exception as e:
        print(f"Client context release failed. Error message: {e}")
        return Response(f"Client context release failed. Error message: {e}", status=400)


@socketio.on("connect")
def handleWsConnection():
    client_id = uuid.UUID(request.args.get('clientId'))
    join_room(client_id)
    print(f"WebSocket connected for client {client_id}.")


@socketio.on("message")
def handleWsMessage(message):
    global client_contexts
    client_id = uuid.UUID(message.get('clientId'))
    path = message.get('path')
    client_context = client_contexts[client_id]
    if path == 'api.audio':
        chat_initiated = client_context['chat_initiated']
        audio_chunk = message.get('audioChunk')
        audio_chunk_binary = base64.b64decode(audio_chunk)
        audio_input_stream = client_context['audio_input_stream']
        if audio_input_stream:
            audio_input_stream.write(audio_chunk_binary)
        if vad_iterator:
            audio_buffer = client_context['vad_audio_buffer']
            audio_buffer.extend(audio_chunk_binary)
            if len(audio_buffer) >= 1024:
                audio_chunk_int = np.frombuffer(bytes(audio_buffer[:1024]), dtype=np.int16)
                audio_buffer.clear()
                audio_chunk_float = int2float(audio_chunk_int)
                vad_detected = vad_iterator(torch.from_numpy(audio_chunk_float))
                if vad_detected:
                    print("Voice activity detected.")
                    stopSpeakingInternal(client_id)
    elif path == 'api.chat':
        chat_initiated = client_context['chat_initiated']
        if not chat_initiated:
            initializeChatContext(message.get('systemPrompt'), client_id)
            client_context['chat_initiated'] = True
        user_query = message.get('userQuery')
        for chat_response in handleUserQuery(user_query, client_id):
            socketio.emit("response", { 'path': 'api.chat', 'chatResponse': chat_response }, room=client_id)
    elif path == 'api.stopSpeaking':
        stopSpeakingInternal(client_id)


def initializeClient() -> uuid.UUID:
    client_id = uuid.uuid4()
    client_contexts[client_id] = {
        'audio_input_stream': None,
        'vad_audio_buffer': [],
        'speech_recognizer': None,
        'tts_voice': default_tts_voice,
        'personal_voice_speaker_profile_id': None,
        'speech_synthesizer': None, 
        'speech_synthesizer_connection': None, 
        'speech_token': None,
        'ice_token': None, 
        'chat_initiated': False, 
        'messages': [], 
        'data_sources': [], 
        'is_speaking': False, 
        'spoken_text_queue': [],
        'speaking_thread': None,
        'last_speak_time': None 
    }
    return client_id


def refreshIceToken() -> None:
    global ice_token
    ice_token_response = None

    if enable_token_auth_for_speech:
        while not speech_token:
            time.sleep(0.2)
        ice_token_response = requests.get(f'https://{speech_region}.tts.speech.microsoft.com/cognitiveservices/avatar/relay/token/v1', headers={'Authorization': f'Bearer {speech_token}'})
    else:
        ice_token_response = requests.get(f'https://{speech_region}.tts.speech.microsoft.com/cognitiveservices/avatar/relay/token/v1', headers={'Ocp-Apim-Subscription-Key': speech_key})
    if ice_token_response.status_code == 200:
        ice_token = ice_token_response.text
    else:
        raise Exception(f"Failed to get ICE token. Status code: {ice_token_response.status_code}")


def refreshSpeechToken() -> None:
    global speech_token
    while True:
        speech_token = requests.post(f'https://{speech_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken', headers={'Ocp-Apim-Subscription-Key': speech_key}).text
        time.sleep(60 * 9)


def initializeChatContext(system_prompt: str, client_id: uuid.UUID) -> None:
    global client_contexts
    client_context = client_contexts[client_id]

    messages = client_context['messages']
    data_sources = client_context['data_sources']

    data_sources.clear()

    # Initialize messages
    messages.clear()
    if len(data_sources) == 0:
        system_message = {
            'role': 'system',
            'content': system_prompt
        }
        messages.append(system_message)


def handleUserQuery(user_query: str, client_id: uuid.UUID):
    global client_contexts
    client_context = client_contexts[client_id]

    messages = client_context['messages']
    data_sources = client_context['data_sources']

    chat_message = {
        'role': 'user',
        'content': user_query
    }

    messages.append(chat_message)


    if enable_quick_reply:
        speakWithQueue(random.choice(quick_replies), 2000, client_id)

    assistant_reply = ''
    tool_content = ''
    spoken_sentence = ''

    aoai_start_time = datetime.datetime.now(pytz.UTC)
    

    dl_client = DirectLineClient()
    conversation_id = dl_client.start_conversation()
    dl_client.send_message(conversation_id, messages[-1]['content'])
    got_response_from_bot = False
    while not got_response_from_bot:
        responses = dl_client.get_bot_responses(conversation_id)
        if responses:
            bot_response_message = dl_client.get_bot_message(responses)
            if bot_response_message:
                got_response_from_bot = True


    is_first_chunk = True
    is_first_sentence = True
    for chunk in bot_response_message.split():
        if len(chunk) > 0:
            response_token = chunk
            if response_token is not None:
                if is_first_chunk:
                    first_token_latency_ms = round((datetime.datetime.now(pytz.UTC) - aoai_start_time).total_seconds() * 1000)
                    print(f"AOAI first token latency: {first_token_latency_ms}ms")
                    yield f"<FTL>{first_token_latency_ms}</FTL>"
                    is_first_chunk = False
                if oyd_doc_regex.search(response_token):
                    response_token = oyd_doc_regex.sub('', response_token).strip()
                yield response_token + " "
                assistant_reply += response_token + " "
                if response_token == '\n' or response_token == '\n\n':
                    if is_first_sentence:
                        first_sentence_latency_ms = round((datetime.datetime.now(pytz.UTC) - aoai_start_time).total_seconds() * 1000)
                        print(f"AOAI first sentence latency: {first_sentence_latency_ms}ms")
                        yield f"<FSL>{first_sentence_latency_ms}</FSL>"
                        is_first_sentence = False
                    speakWithQueue(spoken_sentence.strip(), 0, client_id)
                    spoken_sentence = ''
                else:
                    response_token = response_token.replace('\n', '')
                    spoken_sentence += response_token + " " 
                    if len(response_token) == 1 or len(response_token) == 2:
                        for punctuation in sentence_level_punctuations:
                            if response_token.startswith(punctuation):
                                if is_first_sentence:
                                    first_sentence_latency_ms = round((datetime.datetime.now(pytz.UTC) - aoai_start_time).total_seconds() * 1000)
                                    print(f"AOAI first sentence latency: {first_sentence_latency_ms}ms")
                                    yield f"<FSL>{first_sentence_latency_ms}</FSL>"
                                    is_first_sentence = False
                                speakWithQueue(spoken_sentence.strip(), 0, client_id)
                                spoken_sentence = ''
                                break

    if spoken_sentence != '':
        speakWithQueue(spoken_sentence.strip(), 0, client_id)
        spoken_sentence = ''

    if len(data_sources) > 0:
        tool_message = {
            'role': 'tool',
            'content': tool_content
        }
        messages.append(tool_message)

    assistant_message = {
        'role': 'assistant',
        'content': assistant_reply
    }
    messages.append(assistant_message)


def speakWithQueue(text: str, ending_silence_ms: int, client_id: uuid.UUID) -> None:
    global client_contexts
    client_context = client_contexts[client_id]
    spoken_text_queue = client_context['spoken_text_queue']
    is_speaking = client_context['is_speaking']
    spoken_text_queue.append(text)
    if not is_speaking:
        def speakThread():
            nonlocal client_context
            nonlocal spoken_text_queue
            nonlocal ending_silence_ms
            tts_voice = client_context['tts_voice']
            personal_voice_speaker_profile_id = client_context['personal_voice_speaker_profile_id']
            client_context['is_speaking'] = True
            while len(spoken_text_queue) > 0:
                text = spoken_text_queue.pop(0)
                try:
                    speakText(text, tts_voice, personal_voice_speaker_profile_id, ending_silence_ms, client_id)
                except Exception as e:
                    print(f"Error in speaking text: {e}")
                client_context['last_speak_time'] = datetime.datetime.now(pytz.UTC)
            client_context['is_speaking'] = False
            print(f"Speaking thread stopped.")
        client_context['speaking_thread'] = threading.Thread(target=speakThread)
        client_context['speaking_thread'].start()


def speakText(text: str, voice: str, speaker_profile_id: str, ending_silence_ms: int, client_id: uuid.UUID) -> str:
    ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='en-US'>
                 <voice name='{voice}'>
                     <mstts:ttsembedding speakerProfileId='{speaker_profile_id}'>
                         <mstts:leadingsilence-exact value='0'/>
                         {html.escape(text)}
                     </mstts:ttsembedding>
                 </voice>
               </speak>"""
    if ending_silence_ms > 0:
        ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='en-US'>
                     <voice name='{voice}'>
                         <mstts:ttsembedding speakerProfileId='{speaker_profile_id}'>
                             <mstts:leadingsilence-exact value='0'/>
                             {html.escape(text)}
                             <break time='{ending_silence_ms}ms' />
                         </mstts:ttsembedding>
                     </voice>
                   </speak>"""
    return speakSsml(ssml, client_id, False)


def speakSsml(ssml: str, client_id: uuid.UUID, asynchronized: bool) -> str:
    global client_contexts
    speech_synthesizer = client_contexts[client_id]['speech_synthesizer']
    speech_sythesis_result = speech_synthesizer.start_speaking_ssml_async(ssml).get() if asynchronized else speech_synthesizer.speak_ssml_async(ssml).get()
    if speech_sythesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_sythesis_result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Result ID: {speech_sythesis_result.result_id}. Error details: {cancellation_details.error_details}")
            raise Exception(cancellation_details.error_details)
    return speech_sythesis_result.result_id


def stopSpeakingInternal(client_id: uuid.UUID) -> None:
    global client_contexts
    client_context = client_contexts[client_id]
    spoken_text_queue = client_context['spoken_text_queue']
    spoken_text_queue.clear()
    avatar_connection = client_context['speech_synthesizer_connection']
    if avatar_connection:
        avatar_connection.send_message_async('synthesis.control', '{"action":"stop"}').get()


def disconnectAvatarInternal(client_id: uuid.UUID) -> None:
    global client_contexts
    client_context = client_contexts[client_id]
    stopSpeakingInternal(client_id)
    time.sleep(2)
    avatar_connection = client_context['speech_synthesizer_connection']
    if avatar_connection:
        avatar_connection.close()


def disconnectSttInternal(client_id: uuid.UUID) -> None:
    global client_contexts
    client_context = client_contexts[client_id]
    speech_recognizer = client_context['speech_recognizer']
    audio_input_stream = client_context['audio_input_stream']
    if speech_recognizer:
        speech_recognizer.stop_continuous_recognition()
        connection = speechsdk.Connection.from_recognizer(speech_recognizer)
        connection.close()
        client_context['speech_recognizer'] = None
    if audio_input_stream:
        audio_input_stream.close()
        client_context['audio_input_stream'] = None


speechTokenRefereshThread = threading.Thread(target=refreshSpeechToken)
speechTokenRefereshThread.daemon = True
speechTokenRefereshThread.start()


refreshIceToken()