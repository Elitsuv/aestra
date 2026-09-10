document.addEventListener('DOMContentLoaded', () => {
  route();
  tabs();
  copy();
  commits();
});

/* ═══ ROUTING ═══ */
function route() {
  const links = document.querySelectorAll('.sl');
  const pages = document.querySelectorAll('.pg');

  function go(id) {
    pages.forEach(p => p.classList.remove('on'));
    links.forEach(l => l.classList.remove('on'));
    const pg = document.getElementById(id) || document.getElementById('overview');
    const ln = document.querySelector(`.sl[href="#${id}"]`) || links[0];
    if (pg) pg.classList.add('on');
    if (ln) ln.classList.add('on');
    window.scrollTo({ top: 0, behavior: 'instant' });
    buildToc(pg);
  }

  go(location.hash.slice(1) || 'overview');
  window.addEventListener('hashchange', () => go(location.hash.slice(1) || 'overview'));
}

/* ═══ RIGHT TOC + SCROLL SPY ═══ */
function buildToc(page) {
  const tocList = document.getElementById('toc-list');
  const toc = document.getElementById('toc');
  if (!tocList || !toc || !page) return;

  const headings = page.querySelectorAll('h2[data-toc]');
  tocList.innerHTML = '';

  if (headings.length === 0) {
    toc.style.display = 'none';
    return;
  }

  toc.style.display = '';

  headings.forEach((h, i) => {
    const id = 'toc-' + page.id + '-' + i;
    h.id = id;

    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = '#' + id;
    a.textContent = h.textContent;
    a.addEventListener('click', (e) => {
      e.preventDefault();
      h.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    li.appendChild(a);
    tocList.appendChild(li);
  });

  // Scroll spy
  if (window._tocObserver) window._tocObserver.disconnect();

  const tocLinks = tocList.querySelectorAll('a');

  window._tocObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        tocLinks.forEach(l => l.classList.remove('on'));
        const match = tocList.querySelector(`a[href="#${entry.target.id}"]`);
        if (match) match.classList.add('on');
      }
    });
  }, {
    rootMargin: '-80px 0px -60% 0px',
    threshold: 0
  });

  headings.forEach(h => window._tocObserver.observe(h));

  // Activate first by default
  if (tocLinks.length > 0) tocLinks[0].classList.add('on');
}

/* ═══ TABS ═══ */
function tabs() {
  document.querySelectorAll('.tab-t').forEach(btn => {
    btn.addEventListener('click', () => {
      const wrap = btn.closest('.tabs');
      wrap.querySelectorAll('.tab-t').forEach(b => b.classList.remove('on'));
      wrap.querySelectorAll('.tab-p').forEach(p => p.classList.remove('on'));
      btn.classList.add('on');
      const panel = wrap.querySelector('#' + btn.dataset.tab);
      if (panel) panel.classList.add('on');
    });
  });
}

/* ═══ COPY ═══ */
function copy() {
  document.querySelectorAll('.cb-copy').forEach(btn => {
    btn.addEventListener('click', async () => {
      const el = document.getElementById(btn.dataset.target);
      if (!el) return;
      try {
        await navigator.clipboard.writeText(el.innerText.trim());
        const original = btn.innerHTML;
        btn.innerHTML = '<i data-lucide="check" stroke-width="1.8"></i> Copied';
        if (typeof lucide !== 'undefined') lucide.createIcons({ nodes: [btn] });
        setTimeout(() => {
          btn.innerHTML = original;
          if (typeof lucide !== 'undefined') lucide.createIcons({ nodes: [btn] });
        }, 1500);
      } catch (e) { /* clipboard unavailable */ }
    });
  });
}

/* ═══ COMMITS & SECURITY ═══ */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function commits() {
  const el = document.getElementById('commits');
  if (!el) return;
  try {
    const r = await fetch('https://api.github.com/repos/Elitsuv/aestra/commits?per_page=10');
    if (!r.ok) throw 0;
    const data = await r.json();
    el.innerHTML = data.map(c => {
      const rawMsg = c && c.commit && c.commit.message ? c.commit.message.split('\n')[0] : '';
      const msg = escapeHtml(rawMsg);
      const sha = escapeHtml((c.sha || '').substring(0, 7));
      const rawUrl = String(c.html_url || '');
      const safeUrl = rawUrl.startsWith('https://github.com/') ? rawUrl : 'https://github.com/Elitsuv/aestra';
      const d = c.commit && c.commit.author && c.commit.author.date
        ? new Date(c.commit.author.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
        : '';
      return `<div style="display:flex;align-items:baseline;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--border);font-size:13px">
        <div style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
          <a href="${safeUrl}" target="_blank" rel="noopener noreferrer" style="font-family:var(--mono);font-size:12px;color:var(--blue);margin-right:8px">${sha}</a>
          <span style="color:var(--t2)">${msg}</span>
        </div>
        <span style="color:var(--t4);font-size:11px;white-space:nowrap;margin-left:12px">${escapeHtml(d)}</span>
      </div>`;
    }).join('');
  } catch {
    el.innerHTML = `<p style="color:var(--t4);font-size:13px">See <a href="https://github.com/Elitsuv/aestra/commits" target="_blank" rel="noopener noreferrer" style="color:var(--blue)">commits on GitHub</a>.</p>`;
  }
}
