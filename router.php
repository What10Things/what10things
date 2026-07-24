<?php
// Local-only router for PHP's built-in development server.
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) ?: '/';
$file = __DIR__ . $path;
if ($path !== '/' && is_file($file)) { return false; }
$routes = [
    '#^/guides/?$#' => ['guides.php', []],
    '#^/guides/([a-z0-9-]+)/?$#' => ['guide.php', ['slug']],
    '#^/category/([a-z0-9-]+)/?$#' => ['category.php', ['slug']],
    '#^/travel/?$#' => ['travel.php', []],
    '#^/travel/([a-z0-9-]+)/?$#' => ['destination.php', ['slug']],
    '#^/search/?$#' => ['search.php', []],
    '#^/about/?$#' => ['about.php', []],
    '#^/methodology/?$#' => ['methodology.php', []],
    '#^/contact/?$#' => ['contact.php', []],
    '#^/privacy/?$#' => ['privacy.php', []],
    '#^/terms/?$#' => ['terms.php', []],
    '#^/affiliate-disclosure/?$#' => ['affiliate-disclosure.php', []],
];
if ($path === '/') { require __DIR__ . '/index.php'; exit; }
foreach ($routes as $pattern => [$target, $names]) {
    if (preg_match($pattern, $path, $matches)) {
        foreach ($names as $index => $name) { $_GET[$name] = $matches[$index + 1]; }
        require __DIR__ . '/' . $target;
        exit;
    }
}
require __DIR__ . '/404.php';
