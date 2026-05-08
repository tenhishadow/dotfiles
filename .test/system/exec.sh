#!/bin/bash
set -euxo pipefail

export UV_PROJECT_ENVIRONMENT="/tmp/${RANDOM}"
export ANSIBLE_FORCE_COLOR="true"

pacman --disable-sandbox -Sy --noconfirm --needed --noprogressbar reflector go-task uv git sudo >/dev/null

sudo reflector \
  --ipv4 \
  --protocol https \
  --completion-percent 95 \
  --score 10 \
  --latest 30 \
  --fastest 10 \
  --threads 8 \
  --connection-timeout 1 \
  --download-timeout 2 \
  --save /etc/pacman.d/mirrorlist

go-task system -- --skip-tags pkg

# idempotency
go-task system -- --skip-tags pkg
