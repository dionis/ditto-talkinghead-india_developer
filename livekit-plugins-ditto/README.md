# LiveKit Plugins - Ditto

LiveKit Agents plugin for integrating [Ditto TalkingHead](https://github.com/antgroup/ditto-talkinghead) as a virtual avatar provider.

## Overview

This plugin enables real-time talking head video generation using the Ditto model within LiveKit Agents Framework. It treats the Ditto SDK as an external resource and provides a clean integration layer.

## Features

- ✅ Real-time talking head video generation
- ✅ Seamless integration with LiveKit Agents
- ✅ Support for custom avatar images
- ✅ Audio-video synchronization
- ✅ Configurable video quality and frame rate
- ✅ External Ditto SDK management

## Installation

### Prerequisites

1. **Ditto TalkingHead** installed and configured
   - Follow the [Ditto installation guide](https://github.com/antgroup/ditto-talkinghead)
   - Download model checkpoints
   - Verify Ditto works standalone

2. **Python 3.10** (required for compatibility)

3. **NVIDIA GPU** with CUDA support (recommended)

### Install Plugin

```bash
# From the plugin directory
pip install -e .

# Or install dependencies separately
pip install livekit livekit-agents
```

### Install Additional Plugins

```bash
# For STT, LLM, TTS
pip install livekit-plugins-deepgram
pip install livekit-plugins-openai
pip install livekit-plugins-elevenlabs
pip install livekit-plugins-silero  # For VAD
```

## Quick Start

### 1. Configure Environment

Create a `.env` file with your API keys:

```bash
# LiveKit
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# AI Services
OPENAI_API_KEY=your-openai-key
DEEPGRAM_API_KEY=your-deepgram-key
ELEVENLABS_API_KEY=your-elevenlabs-key
```

### 2. Create Your Agent

```python
from livekit import agents
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins import openai, silero, deepgram, elevenlabs
from livekit.plugins.ditto import DittoAvatarSession

class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a helpful AI assistant."
        )

async def entrypoint(ctx: agents.JobContext):
    # Create avatar session
    avatar_session = DittoAvatarSession(
        ditto_path="/path/to/ditto",
        source_image="/path/to/avatar.png",
        data_root="/path/to/checkpoints/ditto_pytorch",
        cfg_pkl="/path/to/checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl",
    )
    
    # Create agent session
    session = AgentSession(
        stt=deepgram.STT(model="nova-2"),
        llm=openai.LLM(model="gpt-4o"),
        tts=elevenlabs.TTS(voice="Rachel"),
        vad=silero.VAD.load(),
    )
    
    # Start avatar and agent
    await avatar_session.start(session, room=ctx.room)
    await session.start(room=ctx.room, agent=MyAgent())
    await session.generate_reply()

if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )
```

### 3. Run the Agent

```bash
python your_agent.py dev
```

## Configuration

### DittoAvatarSession Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ditto_path` | str | **Required** | Path to Ditto installation |
| `source_image` | str | **Required** | Path to avatar source image |
| `avatar_participant_identity` | str | `"ditto-avatar"` | Identity for avatar participant |
| `data_root` | str | `"./checkpoints/ditto_pytorch"` | Path to Ditto checkpoints |
| `cfg_pkl` | str | `"./checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl"` | Path to config file |
| `video_width` | int | `512` | Video width in pixels |
| `video_height` | int | `512` | Video height in pixels |
| `video_fps` | int | `25` | Video frames per second |
| `audio_chunk_ms` | int | `200` | Audio chunk size in ms |

## Architecture

```
User → WebRTC → LiveKit Room → AgentSession → DittoAvatarSession
                                     ↓              ↓
                                   LLM/TTS    Ditto SDK (External)
                                     ↓              ↓
                                   Audio      Video Frames
                                     ↓              ↓
                                 Avatar Worker → LiveKit Room → User
```

### Components

- **DittoAvatarSession**: Main coordinator class
- **DittoSDKWrapper**: Manages external Ditto SDK
- **DittoVideoSource**: Handles video frame publishing
- **DittoAudioProcessor**: Processes audio streams

## Examples

See the `examples/` directory for complete examples:

- `basic_agent.py` - Simple voice agent with avatar
- `.env.example` - Environment configuration template

## Development

### Project Structure

```
livekit-plugins-ditto/
├── livekit/
│   └── plugins/
│       └── ditto/
│           ├── __init__.py
│           ├── avatar.py          # Main AvatarSession
│           ├── video_source.py    # Video management
│           ├── audio_processor.py # Audio processing
│           ├── ditto_sdk.py       # SDK wrapper
│           └── version.py
├── examples/
│   ├── basic_agent.py
│   └── .env.example
├── pyproject.toml
└── README.md
```

### Testing

```bash
# Run with LiveKit Playground
python examples/basic_agent.py dev

# Test in a real room
python examples/basic_agent.py connect \
  --room your-room-name \
  --url wss://your-server.com
```

## Troubleshooting

### Common Issues

**1. Ditto SDK not found**
```
RuntimeError: Could not load Ditto SDK from /path/to/ditto
```
- Verify `ditto_path` points to correct Ditto installation
- Check that `stream_pipeline_online.py` exists in that path

**2. Model checkpoints not found**
```
FileNotFoundError: Checkpoint file not found
```
- Verify `data_root` and `cfg_pkl` paths are correct
- Download Ditto checkpoints from HuggingFace

**3. CUDA/GPU errors**
```
RuntimeError: CUDA out of memory
```
- Reduce video resolution (e.g., 256x256)
- Close other GPU-intensive applications
- Use TensorRT models for better performance

**4. Audio-video sync issues**
- Adjust `audio_chunk_ms` parameter
- Check network latency
- Verify GPU performance

## Performance Optimization

### Recommended Settings

**For Low Latency (<1s)**:
```python
avatar_session = DittoAvatarSession(
    video_width=256,
    video_height=256,
    video_fps=20,
    audio_chunk_ms=150,
)
```

**For High Quality**:
```python
avatar_session = DittoAvatarSession(
    video_width=512,
    video_height=512,
    video_fps=25,
    audio_chunk_ms=200,
)
```

## Limitations

- Requires NVIDIA GPU with CUDA support
- Ditto SDK must be installed separately
- Python 3.10 only (Ditto requirement)
- Frame generation latency ~100-200ms

## Roadmap

- [ ] Implement frame retrieval from Ditto SDK
- [ ] Add emotion control support
- [ ] Optimize audio-video synchronization
- [ ] Add metrics and monitoring
- [ ] Support for multiple concurrent avatars
- [ ] TensorRT optimization integration

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

Apache-2.0 License - see LICENSE file for details

## Credits

- **Ditto TalkingHead**: [Ant Group](https://github.com/antgroup/ditto-talkinghead)
- **LiveKit**: [LiveKit Inc.](https://livekit.io)

## Support

- [LiveKit Documentation](https://docs.livekit.io)
- [Ditto Documentation](https://digital-avatar.github.io/ai/Ditto/)
- [GitHub Issues](https://github.com/yourusername/livekit-plugins-ditto/issues)

## Related Projects

- [livekit-plugins-hedra](https://github.com/livekit/agents/tree/main/livekit-plugins/livekit-plugins-hedra)
- [livekit-plugins-simli](https://github.com/livekit/agents/tree/main/livekit-plugins/livekit-plugins-simli)
- [Ditto TalkingHead](https://github.com/antgroup/ditto-talkinghead)
