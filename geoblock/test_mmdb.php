<?php
// Testscript — nach dem Test vom Server löschen!
// Aufruf: https://deineforum.de/geoblock/test_mmdb.php?ip=77.88.8.8
// ACHTUNG: Dieser Script ist öffentlich erreichbar solange er hochgeladen ist.

// Minimaler Schutz: nur mit korrektem Token aufrufbar
// Token vor Upload ändern!
define('TEST_TOKEN', 'AENDERN_VOR_UPLOAD_geheim123');

if (($_GET['token'] ?? '') !== TEST_TOKEN) {
    http_response_code(403);
    echo 'Token fehlt oder falsch. URL: ?token=AENDERN_VOR_UPLOAD_geheim123&ip=77.88.8.8';
    exit;
}

$base = __DIR__;
require_once $base . '/MaxMind/Db/Reader/InvalidDatabaseException.php';
require_once $base . '/MaxMind/Db/Reader/Util.php';
require_once $base . '/MaxMind/Db/Reader/Decoder.php';
require_once $base . '/MaxMind/Db/Reader/Metadata.php';
require_once $base . '/MaxMind/Db/Reader.php';

$db = $base . '/dbip-country-lite.mmdb';
if (!file_exists($db)) {
    die('FEHLER: dbip-country-lite.mmdb nicht gefunden in ' . $db);
}

$reader = new \MaxMind\Db\Reader($db);

$test_ips = [
    '77.88.8.8'       => ['Yandex RU',        true],
    '1.0.1.5'         => ['China Telecom CN',  true],
    '1.6.0.5'         => ['BSNL India IN',     true],
    '8.8.8.8'         => ['Google US',         false],
    '217.247.0.1'     => ['Telekom DE',        false],
    '85.214.0.1'      => ['Strato DE',         false],
    $_GET['ip'] ?? '8.8.8.8' => ['Eigene Test-IP', null],
];

echo '<pre>';
echo "=== MMDB Geo-Block Test ===\n";
echo "DB: $db\n";
echo "DB-Größe: " . round(filesize($db) / 1024 / 1024, 1) . " MB\n\n";

$blocked_countries = ['RU', 'CN', 'IN', 'KP', 'IR', 'VN', 'PK', 'BD'];
$ok = $fail = 0;

foreach ($test_ips as $ip => [$label, $should_block]) {
    $record  = $reader->get($ip);
    $country = null;
    if ($record !== null) {
        $country = $record['country'] ?? $record['country']['iso_code'] ?? null;
        if (is_array($country)) $country = $country['iso_code'] ?? null;
    }
    $blocked = $country !== null && in_array(strtoupper((string)$country), $blocked_countries, true);

    if ($should_block === null) {
        $status = '    ';
        echo "[ -- ] $ip  ($label)  → Land: " . ($country ?? 'unbekannt') . ($blocked ? " GEBLOCKT" : "") . "\n";
    } else {
        $pass = ($blocked === $should_block);
        $status = $pass ? 'OK  ' : 'FAIL';
        $pass ? $ok++ : $fail++;
        $action = $blocked ? 'GEBLOCKT    ' : 'durchgelassen';
        $expect = $should_block ? 'soll blocken' : 'soll durch  ';
        echo "[$status] $ip  ($label | Land: " . ($country ?? '??') . ")  → $action  [$expect]\n";
    }
}

$reader->close();
echo "\n$ok/". ($ok+$fail) ." Tests bestanden" . ($fail ? ", $fail FEHLGESCHLAGEN" : " ✓") . "\n";
echo "\nNach dem Test diese Datei vom Server löschen!\n";
echo '</pre>';
