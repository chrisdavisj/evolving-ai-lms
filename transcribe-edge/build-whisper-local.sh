#!/bin/bash
cd ../whisper-local && make && cd ../transcribe-edge && npm install && node server.js