#!/usr/bin/env bash
# Read only the disposable CI host; preserve resource evidence before emulator failure.
set -euo pipefail
label="${1:?Missing capture label}"
folder="${2:?Missing evidence folder}"
mkdir -p "$folder"
{
  date --utc --iso-8601=seconds
  free --mebi
  df -h . /dev/shm
  ps -eo pid,ppid,rss,comm --sort=-rss
} | tee "$folder/host-$label.txt"
