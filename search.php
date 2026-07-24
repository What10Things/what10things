<?php

declare(strict_types=1);
require_once __DIR__ . '/includes/functions.php';
$query = trim((string) ($_GET['q'] ?? ''));
$results = search_content($query);
$pageTitle = $query === '' ? 'Search' : 'Search results for “' . $query . '”';
$pageDescription = 'Search What 10 Things guides, categories and destinations.';
$canonicalPath = 'search' . ($query !== '' ? '?q=' . rawurlencode($query) : '');
require __DIR__ . '/includes/header.php';
?>
<section class="search-page">
    <div class="shell search-page__inner">
        <p class="eyebrow">Search the site</p>
        <h1><?= $query === '' ? 'What do you need to know?' : 'Results for “' . e($query) . '”' ?></h1>
        <form class="search-form" action="/search" method="get" role="search">
            <label for="site-search">Search guides, subjects and places</label>
            <div><input id="site-search" type="search" name="q" value="<?= e($query) ?>" placeholder="Type a subject"><button type="submit">Search</button></div>
        </form>
        <?php if ($query !== ''): ?>
            <p class="search-count"><?= count($results) ?> result<?= count($results) === 1 ? '' : 's' ?></p>
            <?php if ($results): ?>
                <div class="search-results">
                    <?php foreach ($results as $result): ?>
                        <article><a href="<?= e($result['url']) ?>"><span><?= e($result['type']) ?></span><h2><?= e($result['title']) ?></h2><p><?= e($result['summary']) ?></p><b aria-hidden="true">→</b></a></article>
                    <?php endforeach; ?>
                </div>
            <?php else: ?>
                <div class="no-results"><strong>No exact match yet.</strong><p>Try a shorter word, browse all guides or start with one of the popular subjects below.</p><div><a href="/guides">All guides</a><a href="/category/buying-guides">Buying guides</a><a href="/travel">Travel</a></div></div>
            <?php endif; ?>
        <?php else: ?>
            <div class="search-suggestions"><span>Try:</span><a href="/search?q=holiday">holiday</a><a href="/search?q=wifi">Wi-Fi</a><a href="/search?q=chair">chair</a><a href="/search?q=energy">energy</a></div>
        <?php endif; ?>
    </div>
</section>
<?php require __DIR__ . '/includes/footer.php'; ?>
