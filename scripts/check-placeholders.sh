#!/usr/bin/env bash
# Fails if any <DOCKERHUB_USERNAME> or <GITHUB_USERNAME> placeholders remain
# in files Argo CD or kubectl would deploy. Run this before every git push.
set -euo pipefail
cd "$(dirname "$0")/.."

if grep -rnE '<(DOCKERHUB|GITHUB)_USERNAME>' manifests argocd; then
  echo "ERROR: placeholders found above. Replace them before deploying." >&2
  exit 1
fi
echo "OK: no placeholders left in manifests/ or argocd/."
