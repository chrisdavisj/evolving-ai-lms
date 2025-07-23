#!/bin/bash
cd ../whisper-local && make && cd ../transcribe-edge && node server.js