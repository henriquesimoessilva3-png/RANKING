/* banco.js — onde o Relatório Jogadores guarda tudo: Firestore do projeto ranking-botafogo (etapa 2 do site
   online, 02/10/2026). Mesmo banco e mesma regra do Ranking: SEM login, quem tem o link vê e edita
   (decisão do Henrique). As regras publicadas liberam só a coleção `selecionados` (doc por doc, sem
   subcoleção) — por isso, como o Comparativo da web, tudo mora em docs `selecionados/_rj_*`:
     _rj_lista          {itens: {<slug>: {nome, linha, sigla, atualizado, foto, escudo, apagado}}}  (miniaturas)
     _rj_rel_<slug>     {dados: "<JSON do relatório>", atualizado}
     _rj_img_<id>       {dados: "data:image/...;base64,...", tipo}  (uma imagem por doc, < 1 MB)
   No relatório a imagem é "fs:<id>". Deletar = marcar apagado na lista (o relatório fica, dá para voltar). */
(function () {
  const FB_CONFIG = {apiKey: 'AIzaSyAvMa3JgXBRGK0_i9FVNDIYnKT9QQDdGyg', authDomain: 'ranking-botafogo.firebaseapp.com',
    projectId: 'ranking-botafogo', storageBucket: 'ranking-botafogo.firebasestorage.app',
    messagingSenderId: '1011863859152', appId: '1:1011863859152:web:d076d80a656c831c4c13d5'};
  const COL = 'selecionados', LISTA = '_rj_lista', LIMITE = 950000;   // bytes do texto da imagem (o doc tem teto de 1 MiB)
  let db = null;
  function banco() {
    if (db) return db;
    if (typeof firebase === 'undefined' || !firebase.firestore) throw new Error('Firebase não carregou (sem internet?)');
    if (!firebase.apps.length) firebase.initializeApp(FB_CONFIG);
    db = firebase.firestore();
    return db;
  }
  const doc = id => banco().collection(COL).doc(id);
  const slugify = s => (String(s).normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'sem_nome').slice(0, 60);
  const quando = ms => new Date(ms).toLocaleString('pt-BR', {day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'}).replace(',', '');

  /* ── imagens ── */
  const urls = new Map();          // "fs:<id>" -> object URL (já baixada nesta página)
  const blobDeDataURL = d => fetch(d).then(r => r.blob());
  const lerBlob = b => new Promise((ok, er) => { const f = new FileReader(); f.onload = () => ok(f.result); f.onerror = er; f.readAsDataURL(b); });
  async function imagemDe(blob) { const u = URL.createObjectURL(blob); try { const im = new Image(); im.src = u; await im.decode(); return im; } finally { setTimeout(() => URL.revokeObjectURL(u), 0); } }
  // cabe no doc: tenta como veio; senão JPEG/WebP diminuindo qualidade e tamanho
  async function compactar(blob) {
    let d = await lerBlob(blob);
    if (d.length <= LIMITE) return d;
    const im = await imagemDe(blob);
    let w = im.naturalWidth, h = im.naturalHeight;
    for (const [esc, q] of [[1, .9], [1, .8], [.8, .82], [.65, .8], [.5, .78], [.38, .75], [.28, .72]]) {
      const c = document.createElement('canvas'); c.width = Math.round(w * esc); c.height = Math.round(h * esc);
      const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height); g.drawImage(im, 0, 0, c.width, c.height);
      d = c.toDataURL('image/jpeg', q);
      if (d.length <= LIMITE) return d;
    }
    throw new Error('imagem grande demais mesmo reduzida');
  }
  async function guardarImagem(blob, campo, slug) {
    const id = `${slug}_${String(campo).replace(/[^a-z0-9_]/gi, '_')}_${Date.now().toString(36)}`;
    const dados = await compactar(blob);
    await doc('_rj_img_' + id).set({dados, slug, campo, criado: Date.now()});
    urls.set('fs:' + id, URL.createObjectURL(await blobDeDataURL(dados)));
    return 'fs:' + id;
  }
  async function apagarImagem(ref) {
    if (!/^fs:/.test(ref || '')) return;
    try { await doc('_rj_img_' + ref.slice(3)).delete(); } catch (e) { console.warn('apagar imagem', e); }
    urls.delete(ref);
  }
  // todas as "fs:" que aparecem no relatório (img.*, mapas da folha 3...)
  function refs(o, out = new Set()) {
    if (typeof o === 'string') { if (o.startsWith('fs:')) out.add(o); }
    else if (o && typeof o === 'object') Object.values(o).forEach(v => refs(v, out));
    return out;
  }
  async function carregarImagens(R) {
    await Promise.all([...refs(R)].filter(r => !urls.has(r)).map(async r => {
      try { const s = await doc('_rj_img_' + r.slice(3)).get(); if (s.exists) urls.set(r, URL.createObjectURL(await blobDeDataURL(s.data().dados))); }
      catch (e) { console.warn('imagem', r, e); }
    }));
  }
  const url = ref => urls.get(ref) || '';
  async function miniatura(ref, lado) {
    const u = url(ref); if (!u) return '';
    const im = new Image(); im.src = u; await im.decode().catch(() => {});
    if (!im.naturalWidth) return '';
    const k = Math.min(1, lado / Math.max(im.naturalWidth, im.naturalHeight)), c = document.createElement('canvas');
    c.width = Math.round(im.naturalWidth * k); c.height = Math.round(im.naturalHeight * k);
    c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
    return c.toDataURL('image/png');
  }

  /* ── relatórios ── */
  async function listar() {
    const s = await doc(LISTA).get();
    const it = (s.exists && s.data().itens) || {};
    return Object.entries(it).filter(([, m]) => !m.apagado)
      .map(([slug, m]) => ({slug, nome: m.nome || slug, linha: m.linha || '', sigla: m.sigla || '', foto: m.foto || '', escudo: m.escudo || '',
        _ts: m.atualizado || 0, atualizado: m.atualizado ? quando(m.atualizado) : ''}))
      .sort((a, b) => b._ts - a._ts);
  }
  async function ler(slug) {
    const s = await doc('_rj_rel_' + slug).get();
    if (!s.exists) throw new Error('relatório não encontrado: ' + slug);
    const R = JSON.parse(s.data().dados);
    await carregarImagens(R);
    return R;
  }
  const miniCache = {};            // slug -> {foto_ref, foto, escudo_ref, escudo}
  async function gravar(slug, R) {
    const texto = JSON.stringify(R);
    if (texto.length > 1000000) throw new Error('relatório grande demais para o banco (' + Math.round(texto.length / 1024) + ' KB)');
    const agora = Date.now();
    await doc('_rj_rel_' + slug).set({dados: texto, atualizado: agora});
    const mc = miniCache[slug] = miniCache[slug] || {};
    const foto = R.img?.foto || '', escudo = R.img?.escudo || '';
    if (mc.foto_ref !== foto) { mc.foto_ref = foto; mc.foto = await miniatura(foto, 96); }
    if (mc.escudo_ref !== escudo) { mc.escudo_ref = escudo; mc.escudo = await miniatura(escudo, 40); }
    await doc(LISTA).set({itens: {[slug]: {nome: R.nome || slug, linha: R.linha || '', sigla: R.sigla || '', atualizado: agora,
      foto: mc.foto || '', escudo: mc.escudo || '', apagado: false}}}, {merge: true});
  }
  async function novo(nome, modelo) {
    const s = await doc(LISTA).get(), usados = new Set(Object.keys((s.exists && s.data().itens) || {}));
    const base = slugify(nome); let slug = base, n = 2;
    while (usados.has(slug)) slug = `${base}_${n++}`;
    await gravar(slug, modelo);
    return slug;
  }
  async function apagar(slug) {   // some da lista; o relatório e as imagens ficam no banco (dá para voltar)
    await doc(LISTA).set({itens: {[slug]: {apagado: Date.now()}}}, {merge: true});
  }

  window.Banco = {listar, ler, gravar, novo, apagar, guardarImagem, apagarImagem, carregarImagens, url, slugify};
})();
