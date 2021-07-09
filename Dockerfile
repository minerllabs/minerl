FROM ubuntu:18.04 as base

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -q  # Fuse these two statements together when not in Dockerfile development
RUN apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    git \
    libffi-dev \
    libgl1-mesa-dev \
    libgl1-mesa-glx \
    libglew-dev \
    libosmesa6-dev \
    libssl-dev \
    net-tools \
    openssh-client \
    openjdk-8-jre-headless=8u162-b12-1 \
    openjdk-8-jdk-headless=8u162-b12-1 \
    openjdk-8-jre=8u162-b12-1 \
    openjdk-8-jdk=8u162-b12-1 \
    parallel \
    python3-dev \
    python3-pip \
    python3.7-dev \
    rsync \
    software-properties-common \
    unzip \
    vim \
    virtualenv \
    x11-xserver-utils \
    xpra \
    xvfb \
    xserver-xorg-dev \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip setuptools pytest

COPY . minerl

WORKDIR /minerl

FROM base as dev
RUN pip3 install -e .
