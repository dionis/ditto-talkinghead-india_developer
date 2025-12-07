"""
Real-time Talking Avatar with Gemini AI

This script creates an interactive experience where:
1. You speak into the microphone
2. Gemini AI processes your speech and responds
3. The Ditto avatar animates and "speaks" Gemini's response

Requirements:
- Set GOOGLE_API_KEY environment variable
- Provide an avatar source image
"""

import asyncio
import argparse
import os
import sys
import tempfile
import threading
import queue
import time
import numpy as np
import cv2
from pathlib import Path

from gemini_realtime import (
    GeminiLiveClient, 
    AudioRecorder, 
    AudioPlayer,
    resample_audio,
    save_audio_to_wav,
)
from stream_pipeline_offline import StreamSDK


class RealtimeAvatarSession:
    """Manages real-time avatar conversation session."""
    
    def __init__(
        self,
        source_image: str,
        data_root: str = "./checkpoints/ditto_pytorch",
        cfg_pkl: str = "./checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl",
        output_dir: str = "./tmp",
        api_key: str = None,
        system_prompt: str = "You are a friendly AI assistant. Keep responses brief and conversational, under 2 sentences when possible.",
    ):
        """
        Initialize the realtime avatar session.
        
        Args:
            source_image: Path to avatar source image
            data_root: Path to model checkpoints
            cfg_pkl: Path to config pickle file
            output_dir: Directory for temporary output files
            api_key: Google AI API key (or set GOOGLE_API_KEY env var)
            system_prompt: System instruction for Gemini
        """
        self.source_image = source_image
        self.data_root = data_root
        self.cfg_pkl = cfg_pkl
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Gemini client
        self.gemini = GeminiLiveClient(
            api_key=api_key,
            system_instruction=system_prompt,
        )
        
        # Initialize Ditto SDK
        print("Loading Ditto avatar model...")
        self.sdk = StreamSDK(cfg_pkl, data_root)
        print("Avatar model loaded!")
        
        # Audio components
        self.recorder = AudioRecorder(sample_rate=16000)
        self.player = AudioPlayer(sample_rate=24000)
        
        # State
        self.is_running = False
        self.audio_response_queue = queue.Queue()
        self.response_counter = 0
        
    async def process_response_audio(self) -> str:
        """
        Collect audio response from Gemini and save to WAV file.
        
        Returns:
            Path to the saved WAV file
        """
        audio_chunks = []
        
        try:
            async for audio_data in self.gemini.receive_audio():
                if audio_data:
                    audio_chunks.append(audio_data)
        except Exception as e:
            print(f"Error receiving audio: {e}")
            
        if not audio_chunks:
            return None
            
        # Combine all audio chunks
        full_audio = b"".join(audio_chunks)
        
        # Gemini outputs 24kHz, Ditto needs 16kHz
        resampled_audio = resample_audio(full_audio, from_rate=24000, to_rate=16000)
        
        # Save to WAV file
        self.response_counter += 1
        wav_path = str(self.output_dir / f"response_{self.response_counter}.wav")
        save_audio_to_wav(resampled_audio, wav_path, sample_rate=16000)
        
        return wav_path
        
    def animate_avatar(self, audio_path: str) -> str:
        """
        Generate avatar animation from audio.
        
        Args:
            audio_path: Path to audio WAV file
            
        Returns:
            Path to output video
        """
        import librosa
        import math
        
        output_path = str(self.output_dir / f"avatar_{self.response_counter}.mp4")
        
        # Setup avatar
        self.sdk.setup(self.source_image, output_path)
        
        # Load audio
        audio, sr = librosa.core.load(audio_path, sr=16000)
        num_frames = math.ceil(len(audio) / 16000 * 25)
        
        self.sdk.setup_Nd(N_d=num_frames, fade_in=-1, fade_out=-1)
        
        # Process audio
        aud_feat = self.sdk.wav2feat.wav2feat(audio)
        self.sdk.audio2motion_queue.put(aud_feat)
        self.sdk.close()
        
        # Merge with audio using imageio-ffmpeg for Windows compatibility
        final_output = str(self.output_dir / f"final_{self.response_counter}.mp4")
        try:
            import subprocess
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            subprocess.run([
                ffmpeg_exe, '-loglevel', 'error', '-y',
                '-i', self.sdk.tmp_output_path,
                '-i', audio_path,
                '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'aac',
                final_output
            ], check=True)
        except Exception as e:
            # Fallback to system ffmpeg
            cmd = f'ffmpeg -loglevel error -y -i "{self.sdk.tmp_output_path}" -i "{audio_path}" -map 0:v -map 1:a -c:v copy -c:a aac "{final_output}"'
            os.system(cmd)
        
        return final_output
        
    def play_video_with_audio(self, video_path: str, audio_path: str) -> None:
        """
        Play video with audio synchronization.
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio WAV file
        """
        import threading
        import wave
        import pyaudio
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        delay = int(1000 / fps) if fps > 0 else 40
        
        # Setup audio playback
        audio_finished = threading.Event()
        
        def play_audio():
            try:
                wf = wave.open(audio_path, 'rb')
                p = pyaudio.PyAudio()
                stream = p.open(
                    format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                
                chunk = 1024
                data = wf.readframes(chunk)
                while data and not audio_finished.is_set():
                    stream.write(data)
                    data = wf.readframes(chunk)
                    
                stream.stop_stream()
                stream.close()
                p.terminate()
                wf.close()
            except Exception as e:
                print(f"Audio playback error: {e}")
            finally:
                audio_finished.set()
        
        # Start audio in separate thread
        audio_thread = threading.Thread(target=play_audio, daemon=True)
        audio_thread.start()
        
        window_name = "AI Avatar"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 512, 512)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            cv2.imshow(window_name, frame)
            
            key = cv2.waitKey(delay) & 0xFF
            if key == ord('q'):
                audio_finished.set()
                break
                
        cap.release()
        
        # Wait for audio to finish
        audio_thread.join(timeout=1.0)
        
    def play_video(self, video_path: str) -> None:
        """
        Play video in a window using OpenCV (no audio).
        
        Args:
            video_path: Path to video file
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        delay = int(1000 / fps) if fps > 0 else 40
        
        window_name = "AI Avatar"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 512, 512)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            cv2.imshow(window_name, frame)
            
            key = cv2.waitKey(delay) & 0xFF
            if key == ord('q'):
                break
                
        cap.release()
        
    async def run_conversation_turn(self, audio_data: bytes) -> None:
        """
        Process one turn of conversation.
        
        Args:
            audio_data: Recorded audio bytes from user
        """
        print("\n🎤 Processing your speech...")
        
        # Send audio to Gemini
        await self.gemini.send_audio(audio_data)
        
        # Wait a moment for Gemini to process
        await asyncio.sleep(0.5)
        
        print("🤖 Getting AI response...")
        
        # Get response audio
        audio_path = await self.process_response_audio()
        
        if not audio_path:
            print("No audio response received")
            return
            
        print("🎬 Animating avatar...")
        
        # Generate avatar animation
        video_path = self.animate_avatar(audio_path)
        
        print(f"▶️  Playing response: {video_path}")
        
        # Play the video with audio
        self.play_video_with_audio(video_path, audio_path)
        
    async def record_and_send(self, duration: float = 5.0) -> bytes:
        """
        Record audio for specified duration.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Recorded audio bytes
        """
        print(f"\n🎙️  Recording for {duration} seconds... Speak now!")
        
        self.recorder.start()
        
        chunks = []
        num_chunks = int(16000 * duration / self.recorder.chunk_size)
        
        for _ in range(num_chunks):
            chunk = self.recorder.read_chunk()
            chunks.append(chunk)
            
        self.recorder.stop()
        
        print("✅ Recording complete!")
        
        return b"".join(chunks)
        
    async def run_interactive(self) -> None:
        """Run interactive conversation loop."""
        print("\n" + "="*60)
        print("🤖 Real-time Avatar Conversation")
        print("="*60)
        print("\nCommands:")
        print("  [Enter] - Record and send message (5 seconds)")
        print("  [q]     - Quit")
        print("\n" + "-"*60)
        
        await self.gemini.connect()
        self.is_running = True
        
        try:
            while self.is_running:
                user_input = input("\nPress Enter to speak (or 'q' to quit): ").strip().lower()
                
                if user_input == 'q':
                    print("\nGoodbye! 👋")
                    break
                    
                # Record audio
                audio_data = await self.record_and_send(duration=5.0)
                
                # Process conversation turn
                await self.run_conversation_turn(audio_data)
                
        except KeyboardInterrupt:
            print("\n\nInterrupted. Cleaning up...")
        finally:
            await self.cleanup()
            
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.is_running = False
        self.recorder.cleanup()
        self.player.cleanup()
        await self.gemini.close()
        cv2.destroyAllWindows()
        

def main():
    parser = argparse.ArgumentParser(
        description="Real-time Talking Avatar with Gemini AI"
    )
    parser.add_argument(
        "--image", "-i",
        type=str,
        default="./example/image.png",
        help="Path to avatar source image"
    )
    parser.add_argument(
        "--data_root",
        type=str,
        default="./checkpoints/ditto_pytorch",
        help="Path to model checkpoints (use ditto_pytorch for GPU)"
    )
    parser.add_argument(
        "--cfg_pkl",
        type=str,
        default="./checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl",
        help="Path to config pickle file"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./tmp",
        help="Directory for temporary output files"
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default=None,
        help="Google AI API key (or set GOOGLE_API_KEY environment variable)"
    )
    parser.add_argument(
        "--system_prompt",
        type=str,
        default="You are a friendly AI assistant. Keep responses brief and conversational, under 2 sentences when possible.",
        help="System prompt for the AI"
    )
    
    args = parser.parse_args()
    
    # Validate source image exists
    if not os.path.exists(args.image):
        print(f"Error: Source image not found: {args.image}")
        sys.exit(1)
        
    # Check for API key
    if not args.api_key and not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set.")
        print("Get an API key at: https://aistudio.google.com/apikey")
        print("Then run: set GOOGLE_API_KEY=your-key-here")
        sys.exit(1)
        
    # Create and run session
    session = RealtimeAvatarSession(
        source_image=args.image,
        data_root=args.data_root,
        cfg_pkl=args.cfg_pkl,
        output_dir=args.output_dir,
        api_key=args.api_key,
        system_prompt=args.system_prompt,
    )
    
    asyncio.run(session.run_interactive())


if __name__ == "__main__":
    main()
