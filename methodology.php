<?php

declare(strict_types=1);
require_once __DIR__ . '/includes/functions.php';
$pageTitle = 'How we work';
$pageDescription = 'The editorial method behind What 10 Things guides: define the decision, research the checks and make every item actionable.';
$canonicalPath = 'methodology';
require __DIR__ . '/includes/header.php';
$steps = [
    ['Define the reader’s decision', 'We state the question in plain language and identify what a useful answer should help someone do next.'],
    ['Set the scope', 'We decide what belongs in the guide and what would distract from the main decision.'],
    ['Find the important checks', 'We identify recurring trade-offs, failure points and practical considerations.'],
    ['Prefer primary information', 'Where a guide relies on changing facts, we look first for official or first-party sources.'],
    ['Separate facts from judgement', 'We distinguish verifiable information from editorial interpretation and explain the basis for recommendations.'],
    ['Remove duplicated points', 'Similar advice is combined so each item adds a genuinely different consideration.'],
    ['Write from the reader’s side', 'Headings describe what someone should check or do, not how the information was gathered.'],
    ['Test the sequence', 'We arrange the guide in the order a person can realistically use it, from first checks to final decision.'],
    ['Review for clarity and safety', 'We remove vague claims, check links and add context where the subject needs professional or current advice.'],
    ['Update when the decision changes', 'Guides are reviewed when products, rules or common user needs materially change.'],
];
?>
<section class="page-hero"><div class="shell narrow"><p class="eyebrow">Editorial method</p><h1>Ten steps behind every ten-point guide.</h1><p>A repeatable process keeps the site useful as it grows and makes it easier to see why each item is included.</p></div></section>
<section class="section"><div class="shell method-list"><?php foreach ($steps as $index => $step): ?><article><span><?= str_pad((string) ($index + 1), 2, '0', STR_PAD_LEFT) ?></span><div><h2><?= e($step[0]) ?></h2><p><?= e($step[1]) ?></p></div></article><?php endforeach; ?></div></section>
<section class="section methodology-note"><div class="shell narrow"><h2>Corrections and updates</h2><p>Clear mistakes should be corrected, not hidden. Guide pages show an update date, and material changes should be reflected in the content rather than only changing the timestamp.</p><a class="button" href="/contact">Contact the editorial team →</a></div></section>
<?php require __DIR__ . '/includes/footer.php'; ?>
