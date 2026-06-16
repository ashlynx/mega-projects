#!/usr/bin/env bash
# 全国メガプロジェクト・マップ 自動更新 (cron 例: 0 6 * * *  /root/mega-projects/refresh.sh)
set -euo pipefail
cd "$(dirname "$0")"

python3 scripts/build.py

# 変更があればコミットして push (tender-maps と同じ運用)
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  git commit -m "auto: refresh mega-projects $(date +%F_%H%M)" || true
  git push --force
  echo "[refresh] pushed."
else
  echo "[refresh] no changes."
fi
