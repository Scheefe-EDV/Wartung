Wartung
=======

Wartungs- und Sicherheitsskripte für verwaltete Server von Scheefe EDV.

Aktueller Schwerpunkt: Absicherung des phpBB-Forums **www.funkbasis.de** gegen
unerwünschte Zugriffe. Der Server ist ein Managed Server ohne Root- und
Firewall-Zugriff — alles läuft über PHP, `.htaccess` und FTP-Upload.

| Bereich | Inhalt |
|---|---|
| `geoblock/` | Ländersperre (RU, CN, IN, KP, IR …) als PHP-Prepend-Datei, in zwei Varianten: Binary Search über IPv4-Ranges und MaxMind/db-ip MMDB mit IPv6 |
| `bot_analyse.py` | Wertet Apache-Access-Logs aus und zeigt, welche Bots in der phpBB-Bot-Liste noch fehlen |
| `robots.txt` | Crawler-Regeln fürs Forum, fertig zum Upload |
| `phpbb_htaccess_zusaetze.txt` | `.htaccess`-Regeln gegen AI-Crawler, Scraper-Botnetz und Anhang-Absaugen |
| `index.htm` | Schlichte Wartungsseite |

Details, Hintergrund und Anleitungen: [CLAUDE.md](CLAUDE.md) sowie
[geoblock/ANLEITUNG.md](geoblock/ANLEITUNG.md).
