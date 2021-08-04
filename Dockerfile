FROM ubuntu:18.04 as circleci-base

# The `circleci-base` stage Docker image, tagged and uploaded as `springulum/minerl-circleci-base`,
# bundles all of the Ubuntu packages needed to run and test minerl locally.
# It does not include the minerl repository because this is meant to be downloaded
# fresh by CircleCI, or whatever service is using the image.

# TODO(shwang): Since we don't need any local files here, (in fact, the .dockerignore
# ignores all files!) why not just skip the Docker image part, and use a CircleCI Ubuntu executor?
# See https://circleci.com/blog/how-to-build-a-docker-image-on-circleci-2-0/
#
# One nice thing about not needing local files is that this Docker image will not need to
# be updated often.

# Prevent hanging build from interactive `apt-get install` (due to tzinfo).
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -q && apt-get install -y --no-install-recommends \
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


FROM circleci-base as dev

# The `dev` stage is like the previous stage, but it also downloads and installs the latest
# version of minerl in the default Python 3 environment.
#
# Some version of this image, with whatever
# version of minerl existed at the time, is hosted at springulum/minerl-dev (not maintained).
# For the latest version of minerl, build your own image locally.
#
# Note that you may have to prepend your minerl runs with `xvfb-run` because the Docker container
# does not have access to a display.

RUN git clone https://github.com/minerllabs/minerl
WORKDIR /minerl
RUN pip3 install -e .


FROM dev as data-processing

# The `data-processing` image adds to the previous stage additional packages used for MineRL
# data processing, and sets the default Docker command to the pipeline script,
# `minerl.data.pipeline.pipeline`.
#
# Some version of this image, with whatever
# version of minerl existed at the time, is hosted at springulum/minerl-data-processing (not maintained).
# For the latest version of minerl, build your own image locally.
#
# Example usage:
#
# - Run the interactive version of the script, single-threaded. Note that to download, you must
#   attach your AWS credentials.
# docker run -it --rm springulum/minerl-data-processing \
#    -v local_minerl_data_dir:/root/minerl.data
#    -v ~/.aws/credentials:/root/.aws/credentials
#
# - Run in noninteractive mode with 8 threads:
# docker run --rm springulum/minerl-data-processing -v local_minerl_data_dir:/root/minerl.data \
#      python -m minerl.data.pipeline.pipeline -j 8
#
# - Show script help:
# docker run -it --rm springulum/minerl-data-processing python3 -m minerl.data.pipeline.pipeline --help

# Prevent interactive `apt-get install` again, as described above.
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -q && apt-get install -y --no-install-recommends \
    awscli \
    p7zip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Required for our download script
RUN pip3 install boto3

# This is the directory used for holding new datasets and raw demonstration packets downloaded
# from S3. To save your results and prevent the container size from ballooning, mount a host
# directory to this container path via Docker's `-v YOUR_DATA_DIR:/root/minerl.data` flag.
VOLUME /root/minerl.data

# You will need to mount AWS credentials for s3://pizza-party to download raw demonstration
# files. This step can be skipped if you don't need to download any files (for example,
# if the raw demonstration files are already saved in `~/minerl.data` locally).
VOLUME /root/.aws/credentials

# Set python encoding to utf8 explicitly because the download menu otherwise fails.
ENV PYTHONIOENCODING=utf8

CMD python3 -m minerl.data.pipeline.pipeline -i
