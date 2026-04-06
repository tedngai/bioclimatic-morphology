#!/usr/bin/env bash
# Gemini Deep Research — start a research task and poll until complete.
# Usage: deep_research.sh "<query>" [poll_interval_seconds]
#
# Requires: GEMINI_API_KEY env var, curl, jq
# Output: final report markdown on stdout; progress on stderr

set -euo pipefail

QUERY="${1:?Usage: deep_research.sh \"<query>\" [poll_interval]}"
POLL_INTERVAL="${2:-10}"
BASE="https://generativelanguage.googleapis.com/v1beta"
AGENT="deep-research-pro-preview-12-2025"

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "Error: GEMINI_API_KEY is not set" >&2
  exit 1
fi

command -v jq >/dev/null 2>&1 || { echo "Error: jq is required" >&2; exit 1; }

# --- Start the research task ---
START_RESPONSE=$(curl -sS -X POST "${BASE}/interactions" \
  -H "Content-Type: application/json" \
  -H "x-goog-api-key: ${GEMINI_API_KEY}" \
  -d "$(jq -n --arg q "$QUERY" --arg a "$AGENT" '{
    input: $q,
    agent: $a,
    background: true
  }')")

INTERACTION_ID=$(echo "$START_RESPONSE" | jq -r '.id // empty')

if [[ -z "$INTERACTION_ID" ]]; then
  echo "Error: Failed to start research task" >&2
  echo "$START_RESPONSE" >&2
  exit 1
fi

echo "Research started: ${INTERACTION_ID}" >&2

# --- Poll until done ---
while true; do
  sleep "$POLL_INTERVAL"

  POLL_RESPONSE=$(curl -sS -X GET "${BASE}/interactions/${INTERACTION_ID}" \
    -H "x-goog-api-key: ${GEMINI_API_KEY}")

  STATUS=$(echo "$POLL_RESPONSE" | jq -r '.status // "unknown"')

  case "$STATUS" in
    completed)
      echo "$POLL_RESPONSE" | jq -r '.outputs[-1].text // "No output text found"'
      echo "" >&2
      echo "Research completed." >&2
      exit 0
      ;;
    failed)
      ERROR=$(echo "$POLL_RESPONSE" | jq -r '.error // "Unknown error"')
      echo "Research failed: ${ERROR}" >&2
      exit 1
      ;;
    *)
      echo "Status: ${STATUS} — polling again in ${POLL_INTERVAL}s..." >&2
      ;;
  esac
done
