# What 10 Things

Production source for [what10things.co.uk](https://what10things.co.uk).

## What is included

- Fast, database-free PHP site suitable for GoDaddy shared hosting
- Ten complete launch guides, each with exactly ten actionable items
- Category pages, destination discovery and server-rendered search
- Clean URLs through `.htaccess`
- Responsive, accessible design with reduced-motion support
- Legal, privacy, methodology and affiliate-disclosure pages
- Sitemap, robots file, web manifest and local SVG brand assets
- GitHub Actions validation and FTPS deployment

## Local development

```bash
php -S 127.0.0.1:8080 router.php
```

Open `http://127.0.0.1:8080`.

Run validation:

```bash
find . -type f -name '*.php' -not -path './.git/*' -print0 | xargs -0 -n1 php -l
php tests/validate.php
```

## GoDaddy deployment

The workflow `.github/workflows/deploy.yml` runs on every push to `main`.

Create these repository secrets:

- `FTP_SERVER` — GoDaddy FTP hostname, for example `ftp.what10things.co.uk`
- `FTP_USERNAME` — the FTP account restricted to the What 10 Things document root
- `FTP_PASSWORD` — FTP account password
- `FTP_SERVER_DIR` — use `./` when the FTP account opens directly in `public_html/what10things.co.uk`

The workflow uses explicit FTPS on port 21 and does not delete production-only files.

## Content editing

Guides, categories and destinations are stored in `data/site.php`. Each guide must have exactly ten items; the validation script prevents incomplete lists from deploying.
