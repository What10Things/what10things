<?php

declare(strict_types=1);

require_once __DIR__ . '/functions.php';

$pageTitle = $pageTitle ?? $site['name'];
$pageDescription = $pageDescription ?? $site['description'];
$canonicalPath = $canonicalPath ?? ltrim(current_path(), '/');
$bodyClass = $bodyClass ?? '';
$fullTitle = $pageTitle === $site['name'] ? $pageTitle : $pageTitle . ' | ' . $site['name'];
$canonical = site_url($canonicalPath);
?>
<!doctype html>
<html lang="en-GB">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= e($fullTitle) ?></title>
    <meta name="description" content="<?= e($pageDescription) ?>">
    <meta name="theme-color" content="#101c2c">
    <meta name="color-scheme" content="light">
    <link rel="canonical" href="<?= e($canonical) ?>">
    <link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
    <link rel="manifest" href="/manifest.webmanifest">
    <meta property="og:type" content="website">
    <meta property="og:title" content="<?= e($fullTitle) ?>">
    <meta property="og:description" content="<?= e($pageDescription) ?>">
    <meta property="og:url" content="<?= e($canonical) ?>">
    <meta property="og:image" content="<?= e(site_url('assets/img/social-card.svg')) ?>">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/assets/css/site.css?v=1.0.0">
    <script defer src="/assets/js/site.js?v=1.0.0"></script>
</head>
<body class="<?= e($bodyClass) ?>">
<a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header" data-header>
    <div class="shell site-header__inner">
        <a class="brand" href="/" aria-label="What 10 Things home">
            <svg class="brand__mark" viewBox="0 0 48 48" aria-hidden="true">
                <rect x="3" y="3" width="42" height="42" rx="11"></rect>
                <path d="M14 14h7v20h-7zM27 14h7v20h-7z"></path>
                <path class="brand__slash" d="M10 25h28"></path>
            </svg>
            <span class="brand__text"><strong>What</strong><b>10</b><strong>Things</strong></span>
        </a>
        <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-navigation" data-nav-toggle>
            <span></span><span></span><span></span><span class="sr-only">Open menu</span>
        </button>
        <nav class="site-nav" id="primary-navigation" aria-label="Primary navigation" data-nav>
            <a href="/guides" <?= is_active('/guides') ? 'aria-current="page"' : '' ?>>All guides</a>
            <a href="/category/buying-guides" <?= is_active('/category/buying-guides') ? 'aria-current="page"' : '' ?>>Buying</a>
            <a href="/travel" <?= is_active('/travel') ? 'aria-current="page"' : '' ?>>Travel</a>
            <a href="/methodology" <?= is_active('/methodology') ? 'aria-current="page"' : '' ?>>How we work</a>
            <a class="site-nav__search" href="/search" aria-label="Search What 10 Things">
                <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"></circle><path d="m16 16 4 4"></path></svg>
                <span>Search</span>
            </a>
        </nav>
    </div>
</header>
<main id="main-content">
