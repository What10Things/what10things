<?php

declare(strict_types=1);
require_once __DIR__ . '/includes/functions.php';
$slug = isset($_GET['slug']) ? preg_replace('/[^a-z0-9-]/', '', (string) $_GET['slug']) : '';
$destination = get_destination($slug);
if ($destination === null) {
    http_response_code(404);
    require __DIR__ . '/404.php';
    exit;
}
$pageTitle = $destination['name'] . ', ' . $destination['country'];
$pageDescription = $destination['summary'];
$canonicalPath = 'travel/' . $slug;
require __DIR__ . '/includes/header.php';
?>
<section class="destination-hero">
    <div class="shell destination-hero__grid">
        <div>
            <a class="back-link" href="/travel">← Travel desk</a>
            <p class="eyebrow"><?= e($destination['region']) ?> · <?= e($destination['country']) ?></p>
            <h1><?= e($destination['name']) ?></h1>
            <p><?= e($destination['summary']) ?></p>
        </div>
        <div class="destination-hero__ticket" aria-hidden="true"><span><?= e(strtoupper(substr($destination['name'], 0, 3))) ?></span><strong>10</strong><small>What to know</small></div>
    </div>
</section>
<section class="section">
    <div class="shell destination-body">
        <div>
            <p class="eyebrow">Destination note</p>
            <h2>A useful starting point</h2>
            <p>Build the trip around the pace, weather, transport and attractions that matter to your group. Check current official information before booking tickets or relying on opening arrangements.</p>
            <div class="destination-facts">
                <div><span>Plan by</span><strong>Neighbourhood</strong></div>
                <div><span>Protect</span><strong>Rest time</strong></div>
                <div><span>Verify</span><strong>Current entry rules</strong></div>
            </div>
        </div>
        <aside>
            <?php if ($destination['guide'] !== null && isset($guides[$destination['guide']])): $guide = $guides[$destination['guide']]; ?>
                <span class="pill">Related ten-point guide</span>
                <h2><?= e($guide['title']) ?></h2>
                <p><?= e($guide['summary']) ?></p>
                <a class="button" href="<?= e(guide_url($destination['guide'])) ?>">Read the guide →</a>
            <?php else: ?>
                <span class="pill">Guide in development</span>
                <h2>A full <?= e($destination['name']) ?> guide is being prepared.</h2>
                <p>Use the travel library for practical planning checklists while this destination guide is expanded.</p>
                <a class="button" href="/travel">Browse travel guides →</a>
            <?php endif; ?>
        </aside>
    </div>
</section>
<?php require __DIR__ . '/includes/footer.php'; ?>
