FROM python:3.10-slim-bullseye

# install ffmpeg
RUN apt-get -y update
RUN apt-get install -y --no-install-recommends procps ffmpeg gunicorn
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
RUN pip install -r /requirements.txt

EXPOSE 8050

COPY main.py /
COPY hello-world.py /
COPY dashboard.py /

CMD [ "gunicorn", "-w", "2", "-b", "0.0.0.0:8050", "dashboard:server" ]

