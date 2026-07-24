(() => {
    const navToggle = document.querySelector('[data-nav-toggle]');
    const nav = document.querySelector('[data-nav]');

    if (navToggle && nav) {
        navToggle.addEventListener('click', () => {
            const open = navToggle.getAttribute('aria-expanded') === 'true';
            navToggle.setAttribute('aria-expanded', String(!open));
            nav.classList.toggle('is-open', !open);
            document.body.classList.toggle('nav-open', !open);
        });

        nav.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                navToggle.setAttribute('aria-expanded', 'false');
                nav.classList.remove('is-open');
                document.body.classList.remove('nav-open');
            });
        });
    }

    document.querySelectorAll('[data-filter-scope]').forEach((scope) => {
        const buttons = Array.from(scope.querySelectorAll('[data-filter]'));
        const items = Array.from(scope.querySelectorAll('[data-category]'));
        const empty = scope.querySelector('[data-filter-empty]');
        if (!buttons.length || !items.length) return;

        buttons.forEach((button) => {
            button.addEventListener('click', () => {
                const filter = button.dataset.filter || 'all';
                buttons.forEach((candidate) => candidate.classList.toggle('is-active', candidate === button));
                let visible = 0;
                items.forEach((item) => {
                    const matches = filter === 'all' || item.dataset.category === filter;
                    item.hidden = !matches;
                    if (matches) visible += 1;
                });
                if (empty) empty.hidden = visible !== 0;
            });
        });
    });

    const header = document.querySelector('[data-header]');
    if (header) {
        const updateHeader = () => header.classList.toggle('is-scrolled', window.scrollY > 16);
        updateHeader();
        window.addEventListener('scroll', updateHeader, { passive: true });
    }

    document.querySelectorAll('.guide-progress a').forEach((link) => {
        link.addEventListener('click', (event) => {
            const target = document.querySelector(link.getAttribute('href'));
            if (!target) return;
            event.preventDefault();
            target.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
            history.replaceState(null, '', link.getAttribute('href'));
        });
    });
})();
