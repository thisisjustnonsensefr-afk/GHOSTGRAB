FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY --from=denoland/deno:bin /deno /usr/local/bin/deno
WORKDIR /app
RUN pip install --no-cache-dir -U "yt-dlp[default]"
COPY ghostgrab.py .
ENV HOST=0.0.0.0
CMD ["python", "ghostgrab.py"]
