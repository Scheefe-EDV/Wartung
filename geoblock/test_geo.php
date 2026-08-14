<?php
// Lokaler Test — nicht auf den Server hochladen
// Ausfuehren mit: php test_geo.php

$test_ips = [
    '77.88.8.8'       => ['Yandex DNS (RU)',        true],  // soll blocken
    '8.7.198.45'      => ['China Telecom (CN)',       true],  // soll blocken
    '1.186.0.1'       => ['BSNL India (IN)',          true],  // soll blocken
    '176.9.0.1'       => ['Hetzner DE (RU-nahe)',    false],  // darf NICHT blocken (Hetzner Deutschland)
    '8.8.8.8'         => ['Google DNS (US)',          false],  // darf NICHT blocken
    '91.198.174.192'  => ['Wikimedia DE',             false],  // darf NICHT blocken
    '217.247.0.1'     => ['Telekom Deutschland',      false],  // darf NICHT blocken
    '85.214.0.1'      => ['Strato AG (DE)',           false],  // darf NICHT blocken
];

// Ranges aus geo_block.php einlesen (nur die Array-Zeilen)
$ranges = [];
$f = fopen(__DIR__ . '/geo_block.php', 'r');
$in_array = false;
while (($line = fgets($f)) !== false) {
    if (strpos($line, '$ranges = [') !== false) { $in_array = true; continue; }
    if ($in_array && $line === "];\n") break;
    if ($in_array) {
        if (preg_match('/\[(\d+),(\d+)\]/', $line, $m)) {
            $ranges[] = [(int)$m[1], (int)$m[2]];
        }
    }
}
fclose($f);

function is_blocked(string $ip, array $ranges): bool {
    $ip_long = ip2long($ip);
    if ($ip_long === false || $ip_long < 0) return false;
    $lo = 0; $hi = count($ranges) - 1;
    while ($lo <= $hi) {
        $mid = ($lo + $hi) >> 1;
        if ($ip_long < $ranges[$mid][0])      $hi = $mid - 1;
        elseif ($ip_long > $ranges[$mid][1])  $lo = $mid + 1;
        else return true;
    }
    return false;
}

echo "=== Geo-Block Test (" . count($ranges) . " Ranges geladen) ===\n\n";
$ok = 0; $fail = 0;
foreach ($test_ips as $ip => [$label, $should_block]) {
    $blocked = is_blocked($ip, $ranges);
    $status  = $blocked === $should_block ? 'OK  ' : 'FAIL';
    $action  = $blocked ? 'GEBLOCKT  ' : 'durchgelassen';
    $expect  = $should_block ? 'soll blocken' : 'soll durch';
    echo "[$status] $ip  ($label)\n       → $action  [$expect]\n";
    $blocked === $should_block ? $ok++ : $fail++;
}
echo "\n$ok/" . count($test_ips) . " Tests bestanden" . ($fail ? ", $fail fehlgeschlagen" : "") . "\n";
