# -*- coding: utf-8 -*-
"""Dashboard-síntese: a recomendação de contratação do Botafogo por posição."""
import json, html, os
def esc(s): return html.escape(str(s))
R=json.load(open('estudo/data/reco_botafogo.json'))
CSS=open('estudo/build/shared.css').read()
GORD=R['grupos_ordem']; R2=R['recos']
GFULL={'Goleiro':'Goleiro','Zagueiro':'Zagueiro','Lateral':'Lateral','Volante':'Volante (1º volante)',
 'Medio':'Meio-campo','Meia':'Meia armador','Extremo':'Extremo (ponta)','Atacante':'Centroavante'}
FLAB={'total_distance_p90':'volume de corrida','running_distance_p90':'dist. em corrida','hi_distance_p90':'dist. alta intensidade',
 'hi_actions_p90':'ações de alta intensidade','hsr_distance_p90':'dist. veloz','hsr_count_p90':'corridas velozes',
 'sprint_distance_p90':'dist. em sprint','n_sprints_p90':'volume de sprints','psv99':'velocidade de ponta','top5_psv99':'velocidade máx.',
 'high_accel_p90':'acelerações fortes','med_accel_p90':'acelerações','high_decel_p90':'freadas fortes','med_decel_p90':'freadas',
 'explosive_accel_to_sprint':'explosão','cod_count_p90':'mudança de direção','m_min':'intensidade (m/min)','m_min_tip':'intensidade c/ posse',
 'm_min_otip':'intensidade s/ posse','top3_time_to_sprint':'arranque','top3_time_to_hsr':'arranque curto',
 'Defensive duels won, %':'duelo defensivo','Aerial duels won, %':'jogo aéreo','PAdj Interceptions':'interceptações',
 'Successful defensive actions per 90':'ações defensivas','Sliding tackles per 90':'desarme','Shots blocked per 90':'bloqueios',
 'Passes per 90':'volume de passe','Accurate passes, %':'acerto de passe','Progressive passes per 90':'passe progressivo',
 'Accurate long passes, %':'passe longo','Long passes per 90':'passes longos','Forward passes per 90':'passe p/ frente',
 'Passes to final third per 90':'passe ao terço final','Received passes per 90':'envolvimento (passes recebidos)',
 'Key passes per 90':'passe decisivo','Smart passes per 90':'passe inteligente','Through passes per 90':'passe em profundidade',
 'xA per 90':'criação (xA)','Passes to penalty area per 90':'passe à área','Deep completions per 90':'chegada ao terço',
 'Shot assists per 90':'assist. p/ finalização','Accurate crosses, %':'cruzamento','Crosses per 90':'cruzamentos',
 'Deep completed crosses per 90':'cruzamento ao terço','Second assists per 90':'2ª assistência','Progressive runs per 90':'condução progressiva',
 'Successful dribbles per 90':'dribles certos','Dribbles per 90':'dribles','Accelerations per 90':'arranques',
 'xG per 90':'volume de chance (xG)','Non-penalty goals per 90':'gols','Goals per 90':'gols','Shots per 90':'finalizações',
 'Touches in box per 90':'presença na área','Goal conversion, %':'conversão','Head goals per 90':'gol de cabeça','Assists per 90':'assistências'}
def flab(f): return FLAB.get(f,f)
def mv(v): return (f'{v/1e6:.1f}M€'.replace('.0M','M') if v and v>=1e6 else '—')
def foot(f): return {'direito':'destro','esquerdo':'canhoto'}.get(f,f or '')

def need_tag(inc):
    if not inc: return ('Sem titular fixo mapeado','need-hi')
    old=[i for i in inc if (i['age'] or 0)>=30]
    top=inc[0]
    if old: return (f"Titular veterano ({old[0]['name']}, {old[0]['age']:.0f})",'need-hi')
    if (top['age'] or 0)>=27: return (f"Titular {top['name']} ({top['age']:.0f}) — janela curta",'need-md')
    return (f"{top['name']} ({top['age']:.0f}) no elenco",'need-lo')

def bars(t):
    return f'''<div class="rb"><span>Prontidão</span><i class="rbt"><b style="width:{t['readiness']:.0f}%"></b></i><u>{t['readiness']:.0f}</u></div>
      <div class="rb"><span>Revenda</span><i class="rbt rev"><b style="width:{t['resale']:.0f}%"></b></i><u>{t['resale']:.0f}</u></div>'''

def alt(t):
    return f'''<div class="altc"><div><b>{esc(t['name'])}</b> <span>{esc(t['team'])} · {esc(t['league'])} · {t['age']:.0f}a</span></div>
      <div class="altc-r"><span class="chip sm">{esc(t['arch'])} {t['arch_match']:.0f}%</span><b class="sc">{t['score']:.0f}</b></div></div>'''

def block(g):
    r=R2[g]; nt,ncls=need_tag(r['incumbentes'])
    inc=', '.join(f"{i['name']} ({i['age']:.0f})" for i in r['incumbentes'][:3]) if r['incumbentes'] else '—'
    if not r['cands']:
        return f'''<section class="posblock"><div class="pb-head"><h3>{esc(GFULL[g])}</h3><span class="need {ncls}">{esc(nt)}</span></div>
          <p class="pb-inc">Elenco atual: {esc(inc)}</p>
          <div class="noalvo">Sem candidato jovem elegível na base com dados físicos — recomenda-se busca fora do escopo atual (ligas sem rastreamento ou outra faixa etária).</div></section>'''
    t=r['cands'][0]
    traits=', '.join(flab(x['lab']) for x in t['traits'])
    refs=' / '.join(t['arch_refs'][:2])
    alts=''.join(alt(x) for x in r['cands'][1:4])
    return f'''<section class="posblock" id="g-{esc(g)}">
      <div class="pb-head"><h3>{esc(GFULL[g])}</h3><span class="need {ncls}">{esc(nt)}</span></div>
      <p class="pb-inc">Elenco atual: {esc(inc)}</p>
      <div class="pb-main">
        <div class="pick">
          <div class="pick-top">
            <div><div class="pick-n">{esc(t['name'])}</div><div class="pick-id">{esc(t['team'])} · {esc(t['league'])} · {t['age']:.0f} anos · {t['minutes']}′{' · '+foot(t['foot']) if t['foot'] else ''}{' · '+str(t['height'])+'cm' if t['height'] else ''}</div></div>
            <div class="pick-score"><b>{t['score']:.0f}</b><span>score</span></div>
          </div>
          <div class="pick-arch"><span class="chip">{esc(t['arch'])}</span> perfil de <b>{esc(refs)}</b> · afinidade {t['arch_match']:.0f}%</div>
          <div class="pick-bars">{bars(t)}</div>
          <div class="pick-tr"><span>Destaques vs. média SA:</span> {esc(traits)}</div>
        </div>
        <div class="alts"><div class="alts-lab">Alternativas</div>{alts if alts else '<p class="noalt">—</p>'}</div>
      </div>
    </section>'''

blocks=''.join(block(g) for g in GORD)
nav=''.join(f'<a href="#g-{esc(g)}">{esc(GFULL[g].split(" (")[0])}</a>' for g in GORD if R2[g]['cands'])

# resumo topo: XI
xi=[]
for g in GORD:
    if R2[g]['cands']:
        t=R2[g]['cands'][0]; xi.append((g,t))

EXTRA='''
.posblock{border-top:1px solid var(--line);padding:22px 0}
.posblock:first-of-type{border-top:none}
.pb-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.pb-head h3{font-size:20px}
.need{font-size:11px;font-weight:660;padding:3px 10px;border-radius:20px}
.need-hi{color:#fff;background:var(--amber)}
.need-md{color:var(--ink);background:color-mix(in srgb,var(--amber) 26%,transparent)}
.need-lo{color:var(--ink2);background:var(--surface2)}
.pb-inc{font-size:12px;color:var(--muted);margin:4px 0 12px}
.pb-main{display:grid;grid-template-columns:1.5fr 1fr;gap:16px}
.pick{background:var(--surface);border:1px solid color-mix(in srgb,var(--accent) 30%,var(--line));border-radius:16px;padding:16px;box-shadow:var(--shadow)}
.pick-top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.pick-n{font-size:20px;font-weight:750;letter-spacing:-.01em}
.pick-id{font-size:12px;color:var(--ink2)}
.pick-score{text-align:center;flex:none}
.pick-score b{font-size:30px;font-weight:780;color:var(--accent);line-height:1;font-variant-numeric:tabular-nums}
.pick-score span{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.pick-arch{font-size:12.5px;color:var(--ink2);margin:12px 0 12px}
.pick-arch b{color:var(--ink)}
.pick-bars{display:flex;flex-direction:column;gap:6px;margin-bottom:12px}
.rb{display:grid;grid-template-columns:66px 1fr 30px;align-items:center;gap:9px}
.rb span{font-size:11px;color:var(--muted);font-weight:600}
.rbt{height:9px;background:color-mix(in srgb,var(--ink) 8%,transparent);border-radius:5px;overflow:hidden}
.rbt b{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:5px}
.rbt.rev b{background:linear-gradient(90deg,var(--amber),color-mix(in srgb,var(--amber) 70%,#fff))}
.rb u{font-size:12px;font-variant-numeric:tabular-nums;text-decoration:none;font-weight:680;text-align:right}
.pick-tr{font-size:11.5px;color:var(--ink2);border-top:1px solid var(--line);padding-top:10px}
.pick-tr span{color:var(--muted);font-weight:600}
.alts{background:var(--surface2);border-radius:14px;padding:14px}
.alts-lab{font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);font-weight:660;margin-bottom:9px}
.altc{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid var(--line)}
.altc:last-child{border-bottom:none}
.altc b{font-size:13px}.altc span{font-size:10.5px;color:var(--muted);display:block}
.altc-r{display:flex;align-items:center;gap:8px;flex:none}
.chip.sm{font-size:9px;padding:2px 7px}
.sc{font-size:15px;color:var(--accent);font-variant-numeric:tabular-nums}
.noalvo,.noalt{font-size:13px;color:var(--muted);background:var(--surface2);border-radius:12px;padding:14px}
.xi{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:8px}
.xic{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px;box-shadow:var(--shadow)}
.xic .pos{font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:var(--accent);font-weight:700}
.xic .nm{font-size:15px;font-weight:700;margin:3px 0 1px}
.xic .mt{font-size:11px;color:var(--muted)}
.xic .sc2{font-size:12px;color:var(--ink2);margin-top:6px;font-weight:600}
@media(max-width:760px){.pb-main{grid-template-columns:1fr}.xi{grid-template-columns:repeat(2,1fr)}}
'''

xicards=''.join(f'''<div class="xic"><div class="pos">{esc(GFULL[g].split(" (")[0])}</div>
  <div class="nm">{esc(t['name'])}</div><div class="mt">{esc(t['team'])} · {t['age']:.0f}a · {esc(t['league'])}</div>
  <div class="sc2">score {t['score']:.0f} · {esc(t['arch_tag'])}</div></div>''' for g,t in xi)

body=f'''<div id="top"></div>
<header class="site"><div class="wrap site-in">
  <div class="brand"><span class="dot"></span> Alvos de Contratação · Botafogo</div>
  <nav class="jump">{nav}</nav><button id="theme">◐</button>
</div></header>
<main class="wrap">
  <section class="hero">
    <p class="eyebrow">Titular agora · revenda depois</p>
    <h1>Quem contratar, por posição, para ser titular e revender com lucro</h1>
    <p class="lede">Para cada posição, o jovem sul-americano (≤ {R['meta']['idade_max']} anos, ≥ {R['meta']['min_min']}′) que melhor combina <b>prontidão</b> — nível, minutos e força da liga, para já entrar e entregar resultado — com <b>potencial de revenda</b> — afinidade a um arquétipo valorizado na Europa, juventude e ferramentas físicas que o mercado paga. Atletas já do Botafogo foram excluídos.</p>
    <div class="xi">{xicards}</div>
  </section>
  <section class="finding">
    <h2>Como o score é montado</h2>
    <p>{esc(R['meta']['formula'])}. A <b>prontidão</b> responde "consegue ser titular e ganhar já?"; a <b>revenda</b> responde "a Europa compra esse perfil depois?". O peso é 50/50 — ajustável conforme a prioridade do projeto. Cada alvo mostra o arquétipo europeu que espelha e o jogador de elite que serve de referência.</p>
  </section>
  <section class="finding">
    <h2>Posição por posição</h2>
    {blocks}
  </section>
  <footer class="foot">
    <h3>Leitura & limites</h3>
    <ul>
      <li><b>Prontidão</b> = 45% nível (percentil do índice do modelo no campo sul-americano) + 25% minutos (titular regular) + 30% força da liga (Brasil A e Argentina A no topo). <b>Revenda</b> = 50% afinidade ao arquétipo premium + 25% juventude + 25% velocidade de ponta.</li>
      <li><b>Filtro de estilo, não garantia de sucesso.</b> A afinidade mede semelhança de perfil ao molde europeu; validação em vídeo, contexto tático, personalidade e situação contratual continuam essenciais.</li>
      <li>Universo: jovens de {esc(', '.join(R['meta']['ligas']))} com rastreamento físico. Ligas sem físico (reservas/2ªs divisões) e goleiros jovens ficaram fora — para essas frentes, uma rodada dedicada (inclusive match técnico-apenas) é o próximo passo.</li>
      <li>Necessidade por posição sinalizada pela idade dos titulares atuais do Botafogo na base (ex.: lateral e zaga com veteranos, ponta-direita com Edenílson aos 36).</li>
    </ul>
  </footer>
</main>
<script>
(function(){{var root=document.documentElement,b=document.getElementById('theme');
function set(t){{root.setAttribute('data-theme',t);try{{localStorage.setItem('e5t',t)}}catch(e){{}}}}
var s;try{{s=localStorage.getItem('e5t')}}catch(e){{}}if(s)set(s);
b.onclick=function(){{var d=root.getAttribute('data-theme')==='dark'||(!root.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme:dark)').matches);set(d?'light':'dark')}};
var L=[].slice.call(document.querySelectorAll('.jump a')),S=L.map(function(a){{return document.querySelector(a.getAttribute('href'))}});
function spy(){{var y=scrollY+120,c=-1;for(var i=0;i<S.length;i++)if(S[i]&&S[i].offsetTop<=y)c=i;L.forEach(function(a,i){{a.classList.toggle('on',i===c)}})}}
addEventListener('scroll',spy,{{passive:true}});spy();}})();
</script>'''

full=('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
 '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Alvos de Contratação · Botafogo</title>'
 '<style>'+CSS+EXTRA+'</style></head><body>'+body+'</body></html>')
open('estudo/reco_botafogo.html','w').write(full)
open('estudo/build/artifact_botafogo.html','w').write('<style>\n'+CSS+EXTRA+'\n</style>\n<title>Alvos de Contratação · Botafogo</title>\n'+body)
print('botafogo dashboard bytes:',len(full),'| XI:',len(xi))
