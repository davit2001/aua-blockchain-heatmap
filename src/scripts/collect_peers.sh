#!/bin/bash
# macOS-compatible Bitcoin node peer collector

TARGET=${1:-10000000}
BANTIME=${2:-14400}
SLEEP=${3:-60}
OUT="peers_collected.txt"
TMP="peers_tmp.txt"

touch "$OUT"
echo "Target: $TARGET peers. Starting with $(wc -l < "$OUT" 2>/dev/null || echo 0) saved."

while [ "$(wc -l < "$OUT" 2>/dev/null || echo 0)" -lt "$TARGET" ]; do
  echo "=== Round: have $(wc -l < "$OUT" 2>/dev/null || echo 0) / $TARGET peers ==="

  # get peers, extract IPs, skip .onion
  bitcoin-cli getpeerinfo \
    | jq -r '.[] | .addr' \
    | sed -E 's/\[?(.*)\]?:[0-9]+$/\1/' \
    | grep -v '\.onion$' > "$TMP"

  # append new IPs only
  while IFS= read -r ip || [ -n "$ip" ]; do
    [ -z "$ip" ] && continue
    case "$ip" in
      10.*|127.*|192.168.*|172.1[6-9].*|172.2[0-9].*|172.3[0-1].*) continue ;;
    esac
    if ! grep -Fxq "$ip" "$OUT"; then
      echo "NEW: $ip"
      echo "$ip" >> "$OUT"
    fi
  done < "$TMP"

  # Ban and disconnect to rotate peers
  bitcoin-cli getpeerinfo \
    | jq -r '.[] | .addr' \
    | sed -E 's/\[?(.*)\]?:[0-9]+$/\1/' \
    | grep -v '\.onion$' \
    | while IFS= read -r ip || [ -n "$ip" ]; do
        [ -z "$ip" ] && continue
        case "$ip" in
          10.*|127.*|192.168.*|172.1[6-9].*|172.2[0-9].*|172.3[0-1].*) continue ;;
        esac
        echo "Banning/disconnecting $ip"
        bitcoin-cli setban "$ip" add "$BANTIME" 2>/dev/null || true
        bitcoin-cli disconnectnode "$ip" 2>/dev/null || true
    done

  echo "Sleeping $SLEEP seconds..."
  sleep "$SLEEP"
done

echo "Done. Collected $(wc -l < "$OUT") peers -> $OUT"
