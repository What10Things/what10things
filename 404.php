<?php

declare(strict_types=1);
if (!isset($site)) { require_once __DIR__ . '/includes/functions.php'; }
http_response_code(404);
$pageTitle = 'Page not found';
$pageDescription = 'The page could not be found.';
$canonicalPath = '404';
require __DIR__ . '/includes/header.php';
?>
<section class="not-found"><div class="shell not-found__grid"><div class="not-found__number" aria-hidden="true">10?</div><div><p class="eyebrow">Page not found</p><h1>That is one thing we could not find.</h1><p>The address may have changed or the guide may not exist yet. Search the site or return to the full guide library.</p><form class="search-form" action="/search" method="get"><label for="404-search">Search What 10 Things</label><div><input id="404-search" name="q" type="search" placeholder="What are you looking for?"><button type="submit">Search</button></div></form><a class="text-link" href="/guides">Browse all guides →</a></div></div></section>
<?php require __DIR__ . '/includes/footer.php'; ?>
