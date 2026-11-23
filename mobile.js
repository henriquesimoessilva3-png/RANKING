/* ==========================================================================
   Ranking BFR — ajuste para celular (só age em telas de até 820px).
   1) Menu lateral vira gaveta (botão ☰ no cabeçalho).
   2) "Encaixe": depois que cada aba desenha, acha o que passou da largura da
      tela e corrige — tabela rola de lado com a 1ª coluna presa, linhas
      quebram, grades viram 1–2 colunas, larguras fixas soltam, janelas por
      cima ocupam a tela. O site do computador não muda.
   ========================================================================== */
(function () {
  'use strict';
  var MQ = window.matchMedia('(max-width: 820px)');
  function celular() { return MQ.matches; }

  // ---------- gaveta ----------
  function montarMenu() {
    var h = document.querySelector('header.header');
    if (!h || document.getElementById('mobMenu')) return;
    var b = document.createElement('button');
    b.id = 'mobMenu'; b.type = 'button'; b.setAttribute('aria-label', 'Abrir menu'); b.innerHTML = '&#9776;';
    h.insertBefore(b, h.firstChild);
    var f = document.createElement('div'); f.id = 'mobFundo'; document.body.appendChild(f);
    var abre = function (on) { document.body.classList.toggle('mob-menu-aberto', on); };
    b.addEventListener('click', function () { abre(!document.body.classList.contains('mob-menu-aberto')); });
    f.addEventListener('click', function () { abre(false); });
    document.querySelectorAll('.sidebar .nav-item').forEach(function (it) {
      it.addEventListener('click', function () { if (celular()) { abre(false); window.scrollTo(0, 0); } });
    });
  }

  // ---------- encaixe ----------
  function rolavel(el) {
    for (var a = el.parentElement; a && a !== document.body && a !== document.documentElement; a = a.parentElement) {
      if (a.classList.contains('main') || a.classList.contains('layout')) continue;
      var ov = getComputedStyle(a).overflowX;
      if (ov === 'auto' || ov === 'scroll') return a;
    }
    return null;
  }
  function envolverTabela(t) {
    var p = t.parentElement;
    if (!p) return;
    var scr = rolavel(t);
    if (!scr) {
      var w = document.createElement('div'); w.className = 'mob-rola';
      p.insertBefore(w, t); w.appendChild(t); scr = w;
    }
    var cab = t.querySelector('tr'); var n = cab ? cab.children.length : 0;
    if (n >= 5 && !t.classList.contains('mob-fixa-1')) {
      // prende a coluna do nome: se a 1ª coluna é só número/posição (#), prende as duas primeiras
      var c1 = (cab.children[0].textContent || '').trim();
      t.classList.add(c1.length <= 3 ? 'mob-fixa-2' : 'mob-fixa-1');
      if (c1.length <= 3) {
        var larg = cab.children[0].getBoundingClientRect().width;
        t.querySelectorAll('tr > :nth-child(2)').forEach(function (c) { c.style.left = larg + 'px'; });
      }
    }
  }
  function encaixar(raiz) {
    if (!celular() || !raiz) return;
    var W = document.documentElement.clientWidth;
    for (var volta = 0; volta < 4; volta++) {
      var mudou = false;
      var todos = raiz.querySelectorAll('*');
      for (var i = 0; i < todos.length; i++) {
        var e = todos[i];
        if (e.closest('.mob-rola') && e.tagName !== 'TABLE') continue;
        var r = e.getBoundingClientRect();
        if (!r.width || r.right <= W + 2) continue;
        if (rolavel(e) && e.tagName !== 'TABLE') continue;
        var tag = e.tagName;
        if (tag === 'TABLE') { if (!e.closest('.mob-rola') && !rolavel(e)) { envolverTabela(e); mudou = true; } else envolverTabela(e); continue; }
        if (tag === 'TBODY' || tag === 'THEAD' || tag === 'TR' || tag === 'TD' || tag === 'TH') continue;
        if (tag === 'svg' || tag === 'CANVAS' || tag === 'IMG') { e.style.maxWidth = '100%'; e.style.height = 'auto'; mudou = true; continue; }
        var cs = getComputedStyle(e);
        if (cs.display === 'inline' || cs.display === 'inline-block' && r.width < 160) continue;
        if (cs.display.indexOf('flex') >= 0 && cs.flexWrap === 'nowrap' && cs.flexDirection.indexOf('row') === 0 && e.children.length > 1) {
          e.classList.add('mob-quebra'); mudou = true; continue;
        }
        if (cs.display.indexOf('grid') >= 0 && !e.classList.contains('mob-uma-col')) {
          var cols = cs.gridTemplateColumns.split(' ').filter(Boolean).length;
          if (cols >= 2) { e.classList.add('mob-uma-col'); mudou = true; continue; }
        }
        if (!e.classList.contains('mob-larg') && (r.left >= -2 || e.style.width || e.style.minWidth)) {
          e.classList.add('mob-larg'); mudou = true;
        }
      }
      if (!mudou) break;
    }
    // grades de 3+ colunas apertadas demais (colunas com menos de 140px) viram 1–2 colunas
    raiz.querySelectorAll('*').forEach(function (e) {
      if (e.classList.contains('mob-uma-col') || e.closest('.mob-rola')) return;
      var cs = getComputedStyle(e);
      if (cs.display.indexOf('grid') < 0) return;
      var cols = cs.gridTemplateColumns.split(' ').filter(Boolean);
      if (cols.length < 3) return;
      var med = cols.reduce(function (s, c) { return s + (parseFloat(c) || 0); }, 0) / cols.length;
      if (med && med < 140 && e.children.length >= 3 && e.querySelector('table, .card, [class*="card"]')) e.classList.add('mob-uma-col');
    });
    // janelas por cima (position: fixed) maiores que a tela
    document.querySelectorAll('body > *').forEach(function (e) {
      if (e.id === 'mobFundo' || e.classList.contains('sidebar')) return;
      var cs = getComputedStyle(e);
      if (cs.position !== 'fixed' || cs.display === 'none') return;
      var box = e.firstElementChild && e.getBoundingClientRect().width >= W - 4 ? e.firstElementChild : e;
      var r = box.getBoundingClientRect();
      if (r.width > W - 8 || r.height > window.innerHeight) box.classList.add('mob-modal');
    });
  }
  function secaoAtiva() {
    var s = document.querySelectorAll('.section.active');
    return s.length ? s : [document.querySelector('.main')];
  }
  var pendente = null;
  function agendar() {
    if (!celular()) return;
    clearTimeout(pendente);
    pendente = setTimeout(function () {
      montarFiltros();
      secaoAtiva().forEach(encaixar);
      encaixar(document.body.querySelector(':scope > [style*="position: fixed"], :scope > [style*="position:fixed"]'));
    }, 180);
  }

  // ---------- filtros recolhíveis: o campinho fica, o resto abre num botão ----------
  function montarFiltros() {
    if (!celular()) return;
    document.querySelectorAll('.filter-layout').forEach(function (fl) {
      if (fl.dataset.mobFiltros) return;
      var col = fl.querySelector('.filters-col'); if (!col) return;
      fl.dataset.mobFiltros = '1';
      fl.classList.add('mob-filtros-fechado');
      var b = document.createElement('button'); b.type = 'button'; b.className = 'mob-filtros-btn';
      var txt = function () { b.innerHTML = (fl.classList.contains('mob-filtros-fechado') ? 'Mostrar filtros' : 'Esconder filtros') + ' <span>' + (fl.classList.contains('mob-filtros-fechado') ? '&#9662;' : '&#9652;') + '</span>'; };
      b.addEventListener('click', function () { fl.classList.toggle('mob-filtros-fechado'); txt(); agendar(); });
      txt();
      fl.insertBefore(b, col);
    });
  }

  function iniciar() {
    montarMenu();
    montarFiltros();
    var obs = new MutationObserver(agendar);
    obs.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'style'] });
    window.addEventListener('resize', agendar);
    agendar();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
