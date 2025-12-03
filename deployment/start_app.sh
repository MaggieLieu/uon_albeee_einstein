#!/bin/bash
set -e

source /usr/src/app/set_ffmpeg_path.sh
source /usr/src/app/set_api_key.sh
source /usr/src/app/generate_ssl.sh

exec supervisord -c /etc/supervisor.conf