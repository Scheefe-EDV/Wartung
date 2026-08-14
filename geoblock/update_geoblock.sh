#!/bin/sh
# Aktualisiert IP-Ranges (geo_block.php) UND GeoIP-Datenbank (dbip-country-lite.mmdb)
# Kompatibel mit macOS sh (kein bash 4 noetig)

COUNTRIES="ru cn in kp ir"
DIR="$(cd "$(dirname "$0")" && pwd)"
YEAR=$(date '+%Y')
MONTH=$(date '+%m')

# ── 1. GeoIP-Datenbank (MMDB) aktualisieren ──────────────────────────────────
echo "=== Aktualisiere GeoIP-Datenbank (db-ip.com) ==="
MMDB_URL="https://download.db-ip.com/free/dbip-country-lite-${YEAR}-${MONTH}.mmdb.gz"
printf "  Lade %s... " "$MMDB_URL"
curl -sL --max-time 120 "$MMDB_URL" -o "$DIR/dbip-country-lite.mmdb.gz"
if [ $? -eq 0 ] && [ -s "$DIR/dbip-country-lite.mmdb.gz" ]; then
  gunzip -f "$DIR/dbip-country-lite.mmdb.gz"
  SIZE=$(ls -lh "$DIR/dbip-country-lite.mmdb" | awk '{print $5}')
  echo "OK ($SIZE)"
else
  echo "FEHLER — alte MMDB bleibt erhalten"
fi

# ── 2. IP-Ranges (Fallback geo_block.php) aktualisieren ──────────────────────
echo ""
echo "=== Lade IP-Ranges von ipdeny.com ==="
for CC in $COUNTRIES; do
  CC_UPPER=$(echo "$CC" | tr '[:lower:]' '[:upper:]')
  printf "  %s... " "$CC_UPPER"
  curl -s --max-time 30 "https://www.ipdeny.com/ipblocks/data/countries/${CC}.zone" -o "$DIR/${CC}.zone"
  COUNT=$(wc -l < "$DIR/${CC}.zone" | tr -d ' ')
  echo "$COUNT Eintraege"
done

echo ""
echo "=== Generiere geo_block.php (IPv4-Fallback) ==="

python3 - "$DIR" << 'PYEOF'
import ipaddress, sys, datetime

d = sys.argv[1]
countries = ['ru', 'cn', 'in', 'kp', 'ir']
ranges = []

for cc in countries:
    with open(f'{d}/{cc}.zone') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                net = ipaddress.ip_network(line, strict=False)
                ranges.append((int(net.network_address), int(net.broadcast_address)))
            except ValueError:
                pass

ranges.sort()
merged = []
for start, end in ranges:
    if merged and start <= merged[-1][1] + 1:
        merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    else:
        merged.append([start, end])

lines = [f"<?php\n// Laendersperre: RU, CN, IN, KP, IR\n// Generiert {datetime.date.today().isoformat()} — ipdeny.com\n// Binary Search: ~14 Vergleiche (OPcache-optimiert)\n\n"]
lines.append("$ip_raw = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '';\n")
lines.append("if (strpos($ip_raw, ',') !== false) $ip_raw = trim(explode(',', $ip_raw)[0]);\n")
lines.append("$ip_long = ip2long($ip_raw);\nif ($ip_long === false || $ip_long < 0) return;\n\n")
lines.append("$ranges = [\n")
for s, e in merged:
    lines.append(f"[{s},{e}],\n")
lines.append("];\n\n")
lines.append('$lo=0;$hi=count($ranges)-1;\nwhile($lo<=$hi){$mid=($lo+$hi)>>1;\nif($ip_long<$ranges[$mid][0])$hi=$mid-1;\nelseif($ip_long>$ranges[$mid][1])$lo=$mid+1;\nelse{header("HTTP/1.1 403 Forbidden");echo"Access from your region is not permitted.";exit;}}\n')

with open(f'{d}/geo_block.php', 'w') as f:
    f.write(''.join(lines))

import os
print(f"  geo_block.php: {os.path.getsize(f'{d}/geo_block.php')//1024} KB, {len(merged)} Ranges")
print("  Fertig — jetzt geo_block.php per FTP hochladen.")
PYEOF
