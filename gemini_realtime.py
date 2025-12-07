"""
Gemini Live API Real-time Audio Module

This module handles real-time audio streaming to and from Google's Gemini API
for interactive voice conversations.
"""

import asyncio
import base64
import os
import numpy as np
from typing import AsyncGenerator, Optional, Callable
import wave
import io

try:
    from google import genai
    from google.genai import types
except ImportError:
    raise ImportError("Please install google-genai: pip install google-genai")


class GeminiLiveClient:
    """Client for Gemini Live API real-time audio conversations."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash-native-audio-preview-09-2025",
        system_instruction: str = "You are a friendly and helpful AI assistant. Keep your responses concise and conversational.",
    ):
        """
        Initialize Gemini Live client.
        
        Args:
            api_key: Google AI API key. If None, uses GOOGLE_API_KEY environment variable.
            model: Gemini model to use for live conversations.
            system_instruction: System prompt for the AI assistant.
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = model
        self.system_instruction = system_instruction
        self.session = None
        self._audio_buffer = []
        
    async def connect(self) -> None:
        """Establish connection to Gemini Live API."""
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"  # Natural sounding voice
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part(text=self.system_instruction)]
            ),
        )
        
        # The live.connect returns an async context manager, we need to enter it
        self._session_cm = self.client.aio.live.connect(
            model=self.model,
            config=config,
        )
        self.session = await self._session_cm.__aenter__()
        print("Connected to Gemini Live API")
        
    async def send_audio(self, audio_data: bytes, mime_type: str = "audio/pcm") -> None:
        """
        Send audio data to Gemini.
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM, 16kHz, mono)
            mime_type: Audio MIME type
        """
        if not self.session:
            raise RuntimeError("Not connected. Call connect() first.")
            
        await self.session.send(
            input=types.LiveClientRealtimeInput(
                media_chunks=[
                    types.Blob(data=audio_data, mime_type=mime_type)
                ]
            )
        )
        
    async def receive_audio(self) -> AsyncGenerator[bytes, None]:
        """
        Receive audio responses from Gemini.
        
        Yields:
            Audio data chunks (24kHz PCM)
        """
        if not self.session:
            raise RuntimeError("Not connected. Call connect() first.")
            
        async for response in self.session.receive():
            if hasattr(response, 'data') and response.data:
                yield response.data
            elif hasattr(response, 'server_content'):
                content = response.server_content
                if hasattr(content, 'model_turn') and content.model_turn:
                    for part in content.model_turn.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            yield part.inline_data.data
                            
    async def close(self) -> None:
        """Close the Gemini Live session."""
        if self.session and hasattr(self, '_session_cm'):
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self.session = None
            print("Disconnected from Gemini Live API")


def resample_audio(audio_data: bytes, from_rate: int, to_rate: int) -> bytes:
    """
    Resample audio data from one sample rate to another.
    
    Args:
        audio_data: Raw PCM audio bytes (16-bit)
        from_rate: Source sample rate (e.g., 24000)
        to_rate: Target sample rate (e.g., 16000)
        
    Returns:
        Resampled audio bytes
    """
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    # Calculate resampling ratio
    ratio = to_rate / from_rate
    new_length = int(len(audio_array) * ratio)
    
    # Simple linear interpolation resampling
    indices = np.linspace(0, len(audio_array) - 1, new_length)
    resampled = np.interp(indices, np.arange(len(audio_array)), audio_array)
    
    return resampled.astype(np.int16).tobytes()


def save_audio_to_wav(audio_data: bytes, filepath: str, sample_rate: int = 16000) -> None:
    """
    Save raw PCM audio data to a WAV file.
    
    Args:
        audio_data: Raw PCM audio bytes (16-bit, mono)
        filepath: Output WAV file path
        sample_rate: Audio sample rate
    """
    with wave.open(filepath, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)


def audio_bytes_to_wav_buffer(audio_data: bytes, sample_rate: int = 16000) -> io.BytesIO:
    """
    Convert raw PCM audio to WAV format in memory.
    
    Args:
        audio_data: Raw PCM audio bytes (16-bit, mono)
        sample_rate: Audio sample rate
        
    Returns:
        BytesIO buffer containing WAV data
    """
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)
    buffer.seek(0)
    return buffer


class AudioRecorder:
    """Record audio from microphone using PyAudio."""
    
    def __init__(
        self, 
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
    ):
        """
        Initialize audio recorder.
        
        Args:
            sample_rate: Recording sample rate (16000 for Gemini)
            channels: Number of audio channels (1 for mono)
            chunk_size: Samples per chunk
        """
        try:
            import pyaudio
        except ImportError:
            raise ImportError("Please install pyaudio: pip install pyaudio")
            
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None
        self._recording = False
        
    def start(self) -> None:
        """Start recording from microphone."""
        import pyaudio
        
        self.stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )
        self._recording = True
        print("Microphone recording started")
        
    def read_chunk(self) -> bytes:
        """Read a chunk of audio data."""
        if not self.stream or not self._recording:
            return b""
        return self.stream.read(self.chunk_size, exception_on_overflow=False)
        
    def stop(self) -> None:
        """Stop recording."""
        self._recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        print("Microphone recording stopped")
        
    def cleanup(self) -> None:
        """Clean up PyAudio resources."""
        self.stop()
        self.pyaudio.terminate()


class AudioPlayer:
    """Play audio through speakers using PyAudio."""
    
    def __init__(self, sample_rate: int = 24000, channels: int = 1):
        """
        Initialize audio player.
        
        Args:
            sample_rate: Playback sample rate (24000 from Gemini)
            channels: Number of audio channels
        """
        try:
            import pyaudio
        except ImportError:
            raise ImportError("Please install pyaudio: pip install pyaudio")
            
        self.sample_rate = sample_rate
        self.channels = channels
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None
        
    def start(self) -> None:
        """Start playback stream."""
        import pyaudio
        
        self.stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
        )
        print("Audio playback started")
        
    def play(self, audio_data: bytes) -> None:
        """Play audio data."""
        if self.stream:
            self.stream.write(audio_data)
            
    def stop(self) -> None:
        """Stop playback."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        print("Audio playback stopped")
        
    def cleanup(self) -> None:
        """Clean up PyAudio resources."""
        self.stop()
        self.pyaudio.terminate()


if __name__ == "__main__":
    # Simple test
    async def test():
        client = GeminiLiveClient()
        await client.connect()
        print("Test connection successful!")
        await client.close()
        
    asyncio.run(test())
