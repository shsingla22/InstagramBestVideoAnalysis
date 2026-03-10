#!/usr/bin/env bash
# Install and enable both systemd services.
# Run as root: sudo ./scripts/install_systemd.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Copying service files to /etc/systemd/system/ ..."
cp "$SCRIPT_DIR/systemd/vllm-qwen3vl.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/reel-analyzer.service" /etc/systemd/system/

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling services..."
systemctl enable vllm-qwen3vl.service
systemctl enable reel-analyzer.service

echo ""
echo "Services installed. Commands:"
echo "  sudo systemctl start vllm-qwen3vl    # Start vLLM"
echo "  sudo systemctl start reel-analyzer    # Start dashboard"
echo "  sudo systemctl status vllm-qwen3vl   # Check vLLM status"
echo "  sudo journalctl -fu vllm-qwen3vl     # vLLM logs"
echo "  sudo journalctl -fu reel-analyzer     # Dashboard logs"
