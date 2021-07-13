FROM ubuntu:18.04

# This Docker image, tagged and uploaded as `springulum/minerl-circleci-base`,
# bundles all of the Ubuntu packages needed to run and test minerl locally.
# It does not include the minerl repository because this is meant to be downloaded
# fresh by CircleCI, or whatever service is using the image.

# TODO(shwang): Since we don't need any local files here, why not just
# skip the Docker image part, and use a CircleCI Ubuntu executor?
# See https://circleci.com/blog/how-to-build-a-docker-image-on-circleci-2-0/
#
# One nice thing about not needing local files is that this Docker image will not need to
# be updated often.
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

RUN pip3 install --upgrade pip setuptools
