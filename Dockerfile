FROM python:3.8-slim

# install google chrome
RUN apt update && apt install -y gnupg2 wget curl git
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt update && apt install -y google-chrome-stable unzip

# install chromedriver
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99

RUN apt clean autoclean && apt autoremove --yes

# install selenium
RUN pip install selenium

# install project requirements
COPY requirements.txt requirements.txt
RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "run.py"]