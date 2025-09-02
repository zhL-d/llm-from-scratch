# Dockerfile (dev-friendly, bind-mount code at runtime)
FROM python:3.12-slim

# ---- Base OS deps (minimal) ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential git \
 && rm -rf /var/lib/apt/lists/*

# ---- uv (reproducible Python) ----
# uv: copy binary into /usr/local/bin (avoid /root symlink)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
 && install -m 0755 /root/.local/bin/uv /usr/local/bin/uv

# ---- azcopy (pin-less; keep as-is or pin a version you trust) ----
RUN mkdir -p /tmp/azc && cd /tmp/azc \
 && curl -sL https://aka.ms/downloadazcopy-v10-linux | tar -xz \
 && cp azcopy_linux_amd64_*/azcopy /usr/local/bin/ \
 && chmod +x /usr/local/bin/azcopy \
 && rm -rf /tmp/azc

# ---- App user & workdir BEFORE syncing deps so venv files are owned correctly ----
# --- create non-root user and give them /app ---
RUN useradd -m -u 1000 appuser \
 && install -d -o appuser -g appuser /app   # ensure /app is writable by appuser

WORKDIR /app
# Copy only lockfiles for layer caching; make them owned by appuser
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

USER appuser

# Sync Python deps into /app/.venv (owned by appuser), cached as a layer
RUN uv sync --frozen

# ---- Runtime env ----
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Code is bind-mounted in dev; entrypoint script lives in repo
CMD ["bash", "-lc", "./start_zhl.sh"]

