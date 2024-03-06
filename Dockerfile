FROM nvidia/cuda:11.6.2-cudnn8-runtime-ubuntu20.04

WORKDIR /app

COPY . .

# Install dependenceis to add PPAs
RUN apt-get update
RUN apt-get install -y -qq ffmpeg
RUN apt-get install -y software-properties-common
RUN rm -rf /var/lib/apt/lists/*

# Add the deadsnakes PPA to get Python 3.10
RUN add-apt-repository ppa:deadsnakes/ppa

# Install Python 3.10 and pip
RUN apt-get update
RUN apt-get install -y build-essential python-dev python3-dev python3.10-distutils python3.10-dev python3.10 curl
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
RUN cat get_pip.py | python3.10

RUN apt-get install -y  libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
RUN python3 -m pip install pyaudio --no-cache-dir -i https://mirrors.cloud.tencent.com/pypi/simple
RUN python3 -m pip install . --no-cache-dir -i https://mirrors.cloud.tencent.com/pypi/simple

ENV FURCHAIN_TEXT_MONGO_URL=mongodb://localhost:27017
ENV FURCHAIN_TEXT_MONGO_DB=FurChain
ENV FURCHAIN_TEXT_MONGO_CHARACTER_COLLECTION=CharacterPreset
ENV FURCHAIN_TEXT_MONGO_SCENARIO_COLLECTION=ScenarioPreset
ENV FURCHAIN_TEXT_LLAMA_CPP_API_BASE=http://localhost:8000
ENV FURCHAIN_TEXT_NPC_NAME=Assistant
ENV FURCHAIN_TEXT_NPC_PERSONA="A helpful assistant."
ENV FURCHAIN_TEXT_PLAYER_NAME=User
ENV FURCHAIN_TEXT_PLAYER_PERSONA="A human."
ENV FURCHAIN_TEXT_SCENARIO_DESCRIPTION="In a chat room."
ENV FURCHAIN_AUDIO_RVC_API=http://localhost:8001
ENV FURCHAIN_AUDIO_FUNASR_API=ws://localhost:10095
ENV FURCHAIN_AUDIO_GPT_SOVITS_API_BASE=http://localhost:9880