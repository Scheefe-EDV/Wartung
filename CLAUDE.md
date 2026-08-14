# Wartung – Scheefe EDV

Dieses Repository enthält Wartungs- und Sicherheitsskripte für verwaltete Server von Scheefe EDV.

Betroffenes System: phpBB-Forum **www.funkbasis.de** auf einem Managed Server
(kein Root, keine Firewall, kein `mod_geoip`, Zugang nur per FTP/SFTP).

## Projektstruktur

```
geoblock/                      Ländersperre für phpBB-Forum (siehe unten)
bot_analyse.py                 Bot-Erkennung aus Apache-Access-Logs
robots.txt                     Crawler-Regeln fürs Forum (fertig zum Upload)
phpbb_htaccess_zusaetze.txt    .htaccess-Regeln gegen Scraper/AI-Crawler
index.htm                      Wartungsseite (Platzhalter)
README.md
CLAUDE.md                      Diese Datei
```

Da alles per FTP auf einen Managed Server geht, gibt es keinen Build- und keinen
Deploy-Schritt: Datei bearbeiten → hochladen. Es gibt auch keine Testsuite —
Prüfung erfolgt über die unten beschriebenen Testskripte.

### Nicht im Repo (siehe `.gitignore`)

Regenerierbare bzw. sensible Dateien sind bewusst ausgeschlossen:

| Muster | Grund |
|---|---|
| `geoblock/*.zone` | Rohdaten von ipdeny.com — lädt `update_geoblock.sh` |
| `geoblock/*.mmdb` | 8 MB Binärdatei, monatlich neu — lädt `update_geoblock.sh` |
| `geoblock/geoblock_deny_apache2*.conf` | Altlast, durch `geo_block.php` ersetzt |
| `*.log`, `*access.log*` | Server-Logs enthalten IP-Adressen |
| `.claude/settings.local.json` | Maschinenspezifisch |

Nach frischem `git clone` also zuerst `geoblock/update_geoblock.sh` laufen lassen,
sonst fehlt die MMDB für Variante B.

---

## geoblock – Ländersperre für phpBB

### Hintergrund

Das phpBB-Forum erhält unerwünschte Zugriffe aus RU, CN, IN, KP, IR.
Cloudflare hat das Problem gelöst, aber das Routing Cloudflare → Telekom war zu langsam.
Kein Zugriff auf Firewall (managed Server), kein Apache-Modul `mod_geoip` verfügbar.
Server-Zugang: nur FTP/SFTP.

### Zwei Varianten

#### Variante A — Binary Search (`geo_block.php`) · aktiv im Einsatz

Schnellste Variante, kein File-I/O, IPv4 only.

- Quelle: ipdeny.com Zone-Dateien (RU, CN, IN, KP, IR)
- 16.948 gemergde IPv4-Ranges, sortiert
- Binary Search: ~14 Vergleiche pro Request
- OPcache hält das Array im Speicher — kein Datei-Lesen zur Laufzeit
- **Nachteil:** Kein IPv6, monatliche manuelle Updates nötig
- Dateigröße: ~410 KB

#### Variante B — MaxMind DB Reader (`geo_block_mmdb.php`) · bereit, noch nicht aktiv

Genauere Variante mit IPv6-Unterstützung.

- Quelle: db-ip.com Country Lite (MMDB-Format, kostenlos, kein Account)
- MaxMind DB Reader PHP-Bibliothek (ohne Composer, nur 5 PHP-Dateien)
- Deckt IPv4 + IPv6 ab
- **Nachteil:** Etwas langsamer als Variante A (fopen + fseek je Request), 8 MB DB-Datei
- Geeignet wenn IPv6-Abdeckung wichtiger als maximale Performance

### Einbinden (phpBB)

**Option 1** — .htaccess (bevorzugt, falls erlaubt):
```apache
php_value auto_prepend_file /absoluter/pfad/zu/geoblock/geo_block.php
```

**Option 2** — config.php (Fallback, wenn php_value gesperrt):
```php
// In phpbb/config.php ganz oben:
require_once __DIR__ . '/geoblock/geo_block.php';
```
Achtung: geht bei phpBB-Updates verloren.

### Gesperrte Länder

`BLOCKED_COUNTRIES` in `geo_block_mmdb.php` bzw. direkt in `update_geoblock.sh`:

```
RU  Russland
CN  China
IN  Indien
KP  Nordkorea
IR  Iran
VN  Vietnam   (nur MMDB-Variante)
PK  Pakistan  (nur MMDB-Variante)
BD  Bangladesch (nur MMDB-Variante)
```

### Monatliches Update

```bash
cd geoblock/
./update_geoblock.sh
```

Aktualisiert:
- Zone-Dateien von ipdeny.com → regeneriert `geo_block.php`
- MMDB von db-ip.com → ersetzt `dbip-country-lite.mmdb`

Danach geänderte Dateien per FTP hochladen.

### Testen (nach Upload)

**Lokal (ohne Server):**
```bash
cd geoblock/ && php test_geo.php
```

**Auf dem Server (MMDB-Variante):**
```
https://forum.example.com/geoblock/test_mmdb.php?token=TOKEN&ip=77.88.8.8
```
Token vorher in `test_mmdb.php` Zeile 10 setzen. Datei nach Test löschen!

**Schnelltest lokal (simuliert Serverseite):**
Zeile oben in `geo_block.php` einfügen, Forum aufrufen, prüfen ob 403:
```php
$_SERVER['REMOTE_ADDR'] = '1.0.1.5'; // China
```

### Dateien im geoblock/-Ordner

| Datei | Zweck | Im Repo? |
|---|---|---|
| `geo_block.php` | Aktive Ländersperre (Binary Search, IPv4) | ja |
| `geo_block_mmdb.php` | Erweiterte Ländersperre (MMDB, IPv4+IPv6) | ja |
| `MaxMind/` | PHP-Reader-Bibliothek (5 Dateien, ohne Composer) | ja |
| `.htaccess` | Schützt Ordner vor direktem Web-Zugriff | ja |
| `update_geoblock.sh` | Update-Script (macOS-kompatibel, kein bash4 nötig) | ja |
| `ANLEITUNG.md` | Schritt-für-Schritt-Einbindung für den Server | ja |
| `test_mmdb.php` | Server-seitiger Test (nach Test löschen!) | ja |
| `test_geo.php` | Lokaler Test (nicht hochladen) | ja |
| `dbip-country-lite.mmdb` | GeoIP-Datenbank (8 MB, monatlich aktualisieren) | nein |
| `ru.zone` … `ir.zone` | Rohdaten von ipdeny.com | nein |
| `geoblock_deny_apache2*.conf` | Altlast: verworfener „Deny from"-Ansatz | nein |

---

## Bot- und Scraper-Schutz (funkbasis.de)

Zweite Baustelle neben der Ländersperre: AI-Crawler und ein verteiltes
Scraper-Botnetz erzeugen massenhaft phpBB-Sessions (Bots senden keine Cookies,
also legt phpBB pro Request eine neue Session an) und saugen Datei-Anhänge ab.

### `bot_analyse.py` — Log-Auswertung

Erkennt Bots per UA-Regex im Apache-Access-Log und zeigt vor allem, **welche
davon in der phpBB-Bot-Liste noch fehlen** (Spalte „in phpBB" / „✗ FEHLT").
Trägt man die dort ein (ACP → Board-Konfiguration → Board-Features → Bots
verwalten), legt phpBB für sie gar keine Session mehr an.

```bash
python3 bot_analyse.py /pfad/zu/access.log [weitere.log ...]
```

Log-Dateien sind per `.gitignore` ausgeschlossen — lokal analysieren, nicht committen.

### `robots.txt`

Fertige Datei für den Forum-Webroot. Sperrt GPTBot, Applebot,
meta-externalagent, PerplexityBot u.a. komplett; hält weitere Crawler von
session-intensiven Seiten (`ucp.php`, `memberlist.php`, `search.php`) und von
`download/file.php` fern. Greift nur bei Bots, die sich daran halten.

### `phpbb_htaccess_zusaetze.txt`

Das, was greift, wenn `robots.txt` ignoriert wird. Die Regeln gehören **oben**
in die phpBB-`.htaccess` im Webroot, vor `DirectoryIndex index.php`:

1. **Anhang-Schutz** — `download/file.php` nur mit Referer von einer echten
   Forenseite. Das Botnetz schickt immer die Homepage als Referer, echte User
   kommen von `viewtopic`/`viewforum`/…
2. **AI-Crawler** per User-Agent sperren (GPTBot, Applebot, ClaudeBot, …)
3. **Botnetz** über den exakten UA `Mozilla/5.0 (compatible; crawler)` sperren
   (exakter Match nötig — „crawler" als Substring trifft zu viele echte UAs)
4. **Alte Chrome-Versionen** sperren — auskommentiert, sperrt auch echte User

Jede Regel hat ein `RewriteCond %{REQUEST_URI} !^/_errordocs/`, damit die
Fehlerseiten nicht selbst geblockt werden und keine Redirect-Schleife entsteht.

Die Zahlen in den Kommentaren beider Dateien (Requests/Sessions pro Tag) stammen
aus einer `bot_analyse.py`-Auswertung vom April 2026 — bei erneuter Auswertung
mit aktualisieren.
