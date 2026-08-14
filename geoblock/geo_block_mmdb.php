<?php
declare(strict_types=1);

// ============================================================
// Ländersperre via MaxMind DB Reader + db-ip.com Country Lite
// Deckt IPv4 UND IPv6 ab, OPcache-freundlich, kein Apache-Modul
// ============================================================

// Gesperrte Länder (ISO 3166-1 alpha-2)
const BLOCKED_COUNTRIES = ['RU', 'CN', 'IN', 'KP', 'IR', 'VN', 'PK', 'BD'];

// Suchmaschinen durchlassen (User-Agent-Prüfung)
$ua = $_SERVER['HTTP_USER_AGENT'] ?? '';
if ($ua !== '' && preg_match('/Googlebot|Bingbot|DuckDuckBot|YandexBot|Baiduspider/i', $ua)) {
    return;
}

// IP ermitteln — X-Forwarded-For nur wenn Server hinter Proxy/CDN steht
$ip = $_SERVER['REMOTE_ADDR'] ?? '';
$forwarded = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? '';
if ($forwarded !== '') {
    $first = trim(explode(',', $forwarded)[0]);
    // Nur nutzen wenn REMOTE_ADDR eine private/lokale IP ist (Server hinter Proxy)
    if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) === false) {
        $ip = $first;
    }
}

// Lokale/private IPs immer durchlassen
if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) === false) {
    return;
}

// MaxMind DB Reader laden
$base = __DIR__;
require_once $base . '/MaxMind/Db/Reader/InvalidDatabaseException.php';
require_once $base . '/MaxMind/Db/Reader/Util.php';
require_once $base . '/MaxMind/Db/Reader/Decoder.php';
require_once $base . '/MaxMind/Db/Reader/Metadata.php';
require_once $base . '/MaxMind/Db/Reader.php';

$db = $base . '/dbip-country-lite.mmdb';
if (!file_exists($db)) {
    return; // Fail open: DB fehlt → nicht blocken
}

try {
    $reader = new \MaxMind\Db\Reader($db);
    $record = $reader->get($ip);
    $reader->close();
} catch (\Exception $e) {
    return; // Fail open
}

if ($record === null) {
    return; // IP nicht in DB → durchlassen
}

// db-ip.com Country Lite: $record['country'] ist direkt der ISO-Code
// MaxMind GeoLite2:        $record['country']['iso_code']
$country = $record['country'] ?? $record['country']['iso_code'] ?? null;
if (is_array($country)) {
    $country = $country['iso_code'] ?? null;
}

if ($country === null) {
    return;
}

if (in_array(strtoupper((string)$country), BLOCKED_COUNTRIES, true)) {
    http_response_code(403);
    header('Content-Type: text/html; charset=UTF-8');
    header('Cache-Control: no-store');
    echo '<!DOCTYPE html><html lang="de"><head><meta charset="UTF-8"><title>403 Zugriff verweigert</title>'
       . '<style>body{font-family:sans-serif;text-align:center;padding:4rem;color:#444}'
       . 'h1{font-size:2rem}p{max-width:40ch;margin:1rem auto}</style></head><body>'
       . '<h1>Zugriff verweigert</h1>'
       . '<p>Der Zugriff aus Ihrer Region ist nicht gestattet.</p>'
       . '<p>Access from your region is not permitted.</p>'
       . '</body></html>';
    exit;
}
