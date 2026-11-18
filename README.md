# What 10 Things

Production source for [what10things.co.uk](https://what10things.co.uk).

## Other Urban Sky Web projects

- [Urban Sky Web Ltd](https://urbanskyweb.co.uk/) — Company website
- [Mainbuyer](https://mainbuyer.com/) — Product comparisons
- [MyPHU](https://myphu.com/) — Health information
- [1V14](https://1v14.com/) — Tools for creators
- [4TU8](https://4tu8.com/) — Web design for businesses
- [PremisesPulse](https://premisespulse.com/) — Local-authority change monitoring
- [EFL by Level](https://englishasaforeignlanguage.com/) — English learning and teaching resources
- [Exterior Wall Cladding](https://exteriorwallcladding.com/) — Exterior wall cladding information

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
