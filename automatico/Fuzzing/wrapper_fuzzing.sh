#!/bin/bash
timeout 3s socat - TCP:172.16.124.103:1234 < "$1"
echo "." >&2
