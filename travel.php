<?php

declare(strict_types=1);
require_once __DIR__ . '/includes/functions.php';
$pageTitle = 'Travel';
$pageDescription = 'Practical destination notes and ten-point travel guides for city breaks, family holidays and first visits.';
$canonicalPath = 'travel';
$bodyClass = 'travel-page';
require __DIR__ . '/includes/header.php';
$regions = array_values(array_unique(array_column($destinations, 'region')));
?>
<section class="travel-hero">
    <div class="shell travel-hero__grid">
        <div>
            <p class="eyebrow">Travel desk</p>
            <h1>Know the ten things.<br>Then go and enjoy it.</h1>
            <p>Practical preparation for the parts of a trip that can create stress: where to stay, what to book, how to pace the day and what families need.</p>
        </div>
        <div class="travel-orbit" aria-hidden="true"><span>10</span><i></i><b>places</b></div>
    </div>
</section>
<section class="section">
    <div class="shell" data-filter-scope>
        <div class="filter-bar filter-bar--travel" aria-label="Filter destinations">
            <button class="is-active" type="button" data-filter="all">All regions</button>
            <?php foreach ($regions as $region): ?><button type="button" data-filter="<?= e(strtolower(str_replace(' ', '-', $region))) ?>"><?= e($region) ?></button><?php endforeach; ?>
        </div>
        <div class="destination-grid" data-filter-list>
            <?php $n = 1; foreach ($destinations as $slug => $destination): $filter = strtolower(str_replace(' ', '-', $destination['region'])); ?>
                <article class="destination-card" data-category="<?= e($filter) ?>">
                    <a href="<?= e(destination_url($slug)) ?>">
                        <span class="destination-card__index"><?= str_pad((string) $n, 2, '0', STR_PAD_LEFT) ?></span>
                        <small><?= e($destination['region']) ?></small>
                        <h2><?= e($destination['name']) ?></h2>
                        <p><?= e($destination['summary']) ?></p>
                        <strong><?= e($destination['country']) ?> <span aria-hidden="true">→</span></strong>
                    </a>
                </article>
            <?php $n++; endforeach; ?>
        </div>
        <p class="empty-state" hidden data-filter-empty>No destinations match this region yet.</p>
    </div>
</section>
<section class="section travel-checklist-promo">
    <div class="shell travel-checklist-promo__inner">
        <div><p class="eyebrow">Family travel</p><h2>Start with the holiday, not the hotel advert.</h2><p>Use our family all-inclusive checklist to compare room layout, children’s facilities, food, entertainment and the real final cost.</p></div>
        <a class="button" href="/guides/family-all-inclusive-holiday">Open the ten-point checklist →</a>
    </div>
</section>
<?php require __DIR__ . '/includes/footer.php'; ?>
