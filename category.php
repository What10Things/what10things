<?php

declare(strict_types=1);
require_once __DIR__ . '/includes/functions.php';
$slug = isset($_GET['slug']) ? preg_replace('/[^a-z0-9-]/', '', (string) $_GET['slug']) : '';
$category = get_category($slug);
if ($category === null) {
    http_response_code(404);
    require __DIR__ . '/404.php';
    exit;
}
$categoryGuides = guides_for_category($slug);
$pageTitle = $category['name'];
$pageDescription = $category['description'];
$canonicalPath = 'category/' . $slug;
require __DIR__ . '/includes/header.php';
?>
<section class="category-hero accent-bg-<?= e($category['accent']) ?>">
    <div class="shell category-hero__grid">
        <div>
            <p class="eyebrow"><?= e($category['short']) ?></p>
            <h1><?= e($category['name']) ?></h1>
            <p><?= e($category['description']) ?></p>
        </div>
        <div class="category-hero__symbol" aria-hidden="true"><?= e($category['symbol']) ?><span>10</span></div>
    </div>
</section>
<section class="section">
    <div class="shell">
        <div class="section-heading section-heading--inline"><div><p class="eyebrow"><?= count($categoryGuides) ?> guides</p><h2>Start with one clear question</h2></div></div>
        <div class="guide-library__list">
            <?php foreach ($categoryGuides as $guideSlug => $guide): guide_card($guideSlug, $guide); endforeach; ?>
        </div>
    </div>
</section>
<?php require __DIR__ . '/includes/footer.php'; ?>
