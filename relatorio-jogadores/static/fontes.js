/* fontes.js — leitura do Transfermarkt e do ogol NO NAVEGADOR (etapa 1 do site online, 02/10/2026).
   Tradução fiel de _fonte/fontes.py. Quem busca as páginas é o "carteiro" passado em Fontes.usar():
   no site online, a extensão BFR Relatório Jogadores; no Mac do Henrique, o servidor local
   (/api/fontes/proxy). Assim a mesma leitura vale nos dois lugares.
   Regras da folha 3 (Pedro Martins + Henrique, 02/10): histórico = ogol; calendário, banco e lesão =
   Transfermarkt; minutos, posições e mapa de calor = Wyscout (pela extensão, fora daqui). */
(function () {
  const OGOL = 'https://www.ogol.com.br', TM = 'https://www.transfermarkt.com.br', TMAPI = 'https://tmapi.transfermarkt.technology';
  let carteiro = null;            // async (url, como: 'texto' | 'json' | 'bytes') -> string | Blob
  const cache = new Map();
  async function get(url, como = 'texto') {
    if (!carteiro) throw new Error('fontes: sem carteiro (extensão ou servidor local)');
    const k = como + ' ' + url;
    if (!cache.has(k)) cache.set(k, carteiro(url, como).catch(e => { cache.delete(k); throw e; }));
    return cache.get(k);
  }
  const getJSON = async url => JSON.parse(await get(url, 'json'));

  const ta = document.createElement('textarea');
  const unesc = s => { if (!/&/.test(s)) return s; ta.innerHTML = s; return ta.value; };
  // HTML -> pedaços de texto na ordem da página (igual ao _texto do Python)
  function texto(s) {
    s = s.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g, '');
    return s.split(/<[^>]+>/).map(p => unesc(p.replace(/\s+/g, ' ')).trim()).filter(Boolean);
  }
  const num = t => /^(\d+|-)$/.test(t || '') ? t : '';

  /* ─────────────── ogol ─────────────── */
  async function ogolBusca(q) {
    const s = await get(`${OGOL}/pesquisa?search_txt=${encodeURIComponent(q).replace(/%20/g, '+')}`);
    const out = [];
    for (const bloco of s.split(/(?=<div class="zz-search-item player)/).slice(1)) {
      const m = bloco.match(/href="(\/jogador\/[^"?]+)/); if (!m) continue;
      const nome = bloco.match(/class="title"[^>]*>([\s\S]*?)<\/a>/), sub = bloco.match(/class="subtitle">([^<]*)/);
      const local = bloco.match(/<\/a>([^<]*\d{4}-\d{2}-\d{2})<\/div>/), pais = bloco.match(/<a title="([^"]+)" href="\/pais\//);
      const pos = bloco.match(/class="stamp position"[^>]*>([^<]+)/), idade = bloco.match(/title="Idade" class="stamp">(\d+)/);
      const clube = bloco.match(/href="\/equipe\/[^"]+">([^<]+)<\/a>/), foto = bloco.match(/<div class="img"><a [^>]*><img src="([^"]+)"/);
      out.push({url: OGOL + m[1],
        nome: nome ? unesc(nome[1].replace(/<[^>]+>/g, ' ')).trim().replace(/^\d+\s+/, '') : '',   // tira o nº da camisa
        clube: clube ? unesc(clube[1]).trim() : '',
        foto: foto && foto[1].startsWith('/') && !foto[1].includes('No_Photo') ? OGOL + foto[1] : '',
        subtitulo: sub ? unesc(sub[1]) : '', pais: pais ? pais[1] : '',
        nasc: local ? local[1].split(',').pop().trim() : '', posicao: pos ? pos[1] : '', idade: idade ? idade[1] : ''});
      if (out.length >= 12) break;
    }
    return out;
  }
  const baseOgol = url => { const m = String(url).trim().match(/^(https:\/\/www\.ogol\.com\.br\/jogador\/[^/?#]+\/(\d+))/); if (!m) throw new Error('Link do ogol inválido (precisa ser .../jogador/<nome>/<número>)'); return m; };

  // Tabela "Histórico" (carreira inteira) + seleções de /equipes. Dois clubes na mesma temporada: o ogol
  // não repete o ano; "(E)" = empréstimo; "[FC Tokyo]" = dono do passe (sai); "[S17]", "[B]" = categoria (entra).
  async function ogolHistorico(url) {
    const base = baseOgol(url)[1];
    const t = texto(await get(base));
    const clube = [];
    let i = null;
    for (let k = 0; k < t.length - 4; k++) if (t[k] === 'TEMPORADA' && t[k+1] === 'EQUIPE' && t[k+2] === 'J' && t[k+3] === 'G' && t[k+4] === 'ASS') { i = k + 5; break; }
    let temp = '';
    while (i !== null && i < t.length) {
      if (/^\d{4}(\/\d{2,4})?$/.test(t[i])) { temp = t[i]; i++; }
      if (!temp || i >= t.length) break;
      let equipe = t[i], j = i + 1;
      if (t[j] === '(E)') { equipe += ' (E)'; j++; }
      while (j < t.length && /^\[[^\]]+\]$/.test(t[j])) {   // pode vir mais de uma: "[S23] [Lanús]"
        const marca = t[j].slice(1, -1); j++;
        if (/^(S\d+|U\d+|B|II|Sub-?\d+|Jun\.?|Juniores|Reservas?)$/i.test(marca)) equipe = equipe.replace(' (E)', '') + ' ' + marca + (equipe.includes(' (E)') ? ' (E)' : '');
      }
      const nums = t.slice(j, j + 3);
      if (nums.length < 3 || !nums.every(x => /^(\d+|-)$/.test(x))) break;   // acabou a tabela
      clube.push([temp, equipe.toUpperCase(), ...nums.map(num)]);
      i = j + 3;
    }
    const t2 = texto(await get(base + '/equipes'));
    const selecao = [];
    t2.forEach((p, k) => {
      if (!p.startsWith('Seleção [')) return;
      let j = k + 1;
      while (j < t2.length && t2[j] !== 'ASS') j++;
      j++;
      while (j < t2.length && t2[j] !== 'Total') {
        const nome = t2[j]; j++;
        let cat = '';
        if (j < t2.length && !/^(\d+|-)$/.test(t2[j])) { cat = t2[j]; j++; }
        const nums = t2.slice(j, j + 3); j += 3;
        if (t2[j] === 'detalhes') j++;
        selecao.push([(nome + (cat ? ' ' + cat : '')).toUpperCase(), ...nums.map(num)]);
      }
    });
    // principal primeiro; base da mais velha para a mais nova (S23 > S20 > S17)
    const idade = e => { const m = e[0].match(/S(\d+)/); return m ? +m[1] : 99; };
    selecao.sort((a, b) => idade(b) - idade(a));
    return {clube, selecao, url: base};
  }

  // Galeria /fotos (as mais novas primeiro): miniatura + nº da foto; o arquivo grande vem de ogolFotoOriginal
  async function ogolFotos(url) {
    const s = await get(baseOgol(url)[1] + '/fotos');
    const out = [];
    for (const m of s.matchAll(/href="\/foto\.php\?fk_galeria=0&(?:amp;)?nchapter=(\d+)&(?:amp;)?tpe=1&(?:amp;)?ide=\d+"[^>]*><img[^>]+src="([^"]+)"/g)) {
      const d = m[2].match(/_(20\d{2})(\d{2})(\d{2})\d{6}/);
      out.push({n: +m[1], miniatura: m[2].startsWith('http') ? m[2] : OGOL + m[2], data: d ? `${d[3]}/${d[2]}/${d[1]}` : ''});
    }
    return out;
  }
  // A página da foto mostra outras fotos também: só vale o "_ori_" com o MESMO número da miniatura.
  // Foto de perfil não tem _ori_ (a miniatura já é o arquivo inteiro).
  async function ogolFotoOriginal(url, n, miniatura = '') {
    const id = baseOgol(url)[2], numero = (miniatura.match(/\/(\d{6,})_/) || [])[1];
    const s = await get(`${OGOL}/foto.php?fk_galeria=0&nchapter=${+n}&tpe=1&ide=${id}`);
    for (const m of s.matchAll(/"((?:https:\/\/cdn-img\.staticzz\.com)?\/img\/[^"]+_ori_[^"]*\.(?:jpe?g|png|webp))"/g))
      if (!numero || m[1].includes(`/${numero}_`)) return m[1].startsWith('http') ? m[1] : OGOL + m[1];
    if (miniatura) return miniatura;
    throw new Error('foto não encontrada no ogol');
  }

  /* ─────────────── Transfermarkt ─────────────── */
  async function tmBusca(q) {
    const s = await get(`${TM}/schnellsuche/ergebnis/schnellsuche?query=${encodeURIComponent(q).replace(/%20/g, '+')}`);
    const out = [], vistos = new Set();
    for (const linha of s.split(/<tr class="(?:odd|even)">/).slice(1)) {
      const m = linha.match(/href="\/([^/"]+)\/profil\/spieler\/(\d+)"[^>]*>([^<]+)<\/a>/);
      if (!m || vistos.has(m[2])) continue;
      vistos.add(m[2]);
      const clube = linha.match(/title="([^"]+)" href="\/[^"]+\/startseite\/verein\//), cels = texto(linha);
      out.push({id: m[2], nome: unesc(m[3]).trim(), clube: clube ? clube[1] : '',
        idade: cels.find(c => /^\d{2}$/.test(c)) || '', posicao: cels[2] || '', url: `${TM}/${m[1]}/profil/spieler/${m[2]}`});
      if (out.length >= 12) break;
    }
    return out;
  }
  const idTM = id => { if (!/^\d{1,9}$/.test(String(id))) throw new Error('id do Transfermarkt inválido'); return String(id); };

  // Jogo a jogo do TM (carreira, só clube), agrupado por temporada. Banco = "in squad"; lesão = jogo com injuryId.
  async function tmTemporadas(tmId) {
    const d = await getJSON(`${TMAPI}/player/${idTM(tmId)}/performance-game`);
    const grupos = new Map();
    for (const g of (d.data || {}).performance || []) {
      const gi = g.gameInformation; if (gi.isNationalGame) continue;
      const k = gi.season.display; if (!grupos.has(k)) grupos.set(k, []); grupos.get(k).push(g);
    }
    const out = [];
    for (const [rot, L] of grupos) {
      const est = L.map(x => x.statistics.generalStatistics), datas = L.map(x => x.gameInformation.date.dateTimeUTC.slice(0, 10)).sort();
      const jogou = L.filter(x => x.statistics.generalStatistics.participationState === 'played');
      out.push({rotulo: rot, de: datas[0], ate: datas[datas.length - 1], jogos_time: L.length, disputados: jogou.length,
        banco: est.filter(e => e.participationState === 'in squad').length,
        nao_relacionado: est.filter(e => e.participationState === 'not in squad').length,
        ausente: est.filter(e => e.participationState === 'absent').length,
        lesionado: est.filter(e => e.injuryId).length,
        duracao: L.reduce((a, x) => a + (x.gameInformation.gameDuration || 90), 0),
        min_tm: jogou.reduce((a, x) => a + (((x.statistics.playingTimeStatistics || {}).playedMinutes) || 0), 0),
        clubes: [...new Set(est.map(e => e.primaryClubId).filter(Boolean).map(String))].sort()});
    }
    out.sort((a, b) => a.ate < b.ate ? 1 : -1);
    return {tm_id: String(tmId), temporadas: out};
  }

  const MESES_EN = ['Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'Jun.', 'Jul.', 'Aug.', 'Sep.', 'Oct.', 'Nov.', 'Dec.'];
  const POS_TM = {
    1: ['GOLEIRO', 'GOLEIRO', ['GOL'], 'GK'], 2: ['LÍBERO', 'ZAGUEIRO', ['ZGE', 'ZGD'], 'CB'],
    3: ['ZAGUEIRO', 'ZAGUEIRO', ['ZGE', 'ZGD'], 'CB'], 4: ['LATERAL ESQUERDO', 'LATERAL', ['LE'], 'LB'],
    5: ['LATERAL DIREITO', 'LATERAL', ['LD'], 'RB'], 6: ['VOLANTE', 'VOLANTE', ['VOL'], 'DM'],
    7: ['MÉDIO CENTRAL', 'MÉDIO', ['MCE', 'MCD'], 'CM'], 8: ['MEIA DIREITA', 'MEIA', ['ALD'], 'RM'],
    9: ['MEIA ESQUERDA', 'MEIA', ['ALE'], 'LM'], 10: ['MEIA ATACANTE', 'MEIA', ['MA'], 'AM'],
    11: ['PONTA ESQUERDA', 'EXTREMO', ['PE'], 'LW'], 12: ['PONTA DIREITA', 'EXTREMO', ['PD'], 'RW'],
    13: ['SEGUNDO ATACANTE', 'ATACANTE', ['ATA'], 'SS'], 14: ['CENTROAVANTE', 'ATACANTE', ['ATA'], 'CF']};
  const PAIS3 = {'Uruguai':'URU','Argentina':'ARG','Brasil':'BRA','Paraguai':'PAR','Chile':'CHI','Colômbia':'COL','Equador':'EQU','Peru':'PER',
    'Venezuela':'VEN','Bolívia':'BOL','Portugal':'POR','Espanha':'ESP','Itália':'ITA','França':'FRA','Inglaterra':'ING','Alemanha':'ALE',
    'Holanda':'HOL','Países Baixos':'HOL','Bélgica':'BEL','México':'MEX','Estados Unidos':'EUA','Japão':'JAP','Coreia do Sul':'COR',
    'Arábia Saudita':'ARS','Turquia':'TUR','Grécia':'GRE','Rússia':'RUS','Ucrânia':'UCR','Suíça':'SUI','Áustria':'AUT','Dinamarca':'DIN',
    'Suécia':'SUE','Noruega':'NOR','Escócia':'ESC','Croácia':'CRO','Sérvia':'SER','Romênia':'ROM','Hungria':'HUN','Polônia':'POL',
    'Rep. Tcheca':'TCH','Catar':'CAT','Emirados Árabes Unidos':'EAU','Costa Rica':'CRC','Canadá':'CAN','China':'CHN','Austrália':'AUS'};
  const POS_VAZIA = ['', '', [], ''];
  const dataEn = iso => { try { const [a, m, d] = iso.slice(0, 10).split('-'); if (!d) throw 0; return `${MESES_EN[+m - 1]} ${d}, ${a}`; } catch { return iso || '-'; } };
  const milhar = v => v ? Math.trunc(+v).toLocaleString('en-US').replace(/,/g, '.') : '-';
  // só o rótulo da ficha (com dois-pontos), não a palavra solta do menu do site
  const tmInfo = (tx, rot) => { const k = tx.findIndex(p => p.trim().toLowerCase() === rot.toLowerCase() + ':'); return k >= 0 && k + 1 < tx.length ? tx[k + 1].trim() : ''; };
  const valor = c => { c = c || {}; return ((c.prefix || '') + (c.content || '') + (c.suffix || '')).trim(); };

  // Tudo o que a folha 2 usa (API aberta + página em português). foto_url / escudo_url: quem chama baixa e guarda.
  async function tmFicha(tmId) {
    const id = idTM(tmId);
    const p = (await getJSON(`${TMAPI}/player/${id}`)).data, at = p.attributes || {};
    const pagina = await get(TM + (p.relativeUrl || `/x/profil/spieler/${id}`)), tx = texto(pagina);
    const nac = tmInfo(tx, 'Nacionalidade'), clubeAtual = tmInfo(tx, 'Clube atual');
    const emprestado = tmInfo(tx, 'Emprestado de') || tmInfo(tx, 'Por empréstimo de');
    let agente = tmInfo(tx, 'Empresários') || tmInfo(tx, 'Empresário') || (at.consultantAgency || {}).name || '-';
    agente = {Familiar: 'Familiares', Relatives: 'Familiares'}[agente] || agente;

    const tr = (await getJSON(`${TMAPI}/transfer/history/player/${id}`)).data.history;
    const linhas = (tr.pending || []).concat(tr.terminated || []);
    const ids = new Set((p.clubAssignments || []).map(c => String(c.clubId)));
    linhas.forEach(t => { ids.add(String(t.transferSource.clubId)); ids.add(String(t.transferDestination.clubId)); });
    ids.delete('0');
    const clubes = {};
    if (ids.size) {
      const q = [...ids].sort().map(i => `ids[]=${i}`).join('&');
      for (const c of (await getJSON(`${TMAPI}/clubs?${q}`)).data || [])
        clubes[String(c.id)] = {nome: c.name || '', curto: (c.baseDetails || {}).shortName || c.name || '', escudo: c.crestUrl || ''};
    }
    const atual = String(((p.clubAssignments || []).find(c => c.type === 'current') || {}).clubId || '');
    const TAXA = {'Free Transfer': 'Custo zero', 'loan transfer': 'Empréstimo', 'End of loan': 'Fim de empréstimo', '?': '-'};
    const transferencias = linhas.map(t => {
      const dt = t.details, o = clubes[String(t.transferSource.clubId)] || {}, d = clubes[String(t.transferDestination.clubId)] || {};
      let taxa = valor((dt.fee || {}).compact) || '-'; taxa = TAXA[taxa] || taxa;
      const vdm = valor((dt.marketValue || {}).compact);
      return {temporada: (dt.season || {}).display || '', data: `${dt.date.slice(8, 10)}/${dt.date.slice(5, 7)}/${dt.date.slice(0, 4)}`,
        origem: o.curto || '', origem_escudo: o.escudo || '', destino: d.curto || '', destino_escudo: d.escudo || '',
        vdm: vdm && vdm !== '€' ? vdm : '-', taxa};
    });

    const lesoes = [];
    const sInj = await get(`${TM}/x/verletzungen/spieler/${id}`), i = sInj.indexOf('<table class="items"');
    if (i >= 0) {
      const tab = sInj.slice(i, sInj.indexOf('</table>', i));
      for (const r of tab.matchAll(/<tr class="(?:odd|even)[^"]*">([\s\S]*?)<\/tr>/g)) {
        const c = [...r[1].matchAll(/<td[^>]*>([\s\S]*?)<\/td>/g)].map(x => unesc(x[1].replace(/<[^>]+>/g, '')).trim());
        if (c.length >= 6) lesoes.push({temporada: c[0], lesao: c[1], de: c[2], ate: c[3] || '—', dias: c[4], jogos: c[5]});
      }
    }

    const pos = POS_TM[at.positionId] || POS_VAZIA, sec = POS_TM[at.firstSidePositionId || 0] || POS_VAZIA;
    const campo = {}; pos[2].forEach(k => campo[k] = 1); sec[2].forEach(k => { if (!(k in campo)) campo[k] = 2; });
    const pe = {right: 'DESTRO', left: 'CANHOTO', both: 'AMBIDESTRO'}[(at.preferredFoot || {}).name || ''] || '';
    const mv = (p.marketValueDetails || {}).current || {}, cAtual = clubes[atual] || {};
    const mp = pagina.match(/data-header__club-info[\s\S]*?title="([^"]+)"[^>]*class="flaggenrahmen/), paisClube = mp ? mp[1] : '';
    const siglaPais = PAIS3[paisClube] || (paisClube ? paisClube.slice(0, 3).toUpperCase() : '');
    const linha = `${pos[1]} | ${(clubeAtual || cAtual.nome || '').toUpperCase()}` + (siglaPais ? ` (${siglaPais})` : '');
    const vida = p.lifeDates || {};
    return {
      tm_id: id, url: TM + (p.relativeUrl || ''), nome: (p.name || '').toUpperCase(),
      linha, capa_linha: linha.replace(' | ', ' I '), sigla: pos[3],
      ficha: {
        nome_completo: (p.nationalityDetails || {}).passportName || p.name || '', dn: dataEn(vida.dateOfBirth || ''),
        idade: String(vida.age ?? ''), nacionalidade: nac || '-', contrato: dataEn(at.contractUntil || ''),
        emprestado: emprestado || '-', agente, principal: pos[0], secundaria: sec[0] || '-', campo_pos: campo,
        altura: at.height ? `${Math.round(at.height * 100)} cm` : '-', pe: pe || 'DESTRO', moeda: mv.currency || 'EUR',
        valor: milhar(mv.value), valor_fonte: 'TRANSFERMARKT', tm: TM + (p.relativeUrl || ''),
        categorias_base: at.formerClubsNote || '', transferencias, lesoes: lesoes.slice(0, 6)},
      foto_url: p.portraitUrl || '', escudo_url: cAtual.escudo || ''};
  }

  window.Fontes = {
    usar(fn) { carteiro = fn; cache.clear(); },
    imagem: url => get(url, 'bytes'),           // Blob
    ogolBusca, ogolHistorico, ogolFotos, ogolFotoOriginal, tmBusca, tmTemporadas, tmFicha,
  };
})();
