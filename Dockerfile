FROM python:3.9-slim-buster

RUN apt-get update && apt-get -y install libpq-dev gcc build-essential \
    xz-utils curl
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY package-lock.json ./
COPY package.json ./

SHELL ["/bin/bash", "--login", "-c"]
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash
RUN nvm install 12

COPY . .

RUN npm ci && npm run build


CMD [ "python", "-m", "server" ]