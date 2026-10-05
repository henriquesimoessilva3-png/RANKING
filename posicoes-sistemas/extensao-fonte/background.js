// BFR Wyscout — ponte entre o app "Posições e Sistemas" e o Wyscout já logado neste Chrome.
// 1.2.0 (02/10/2026): volta a ser SÓ do Posições e Sistemas. O pré/pós-jogo foi para a extensão
// "BFR Wyscout — Relatório Pré e Pós-jogo" e o Relatório do Atleta para a "BFR Relatório Jogador".
// O app pede (pesquisar jogador / extrair levantamento); a extensão usa a aba do Wyscout
// para fazer as mesmas consultas que as telas do Wyscout fazem. Não guarda senha nem dados.
const VERSAO = '1.2.1';
const WY = 'https://wyscout.hudl.com/app/';
const dorme = (ms) => new Promise((r) => setTimeout(r, ms));
let ABA_CRIADA = null; // aba do Wyscout que a extensão abriu (fecha ao terminar o levantamento)

/* ── funções injetadas na página do Wyscout (rodam lá, com o login de quem usa) ── */
function pgLogado() { return !!(window.uidirectives && window.uidirectives.access_key); }
async function pgApi(caminho, params) {
  const tok = window.uidirectives && window.uidirectives.access_key;
  if (!tok) return { __erro: 'login' };
  const qs = Object.entries({ lang: 'pt', score: 'winning,draw,losing', venue: 'home,away', ...params, token: tok })
    .map(([k, v]) => k + '=' + encodeURIComponent(v)).join('&');
  for (let t = 0; t < 3; t++) {
    try {
      const r = await fetch('https://searchapi.wyscout.com/api/v1' + caminho + '?' + qs);
      if (r.ok) {
        const j = await r.json();
        // A resposta volta para a extensão com as chaves em ordem alfabética; a ORDEM das formações importa
        // (a primeira é a inicial), então ela viaja como lista.
        if (j && Array.isArray(j.matches)) return { matches: j.matches.map((m) => ({ id: m.match.id, esquemas: Object.entries((m.teamStats && m.teamStats.schemes) || {}) })) };
        return j;
      }
      if (r.status === 401 || r.status === 403) return { __erro: 'login' };
    } catch (e) { /* tenta de novo */ }
    await new Promise((ok) => setTimeout(ok, 800 * (t + 1)));
  }
  return { __erro: 'rede' };
}
async function pgBusca(nome) {
  try {
    const body = 'query=' + encodeURIComponent(JSON.stringify({ obj: 'search', act: 'player', params: { search: nome }, navi: { component: 'global_search_player' } }));
    const r = await fetch('/app/aengine-service.php', { method: 'POST', body, headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' } });
    const j = await r.json();
    return (j.list || []).filter((x) => x.obj === 'player').map((x) => ({ id: x.objId, nome: (x.title || '').trim(), subtitulo: (x.subtitle || '').trim(), foto: x.img_url || '' }));
  } catch (e) { return { __erro: 'busca' }; }
}

/* ── aba do Wyscout ── */
async function roda(tabId, func, args = []) {
  const [r] = await chrome.scripting.executeScript({ target: { tabId }, world: 'MAIN', func, args });
  return r ? r.result : undefined;
}
async function abaWyscout(avisa) {
  let [tab] = await chrome.tabs.query({ url: 'https://wyscout.hudl.com/*' });
  let criada = false;
  if (!tab) { avisa('Abrindo o Wyscout...'); tab = await chrome.tabs.create({ url: WY, active: false }); criada = true; }
  const t0 = Date.now();
  while (Date.now() - t0 < 40000) {
    try { if (await roda(tab.id, pgLogado)) return { tab, criada }; } catch (e) { /* página ainda carregando */ }
    await dorme(1000);
    if (!criada && Date.now() - t0 > 6000) { // aba aberta em outra tela do Wyscout: recarrega no app
      try { await chrome.tabs.update(tab.id, { url: WY }); } catch (e) {} criada = true;
    }
  }
  try { await chrome.tabs.update(tab.id, { active: true }); } catch (e) {}
  const err = new Error('Faça o login no Wyscout na aba que abriu e clique de novo.'); err.code = 'login'; throw err;
}
function checa(r) {
  if (r && r.__erro === 'login') { const e = new Error('O Wyscout pediu login. Entre no Wyscout e tente de novo.'); e.code = 'login'; throw e; }
  if (!r || r.__erro) throw new Error('O Wyscout não respondeu. Tente de novo.');
  return r;
}

/* ── regras do levantamento (as mesmas validadas contra os Excel feitos à mão) ── */
// Inglaterra, Escócia, Gales e Irlanda do Norte têm área com X no Wyscout (XEN...), como as competições internacionais (1.2.2)
const LIGA_UK = /^(England|Scotland|Wales|Northern Ireland)\b/i;
const areaX = (m) => (m.competitionFlag || '')[0] === 'X' && !LIGA_UK.test(m.competition || '');
const COPA = /club|intercontinental|libertadores|sudamericana|champions league|europa league|conference league|recopa|super cup|supercopa|leagues cup|concachampions|confederation cup/i;
const BASE = /\bU-?\d{2}\b|\bRes\.?$|Reserves?\b|Youth|Sub-?\d{2}/i;
function clubePorJogo(ms) {
  return ms.map((x, i) => {
    const c = {};
    ms.slice(Math.max(0, i - 6), i + 7).forEach((y) => { c[y.match.teamAId] = (c[y.match.teamAId] || 0) + 1; c[y.match.teamBId] = (c[y.match.teamBId] || 0) + 1; });
    return (c[x.match.teamAId] || 0) >= (c[x.match.teamBId] || 0) ? { id: x.match.teamAId, nome: x.match.teamA } : { id: x.match.teamBId, nome: x.match.teamB };
  });
}
// A aba do Wyscout pode estar aberta há horas: a busca (que usa o cookie) funciona, mas o token
// da página já venceu e a API recusa. Nesse caso recarrega a aba (token novo) e tenta uma vez de novo.
async function api(tabId, caminho, params, avisa) {
  let r = await roda(tabId, pgApi, [caminho, params]);
  if (r && r.__erro === 'login') {
    avisa('Sessão antiga na aba do Wyscout. Recarregando a aba...');
    await chrome.tabs.update(tabId, { url: WY });
    await dorme(1500);
    const t0 = Date.now();
    while (Date.now() - t0 < 40000) {
      try { const t = await chrome.tabs.get(tabId); if (t.status === 'complete' && await roda(tabId, pgLogado)) break; } catch (e) {}
      await dorme(1000);
    }
    r = await roda(tabId, pgApi, [caminho, params]);
  }
  return checa(r);
}
async function extrair(tabId, playerId, avisa) {
  avisa('Baixando todos os jogos do jogador...');
  const raw = await api(tabId, '/match_stats/players/' + playerId, { from: '2010-07-01', to: '', columns: 'name,positions,minutes_on_field' }, avisa);
  const vistos = new Set(); // o Wyscout às vezes lista o mesmo jogo em duas competições
  const ms = [...raw].sort((a, b) => a.match.date.localeCompare(b.match.date) || a.match.id - b.match.id)
    .filter((x) => { const k = x.match.date + '|' + x.match.name; if (vistos.has(k)) return false; vistos.add(k); return true; });
  const cl = clubePorJogo(ms);
  const DOM = {}; ms.forEach((x, i) => { if (!areaX(x.match)) DOM[cl[i].nome] = 1; });
  const jogos = ms.map((x, i) => {
    const m = x.match, clube = cl[i].nome;
    const sem = (areaX(m) && !COPA.test(m.competition) && !DOM[clube]) ? 'Seleção' : BASE.test(clube) ? 'Reservas/base' : null;
    return {
      match_id: m.id, data: m.date, jogo: m.name, competicao: m.competition, temporada: m.seasonName, clube, clube_id: cl[i].id,
      posicoes: x.playerStats.positions || [], minutos: x.playerStats.minutes_on_field || 0, sem_base: sem,
      categoria: sem === 'Seleção' ? 'Seleção' : sem ? 'Base' : /friendl/i.test(m.competition) ? 'Amistoso' : 'Profissional',
    };
  });
  avisa(jogos.length + ' jogos na carreira. Buscando o sistema das equipes, ano a ano...');
  const pedidos = new Map(); // clube_id -> {nome, anos}
  jogos.filter((j) => !j.sem_base).forEach((j) => { const p = pedidos.get(j.clube_id) || { nome: j.clube, anos: new Set() }; p.anos.add(j.data.slice(0, 4)); pedidos.set(j.clube_id, p); });
  const esquema = {};
  for (const [cid, p] of pedidos) {
    for (const ano of [...p.anos].sort()) {
      avisa('Equipe: ' + p.nome + ' ' + ano);
      const t = await api(tabId, '/team_stats/teams/' + cid + '/stats', { from: ano + '-01-01', to: ano + '-12-31', columns: 'name,team,schemes,intervals,minutesOnField' }, avisa);
      (t.matches || []).forEach((m) => {
        const e = m.esquemas || []; if (!e.length) return;
        const top = [...e].sort((a, b) => b[1] - a[1])[0];
        // "sistema" = a primeira formação que o Wyscout registra (igual à coluna Sistema do Excel de equipe)
        esquema[cid + ':' + m.id] = { sistema: e[0][0], pct_sistema: Math.round(e[0][1] * 100) / 10000, predominante: top[0], pct_predominante: Math.round(top[1] * 100) / 10000 };
      });
    }
  }
  jogos.forEach((j) => {
    if (j.sem_base) return;
    const e = esquema[j.clube_id + ':' + j.match_id];
    if (e) Object.assign(j, e); else j.sem_base = 'Jogo ausente no arquivo da equipe';
  });
  avisa('Pronto: ' + jogos.filter((j) => j.sistema).length + ' jogos com o sistema da equipe.');
  return jogos;
}

/* ── conversa com o app ── */
chrome.runtime.onConnectExternal.addListener((port) => {
  port.onMessage.addListener(async (msg) => {
    const id = msg.id, manda = (o) => { try { port.postMessage({ id, ...o }); } catch (e) {} };
    const avisa = (texto) => manda({ log: texto });
    let fechar = null;
    try {
      if (msg.tipo === 'ping') return manda({ ok: true, versao: VERSAO });
      const { tab, criada } = await abaWyscout(avisa);
      if (criada) ABA_CRIADA = tab.id;
      if (ABA_CRIADA === tab.id) fechar = tab.id;
      if (msg.tipo === 'buscar') {
        const r = checa(await roda(tab.id, pgBusca, [String(msg.nome || '')]));
        return manda({ ok: true, jogadores: r });
      }
      if (msg.tipo === 'extrair') {
        const jogos = await extrair(tab.id, parseInt(msg.jogador_id, 10), avisa);
        return manda({ ok: true, jogos });
      }
      manda({ erro: 'Pedido desconhecido.' });
    } catch (e) {
      if (e.code === 'login') fechar = null; // deixa a aba aberta para o login
      manda({ erro: e.message || String(e), code: e.code || null });
    } finally {
      if (fechar && msg.tipo === 'extrair') { try { await chrome.tabs.remove(fechar); } catch (e) {} ABA_CRIADA = null; }
    }
  });
});
chrome.runtime.onMessageExternal.addListener((msg, _s, responde) => { if (msg && msg.tipo === 'ping') responde({ ok: true, versao: VERSAO }); });
