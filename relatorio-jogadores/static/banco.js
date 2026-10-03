/* banco.js — onde o Relatório Jogadores guarda tudo: Firestore do projeto ranking-botafogo (etapa 2 do site
   online, 02/10/2026). Mesmo banco e mesma regra do Ranking: SEM login, quem tem o link vê e edita
   (decisão do Henrique). As regras publicadas liberam só a coleção `selecionados` (doc por doc, sem
   subcoleção) — por isso, como o Comparativo da web, tudo mora em docs `selecionados/_rj_*`:
     _rj_lista          {itens: {<slug>: {nome, linha, sigla, atualizado, foto, escudo, apagado}}}  (miniaturas)
     _rj_rel_<slug>     {dados: "<JSON do relatório>", atualizado}
     _rj_img_<id>       {dados: "data:image/...;base64,...", tipo}  (uma imagem por doc, < 1 MB)
     _rj_bkp_<slug>_<AAAAMMDD>  cópia do dia: o relatório como estava ANTES da 1ª gravação do dia (guarda 7 dias);
     _rj_bkp_<slug>_antes       a versão que foi substituída por uma restauração ou por um "gravar por cima"
     _rj_lixo           {itens: {<id da imagem>: quando saiu}}  imagem trocada só some do banco depois de 8 dias
   No relatório a imagem é "fs:<id>". Deletar = marcar apagado na lista (o relatório fica, dá para voltar).
   Duas pessoas no mesmo relatório: gravar confere a versão do banco (campo `atualizado`); se outra pessoa
   gravou depois que esta página abriu o relatório, dá erro com code "conflito" e a página pergunta. */
(function () {
  const FB_CONFIG = {apiKey: 'AIzaSyAvMa3JgXBRGK0_i9FVNDIYnKT9QQDdGyg', authDomain: 'ranking-botafogo.firebaseapp.com',
    projectId: 'ranking-botafogo', storageBucket: 'ranking-botafogo.firebasestorage.app',
    messagingSenderId: '1011863859152', appId: '1:1011863859152:web:d076d80a656c831c4c13d5'};
  const COL = 'selecionados', LISTA = '_rj_lista', LIXO = '_rj_lixo', LIMITE = 950000;   // bytes do texto da imagem (o doc tem teto de 1 MiB)
  const GUARDA = 7, DIAS_LIXO = 8;   // cópias diárias guardadas por relatório; dias que a imagem trocada ainda fica no banco
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
  const FV = () => firebase.firestore.FieldValue;
  const hoje = () => { const d = new Date(); return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`; };
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
  // imagem trocada ou tirada: não some na hora (as cópias diárias ainda podem usar). Vai para a lixeira de
  // imagens e sai do banco depois de 8 dias (limparLixo).
  async function apagarImagem(ref) {
    if (!/^fs:/.test(ref || '')) return;
    try { await doc(LIXO).set({itens: {[ref.slice(3)]: Date.now()}}, {merge: true}); } catch (e) { console.warn('lixeira de imagens', e); }
  }
  let lixoVisto = false;
  async function limparLixo() {   // uma vez por página aberta
    if (lixoVisto) return; lixoVisto = true;
    try {
      const s = await doc(LIXO).get(), it = (s.exists && s.data().itens) || {}, corte = Date.now() - DIAS_LIXO * 864e5;
      const velhas = Object.entries(it).filter(([, t]) => t < corte).map(([id]) => id).slice(0, 40);
      if (!velhas.length) return;
      await Promise.all(velhas.map(id => doc('_rj_img_' + id).delete().catch(() => {})));
      await doc(LIXO).set({itens: Object.fromEntries(velhas.map(id => [id, FV().delete()]))}, {merge: true});
    } catch (e) { console.warn('limpar lixeira de imagens', e); }
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
  let itensLista = {};             // a lista como veio do banco na última leitura (com os apagados)
  const cartao = ([slug, m]) => ({slug, nome: m.nome || slug, linha: m.linha || '', sigla: m.sigla || '', foto: m.foto || '', escudo: m.escudo || '',
    wy: m.wy ?? null, tm: m.tm ?? null, _ts: m.atualizado || 0, atualizado: m.atualizado ? quando(m.atualizado) : '',
    apagadoEm: m.apagado ? quando(m.apagado) : '', _apagado: m.apagado || 0});
  async function listar() {
    const s = await doc(LISTA).get();
    itensLista = (s.exists && s.data().itens) || {};
    return Object.entries(itensLista).filter(([, m]) => !m.apagado).map(cartao).sort((a, b) => b._ts - a._ts);
  }
  // os deletados (da última leitura da lista), o apagado por último primeiro
  const apagados = () => Object.entries(itensLista).filter(([, m]) => m.apagado).map(cartao).sort((a, b) => b._apagado - a._apagado);
  async function restaurar(slug) { await doc(LISTA).set({itens: {[slug]: {apagado: false}}}, {merge: true}); }

  /* ── duas pessoas no mesmo relatório ── */
  const versoes = {}, minhas = new Set();   // slug -> o "atualizado" que esta página conhece; minhas = gravações desta página
  async function ler(slug) {
    const s = await doc('_rj_rel_' + slug).get();
    if (!s.exists) throw new Error('relatório não encontrado: ' + slug);
    const R = JSON.parse(s.data().dados);
    if (!R || typeof R !== 'object' || Array.isArray(R)) throw new Error('o relatório está vazio no banco: ' + slug);
    versoes[slug] = s.data().atualizado || 0;
    await carregarImagens(R);
    return R;
  }
  // avisa (fn) quando OUTRA pessoa grava o relatório aberto; devolve a função que para de vigiar
  function vigiar(slug, fn) {
    const ref = doc('_rj_rel_' + slug);
    if (!ref.onSnapshot) return () => {};
    return ref.onSnapshot(s => {
      if (!s.exists || (s.metadata && s.metadata.hasPendingWrites)) return;
      const t = s.data().atualizado || 0;
      if (t && t !== versoes[slug] && !minhas.has(t)) fn(t, quando(t));
    }, () => {});
  }

  /* ── cópias de segurança ── */
  const copiado = {};              // slug -> dia em que esta página já conferiu a cópia do dia
  async function guardarCopia(slug, chave, d) {   // chave = dia (AAAAMMDD) ou "antes"
    await doc(`_rj_bkp_${slug}_${chave}`).set({dados: d.dados, atualizado: d.atualizado || 0, copiado: Date.now()});
    await doc(LISTA).set({itens: {[slug]: {copias: {[chave]: d.atualizado || 0}}}}, {merge: true});
  }
  // na 1ª gravação do dia, guarda o relatório como estava antes dela; fica com as 7 cópias mais novas
  async function copiaDoDia(slug, antes) {
    const dia = hoje(); if (copiado[slug] === dia) return;
    if (!antes || !antes.dados) { copiado[slug] = dia; return; }   // relatório novo: ainda não há o que guardar
    const s = await doc(LISTA).get(), cop = (((s.exists && s.data().itens) || {})[slug] || {}).copias || {};
    copiado[slug] = dia;
    if (cop[dia] != null) return;                                  // outra pessoa (ou outra aba) já guardou a de hoje
    await guardarCopia(slug, dia, antes);
    const dias = Object.keys(cop).filter(k => /^\d{8}$/.test(k)).concat(dia).sort(), sobra = dias.slice(0, Math.max(0, dias.length - GUARDA));
    if (sobra.length) {
      await Promise.all(sobra.map(k => doc(`_rj_bkp_${slug}_${k}`).delete().catch(() => {})));
      await doc(LISTA).set({itens: {[slug]: {copias: Object.fromEntries(sobra.map(k => [k, FV().delete()]))}}}, {merge: true});
    }
  }
  // guarda a versão de agora em "antes" (o ↻ Atualizar dados chama antes de mexer: dá para desfazer)
  async function guardarAntes(slug) { const a = await doc('_rj_rel_' + slug).get(); if (a.exists) await guardarCopia(slug, 'antes', a.data()); }
  async function copias(slug) {   // as cópias guardadas: "antes" primeiro, depois da mais nova para a mais velha
    const s = await doc(LISTA).get(), cop = (((s.exists && s.data().itens) || {})[slug] || {}).copias || {};
    return Object.entries(cop).map(([chave, ts]) => ({chave, ts, quando: ts ? quando(ts) : '',
        dia: /^\d{8}$/.test(chave) ? `${chave.slice(6)}/${chave.slice(4, 6)}/${chave.slice(0, 4)}` : ''}))
      .sort((a, b) => (b.chave === 'antes') - (a.chave === 'antes') || b.chave.localeCompare(a.chave));
  }
  // põe a cópia no lugar do relatório. A versão de agora vai para "antes" (dá para desfazer restaurando o "antes").
  async function restaurarCopia(slug, chave) {
    const c = await doc(`_rj_bkp_${slug}_${chave}`).get();
    if (!c.exists) throw new Error('cópia não encontrada');
    const R = JSON.parse(c.data().dados);
    if (!R || typeof R !== 'object' || Array.isArray(R)) throw new Error('a cópia está vazia');
    const atual = await doc('_rj_rel_' + slug).get();
    if (atual.exists) await guardarCopia(slug, 'antes', atual.data());
    await carregarImagens(R);
    const usadas = [...refs(R)].map(r => r.slice(3));   // as imagens da cópia voltaram a valer: saem da lixeira
    if (usadas.length) await doc(LIXO).set({itens: Object.fromEntries(usadas.map(id => [id, FV().delete()]))}, {merge: true}).catch(() => {});
    await gravar(slug, R, {forcar: true});
    return R;
  }
  const miniCache = {};            // slug -> {foto_ref, foto, escudo_ref, escudo}
  async function gravar(slug, R, op = {}) {   // op.forcar = grava mesmo que outra pessoa tenha gravado depois
    // trava de segurança: nunca grava "vazio" por cima de um relatório
    if (!slug || !R || typeof R !== 'object' || Array.isArray(R)) throw new Error('nada para gravar (relatório vazio)');
    const texto = JSON.stringify(R), bytes = new Blob([texto]).size;   // o teto do banco é em bytes (letra com acento pesa 2)
    if (bytes > 1000000) throw new Error('relatório grande demais para o banco (' + Math.round(bytes / 1024) + ' KB)');
    const agora = Date.now(), ref = doc('_rj_rel_' + slug), conhecida = versoes[slug];
    let antes = null;
    minhas.add(agora);
    await banco().runTransaction(async tx => {
      const s = await tx.get(ref); antes = s.exists ? s.data() : null;
      const noBanco = antes ? (antes.atualizado || 0) : 0;
      if (!op.forcar && conhecida != null && noBanco !== conhecida)
        throw Object.assign(new Error('outra pessoa alterou este relatório' + (noBanco ? ' (' + quando(noBanco) + ')' : '')), {code: 'conflito', quando: noBanco});
      tx.set(ref, {dados: texto, atualizado: agora});
    });
    versoes[slug] = agora;
    try {   // cópias: nunca atrapalham a gravação
      if (op.forcar && antes && conhecida != null && (antes.atualizado || 0) !== conhecida) await guardarCopia(slug, 'antes', antes);   // gravou por cima do de outra pessoa: o dela fica guardado
      await copiaDoDia(slug, antes);
    } catch (e) { console.warn('cópia de segurança', e); }
    const mc = miniCache[slug] = miniCache[slug] || {};
    const foto = R.img?.foto || '', escudo = R.img?.escudo || '';
    if (mc.foto_ref !== foto) { mc.foto_ref = foto; mc.foto = await miniatura(foto, 96); }
    if (mc.escudo_ref !== escudo) { mc.escudo_ref = escudo; mc.escudo = await miniatura(escudo, 40); }
    await doc(LISTA).set({itens: {[slug]: {nome: R.nome || slug, linha: R.linha || '', sigla: R.sigla || '', atualizado: agora,
      foto: mc.foto || '', escudo: mc.escudo || '', apagado: false,
      wy: R.fontes?.wy_id ?? null, tm: R.fontes?.tm_id != null ? String(R.fontes.tm_id) : null}}}, {merge: true});   // wy/tm: o Novo atleta avisa se o jogador já tem relatório
    limparLixo();
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

  window.Banco = {listar, apagados, restaurar, ler, gravar, novo, apagar, guardarImagem, apagarImagem, carregarImagens, url, slugify,
    vigiar, copias, restaurarCopia, guardarAntes, quando};
})();
