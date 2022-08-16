# docker build -t devcontainer:latest -f .\.devcontainer\Dockerfile .
FROM ubuntu:latest
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y apt-utils git

# Latex (from https://github.com/blang/latex-docker/blob/master/Dockerfile.ubuntu)
RUN apt-get update && apt-get install -qy git build-essential wget libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update -q && apt-get install -qy \
    texlive-full \
    python3-pygments gnuplot \
    && rm -rf /var/lib/apt/lists/*

# install basic stuff
RUN apt-get update && apt-get -y upgrade \
    && apt-get install -y \
    build-essential wget curl git cmake sl sudo net-tools iputils-ping nmap file 

# pico stuff
RUN apt-get install -y gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib iputils-ping

# install python stuff
RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository -y ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y python3.10 python3.10-distutils

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 \
    && update-alternatives --config python3

# install pip
RUN apt-get install -y python3-pip 

# to fix annoying pip xserver bug (https://github.com/pypa/pip/issues/8485)
RUN printf "%s\n" "alias pip3='DISPLAY= pip3'" "alias python=python3" > ~/.bash_aliases

# install packages
RUN pip3 install --upgrade pip
RUN pip3 install \
    numpy scipy matplotlib pyqt5 pandas\
    pylint autopep8 jupyter \
    sympy 

RUN pip3 install \
    pyserial \
    plotly dash\
    numba \
    torch torchvision\
    pip install opencv-python opencv-contrib-python \
    networkx \
    dash_bootstrap_components 

RUN git config --global user.email "emil.martens@gmail.com" && git config --global user.name "Emil Martens"
COPY .gitconfig /home

# for grammarly in vscode
# RUN curl -s https://deb.nodesource.com/setup_18.x | sudo bash
# RUN sudo apt-get install nodejs && npm install -g typescript pnpm sandboxed-module  

RUN apt install fonts-firacode
