#!/bin/bash

# Attempt to locate ffmpeg dynamically
FFMPEG_PATH=$(which ffmpeg)

if [ -z "$FFMPEG_PATH" ]; then
    echo "ERROR: ffmpeg not found in PATH."
    exit 1
fi

export FFMPEG_PATH
echo "FFMPEG_PATH set to: $FFMPEG_PATH"
