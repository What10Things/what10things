<?php

declare(strict_types=1);
require_once __DIR__ . '/includes/functions.php';
$pageTitle = 'All guides';
$pageDescription = 'Browse every What 10 Things guide across buying, technology, home, travel, money and everyday decisions.';
$canonicalPath = 'guides';
require __DIR__ . '/includes/header.php';
?>
<section class="page-hero page-hero--compact">
    <div class="shell">
        <p class="eyebrow">The full library</p>
        <h1>Every guide, in one useful index.</h1>
        <p>Filter by the kind of decision, then open the ten-point guide that answers it.</p>
    </div>
</section>
<section class="section">
    <div class="shell guide-library" data-filter-scope>
        <div class="filter-bar" aria-label="Filter guides">
            <button type="button" class="is-active" data-filter="all">All <span><?= count($guides) ?></span></button>
            <?php foreach ($categories as $slug => $category): ?>
                <button type="button" data-filter="<?= e($slug) ?>"><?= e($category['name']) ?> <span><?= count(guides_for_category($slug)) ?></span></button>
            <?php endforeach; ?>
        </div>
        <div class="guide-library__list" data-filter-list>
            <?php foreach ($guides as $slug => $guide): ?>
                <?php guide_card($slug, $guide); ?>
            <?php endforeach; ?>
        </div>
        <p class="empty-state" hidden data-filter-empty>No guides match this filter yet.</p>
    </div>
</section>
<?php require __DIR__ . '/includes/footer.php'; ?>
