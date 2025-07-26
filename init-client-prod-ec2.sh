#!/bin/bash

# Run this on the instance once: sudo setcap 'cap_net_bind_service=+ep' $(which node)
export PATH=/home/ec2-user/.nvm/versions/node/v22.17.1/bin:/usr/bin:/usr/local/bin:/bin

# Clone whisper-local and download model only if the folder does not exist
if [ ! -d "whisper-local" ]; then
  echo "Cloning whisper.cpp into whisper-local..."
  /usr/bin/git clone https://github.com/ggml-org/whisper.cpp.git whisper-local
  cd whisper-local/models && ./download-ggml-model.sh base.en
  cd ../..
else
  echo "whisper-local already exists, skipping clone."
fi

# Build whisper in background
(cd transcribe-edge && ./build-whisper-local.sh) &

# Build and run client app on port 80
(cd client-app && npm install && npm run build && npx vite preview --host 0.0.0.0 --port 80)