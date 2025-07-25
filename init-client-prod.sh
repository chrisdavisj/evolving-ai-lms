#!/bin/bash

# Clone whisper-local and download model only if the folder does not exist
if [ ! -d "whisper-local" ]; then
  echo "Cloning whisper.cpp into whisper-local..."
  git clone https://github.com/ggml-org/whisper.cpp.git whisper-local
  cd whisper-local/models && ./download-ggml-model.sh base.en
  cd ../..
else
  echo "whisper-local already exists, skipping clone."
fi

# Build whisper in background
(cd transcribe-edge && ./build-whisper-local.sh) &

# Build and run client app on port 80
(cd client-app && npm install && npm run build && sudo env "PATH=$PATH" npx vite preview --port 80)
