#!/bin/bash
set -e

/usr/src/app/set_ffmpeg_path.sh
/usr/src/app/set_api_key.sh
/usr/src/app/generate_ssl.sh

exec supervisord -c /etc/supervisor.conf