<?php

declare(strict_types=1);
require_once __DIR__ . '/includes/functions.php';
$slug = isset($_GET['slug']) ? preg_replace('/[^a-z0-9-]/', '', (string) $_GET['slug']) : '';
$guide = get_guide($slug);
if ($guide === null) {
    http_response_code(404);
    require __DIR__ . '/404.php';
    exit;
}
$category = get_category($guide['category']);
$pageTitle = $guide['title'];
$pageDescription = $guide['summary'];
$canonicalPath = 'guides/' . $slug;
$bodyClass = 'guide-page';
require __DIR__ . '/includes/header.php';
?>
<article>
    <header class="guide-hero">
        <div class="shell guide-hero__grid">
            <div>
                <a class="back-link" href="<?= e(category_url($guide['category'])) ?>">← <?= e($category['name']) ?></a>
                <p class="eyebrow"><?= e($guide['reading_time']) ?> · Updated <?= e($guide['updated']) ?></p>
                <h1><?= e($guide['title']) ?></h1>
                <p class="guide-hero__intro"><?= e($guide['intro']) ?></p>
            </div>
            <div class="guide-hero__stamp accent-<?= e($category['accent']) ?>" aria-hidden="true">
                <span>What</span><strong>10</strong><span>Things</span>
            </div>
        </div>
    </header>
    <div class="shell guide-layout">
        <aside class="guide-progress" aria-label="Guide contents">
            <strong>In this guide</strong>
            <ol>
                <?php foreach ($guide['items'] as $index => $item): ?>
                    <li><a href="#thing-<?= $index + 1 ?>"><span><?= $index + 1 ?></span><?= e($item['title']) ?></a></li>
                <?php endforeach; ?>
            </ol>
        </aside>
        <div class="guide-content">
            <?php foreach ($guide['items'] as $index => $item): ?>
                <section id="thing-<?= $index + 1 ?>" class="guide-thing">
                    <div class="guide-thing__number"><span><?= str_pad((string) ($index + 1), 2, '0', STR_PAD_LEFT) ?></span><i></i></div>
                    <div><h2><?= e($item['title']) ?></h2><p><?= e($item['body']) ?></p></div>
                </section>
            <?php endforeach; ?>
            <aside class="guide-note">
                <strong>The final check</strong>
                <p>Write down the three points from this guide that matter most to your situation. Use those as your decision criteria and ignore features that do not change the outcome.</p>
            </aside>
        </div>
    </div>
</article>
<section class="section related-guides">
    <div class="shell">
        <div class="section-heading section-heading--inline"><div><p class="eyebrow">Keep going</p><h2>Related guides</h2></div></div>
        <div class="guide-library__list">
            <?php $shown = 0; foreach (guides_for_category($guide['category']) as $relatedSlug => $related): if ($relatedSlug === $slug) continue; guide_card($relatedSlug, $related, true); $shown++; if ($shown === 3) break; endforeach; ?>
        </div>
    </div>
</section>
<script type="application/ld+json"><?= json_encode([
    '@context' => 'https://schema.org',
    '@type' => 'ItemList',
    'name' => $guide['title'],
    'description' => $guide['summary'],
    'numberOfItems' => 10,
    'itemListElement' => array_map(static fn(array $item, int $index): array => ['@type' => 'ListItem', 'position' => $index + 1, 'name' => $item['title']], $guide['items'], array_keys($guide['items'])),
], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) ?></script>
<?php require __DIR__ . '/includes/footer.php'; ?>
