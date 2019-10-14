FROM ubuntu:16.04 as glvnd

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        make \
        automake \
        autoconf \
        libtool \
        pkg-config \
        python \
        libxext-dev \
        libx11-dev \
        x11proto-gl-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/libglvnd
RUN git clone --branch=v1.0.0 https://github.com/NVIDIA/libglvnd.git . && \
    ./autogen.sh && \
    ./configure --prefix=/usr/local --libdir=/usr/local/lib/x86_64-linux-gnu && \
    make -j"$(nproc)" install-strip && \
    find /usr/local/lib/x86_64-linux-gnu -type f -name 'lib*.la' -delete

RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get install -y --no-install-recommends \
        gcc-multilib \
        libxext-dev:i386 \
        libx11-dev:i386 && \
    rm -rf /var/lib/apt/lists/*

# 32-bit libraries
RUN make distclean && \
    ./autogen.sh && \
    ./configure --prefix=/usr/local --libdir=/usr/local/lib/i386-linux-gnu --host=i386-linux-gnu "CFLAGS=-m32" "CXXFLAGS=-m32" "LDFLAGS=-m32" && \
    make -j"$(nproc)" install-strip && \
    find /usr/local/lib/i386-linux-gnu -type f -name 'lib*.la' -delete

###################################################
##################################################

FROM jenkins/jenkins:lts
##################### NVIDIA DOCKER STUFF


USER root
COPY --from=glvnd /usr/local/lib/x86_64-linux-gnu /usr/local/lib/x86_64-linux-gnu
COPY --from=glvnd /usr/local/lib/i386-linux-gnu /usr/local/lib/i386-linux-gnu

COPY docker/10_nvidia.json /usr/local/share/glvnd/egl_vendor.d/10_nvidia.json

RUN echo '/usr/local/lib/x86_64-linux-gnu' >> /etc/ld.so.conf.d/glvnd.conf && \
    echo '/usr/local/lib/i386-linux-gnu' >> /etc/ld.so.conf.d/glvnd.conf && \
    ldconfig

ENV LD_LIBRARY_PATH /usr/local/lib/x86_64-linux-gnu:/usr/local/lib/i386-linux-gnu${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}


# SET UP X SERVER
# Get virtual GL
WORKDIR /tmp
RUN curl -L -o virtualgl_2.5.2_amd64.deb 'https://downloads.sourceforge.net/project/virtualgl/2.5.2/virtualgl_2.5.2_amd64.deb?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fvirtualgl%2Ffiles%2F2.5.2&ts=1509495317&use_mirror=auto'
RUN dpkg -i virtualgl_2.5.2_amd64.deb
RUN printf "1\nn\nn\nn\nx\n" | /opt/VirtualGL/bin/vglserver_config



# TEST THE HEADLESS MODE
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        g++ \
        libglew-dev \
        mesa-utils \
        freeglut3-dev  \
        x11-xserver-utils && \
    rm -rf /var/lib/apt/lists/*


ENV PATH /usr/local/nvidia/bin:${PATH}
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64:${LD_LIBRARY_PATH}

ENV NVIDIA_VISIBLE_DEVICES \
    ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES \
    ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics

######################################### JENKINS SET UP




# TEST THE HEADLESS MODE

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        g++ \
        libglew-dev \
        freeglut3-dev \
        git \
        cmake \
        ffmpeg \
        lua5.1 \
        libxerces-c3.1 \
        liblua5.1-0-dev \
        libav-tools \
        xvfb\
        libboost-all-dev \
        build-essential \
        swig \
        tar \
        doxygen \
        xsltproc \
        python3-dev  \
        python3-tk \
        python3-pil \
        python3-pil.imagetk \
        libpython3.5-dev \
        python3-pip \
        libpython3.5   && \
    rm -rf /var/lib/apt/lists/*


RUN  python3 -m pip install --upgrade pip setuptools && \
    python3 -m pip install --upgrade \
    gym \
    opencv-python \
    tqdm \
    numpy \
    requests \
    ipython \
    typing \
    lxml \
    psutil \
    Pyro4    \
    getch \
    coloredlogs \
    matplotlib

RUN python3 -m pip install --upgrade \
    pytest-xdist 

USER jenkins

################################3 MINERL THINGS.
# ENV MINERL_DATA_ROOT /minerl
WORKDIR /var/jenkins_home
