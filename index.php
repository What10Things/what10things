<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/functions.php';
$pageTitle = $site['name'];
$pageDescription = $site['description'];
$canonicalPath = '';
$bodyClass = 'home-page';
require __DIR__ . '/includes/header.php';
$heroLabels = ['Buy', 'Travel', 'Tech', 'Home', 'Money', 'Family', 'Work', 'Life', 'Learn', 'Decide'];
?>
<section class="hero">
    <div class="shell hero__grid">
        <div class="hero__copy">
            <p class="eyebrow">Useful answers, counted properly</p>
            <h1>Ten clear things.<br><em>No endless scrolling.</em></h1>
            <p class="hero__lede">Practical guides for the decisions that take too long: what to buy, where to go and what to check before you commit.</p>
            <form class="hero-search" action="/search" method="get" role="search">
                <label for="home-search">What do you need to know?</label>
                <div>
                    <input id="home-search" name="q" type="search" placeholder="Try “air fryer”, “Rome” or “Wi-Fi”" autocomplete="off">
                    <button type="submit">Find ten things <span aria-hidden="true">→</span></button>
                </div>
            </form>
            <div class="hero__quick-links" aria-label="Popular searches">
                <span>Popular:</span>
                <a href="/guides/air-fryer-buying-guide">Air fryers</a>
                <a href="/guides/family-all-inclusive-holiday">Family holidays</a>
                <a href="/guides/improve-home-wifi">Home Wi-Fi</a>
            </div>
        </div>
        <div class="hero__visual">
            <?php render_ten_rail($heroLabels); ?>
        </div>
    </div>
</section>

<section class="section section--featured">
    <div class="shell split-heading">
        <div>
            <p class="eyebrow">Start here</p>
            <h2>Guides people can use immediately</h2>
        </div>
        <p>Every guide starts with the decision, removes the filler and ends after ten useful points.</p>
    </div>
    <div class="shell feature-layout">
        <?php $featured = featured_guides(4); $firstSlug = array_key_first($featured); $first = $featured[$firstSlug]; ?>
        <article class="feature-lead">
            <a href="<?= e(guide_url((string) $firstSlug)) ?>">
                <div class="feature-lead__number" aria-hidden="true">10</div>
                <div class="feature-lead__content">
                    <span class="pill">Featured guide</span>
                    <h3><?= e($first['title']) ?></h3>
                    <p><?= e($first['summary']) ?></p>
                    <strong>Read the guide <span aria-hidden="true">→</span></strong>
                </div>
            </a>
        </article>
        <div class="feature-list">
            <?php foreach (array_slice($featured, 1, null, true) as $slug => $guide): ?>
                <?php guide_card((string) $slug, $guide, true); ?>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<section class="section section--categories">
    <div class="shell">
        <div class="section-heading section-heading--inline">
            <div>
                <p class="eyebrow">Choose a desk</p>
                <h2>One method, six kinds of decision</h2>
            </div>
            <a class="text-link" href="/guides">Browse every guide →</a>
        </div>
        <div class="category-index">
            <?php $n = 1; foreach ($categories as $slug => $category): ?>
                <a class="category-index__item" href="<?= e(category_url($slug)) ?>">
                    <span class="category-index__number"><?= str_pad((string) $n, 2, '0', STR_PAD_LEFT) ?></span>
                    <span class="category-index__symbol accent-<?= e($category['accent']) ?>"><?= e($category['symbol']) ?></span>
                    <span class="category-index__copy"><strong><?= e($category['name']) ?></strong><small><?= e($category['description']) ?></small></span>
                    <span aria-hidden="true">↗</span>
                </a>
            <?php $n++; endforeach; ?>
        </div>
    </div>
</section>

<section class="section section--latest">
    <div class="shell section-heading section-heading--inline">
        <div>
            <p class="eyebrow">The full ten</p>
            <h2>Latest guides</h2>
        </div>
        <p>Ten current starting points across the site.</p>
    </div>
    <div class="shell numbered-guides">
        <?php $number = 1; foreach ($guides as $slug => $guide): ?>
            <article class="numbered-guides__item">
                <a href="<?= e(guide_url($slug)) ?>">
                    <span><?= str_pad((string) $number, 2, '0', STR_PAD_LEFT) ?></span>
                    <div><small><?= e($categories[$guide['category']]['name']) ?></small><strong><?= e($guide['title']) ?></strong></div>
                    <b aria-hidden="true">→</b>
                </a>
            </article>
        <?php $number++; endforeach; ?>
    </div>
</section>

<section class="section travel-desk">
    <div class="shell travel-desk__grid">
        <div class="travel-desk__intro">
            <p class="eyebrow">Travel desk</p>
            <h2>Plan the parts that matter. Leave space for the trip.</h2>
            <p>Destination notes, family checklists and first-visit guides arranged around practical questions rather than generic inspiration.</p>
            <a class="button button--light" href="/travel">Explore destinations <span aria-hidden="true">→</span></a>
        </div>
        <div class="travel-stamps" aria-label="Featured destinations">
            <?php foreach (array_slice($destinations, 0, 6, true) as $slug => $destination): ?>
                <a href="<?= e(destination_url($slug)) ?>">
                    <span><?= e($destination['region']) ?></span>
                    <strong><?= e($destination['name']) ?></strong>
                    <small><?= e($destination['country']) ?></small>
                </a>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<section class="section method-preview">
    <div class="shell method-preview__grid">
        <div>
            <p class="eyebrow">How we work</p>
            <h2>A list is useful only when every item earns its place.</h2>
        </div>
        <ol>
            <li><span>1</span><div><strong>Define the real decision</strong><p>We start with what the reader is trying to choose, avoid or understand.</p></div></li>
            <li><span>2</span><div><strong>Remove duplicated advice</strong><p>Similar points are combined so the list does not reach ten by repetition.</p></div></li>
            <li><span>3</span><div><strong>Make every point actionable</strong><p>Each item should change what someone checks, asks or does next.</p></div></li>
        </ol>
        <a class="text-link" href="/methodology">Read our full methodology →</a>
    </div>
</section>
<?php require __DIR__ . '/includes/footer.php'; ?>
