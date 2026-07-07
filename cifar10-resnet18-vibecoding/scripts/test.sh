#!/usr/bin/env bash
set -euo pipefail
python src/test.py --config configs/default.yaml --checkpoint checkpoints/best_model.pth "$@"

