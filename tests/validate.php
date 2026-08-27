<?php

declare(strict_types=1);
require_once __DIR__ . '/../includes/functions.php';
$errors = [];
if (count($guides) !== 10) { $errors[] = 'Expected exactly 10 launch guides; found ' . count($guides); }
foreach ($guides as $slug => $guide) {
    if (!isset($categories[$guide['category']])) { $errors[] = "$slug uses an unknown category"; }
    if (count($guide['items']) !== 10) { $errors[] = "$slug must contain exactly 10 items"; }
    if (!preg_match('/^[a-z0-9-]+$/', $slug)) { $errors[] = "$slug is not a safe slug"; }
    foreach ($guide['items'] as $index => $item) {
        if (trim($item['title']) === '' || trim($item['body']) === '') { $errors[] = "$slug item " . ($index + 1) . ' is incomplete'; }
    }
}
foreach ($destinations as $slug => $destination) {
    if ($destination['guide'] !== null && !isset($guides[$destination['guide']])) { $errors[] = "$slug links to a missing guide"; }
}
$companyFiles = [
    __DIR__ . '/../includes/footer.php',
    __DIR__ . '/../about.php',
    __DIR__ . '/../privacy.php',
    __DIR__ . '/../affiliate-disclosure.php',
    __DIR__ . '/../terms.php',
];
foreach ($companyFiles as $companyFile) {
    $companyContent = file_get_contents($companyFile);
    if ($companyContent === false || !str_contains($companyContent, 'Urban Sky Web Ltd') || !str_contains($companyContent, '17421062')) {
        $errors[] = basename($companyFile) . ' is missing the company disclosure';
    }
}
$privacyContent = file_get_contents(__DIR__ . '/../privacy.php');
if ($privacyContent === false || !str_contains($privacyContent, 'purposes and lawful bases') || !str_contains($privacyContent, 'Information Commissioner')) {
    $errors[] = 'privacy.php is missing the expanded privacy information';
}
$affiliateContent = file_get_contents(__DIR__ . '/../affiliate-disclosure.php');
if ($affiliateContent === false || !str_contains($affiliateContent, 'visibly marked <strong>Ad</strong>')) {
    $errors[] = 'affiliate-disclosure.php is missing the nearby Ad-labelling commitment';
}
if ($errors) {
    fwrite(STDERR, implode(PHP_EOL, $errors) . PHP_EOL);
    exit(1);
}
echo "Content validation passed: " . count($guides) . " guides, " . count($categories) . " categories, " . count($destinations) . " destinations." . PHP_EOL;
