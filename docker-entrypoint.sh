#!/bin/sh
set -e

# Display VRM client banner
echo "====================================="
echo "  VRM Client Service"
echo "====================================="
echo "Alpine $(cat /etc/alpine-release) | Python $(python -V | cut -d' ' -f2)"
echo "====================================="

# Check if we should drop into shell
if [ "$1" = "shell" ] || [ "$1" = "bash" ] || [ "$1" = "ash" ]; then
    echo "Starting shell..."
    exec /bin/ash
elif [ "$1" = "runner" ] || [ "$1" = "server" ]; then
    echo "Starting VRM Client runner..."
    exec python -m vrm_client.runner
elif [ "$1" = "console" ]; then
    echo "Starting console..."
    exec python ./console.py
elif [ "$1" = "pytest" ]; then
    echo "Starting pytest..."
    exec pytest
else
    echo "Available commands:"
    echo "  (default)   - Start the VRM Client service"
    echo "  shell/ash    - Start a shell session"
    echo "  runner/server  - Run the VRM Client directly (same as default)"
    echo "  pytest      - Run tests using pytest"
    echo "  console     - Open python console with pre-loaded VRM Client"
    echo "  help        - Show this help message"
    exit 0
fi