#!/bin/bash

# Define the target directory for the .env file
TARGET_DIR="/usr/src/app/uon_agent_albeee"
ENV_FILE="$TARGET_DIR/.env"

# Check if the Google API Key is passed as an environment variable
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "ERROR: GOOGLE_API_KEY environment variable is not set."
    exit 1
fi

# 1. Create the .env file in the specific directory
echo "Creating .env file at $ENV_FILE with GOOGLE_API_KEY..."

# Write the API key to the specific file path
echo "GOOGLE_GENAI_USE_VERTEXAI=0" > "$ENV_FILE"
echo "GOOGLE_API_KEY=\"$GOOGLE_API_KEY\"" >> "$ENV_FILE"
echo ".env file created at $ENV_FILE."