FROM python:3.12-slim

# --- base OS deps (minimal) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential git \
 && rm -rf /var/lib/apt/lists/*

# --- install uv system-wide ---
# uv: copy binary into /usr/local/bin (avoid /root symlink)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
 && install -m 0755 /root/.local/bin/uv /usr/local/bin/uv

# --- install azcopy (optional, for uploads) ---
RUN mkdir -p /tmp/azc && cd /tmp/azc \
 && curl -sL https://aka.ms/downloadazcopy-v10-linux | tar -xz \
 && cp azcopy_linux_amd64_*/azcopy /usr/local/bin/ \
 && chmod +x /usr/local/bin/azcopy \
 && rm -rf /tmp/azc

# --- non-root user and writable dirs ---
RUN useradd -m -u 1000 appuser \
 && install -d -o appuser -g appuser /app \
 && install -d -o appuser -g appuser /opt/venv

# --- activate global venv path for all processes ---
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:/usr/local/bin:/usr/bin:/bin"

# --- create the venv and sync deps into /opt/venv ---
USER appuser
WORKDIR /app
# copy only lockfiles for cached dependency layer
COPY --chown=appuser:appuser pyproject.toml uv.lock ./
# ensure the interpreter exists inside /opt/venv, then resolve deps there
RUN python -m venv /opt/venv \
 && uv venv --python /opt/venv/bin/python --seed \
 && uv sync --frozen --no-install-project

# --- runtime env ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# entrypoint script lives in the repo (bind-mounted)
CMD ["bash", "-lc", "./start_zhl.sh"]
