<?php
/**
 * LBar Ivano-Frankivsk — завантаження потрібних фото з сайту Дніпра (https://lbar.com.ua/dnipro/).
 *
 * Як запустити:
 *   1) Покладіть цей файл і dnipro-images.tsv у корінь сайту (поруч з index.php).
 *   2) У браузері: https://ВАШ-САЙТ/fetch_dnipro_images.php?key=lbar-if
 *      або по SSH:  php fetch_dnipro_images.php
 *   3) Якщо хостинг обриває довгі запити — відкривайте сторінку повторно: вже завантажені файли пропускаються.
 *   4) Після завершення ВИДАЛІТЬ обидва файли з сервера.
 */
const KEY = 'lbar-if';
const LIST_FILE = __DIR__ . '/dnipro-images.tsv';
const PER_RUN = 250;               // скільки файлів завантажувати за один запуск у браузері

$cli = (PHP_SAPI === 'cli');
if (!$cli) {
    if (!isset($_GET['key']) || $_GET['key'] !== KEY) { http_response_code(403); exit('Forbidden'); }
    header('Content-Type: text/plain; charset=utf-8');
}
@set_time_limit(0);
@ini_set('memory_limit', '256M');
if (!is_file(LIST_FILE)) exit("Немає файлу dnipro-images.tsv поруч зі скриптом\n");

function fetch_url($url) {
    if (function_exists('curl_init')) {
        $ch = curl_init($url);
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_FOLLOWLOCATION => true, CURLOPT_TIMEOUT => 120,
                                CURLOPT_CONNECTTIMEOUT => 15, CURLOPT_USERAGENT => 'LBar-IF-image-sync']);
        $data = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        return ($code === 200 && $data !== false && strlen($data) > 0) ? $data : null;
    }
    $ctx = stream_context_create(['http' => ['timeout' => 120, 'user_agent' => 'LBar-IF-image-sync']]);
    $data = @file_get_contents($url, false, $ctx);
    return ($data !== false && strlen($data) > 0) ? $data : null;
}

$rows = array_slice(file(LIST_FILE, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES), 1);
$ok = $skip = $fail = 0; $done = 0; $failed = [];
foreach ($rows as $line) {
    list($dest, $src, $fallback) = array_pad(explode("\t", $line), 3, '');
    $dest = ltrim(str_replace('\\', '/', $dest), '/');
    if ($dest === '' || strpos($dest, '..') !== false) continue;
    $path = __DIR__ . '/' . $dest;
    if (is_file($path) && filesize($path) > 0) { $skip++; continue; }
    if (!$cli && $done >= PER_RUN) break;
    $done++;
    $data = fetch_url($src);
    if ($data === null && $fallback !== '') $data = fetch_url($fallback);
    if ($data === null) { $fail++; $failed[] = $dest; echo "FAIL  $dest\n"; continue; }
    if (!is_dir(dirname($path))) mkdir(dirname($path), 0755, true);
    file_put_contents($path, $data);
    $ok++;
    echo "OK    $dest\n";
    if (!$cli) { @ob_flush(); @flush(); }
}
$left = 0;
foreach ($rows as $line) {
    $d = ltrim(str_replace('\\', '/', explode("\t", $line)[0]), '/');
    if ($d === '' || strpos($d, '..') !== false) continue;
    if (!is_file(__DIR__ . '/' . $d)) $left++;
}
echo "\nЗавантажено: $ok, вже були: $skip, помилок: $fail, ще не завантажено: $left\n";
if ($left === 0) echo "Готово. Видаліть fetch_dnipro_images.php і dnipro-images.tsv з сервера.\n";
elseif ($left > $fail && !$cli) echo "Оновіть сторінку, щоб продовжити.\n";
else echo "Ці файли не вдалося завантажити ні з сайту Дніпра, ні з lbar.com.ua — див. рядки FAIL вище.\n";
