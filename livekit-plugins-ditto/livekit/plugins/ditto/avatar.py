"""
Ditto Avatar Session

Main class for managing Ditto avatar sessions in LiveKit.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from livekit import rtc
from livekit.agents import utils

from .ditto_sdk import DittoSDKWrapper
from .video_source import DittoVideoSource
from .audio_processor import DittoAudioProcessor

logger = logging.getLogger(__name__)


class DittoAvatarSession:
    """
    Manages a Ditto avatar session within a LiveKit room.
    
    This class coordinates the Ditto SDK, audio processing, and video publishing
    to create a real-time talking head avatar.
    """
    
    def __init__(
        self,
        *,
        ditto_path: str,
        source_image: str,
        avatar_participant_identity: str = "ditto-avatar",
        data_root: str = "./checkpoints/ditto_pytorch",
        cfg_pkl: str = "./checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl",
        video_width: int = 512,
        video_height: int = 512,
        video_fps: int = 25,
        audio_chunk_ms: int = 200,
    ):
        """
        Initialize the Ditto avatar session.
        
        Args:
            ditto_path: Path to the Ditto TalkingHead installation
            source_image: Path to the avatar source image
            avatar_participant_identity: Identity for the avatar participant
            data_root: Path to Ditto model checkpoints
            cfg_pkl: Path to Ditto configuration file
            video_width: Video width in pixels
            video_height: Video height in pixels
            video_fps: Video frames per second
            audio_chunk_ms: Audio chunk size in milliseconds
        """
        self.ditto_path = ditto_path
        self.source_image = source_image
        self.avatar_identity = avatar_participant_identity
        
        # Initialize components
        self.ditto_sdk = DittoSDKWrapper(
            ditto_path=ditto_path,
            data_root=data_root,
            cfg_pkl=cfg_pkl,
        )
        
        self.video_source = DittoVideoSource(
            width=video_width,
            height=video_height,
            fps=video_fps,
        )
        
        self.audio_processor = DittoAudioProcessor(
            target_sample_rate=16000,
            chunk_size_ms=audio_chunk_ms,
        )
        
        # State
        self._room: Optional[rtc.Room] = None
        self._agent_session = None
        self._tasks: list[asyncio.Task] = []
        self._is_running = False
        
        logger.info(
            f"Initialized DittoAvatarSession: {avatar_participant_identity}, "
            f"image={source_image}"
        )
    
    async def start(
        self,
        agent_session,
        room: rtc.Room,
    ) -> None:
        """
        Start the avatar session.
        
        Args:
            agent_session: The LiveKit AgentSession
            room: The LiveKit Room to publish to
        """
        if self._is_running:
            logger.warning("Avatar session already running")
            return
        
        logger.info("Starting Ditto avatar session")
        
        self._room = room
        self._agent_session = agent_session
        
        try:
            # Load Ditto SDK
            logger.info("Loading Ditto SDK...")
            self.ditto_sdk.load()
            
            # Setup Ditto with source image
            logger.info("Setting up Ditto with source image...")
            output_path = f"./tmp/{self.avatar_identity}_output.mp4"
            Path("./tmp").mkdir(exist_ok=True)
            self.ditto_sdk.setup(self.source_image, output_path)
            
            # Create and publish video track
            logger.info("Creating video track...")
            video_track = self.video_source.create_track(
                f"{self.avatar_identity}-video"
            )
            
            await room.local_participant.publish_track(
                video_track,
                rtc.TrackPublishOptions(
                    source=rtc.TrackSource.SOURCE_CAMERA
                )
            )
            
            logger.info("Video track published successfully")
            
            # Start processing loops
            self._is_running = True
            self.video_source.start_publishing()
            
            # Start audio processing task
            self._tasks.append(
                asyncio.create_task(self._audio_processing_loop())
            )
            
            logger.info("Ditto avatar session started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start avatar session: {e}")
            await self.stop()
            raise
    
    async def _audio_processing_loop(self) -> None:
        """
        Main loop for processing audio and generating video frames.
        """
        logger.info("Starting audio processing loop")
        
        try:
            # Get audio stream from agent session
            # Note: This is a simplified version - actual implementation
            # would need to subscribe to the agent's audio output
            audio_stream = self._get_agent_audio_stream()
            
            async for audio_chunk in self.audio_processor.stream_audio_chunks(audio_stream):
                if not self._is_running:
                    break
                
                # Process audio chunk with Ditto
                self.ditto_sdk.process_audio_chunk(audio_chunk)
                
                # Get generated frames (this is a placeholder)
                # In reality, you'd need to implement frame retrieval from Ditto
                frames = await self._get_generated_frames()
                
                if frames:
                    # Publish frames
                    for frame in frames:
                        await self.video_source.publish_frame(frame)
                
        except Exception as e:
            logger.error(f"Error in audio processing loop: {e}")
        finally:
            logger.info("Audio processing loop ended")
    
    def _get_agent_audio_stream(self):
        """
        Get audio stream from agent session.
        
        This is a placeholder - actual implementation would depend on
        how the AgentSession exposes its audio output.
        """
        # TODO: Implement actual audio stream subscription
        # This might look like:
        # return self._agent_session.audio_output_stream()
        raise NotImplementedError(
            "Audio stream subscription needs to be implemented based on "
            "LiveKit AgentSession API"
        )
    
    async def _get_generated_frames(self):
        """
        Get generated video frames from Ditto SDK.
        
        This is a placeholder - actual implementation would need to
        retrieve frames from Ditto's processing pipeline.
        """
        # TODO: Implement frame retrieval from Ditto SDK
        # This might involve:
        # - Accessing Ditto's frame queue
        # - Converting frames to numpy arrays
        # - Handling synchronization
        return []
    
    async def stop(self) -> None:
        """Stop the avatar session and clean up resources."""
        if not self._is_running:
            return
        
        logger.info("Stopping Ditto avatar session")
        
        self._is_running = False
        self.video_source.stop_publishing()
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self._tasks.clear()
        
        # Close Ditto SDK
        self.ditto_sdk.close()
        
        logger.info("Ditto avatar session stopped")
    
    @property
    def is_running(self) -> bool:
        """Check if the session is running."""
        return self._is_running
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
