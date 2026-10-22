(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const read = key => { try { return localStorage.getItem(key); } catch { return null; } };
  const save = (key, value) => { try { localStorage.setItem(key, value); } catch {} };
  $('#theme').addEventListener('click', () => {
    const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = theme; save('de-theme', theme);
  });
  let size = Math.max(14, Math.min(26, Number(read('de-size')) || 18));
  document.documentElement.style.setProperty('--reader-size', `${size}px`);
  for (const [id, change] of [['smaller', -1], ['larger', 1]]) {
    $(`#${id}`).addEventListener('click', () => {
      size = Math.max(14, Math.min(26, size + change));
      document.documentElement.style.setProperty('--reader-size', `${size}px`); save('de-size', size);
    });
  }
  document.querySelectorAll('article table').forEach(table => {
    const wrap = document.createElement('div'); wrap.className = 'table-wrap';
    table.before(wrap); wrap.append(table);
  });
  document.querySelectorAll('.codehilite').forEach(block => {
    const btn = document.createElement('button'); btn.className = 'copy-code'; btn.textContent = '复制';
    btn.setAttribute('aria-label', '复制此代码块');
    btn.addEventListener('click', async () => {
      const code = block.querySelector('code') || block.querySelector('pre');
      try {
        await navigator.clipboard.writeText(code.textContent);
        btn.textContent = '已复制';
      } catch {
        const selection = window.getSelection(); const range = document.createRange();
        range.selectNodeContents(code); selection.removeAllRanges(); selection.addRange(range);
        btn.textContent = '请按 Ctrl/Cmd+C';
      }
      setTimeout(() => btn.textContent = '复制', 2200);
    });
    block.append(btn);
  });
  let previous;
  try { previous = JSON.parse(read('de-progress') || 'null'); } catch {}
  const chapter = Number(document.body.dataset.chapter);
  if ($('#resume') && previous && previous.chapter >= 1 && previous.chapter <= Number(document.body.dataset.count)) {
    $('#resume').hidden = false; $('#resume').href = `chapter-${String(previous.chapter).padStart(2, '0')}.html`;
    $('#resume').textContent = `继续第 ${previous.chapter} 章 · ${Math.round((previous.ratio || 0) * 100)}% →`;
  }
  let restoring = true;
  if (chapter) {
    const storePosition = () => {
      if (restoring) return;
      const total = document.documentElement.scrollHeight - innerHeight;
      const ratio = total > 0 ? Math.min(1, Math.max(0, scrollY / total)) : 0;
      $('#progress').style.width = `${ratio * 100}%`;
      save('de-progress', JSON.stringify({ chapter, ratio }));
    };
    const restore = () => {
      if (!location.hash && previous?.chapter === chapter && Number.isFinite(previous.ratio)) {
        const max = document.documentElement.scrollHeight - innerHeight;
        window.scrollTo({ top: max * Math.max(0, Math.min(1, previous.ratio)), behavior: 'instant' });
      }
      restoring = false; storePosition();
    };
    if (document.readyState === 'complete') restore(); else window.addEventListener('load', restore, { once: true });
    let timer;
    window.addEventListener('scroll', () => { clearTimeout(timer); timer = setTimeout(storePosition, 150); }, { passive: true });
    window.addEventListener('pagehide', storePosition);
  }
  const dialog = $('#search-dialog'), input = $('#query'), results = $('#search-results'), status = $('#search-status');
  let index, loading;
  const loadIndex = () => {
    if (index) return Promise.resolve(index);
    if (!loading) loading = fetch('search.json').then(r => { if (!r.ok) throw Error('Search index unavailable'); return r.json(); }).then(data => index = data).catch(e => { loading = null; throw e; });
    return loading;
  };
  const openSearch = () => { dialog.showModal(); input.focus(); };
  $('#search-open').addEventListener('click', openSearch);
  $('#search-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', e => { if (e.target === dialog && (e.clientX < dialog.getBoundingClientRect().left || e.clientX > dialog.getBoundingClientRect().right || e.clientY < dialog.getBoundingClientRect().top || e.clientY > dialog.getBoundingClientRect().bottom)) dialog.close(); });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && dialog.open) { e.preventDefault(); dialog.close(); return; }
    if (e.key === '/' && !dialog.open && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName) && !document.activeElement.isContentEditable) { e.preventDefault(); openSearch(); }
  });
  let queryVersion = 0;
  input.addEventListener('input', async () => {
    const version = ++queryVersion, q = input.value.trim().toLowerCase(); results.replaceChildren();
    if (!q) { status.textContent = `输入关键词，搜索 ${document.body.dataset.count} 章内容`; return; }
    status.textContent = '正在搜索…';
    try {
      const entries = await loadIndex(); if (version !== queryVersion) return;
      const matches = entries.filter(e => `${e.title} ${e.section} ${e.text}`.toLowerCase().includes(q));
      status.textContent = matches.length ? `找到 ${matches.length} 处结果${matches.length > 60 ? '，显示前 60 处' : ''}` : '没有找到匹配内容，试试其他关键词。';
      for (const item of matches.slice(0, 60)) {
        const link = document.createElement('a'); link.href = item.url; link.className = 'search-result';
        const small = document.createElement('small'); small.textContent = `第 ${item.chapter} 章 · ${item.title}`;
        const title = document.createElement('strong'); title.textContent = item.section;
        const snippet = document.createElement('p'); const pos = item.text.toLowerCase().indexOf(q);
        const start = Math.max(0, pos - 40); const excerpt = item.text.slice(start, start + 160);
        const at = excerpt.toLowerCase().indexOf(q);
        if (at >= 0) { snippet.append(document.createTextNode((start ? '…' : '') + excerpt.slice(0, at))); const mark = document.createElement('mark'); mark.textContent = excerpt.slice(at, at + q.length); snippet.append(mark, document.createTextNode(excerpt.slice(at + q.length) + '…')); }
        else snippet.textContent = excerpt + '…';
        link.append(small, title, snippet); results.append(link);
      }
    } catch { if (version === queryVersion) status.textContent = '搜索索引加载失败，请检查连接后重新输入。'; }
  });
})();

// Keep external illustrations resilient without blocking the text.
document.querySelectorAll('article img').forEach(img=>{img.loading='lazy'; img.decoding='async'; img.addEventListener('error',()=>{const note=document.createElement('p');note.className='image-fallback';note.textContent='场景图片暂时无法加载，正文可继续阅读。';img.replaceWith(note);},{once:true});});

document.querySelectorAll('article pre').forEach(pre=>{pre.tabIndex=0;pre.setAttribute('aria-label','代码或结构示意，可横向滚动查看');});
