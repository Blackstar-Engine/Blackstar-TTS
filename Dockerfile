# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# ---------- Environment ----------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# ---------- System dependencies ----------
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    ffmpeg \
    ca-certificates \
    tini \
    git && \
    rm -rf /var/lib/apt/lists/*

# ---------- Non-root runtime ----------
RUN useradd -m -u 1000 tts1botuser
WORKDIR /app
RUN chown tts1botuser:tts1botuser /app
USER tts1botuser

# ---------- Dependency layer (for fast rebuilds) ----------
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ---------- Application layer ----------
COPY --chown=tts1botuser:tts1botuser . .

# ---------- Runtime ----------
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uv", "run", "python", "-m", "main"]
