# 🦊🔗 FurChain

🌟 Create Lifelike Digital Personas 🌟

Empower your digital experiences with lifelike characters, complete with their own voices and personalities.
FurChain is your toolkit for creating and interacting with digital personas that feel real.

## 🚀 Features

- 🎤 **Voice Cloning**: Instantly clone any voice and generate speech with unparalleled realism.
- 🎭 **Effortless & Rapid Role-Play Creation**: Instantly bring to life endless role-play scenarios with minimal effort
  and maximum speed.
- 🛠️ **Offline and Open Source**: Full control and customization without the need for an internet connection.

## 🌐 Examples

- 🎶 **Music Voice Alteration**: Change the voice in a song on-the-fly while preserving the original background music.
  Check `examples/singer_change.py`.
- 🤖 **Self-Clone Chatbots**: Craft your own chatbot with a cloned voice and character in mere seconds.
  See `examples/clone_me.py` for a demonstration.
- 🎲 **Text-Based RPGs**: Kickstart a text RPG adventure swiftly. Experience it in `examples/adventure_with_fox.py`.

## 📋 Requirements

To ensure the best experience with FurChain, your system should meet the following requirements:

- CPU: X86_64 architecture
- GPU: Nvidia GPU (recommend >= 12GB VRAM)
- [Docker Compose](https://docs.docker.com/compose/install/): For managing multi-container Docker applications.
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html): For
  GPU support within Docker containers.

## 🏃‍♂️ How to Run

### Starting the API Service

Run the following command to launch the service:

```bash
docker compose up -d
```

This spins up 5 containers, each serving a unique purpose:

- `text-mongo`: Manages chat history with [MongoDB](https://www.mongodb.com/), optimized for CPU usage.
- `text-llama-cpp`: Hosts the [Llama-cpp](https://github.com/ggerganov/llama.cpp) server for large language models,
  utilizing GPU.
- `audio-gpt-sovits`: Runs the [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) server for voice synthesis,
  leveraging GPU.
- `audio-funasr`: Powers the [FunASR](https://github.com/alibaba-damo-academy/FunASR) online server for speech
  recognition, optimized for CPU usage.
- `audio-rvc`: Operates the [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) server for
  voice conversion, utilizing GPU.

### Initiating FurChain

You can use docker to have a quick glance at the capabilities of FurChain:

```bash
docker run --rm --gpus all --network host -v $PWD/data:/app/data -it markyfsun/furchain python3 examples/adventure_with_fox.py
```

The `data` directory serves as the central hub for your models, audio files, and chat logs:

- `gpt-sovits`: Holds reference audio for speech generation.
- `llama-cpp`: Contains LLM GGUF files available for download
  from [huggingface](https://huggingface.co/models?search=gguf).
- `rvc`: Stores models for voice conversion.

Should you wish to contribute or customize `furchain`, clone this repository and install it as an editable package:

```bash
git clone https://github.com/furchain/FurChain.git
cd FurChain
pip install -e .
```