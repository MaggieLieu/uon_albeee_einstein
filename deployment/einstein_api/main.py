# uvicorn main:app --host 0.0.0.0 --port 8964 --workers 1

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Path,
    Query,
    HTTPException,
    Request,
    Response,
    status,
    File,
    UploadFile,
    Body,
)
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
import asyncio
import json
import io
import wave
from piper import PiperVoice
import os
from collections.abc import AsyncGenerator
from httpx import Response as HttpxResponse
import re
import speech_recognition as sr
import tempfile
from pydub import AudioSegment
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ADK Einstein Chat + Real-time Voice")

# ─────────────────────────────────────
# Model loading (fails fast if missing)
# ─────────────────────────────────────
MODEL_PATH = (
    "./piper_model/en_GB-alaneinstein-medium.onnx"
)
if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"Model not found: {MODEL_PATH}")

try:
    voice = PiperVoice.load(MODEL_PATH, use_cuda=True)
    print("Model loaded successfully on GPU (CUDA).")
except Exception as e:
    # Fall back to the CPU
    voice = PiperVoice.load(MODEL_PATH, use_cuda=False)


SAMPLE_RATE = 22050

ADK_BASE_URL = "http://127.0.0.1:8965"
ADK_SSE_URL = f"{ADK_BASE_URL}/run_sse"
APP_NAME = "uon_agent_albeee"


app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"], 
    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for POST body
class AskRequest(BaseModel):
    prompt: str


async def create_adk_session(uid: str, sid: str) -> HttpxResponse | None:
    """Create ADK session if it doesn't exist. Returns the ADK response object."""
    url = f"{ADK_BASE_URL}/apps/{APP_NAME}/users/{uid}/sessions/{sid}"

    SUCCESS_STATUSES = (
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
        status.HTTP_409_CONFLICT,
    )

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json={"initial_state": {}})

            if resp.status_code in SUCCESS_STATUSES:
                return resp
            else:
                print(f"ADK returned unexpected status code: {resp.status_code}")
                return resp

        except httpx.RequestError as e:
            print(f"Failed to contact ADK: {e}")
            return None


async def delete_adk_session(uid: str, sid: str) -> HttpxResponse | None:
    url = f"{ADK_BASE_URL}/apps/{APP_NAME}/users/{uid}/sessions/{sid}"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.delete(url)
            return resp
        except httpx.RequestError as e:
            print(f"Failed to contact ADK: {e}")
            return None

def create_wav_header(
    sample_rate: int = 22050, channels: int = 1, width: int = 2
) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(width)
        wav.setframerate(sample_rate)
    return buffer.getvalue()


async def tts_stream_generator(text: str):
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    yield create_wav_header(sample_rate=SAMPLE_RATE, channels=1, width=2)

    for chunk in voice.synthesize(text.strip()):
        yield chunk.audio_int16_bytes



async def adk_sse_stream(uid: str, sid: str, user_prompt: str):
    payload = {
        "appName": APP_NAME,
        "userId": uid,
        "sessionId": sid,
        "newMessage": {"role": "user", "parts": [{"text": user_prompt}]},
        "streaming": True,
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", ADK_SSE_URL, json=payload) as response:
            response.raise_for_status()

            buffer = b""
            async for chunk in response.aiter_bytes():
                buffer += chunk
                while b"\n" in buffer:
                    line_bytes, buffer = buffer.split(b"\n", 1)
                    line = line_bytes.decode("utf-8").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data:
                        continue
                    try:
                        json_data = json.loads(data)
                        if json_data.get("partial") and json_data.get("content"):
                            text_part = json_data["content"]["parts"][0]["text"]
                            if text_part.strip():
                                yield text_part
                    except (json.JSONDecodeError, KeyError, AttributeError):
                        continue


def refactor_to_speech(text):
    # remove asterisks
    text = text.replace("*", "")
    # convert £ to pounds
    pattern = r"(\u00A3)([\d,]+)"
    replacement = r"\2 pounds"
    text = re.sub(pattern, replacement, text)
    # replace MSci to MSc
    text = re.sub(r"msci", "MSc", text, flags=re.IGNORECASE)
    # replacing physics formulas
    text = re.sub(r'=mc\u00b2', r'= m c squared', text, flags=re.IGNORECASE)
    text = re.sub(r'=mc', r'= m c', text, flags=re.IGNORECASE)
    text = re.sub(r'\u00b2', r'squared', text, flags=re.IGNORECASE)
    return text


async def transcribe_audio(audio_data: bytes) -> str:
    """Transcribe audio data to text using SpeechRecognition."""
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

    try:
        # Save uploaded audio data
        with open(temp_input.name, "wb") as f:
            f.write(audio_data)

        # Convert to WAV format using pydub
        audio = AudioSegment.from_file(temp_input.name)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio.export(temp_output.name, format="wav")

        # Create a recognizer instance
        recognizer = sr.Recognizer()

        # Load the WAV file
        with sr.AudioFile(temp_output.name) as source:
            audio_data_sr = recognizer.record(source)

        # Perform speech recognition
        text = recognizer.recognize_google(audio_data_sr)
        return text

    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand audio")
    except sr.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Recognition service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
    finally:
        try:
            os.unlink(temp_input.name)
            os.unlink(temp_output.name)
        except:
            pass


@app.get(
    "/uid/{uid}/sid/{sid}/init",
    summary="Create or ensure ADK session exists (idempotent)",
    description="Call this once per user/session before using /ask. Returns the ADK service's response payload and status code.",
)
async def init_session(
    uid: str = Path(..., description="User ID"),
    sid: str = Path(..., description="Session ID"),
    response: Response = Response(),
):
    adk_response = await create_adk_session(uid, sid)

    if adk_response is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to contact ADK backend at {ADK_BASE_URL}. Is it running?",
        )

    try:
        response.status_code = adk_response.status_code
        return adk_response.json()

    except httpx.BadJSON as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ADK returned an unexpected non-JSON response with status {adk_response.status_code}. Error: {e}",
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the ADK response.",
        )
    

@app.get(
    "/uid/{uid}/sid/{sid}/delete",
    summary="Delete ADK session",
)
async def delete_session(
    uid: str = Path(..., description="User ID"),
    sid: str = Path(..., description="Session ID"),
    response: Response = Response(),
):
    adk_response = await delete_adk_session(uid, sid)

    if adk_response is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to contact ADK backend at {ADK_BASE_URL}. Is it running?",
        )

    try:
        response.status_code = adk_response.status_code
        return adk_response.json()

    except httpx.BadJSON as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ADK returned an unexpected non-JSON response with status {adk_response.status_code}. Error: {e}",
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the ADK response.",
        )

@app.post(
    "/uid/{uid}/sid/{sid}/ask",
    summary="Real-time Einstein: streams text + audio (SSE + embedded WAV chunks)",
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Server-Sent Events with JSON events containing `text` and/or `audio` (base64)",
        }
    },
)
async def ask_tts_sse(
    uid: str = Path(..., description="User ID"),
    sid: str = Path(..., description="Session ID"),
    ask_request: AskRequest = Body(..., description="Request body with prompt"),
    request: Request = None,
):
    prompt = ask_request.prompt
    
    if not prompt or len(prompt.strip()) == 0:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    async def sse_generator():
        wav_header = create_wav_header(sample_rate=SAMPLE_RATE, channels=1, width=2)
        yield f"data: {json.dumps({'type': 'header', 'sampleRate': SAMPLE_RATE, 'audio': wav_header.hex()})}\n\n"

        sentence_buffer = ""

        async for text_chunk in adk_sse_stream(uid, sid, prompt):
            sentence_buffer += text_chunk

            yield f"data: {json.dumps({'type': 'text', 'content': text_chunk})}\n\n"

            if any(text_chunk.endswith(p) for p in ".!?;:\n"):
                if sentence_buffer.strip():
                    for audio_chunk in voice.synthesize(
                        refactor_to_speech(sentence_buffer).strip()
                    ):
                        audio_b64 = audio_chunk.audio_int16_bytes.hex()
                        yield f"data: {json.dumps({'type': 'audio', 'audio': audio_b64})}\n\n"
                    sentence_buffer = ""

        if sentence_buffer.strip():
            for audio_chunk in voice.synthesize(
                refactor_to_speech(sentence_buffer.strip())
            ):
                audio_b64 = audio_chunk.audio_int16_bytes.hex()
                yield f"data: {json.dumps({'type': 'audio', 'audio': audio_b64})}\n\n"

        yield 'data: {"type": "done"}\n\n'

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.post(
    "/uid/{uid}/sid/{sid}/speak",
    summary="Speech-to-Text-to-Speech: Upload audio, get Einstein's voice response (SSE)",
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Server-Sent Events with transcription + Einstein's text + audio response",
        }
    },
)
async def speak_tts_sse(
    uid: str = Path(..., description="User ID"),
    sid: str = Path(..., description="Session ID"),
    audio: UploadFile = File(..., description="Audio file (webm, wav, etc.)"),
):
    """
    Complete voice conversation flow:
    1. Transcribe user's speech to text
    2. Send to Einstein AI
    3. Stream back Einstein's text + audio response
    """

    async def sse_generator():
        # Step 1: Transcribe the audio
        audio_data = await audio.read()

        try:
            transcript = await transcribe_audio(audio_data)

            # Send the transcription to the client
            yield f"data: {json.dumps({'type': 'transcription', 'text': transcript})}\n\n"

        except HTTPException as e:
            yield f"data: {json.dumps({'type': 'error', 'message': e.detail})}\n\n"
            return

        # Step 2: Send WAV header for audio playback
        wav_header = create_wav_header(sample_rate=SAMPLE_RATE, channels=1, width=2)
        yield f"data: {json.dumps({'type': 'header', 'sampleRate': SAMPLE_RATE, 'audio': wav_header.hex()})}\n\n"

        # Step 3: Get Einstein's response
        sentence_buffer = ""

        async for text_chunk in adk_sse_stream(uid, sid, transcript):
            sentence_buffer += text_chunk

            # Stream Einstein's text response
            yield f"data: {json.dumps({'type': 'text', 'content': text_chunk})}\n\n"

            # Generate and stream audio when sentence ends
            if any(text_chunk.endswith(p) for p in ".!?;:\n"):
                if sentence_buffer.strip():
                    for audio_chunk in voice.synthesize(
                        refactor_to_speech(sentence_buffer).strip()
                    ):
                        audio_b64 = audio_chunk.audio_int16_bytes.hex()
                        yield f"data: {json.dumps({'type': 'audio', 'audio': audio_b64})}\n\n"
                    sentence_buffer = ""

        # Final leftover text
        if sentence_buffer.strip():
            for audio_chunk in voice.synthesize(
                refactor_to_speech(sentence_buffer.strip())
            ):
                audio_b64 = audio_chunk.audio_int16_bytes.hex()
                yield f"data: {json.dumps({'type': 'audio', 'audio': audio_b64})}\n\n"

        # End of stream
        yield 'data: {"type": "done"}\n\n'

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Content-Type-Options": "nosniff",
        },
    )

# app.mount("/static", StaticFiles(directory="static"), name="static")

# @app.get("/{full_path:path}")
# async def serve_spa(full_path: str):
#     return FileResponse("static/index.html")