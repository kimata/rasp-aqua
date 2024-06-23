FROM python:3.10.13-bookworm as build

RUN apt-get update && apt-get install --assume-yes \
    gcc \
    curl \
    python3 \
    python3-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/rasp-aqua

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# NOTE: キャッシュを効かせたいので，まずは pyproject.toml のみコピーする
COPY pyproject.toml .

RUN poetry config virtualenvs.create false \
 && poetry install --without local_lib --without aquarium \
 && rm -rf ~/.cache

COPY . .
RUN poetry install

FROM python:3.10.13-bookworm as prod

ENV TZ=Asia/Tokyo

COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

WORKDIR /opt/rasp-aqua

COPY . .

CMD ["./app/rasp-aqua.py"]
