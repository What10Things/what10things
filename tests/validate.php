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
if ($errors) {
    fwrite(STDERR, implode(PHP_EOL, $errors) . PHP_EOL);
    exit(1);
}
echo "Content validation passed: " . count($guides) . " guides, " . count($categories) . " categories, " . count($destinations) . " destinations." . PHP_EOL;
