<?php

declare(strict_types=1);
require_once __DIR__ . '/includes/functions.php';
header('Content-Type: application/xml; charset=utf-8');
$urls = ['', 'guides', 'travel', 'about', 'methodology', 'contact', 'privacy', 'terms', 'affiliate-disclosure'];
foreach (array_keys($categories) as $slug) { $urls[] = 'category/' . $slug; }
foreach (array_keys($guides) as $slug) { $urls[] = 'guides/' . $slug; }
foreach (array_keys($destinations) as $slug) { $urls[] = 'travel/' . $slug; }
echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<?php foreach ($urls as $path): ?>  <url><loc><?= e(site_url($path)) ?></loc><lastmod>2026-07-24</lastmod></url>
<?php endforeach; ?></urlset>
