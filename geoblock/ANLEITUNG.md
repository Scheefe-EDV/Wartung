# Ländersperre – Kurzanleitung

## Dateien hochladen

Per FTP/SFTP in einen Ordner **außerhalb** des öffentlichen Web-Roots hochladen,
z.B. `/phpbb/geoblock/`:

```
geo_block.php        ← die generierte Sperrdatei
```

## Schritt 1: Absoluten Pfad ermitteln

Temporär eine `pfad.php` im phpBB-Root anlegen:

```php
<?php echo __DIR__; ?>
```

Ausgabe z.B.: `/var/www/html/phpbb` → Pfad zur Sperrdatei wäre `/var/www/html/phpbb/geoblock/geo_block.php`

Danach `pfad.php` wieder löschen.

## Schritt 2: .htaccess anpassen

Ganz oben in der phpBB-`.htaccess` einfügen (erste Zeile!):

```apache
php_value auto_prepend_file /var/www/html/phpbb/geoblock/geo_block.php
```

(Pfad entsprechend anpassen.)

## Schritt 3: Testen

- Deutsche IP → Zugriff normal
- RU/CN/IN/KP/IR IP → `403 Access from your region is not permitted.`
- Test mit VPN oder: https://tools.keycdn.com/geo?host=DEINE-DOMAIN

## Falls 500 Internal Server Error nach .htaccess-Änderung

`php_value` ist auf dem Server deaktiviert (häufig bei PHP-FPM).

**Alternative A**: In der `phpbb/config.php` ganz oben einfügen:
```php
require_once __DIR__ . '/geoblock/geo_block.php';
```
Nachteil: geht bei phpBB-Updates verloren.

**Alternative B**: Hoster fragen ob `php_value auto_prepend_file` in .htaccess erlaubt ist,
oder ob es eine `.user.ini` Alternative gibt:
```ini
; .user.ini im phpBB-Root:
auto_prepend_file = /var/www/html/phpbb/geoblock/geo_block.php
```

## Warum PHP statt .htaccess-Regeln?

| Methode | Regeln | Vergleiche/Request |
|---|---|---|
| .htaccess mit Deny from | 31.000 Zeilen | 31.000 (jedes Mal neu gelesen) |
| PHP + Binary Search | 16.948 Ranges | ~14 (OPcache = einmal kompiliert) |

## Update (monatlich empfohlen)

```bash
cd geoblock/
./update_geoblock.sh   # lädt neue Zones, generiert neue geo_block.php
```
Danach `geo_block.php` per FTP ersetzen.
