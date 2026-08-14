#!/usr/bin/env python3
"""
Bot/Crawler-Erkennung aus Apache Access-Logs
Vergleicht gefundene Bots mit der phpBB-Bot-Liste.

Verwendung:
    python3 bot_analyse.py logfile1 [logfile2 ...]
    python3 bot_analyse.py /var/log/apache2/access.log-*
"""

import re
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# Bekannte Bots: (Regex gegen UA-String, Anzeigename)
# Reihenfolge wichtig — erster Treffer gewinnt.
# ---------------------------------------------------------------------------
KNOWN_BOTS = [
    # KI-Crawler
    (r"GPTBot",                     "GPTBot"),
    (r"OAI-SearchBot",              "OAI-SearchBot"),
    (r"anthropic-ai",               "anthropic-ai"),
    (r"ClaudeBot",                  "ClaudeBot"),
    (r"PerplexityBot",              "PerplexityBot"),
    (r"Applebot",                   "Applebot"),
    (r"Amazonbot",                  "Amazonbot"),
    (r"meta-externalagent",         "meta-externalagent"),
    (r"YouBot",                     "YouBot"),
    (r"cohere-ai",                  "cohere-ai"),
    (r"Diffbot",                    "Diffbot"),
    (r"ImagesiftBot",               "ImagesiftBot"),
    (r"FacebookBot",                "FacebookBot"),
    (r"Bytespider",                 "Bytespider"),
    (r"PetalBot",                   "PetalBot"),
    (r"SemrushBot",                 "Semrush [Bot]"),
    (r"AhrefsBot",                  "Ahrefs [Bot]"),
    (r"MJ12bot",                    "Majestic-12 [Bot]"),
    (r"DotBot",                     "DotBot"),

    # Suchmaschinen
    (r"Googlebot-Image",            "Googlebot-Image"),
    (r"Googlebot-News",             "Googlebot-News"),
    (r"Googlebot-Video",            "Googlebot-Video"),
    (r"Googlebot",                  "Googlebot"),
    (r"Google-InspectionTool",      "Google-InspectionTool"),
    (r"Google Favicon",             "Google Favicon"),
    (r"AdsBot-Google",              "AdsBot [Google]"),
    (r"Mediapartners-Google",       "Google Adsense [Bot]"),
    (r"FeedFetcher-Google",         "Google Feedfetcher"),
    (r"Google Desktop",             "Google Desktop"),
    (r"bingbot",                    "MSN [Bot]"),
    (r"BingPreview",                "MSN [Bot]"),
    (r"msnbot-media",               "MSNbot Media"),
    (r"msnbot",                     "MSN [Bot]"),
    (r"DuckDuckBot",                "DuckDuckGo [Bot]"),
    (r"Slurp",                      "Yahoo Slurp [Bot]"),
    (r"YahooSeeker",                "YahooSeeker [Bot]"),
    (r"Yahoo-MMCrawler",            "Yahoo MMCrawler [Bot]"),
    (r"Baiduspider",                "Baidu [Bot]"),
    (r"YandexBot",                  "Yandex [Bot]"),
    (r"YandexImages",               "Yandex Images"),
    (r"Sogou",                      "Sogou [Bot]"),
    (r"Exabot",                     "Exabot"),
    (r"ia_archiver",                "Alexa [Bot]"),
    (r"archive\.org_bot",           "Archive.org [Bot]"),
    (r"CCBot",                      "CommonCrawl [Bot]"),
    (r"DataForSeoBot",              "DataForSeo [Bot]"),

    # SEO-Tools
    (r"MegaIndex",                  "MegaIndex [Bot]"),
    (r"BLEXBot",                    "BLEXBot"),
    (r"SEOkicks",                   "SEOkicks [Crawler]"),
    (r"SEOSearch\s*Crawler",        "SEOSearch [Crawler]"),
    (r"SEO\s*Crawler",              "SEO Crawler"),
    (r"Screaming Frog",             "Screaming Frog"),
    (r"Sistrix",                    "Sistrix [Bot]"),
    (r"Rogerbot",                   "Moz Rogerbot"),

    # Link-Checker / Tools
    (r"W3C_Validator",              "W3C [Linkcheck]"),
    (r"W3C-checklink",              "W3C [Linkcheck]"),
    (r"linkcheck",                  "Online link [Validator]"),
    (r"Wget",                       "Wget"),
    (r"curl",                       "curl"),
    (r"Python-urllib",              "Python-urllib"),
    (r"python-requests",            "python-requests"),
    (r"Go-http-client",             "Go-http-client"),
    (r"Java/",                      "Java"),
    (r"libwww-perl",                "libwww-perl"),
    (r"zgrab",                      "zgrab [Scanner]"),
    (r"Nuclei",                     "Nuclei [Scanner]"),

    # KI-Assistenten (surfen im Auftrag von Nutzern, keine klassischen Crawler)
    (r"ChatGPT-User",               "ChatGPT-User"),
    (r"Claude-User",                "Claude-User"),
    (r"Perplexity-User",            "Perplexity-User"),

    # Sonstige Suchmaschinen / Crawler
    (r"Qwantbot",                   "Qwantbot"),
    (r"SeznamBot",                  "SeznamBot"),
    (r"Pinterestbot",               "Pinterestbot"),
    (r"LinkedInBot",                "LinkedInBot"),
    (r"Twitterbot",                 "Twitterbot"),
    (r"WhatsApp",                   "WhatsApp"),
    (r"Slackbot",                   "Slackbot"),
    (r"Discordbot",                 "Discordbot"),
    (r"TelegramBot",                "TelegramBot"),
    (r"meta-webindexer",            "meta-webindexer"),
    (r"SERanking",                  "SERanking [Bot]"),
    (r"FleebsBot",                  "FleebsBot"),
    (r"DNSCrawler",                 "DNSCrawler"),

    # Sonstige bekannte Bots
    (r"TurnitinBot",                "TurnitinBot [Bot]"),
    (r"Heritrix",                   "Heritrix [Crawler]"),
    (r"Nutch",                      "Nutch [Bot]"),
    (r"ichiro",                     "ichiro [Crawler]"),
    (r"psbot",                      "psbot [Picsearch]"),
    (r"Francis",                    "Francis [Bot]"),
    (r"Gigabot",                    "Gigabot [Bot]"),
    (r"Voyager",                    "Voyager [Bot]"),
    (r"Telekom\s*Bot",              "Telekom [Bot]"),
    (r"heise-IT-Markt-Crawler",     "Heise IT-Markt [Crawler]"),
    (r"ICCrawler",                  "ICCrawler - ICjobs"),
    (r"Metager2",                   "Metager [Bot]"),
    (r"Snappy",                     "Snappy [Bot]"),
    (r"Barkrowler",                 "Barkrowler"),
    (r"yacybot",                    "yacybot"),
    (r"BlackVeil",                  "BlackVeil"),
    (r"PlagAware",                  "PlagAwareBot"),
    (r"GreenWebChecker",            "GreenWebChecker"),
]

# Generische Keywords — greifen wenn kein KNOWN_BOT zutrifft
BOT_KEYWORDS = re.compile(
    r"\b(bot|crawler|spider|scraper|scan(?:ner)?|fetch(?:er)?|"
    r"index(?:er)?|check(?:er)?|monitor|harvest|slurp|seek(?:er)?|"
    r"grab(?:ber)?|download|archiv(?:er?|al))\b",
    re.IGNORECASE,
)

# Apache Combined Log Format
LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[.*?\] "(?P<request>[^"]*)" \d+ \d+ '
    r'"(?P<referer>[^"]*)" "(?P<ua>[^"]*)"'
)

# ---------------------------------------------------------------------------
# phpBB-Bot-Liste (aus ACP — Stand 28.04.2026)
#
# Enthält die UA-Erkennungsstrings wie in phpBB eingetragen.
# phpBB arbeitet intern mit strpos() — ein Teilstring reicht.
# Der Abgleich hier spiegelt das: bidirektionales Substring-Matching.
# ---------------------------------------------------------------------------
PHPBB_BOTS = {
    # Aktiv gesehen (letzter Besuch bekannt)
    "Amazonbot", "PetalBot", "SemrushBot", "Googlebot", "Qwantbot",
    "compatible; crawler", "Bytespider", "ChatGPT",
    "MJ12bot", "DuckDuckBot", "AhrefsBot", "OAI-SearchBot", "GPTBot",
    "Applebot", "AdsBot-Google", "bingbot", "msnbot", "Mediapartners-Google",
    "FeedFetcher-Google", "msnbot-media",
    # Nie gesehen, aber angelegt
    "AltaVista", "Amazonbot", "Baidu", "Barkrowler", "BlackVeil",
    "DataForSeo", "DotBot", "FAST", "FleebsBot", "Francis",
    "Gigabot", "heise-IT-Markt", "Heritrix", "ICCrawler", "Metager2",
    "Nutch", "PerplexityBot", "SEO Crawler", "SEOSearch", "SERanking",
    "Sensis", "Seoma", "Snappy", "Sogou", "Steeler", "Telekom",
    "TurnitinBot", "Twitterbot", "Yahoo-MMCrawler", "Slurp",
    "YahooSeeker", "Yandex", "meta-externalagent", "yacybot",
    # Ältere Einträge
    "Ask Jeeves", "W3C", "linkcheck", "Voyager", "ichiro",
    "Google Desktop", "psbot", "IBM Research", "MSN NewsBlogs",
    "W3 Sitesearch",
}


def is_in_phpbb(uas: set) -> bool:
    """Prüft wie phpBB es tut: ist irgendein phpBB-Pattern Teilstring eines UA-Strings?"""
    for ua in uas:
        ua_lower = ua.lower()
        for pattern in PHPBB_BOTS:
            if pattern.lower() in ua_lower:
                return True
    return False


def identify_bot(ua: str) -> str | None:
    """Gibt Bot-Namen zurück oder None wenn kein Bot erkannt."""
    for pattern, name in KNOWN_BOTS:
        if re.search(pattern, ua, re.IGNORECASE):
            return name
    if BOT_KEYWORDS.search(ua):
        # Unbekannter Bot — UA-String gekürzt als Name
        return f"[unbekannt] {ua[:80].strip()}"
    return None


def analyse(logfiles: list[str]) -> None:
    bots: dict[str, dict] = defaultdict(lambda: {"requests": 0, "ips": set(), "uas": set()})
    total_lines = 0
    parse_errors = 0

    for path in logfiles:
        try:
            with open(path, "r", errors="replace") as fh:
                for line in fh:
                    total_lines += 1
                    m = LOG_PATTERN.match(line)
                    if not m:
                        parse_errors += 1
                        continue
                    ua = m.group("ua")
                    name = identify_bot(ua)
                    if name:
                        bots[name]["requests"] += 1
                        bots[name]["ips"].add(m.group("ip"))
                        bots[name]["uas"].add(ua)
        except OSError as e:
            print(f"Fehler beim Öffnen von {path}: {e}", file=sys.stderr)

    if not bots:
        print("Keine Bots gefunden.")
        return

    # Sortiert nach Requests absteigend
    sorted_bots = sorted(bots.items(), key=lambda x: x[1]["requests"], reverse=True)

    # --- Ausgabe ---
    col_name  = max(len(n) for n in bots) + 2
    col_name  = max(col_name, 40)

    header = f"{'Bot-Name':<{col_name}} {'Requests':>9}  {'IPs':>6}  {'in phpBB':>10}  UA-Varianten"
    print()
    print(header)
    print("-" * (len(header) + 20))

    in_phpbb_count    = 0
    not_in_phpbb      = []

    for name, data in sorted_bots:
        in_phpbb = is_in_phpbb(data["uas"])
        if in_phpbb:
            in_phpbb_count += 1
            marker = "✓"
        else:
            not_in_phpbb.append(name)
            marker = "✗ FEHLT"

        ua_count = len(data["uas"])
        ua_hint  = f"{ua_count} UA-String{'s' if ua_count != 1 else ''}"

        print(f"{name:<{col_name}} {data['requests']:>9,}  {len(data['ips']):>6,}  {marker:>10}  {ua_hint}")

    # --- Zusammenfassung ---
    print()
    print(f"{'='*60}")
    print(f"Logzeilen gesamt:      {total_lines:>10,}")
    if parse_errors:
        print(f"Nicht parsierbar:      {parse_errors:>10,}")
    print(f"Bot-Typen gefunden:    {len(bots):>10,}")
    print(f"Davon in phpBB:        {in_phpbb_count:>10,}")
    print(f"Davon NICHT in phpBB:  {len(not_in_phpbb):>10,}")

    if not_in_phpbb:
        print()
        print("Bots die in phpBB noch FEHLEN (nach Requests sortiert):")
        for name in not_in_phpbb:
            req = bots[name]["requests"]
            print(f"  {req:>8,}x  {name}")

    # --- UA-Details für unbekannte Bots ---
    unknown = [(n, d) for n, d in sorted_bots if n.startswith("[unbekannt]")]
    if unknown:
        print()
        print("Unbekannte Bot-UAs (vollständig):")
        for name, data in unknown:
            print(f"  {data['requests']:>8,}x  {', '.join(list(data['uas'])[:3])}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Verwendung: {sys.argv[0]} logfile [logfile ...]")
        sys.exit(1)
    analyse(sys.argv[1:])
