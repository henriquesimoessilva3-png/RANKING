# -*- coding: utf-8 -*-
"""Gera o dashboard (standalone + artifact) da Fase 2: ranking de jovens sul-americanos
por similaridade aos arquétipos das 5 grandes ligas."""
import json, html, os
def esc(s): return html.escape(str(s))
R=json.load(open('estudo/data/similares_sa.json'))
CSS=open('estudo/build/shared.css').read()

GROUPS_ORDER=['Zagueiro','Lateral','Volante','Medio','Meia','Extremo','Atacante']
# arquétipos prioritários (escassos / de maior teto e revenda)
PRIORITY={
 'Zagueiro':['Construtor','Defensor de espaço','móvel'],
 'Lateral':['ofensivo','Motor'],
 'Volante':['Organizador'],
 'Medio':['Organizador','Condutor','intensidade'],
 'Meia':['Armador','Condutor'],
 'Extremo':['Craque','Driblador'],
 'Atacante':['Falso-9','profundidade'],
}
def is_priority(g,nome):
    return any(k.lower() in nome.lower() for k in PRIORITY.get(g,[]))

def fmt_min(m): return f'{m}′' if m else '—'
def fmt_age(a): return f'{a:.0f}' if a is not None else '—'
def mv(v): return (f'{v/1e6:.1f}M€'.replace('.0M','M') if v and v>=1e6 else (f'{v/1e3:.0f}k€' if v else '—'))

def matchbar(p,cls=''):
    return (f'<span class="mb {cls}"><i style="width:{max(2,p):.0f}%"></i>'
            f'<b>{p:.0f}<small>%</small></b></span>')

# ---------- headline leaderboard: melhor alvo POR arquétipo prioritário (diversificado) ----------
# Evita o viés de que arquétipos muito físicos dominem: garante 1 melhor jovem por molde valioso.
prio_list=[]
for g in GROUPS_ORDER:
    gd=R['grupos'][g]
    for a in gd['arquetipos']:
        if is_priority(g,a['nome']):
            prio_list.append((g,a))
taken=set(); alvos=[]
# duas passadas: 1º melhor de cada arquétipo, 2º segundos melhores por afinidade
for rank_slot in (0,1):
    for g,a in prio_list:
        picks=[t for t in a['top'] if (t['name'],t['team']) not in taken]
        if len(picks)>rank_slot:
            t=picks[rank_slot]
            if rank_slot==1 and t['match']<68: continue
            taken.add((t['name'],t['team']))
            alvos.append({**t,'g':g,'arch':a['nome'],'tag':a['tag'],'refs':a['referencias']})
alvos=sorted(alvos,key=lambda x:-x['match'])

lead_rows=''
for i,x in enumerate(alvos,1):
    tr=x['traits'][0]
    lead_rows+=f'''<tr>
      <td class="rk">{i}</td>
      <td class="pl"><span class="pl-n">{esc(x['name'])}</span><span class="pl-m">{esc(x['team'])} · {esc(x['league'])} · {fmt_age(x['age'])} anos · {fmt_min(x['minutes'])}</span></td>
      <td class="ar"><span class="chip">{esc(x['g'])}</span> {esc(x['arch'])}<span class="ar-ref">molde: {esc(', '.join(x['refs'][:2]))}</span></td>
      <td class="tr">{esc(tr['lab'])} <b>{esc(tr['v'])}</b></td>
      <td class="mt">{matchbar(x['match'],'big')}</td>
    </tr>'''

# ---------- per-group archetype tables ----------
def arch_block(g,a):
    if not a['top']:
        return ''
    rows=''
    for t in a['top'][:8]:
        traits=' · '.join(f"{esc(x['lab'])} <b>{esc(x['v'])}</b>" for x in t['traits'])
        rows+=f'''<tr>
          <td class="mt">{matchbar(t['match'])}</td>
          <td class="pl"><span class="pl-n">{esc(t['name'])}</span><span class="pl-m">{esc(t['team'])} · {esc(t['league'])}</span></td>
          <td class="c">{fmt_age(t['age'])}</td>
          <td class="c">{fmt_min(t['minutes'])}</td>
          <td class="tr">{traits}</td>
        </tr>'''
    prio=' data-prio="1"' if is_priority(g,a['nome']) else ''
    star='<span class="star" title="Arquétipo prioritário (escasso / alto teto)">★</span>' if is_priority(g,a['nome']) else ''
    return f'''<div class="arch"{prio}>
      <div class="arch-h">
        <h4>{star}{esc(a['nome'])} <span class="chip">{esc(a['tag'])}</span></h4>
        <span class="arch-ref">moldes top-5: {esc(', '.join(a['referencias'][:4]))}</span>
      </div>
      <p class="arch-alvo">{esc(a['alvo'])}</p>
      <div class="tbl-wrap"><table class="mtbl">
        <thead><tr><th>Afinidade</th><th>Jogador</th><th>Idade</th><th>Min</th><th>Destaques (vs. média sul-americana da posição)</th></tr></thead>
        <tbody>{rows}</tbody>
      </table></div>
    </div>'''

sections=''
GFULL={'Zagueiro':'Zagueiros','Lateral':'Laterais','Volante':'Volantes','Medio':'Médios',
 'Meia':'Meias','Extremo':'Extremos','Atacante':'Atacantes'}
for g in GROUPS_ORDER:
    gd=R['grupos'][g]
    # prioritário primeiro
    archs=sorted(gd['arquetipos'],key=lambda a:(0 if is_priority(g,a['nome']) else 1))
    blocks=''.join(arch_block(g,a) for a in archs)
    sections+=f'''<section class="group" id="g-{esc(g)}">
      <div class="group-h"><h3>{esc(GFULL[g])}</h3><span class="group-meta">{gd['n_cands']} jovens analisados · pool de referência {gd['n_pool']}</span></div>
      {blocks}
    </section>'''

nav=''.join(f'<a href="#g-{esc(g)}">{esc(GFULL[g])}</a>' for g in GROUPS_ORDER)
M=R['meta']
ncands=sum(R['grupos'][g]['n_cands'] for g in GROUPS_ORDER)
nligas=len(M['ligas'])

EXTRA_CSS='''
.mb{display:inline-flex;align-items:center;gap:7px;min-width:96px}
.mb i{display:block;height:8px;border-radius:5px;background:linear-gradient(90deg,var(--accent),var(--accent2));flex:none;width:40px}
.mb b{font-size:12.5px;font-variant-numeric:tabular-nums;font-weight:680}
.mb small{font-size:9px;font-weight:600;color:var(--muted)}
.mb.big i{height:10px}
.lead{margin:8px 0 6px;border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:var(--shadow);background:var(--surface)}
.tbl-wrap{overflow-x:auto}
table.leadt,table.mtbl{border-collapse:collapse;width:100%;min-width:680px}
.leadt td{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:middle}
.leadt tr:last-child td{border-bottom:none}
.rk{font-variant-numeric:tabular-nums;font-weight:750;color:var(--muted);width:34px;text-align:center;font-size:15px}
.pl-n{display:block;font-weight:650;font-size:14px}
.pl-m{display:block;font-size:11px;color:var(--muted)}
.ar{font-size:12.5px;color:var(--ink2);max-width:230px}
.ar-ref{display:block;font-size:10.5px;color:var(--muted);margin-top:2px}
.tr{font-size:12px;color:var(--ink2)}
.mtbl th{font-size:10.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);font-weight:640;text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
.mtbl td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:middle;font-size:12.5px}
.mtbl td.c{text-align:center;font-variant-numeric:tabular-nums;color:var(--ink2)}
.mtbl tr:last-child td{border-bottom:none}
.arch{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 16px 6px;margin:14px 0;box-shadow:var(--shadow)}
.arch[data-prio="1"]{border-color:color-mix(in srgb,var(--accent) 45%,var(--line))}
.arch-h{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.arch-h h4{font-size:16px;display:flex;align-items:center;gap:8px}
.star{color:var(--amber)}
.arch-ref{font-size:11px;color:var(--muted)}
.arch-alvo{font-size:12px;color:var(--ink2);margin:6px 0 12px;max-width:80ch}
.legend-note{font-size:12px;color:var(--muted);margin-top:10px}
@media(max-width:720px){.ar,.tr{display:none}.leadt td.tr{display:none}}
'''

body=f'''<div id="top"></div>
<header class="site"><div class="wrap site-in">
  <div class="brand"><span class="dot"></span> Fase 2 · Similares Sul-Americanos</div>
  <nav class="jump">{nav}</nav>
  <button id="theme" aria-label="Alternar tema">◐</button>
</div></header>
<main class="wrap">
  <section class="hero">
    <p class="eyebrow">Do gabarito das 5 grandes ligas → aos jovens da América do Sul</p>
    <h1>Jovens sul-americanos com o DNA dos arquétipos de elite</h1>
    <p class="lede">Cada jovem (≤ {M['idade_max']} anos, ≥ {M['min_min']} min) das ligas sul-americanas com dados físicos foi pontuado por <b>similaridade de perfil</b> aos {sum(len(R['grupos'][g]['arquetipos']) for g in GROUPS_ORDER)} arquétipos das cinco grandes ligas. A afinidade mede o <b>formato</b> do jogo — o quanto o jogador desvia da média da sua posição na mesma direção que o arquétipo desvia da média da elite.</p>
    <div class="kpis">
      <div class="kpi"><b>{ncands}</b><span>jovens sul-americanos avaliados</span></div>
      <div class="kpi"><b>{nligas}</b><span>ligas SA com dados físicos + técnicos</span></div>
      <div class="kpi"><b>{len(alvos)}</b><span>alvos prioritários no shortlist</span></div>
    </div>
  </section>

  <section class="finding">
    <h2>Shortlist — alvos prioritários</h2>
    <p>Os melhores matches aos arquétipos <b>mais escassos e valorizados</b> (construtores, criadores, organizadores, velocistas e craques ★), ordenados por afinidade. É a lista curta para aprofundar em vídeo e contexto.</p>
    <div class="lead"><table class="leadt"><tbody>{lead_rows}</tbody></table></div>
    <p class="legend-note">Afinidade = cosseno entre o perfil do jogador (z vs. média sul-americana da posição) e o centroide do arquétipo. Valores de mercado frequentemente ausentes nas bases SA.</p>
  </section>

  <section class="finding">
    <h2>Ranking completo por posição e arquétipo</h2>
    <p class="sub">Arquétipos prioritários (★) aparecem primeiro em cada posição. Goleiros ficaram de fora — amostra de jovens com dados físicos insuficiente.</p>
    {sections}
  </section>

  <footer class="foot">
    <h3>Como ler & limites</h3>
    <ul>
      <li><b>Afinidade de formato, não de nível.</b> A padronização é feita dentro do contexto sul-americano, então a métrica responde "quem joga no mesmo estilo do arquétipo", controlando o nível da liga. Não é uma previsão de que o jogador rende como o molde — é um filtro de estilo e perfil físico.</li>
      <li><b>Amostra:</b> {ncands} jovens (≤ {M['idade_max']} anos, ≥ {M['min_min']} min) das ligas {esc(', '.join(M['ligas']))} — apenas jogadores com rastreamento físico (SkillCorner), para casar com o espaço de features dos moldes. Reservas e segundas divisões sem dados físicos ficaram fora desta rodada.</li>
      <li><b>Destaques</b> mostram as métricas (do conjunto que define o arquétipo) em que o jogador mais se sobressai vs. a média da sua posição na América do Sul, com o valor por 90 min.</li>
      <li><b>Próximos passos sugeridos:</b> cruzar com idade/contrato/valor, adicionar as ligas sem físico via match técnico-apenas, e validar os finalistas em vídeo.</li>
    </ul>
    <p class="disc">Filtro exploratório de scouting. Afinidades baixas em alguns arquétipos (ex.: armadores clássicos) refletem escassez real desse perfil no pool jovem sul-americano.</p>
  </footer>
</main>
<script id="DATA" type="application/json">{json.dumps({'alvos':len(alvos),'cands':ncands})}</script>
<script>
(function(){{var root=document.documentElement,btn=document.getElementById('theme');
function set(t){{root.setAttribute('data-theme',t);try{{localStorage.setItem('e5t',t)}}catch(e){{}}}}
var s;try{{s=localStorage.getItem('e5t')}}catch(e){{}}if(s)set(s);
btn.onclick=function(){{var d=root.getAttribute('data-theme')==='dark'||(!root.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme:dark)').matches);set(d?'light':'dark')}};
var links=[].slice.call(document.querySelectorAll('.jump a')),secs=links.map(function(a){{return document.querySelector(a.getAttribute('href'))}});
function spy(){{var y=scrollY+120,c=-1;for(var i=0;i<secs.length;i++)if(secs[i]&&secs[i].offsetTop<=y)c=i;links.forEach(function(a,i){{a.classList.toggle('on',i===c)}})}}
addEventListener('scroll',spy,{{passive:true}});spy();}})();
</script>'''

os.makedirs('estudo/build',exist_ok=True)
# standalone
full=('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
 '<meta name="viewport" content="width=device-width,initial-scale=1">'
 '<title>Fase 2 · Similares Sul-Americanos</title>'
 '<style>'+CSS+EXTRA_CSS+'</style></head><body>'+body+'</body></html>')
open('estudo/similares_sa.html','w').write(full)
# artifact
art='<style>\n'+CSS+EXTRA_CSS+'\n</style>\n<title>Fase 2 · Similares Sul-Americanos</title>\n'+body
open('estudo/build/artifact_sa.html','w').write(art)
print('standalone bytes:',len(full),'| shortlist:',len(alvos),'| candidatos:',ncands)
