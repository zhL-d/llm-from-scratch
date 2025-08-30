#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y curl build-essential tmux

# uv
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

# azcopy to ~/tools/bin
mkdir -p "$HOME/tools/bin" && cd "$HOME/tools"
if ! command -v azcopy >/dev/null 2>&1; then
  curl -sL https://aka.ms/downloadazcopy-v10-linux | tar -xz
  cp azcopy_linux_amd64_*/azcopy "$HOME/tools/bin/"
  chmod +x "$HOME/tools/bin/azcopy"
  echo 'export PATH="$HOME/tools/bin:$PATH"' >> ~/.bashrc
fi

# prepare folders
mkdir -p "$HOME/stf-assignment1-basics/data" "$HOME/stf-assignment1-basics/cs336_basics/outputs"
echo "Bootstrap complete. Run: source ~/.bashrc"

