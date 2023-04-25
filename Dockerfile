FROM ubuntu:bionic

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update

RUN apt install -y python3-pip libgl1

RUN python3 -m pip install --upgrade pip

COPY requirements.txt requirements.txt

RUN pip3 install --extra-index-url https://google-coral.github.io/py-repo/ -r requirements.txt

RUN mkdir -p /workspace

WORKDIR /workspace
