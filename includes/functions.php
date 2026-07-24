<?php

declare(strict_types=1);

require_once __DIR__ . '/../data/site.php';

function e(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function lower_text(string $value): string
{
    return function_exists('mb_strtolower') ? mb_strtolower($value, 'UTF-8') : strtolower($value);
}

function site_url(string $path = ''): string
{
    global $site;
    $base = rtrim((string) $site['url'], '/');
    if ($path === '') {
        return $base . '/';
    }
    return $base . '/' . ltrim($path, '/');
}

function path_url(string $path = ''): string
{
    if ($path === '') {
        return '/';
    }
    return '/' . ltrim($path, '/');
}

function guide_url(string $slug): string
{
    return path_url('guides/' . rawurlencode($slug));
}

function category_url(string $slug): string
{
    return path_url('category/' . rawurlencode($slug));
}

function destination_url(string $slug): string
{
    return path_url('travel/' . rawurlencode($slug));
}

function current_path(): string
{
    $uri = $_SERVER['REQUEST_URI'] ?? '/';
    $path = parse_url($uri, PHP_URL_PATH);
    return is_string($path) ? $path : '/';
}

function is_active(string $prefix): bool
{
    $path = current_path();
    if ($prefix === '/') {
        return $path === '/';
    }
    return str_starts_with($path, $prefix);
}

function get_guide(string $slug): ?array
{
    global $guides;
    return $guides[$slug] ?? null;
}

function get_category(string $slug): ?array
{
    global $categories;
    return $categories[$slug] ?? null;
}

function get_destination(string $slug): ?array
{
    global $destinations;
    return $destinations[$slug] ?? null;
}

function guides_for_category(string $categorySlug): array
{
    global $guides;
    return array_filter($guides, static fn(array $guide): bool => $guide['category'] === $categorySlug);
}

function featured_guides(int $limit = 4): array
{
    global $guides;
    $featured = array_filter($guides, static fn(array $guide): bool => (bool) ($guide['featured'] ?? false));
    return array_slice($featured, 0, $limit, true);
}

function search_content(string $query): array
{
    global $guides, $categories, $destinations;
    $needle = lower_text(trim($query));
    if ($needle === '') {
        return [];
    }

    $results = [];
    foreach ($guides as $slug => $guide) {
        $haystack = $guide['title'] . ' ' . $guide['summary'] . ' ' . $guide['intro'];
        foreach ($guide['items'] as $item) {
            $haystack .= ' ' . $item['title'] . ' ' . $item['body'];
        }
        if (str_contains(lower_text($haystack), $needle)) {
            $results[] = [
                'type' => 'Guide',
                'title' => $guide['title'],
                'summary' => $guide['summary'],
                'url' => guide_url($slug),
            ];
        }
    }

    foreach ($categories as $slug => $category) {
        $haystack = lower_text($category['name'] . ' ' . $category['description']);
        if (str_contains($haystack, $needle)) {
            $results[] = [
                'type' => 'Category',
                'title' => $category['name'],
                'summary' => $category['description'],
                'url' => category_url($slug),
            ];
        }
    }

    foreach ($destinations as $slug => $destination) {
        $haystack = lower_text($destination['name'] . ' ' . $destination['country'] . ' ' . $destination['region'] . ' ' . $destination['summary']);
        if (str_contains($haystack, $needle)) {
            $results[] = [
                'type' => 'Destination',
                'title' => $destination['name'] . ', ' . $destination['country'],
                'summary' => $destination['summary'],
                'url' => destination_url($slug),
            ];
        }
    }

    return $results;
}

function guide_card(string $slug, array $guide, bool $compact = false): void
{
    global $categories;
    $category = $categories[$guide['category']];
    $class = $compact ? 'guide-row guide-row--compact' : 'guide-row';
    ?>
    <article class="<?= e($class) ?>" data-category="<?= e($guide['category']) ?>">
        <a class="guide-row__link" href="<?= e(guide_url($slug)) ?>">
            <span class="guide-row__mark accent-<?= e($category['accent']) ?>" aria-hidden="true"><?= e($category['symbol']) ?></span>
            <span class="guide-row__body">
                <span class="guide-row__eyebrow"><?= e($category['name']) ?> · <?= e($guide['reading_time']) ?></span>
                <strong><?= e($guide['title']) ?></strong>
                <span><?= e($guide['summary']) ?></span>
            </span>
            <span class="guide-row__arrow" aria-hidden="true">→</span>
        </a>
    </article>
    <?php
}

function render_ten_rail(array $labels): void
{
    ?>
    <div class="ten-rail" aria-label="Ten guide themes">
        <?php foreach (array_values($labels) as $index => $label): ?>
            <div class="ten-rail__line" style="--i: <?= $index ?>">
                <span><?= e((string) (10 - $index)) ?></span>
                <i></i>
                <b><?= e($label) ?></b>
            </div>
        <?php endforeach; ?>
    </div>
    <?php
}
