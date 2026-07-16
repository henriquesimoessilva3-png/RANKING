# -*- coding: utf-8 -*-
"""Dashboard dos dossiês individuais dos jogadores-referência + reconciliação scout x cluster."""
import json, html, math, os
def esc(s): return html.escape(str(s))
R=json.load(open('estudo/data/dossies_refs.json'))
CSS=open('estudo/build/shared.css').read()
GORD=R['grupos_ordem']
GFULL={'Goleiro':'Goleiros','Zagueiro':'Zagueiros','Lateral':'Laterais','Volante':'Volantes',
 'Medio':'Médios','Meia':'Meias','Extremo':'Extremos','Atacante':'Atacantes'}

def mv(v): return (f'{v/1e6:.0f}M€' if v and v>=1e6 else '—')
def foot(f): return {'direito':'destro','esquerdo':'canhoto','ambidextro':'ambidestro'}.get(f,f or '—')

# radar SVG (8 axes, 0-100 percentil)
def radar(axes, size=172):
    cx=cy=size/2; R0=size/2-24; n=len(axes)
    if n<3: return ''
    def pt(i,r):
        a=-math.pi/2+2*math.pi*i/n
        return (cx+r*math.cos(a), cy+r*math.sin(a))
    rings=''
    for g in (25,50,75,100):
        pts=' '.join(f'{pt(i,R0*g/100)[0]:.1f},{pt(i,R0*g/100)[1]:.1f}' for i in range(n))
        rings+=f'<polygon points="{pts}" class="rg"/>'
    spokes=''
    for i in range(n):
        x,y=pt(i,R0); spokes+=f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}" class="rs"/>'
    poly=' '.join(f'{pt(i,R0*max(2,a["pct"])/100)[0]:.1f},{pt(i,R0*max(2,a["pct"])/100)[1]:.1f}' for i,a in enumerate(axes))
    dots=''.join(f'<circle cx="{pt(i,R0*max(2,a["pct"])/100)[0]:.1f}" cy="{pt(i,R0*max(2,a["pct"])/100)[1]:.1f}" r="2.4" class="rd"/>' for i,a in enumerate(axes))
    labs=''
    for i,a in enumerate(axes):
        lx,ly=pt(i,R0+11)
        anchor='middle'
        if lx<cx-6: anchor='end'
        elif lx>cx+6: anchor='start'
        labs+=f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" class="rl">{esc(a["ax"])}</text>'
    return (f'<svg viewBox="0 0 {size} {size}" class="radar" role="img">'
            f'{rings}{spokes}<polygon points="{poly}" class="rp"/>{dots}{labs}</svg>')

def strbar(t):
    p=t['pct']; p5=t.get('pct5')
    tick=f'<i class="pb-best" style="left:{p5}%" title="entre a elite top-5: p{p5:.0f}"></i>' if p5 is not None else ''
    tag='FÍS' if t['kind']=='fis' else 'TÉC'
    return (f'<div class="pbar"><span class="pb-m">{esc(t["lab"])}</span>'
            f'<span class="pb-cat">{tag}</span>'
            f'<span class="pb-track"><i class="pb-fill" style="width:{max(2,p):.0f}%"></i><i class="pb-50"></i>{tick}</span>'
            f'<span class="pb-v">p{p:.0f}</span></div>')

def card(d):
    strengths=''.join(strbar(t) for t in d['top'][:6])
    ident=f"{esc(d['team'])} · {esc(d['league'])}"
    age=f"{d['age']:.0f} anos" if d.get('age') else '—'
    h=f"{d['height']} cm" if d.get('height') else ''
    same=d['arq_scout'].lower().split()[0][:5]
    # heurística de concordância p/ badge
    return f'''<article class="dcard">
      <div class="dc-head">
        <div><h4>{esc(d['nome'])}</h4><span class="dc-id">{ident}</span></div>
        <div class="dc-meta">{age}{' · '+h if h else ''} · {foot(d.get('foot'))}<br>{d['minutes']}′ · {mv(d.get('mv'))} · {d.get('n_temporadas','?')} temps</div>
      </div>
      <div class="dc-body">
        <div class="dc-radar">{radar(d['radar'])}</div>
        <div class="dc-str"><div class="dc-lab">No que é elite <em>(percentil vs. mundo · ▎ = vs. elite top-5)</em></div>{strengths}</div>
      </div>
      <div class="dc-arch">
        <div class="aq"><span>Arquétipo do scout</span><b>{esc(d['arq_scout'])}</b></div>
        <div class="aq-arrow">↔</div>
        <div class="aq"><span>Cluster do estudo (Fase 1)</span><b>{esc(d['arq_meu'])} <small>{d['arq_meu_match']:.0f}%</small></b></div>
      </div>
    </article>'''

sections=''
for g in GORD:
    ds=[d for d in R['dossies'] if d['grupo']==g and d.get('found')]
    if not ds: continue
    cards=''.join(card(d) for d in ds)
    sections+=f'''<section class="group" id="g-{esc(g)}">
      <div class="group-h"><h3>{esc(GFULL[g])}</h3><span class="group-meta">{len(ds)} referências mundiais</span></div>
      <div class="dgrid">{cards}</div>
    </section>'''

nav=''.join(f'<a href="#g-{esc(g)}">{esc(GFULL[g])}</a>' for g in GORD if any(d['grupo']==g and d.get('found') for d in R['dossies']))
missing=[d['nome'] for d in R['dossies'] if not d.get('found')]

EXTRA='''
.dgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:16px;margin-top:10px}
.dcard{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:12px}
.dc-head{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}
.dc-head h4{font-size:17px}
.dc-id{font-size:12px;color:var(--ink2);font-weight:560}
.dc-meta{font-size:10.5px;color:var(--muted);text-align:right;line-height:1.35;white-space:nowrap}
.dc-body{display:grid;grid-template-columns:176px 1fr;gap:22px;align-items:center}
.radar{width:100%;height:auto;overflow:visible}
.radar .rg{fill:none;stroke:var(--line)}
.radar .rs{stroke:var(--line)}
.radar .rp{fill:color-mix(in srgb,var(--accent) 24%,transparent);stroke:var(--accent);stroke-width:1.6}
.radar .rd{fill:var(--accent)}
.radar .rl{fill:var(--muted);font-size:7.6px;font-weight:600}
.dc-lab{font-size:10.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);font-weight:640;margin-bottom:8px}
.dc-lab em{text-transform:none;letter-spacing:0;font-weight:500}
.dc-str .pbar{grid-template-columns:minmax(96px,1.2fr) 34px 1fr 34px;gap:8px;padding:2.5px 0}
.dc-arch{display:grid;grid-template-columns:1fr 24px 1fr;align-items:center;gap:8px;border-top:1px solid var(--line);padding-top:11px}
.aq span{display:block;font-size:9.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);font-weight:640;margin-bottom:3px}
.aq b{font-size:12.5px;line-height:1.2}
.aq b small{color:var(--accent);font-weight:640}
.aq-arrow{text-align:center;color:var(--muted);font-size:16px}
@media(max-width:520px){.dc-body{grid-template-columns:1fr}.dgrid{grid-template-columns:1fr}}
'''

body=f'''<div id="top"></div>
<header class="site"><div class="wrap site-in">
  <div class="brand"><span class="dot"></span> Dossiês · Referências Mundiais</div>
  <nav class="jump">{nav}</nav><button id="theme">◐</button>
</div></header>
<main class="wrap">
  <section class="hero">
    <p class="eyebrow">Os benchmarks do ranking, um a um</p>
    <h1>Dossiê dos jogadores-referência — no que cada um é elite</h1>
    <p class="lede">Os {R['meta']['found']} jogadores usados hoje como <b>referência mundial</b> por posição (lista validada com o scout), cada um com o seu radar de percentis <b>vs. o mundo</b>, as métricas em que é elite, e a <b>reconciliação</b> entre o arquétipo do scout e o cluster estatístico do estudo (Fase 1).</p>
    <div class="kpis">
      <div class="kpi"><b>{R['meta']['found']}</b><span>referências analisadas</span></div>
      <div class="kpi"><b>8</b><span>posições cobertas</span></div>
      <div class="kpi"><b>vs. mundo</b><span>percentis sobre todos os titulares (≥900′) da posição</span></div>
    </div>
  </section>
  <section class="finding">
    <h2>Reavaliação — o scout e os dados concordam?</h2>
    <p>Em geral, <b>sim</b>: os arquétipos do scout batem com os clusters do estudo nos casos claros — <b>Rúben Dias</b> e <b>Cubarsí</b> como construtores, <b>Rodri/Vitinha/Pedri</b> como organizadores, <b>Vinicius/Doku/Olise/Yamal</b> como craques-criadores, <b>Donnarumma</b> como goleiro de rendimento. Isso valida o esqueleto de arquétipos da Fase 1.</p>
    <p>As <b>divergências</b> é que informam: <b>Militão</b>, rotulado "balanceado", é estatisticamente um <b>defensor de espaço</b> (velocidade de ponta no p99); <b>Alexander-Arnold</b> aparece como <b>lateral posicional</b> — confirma que aquele cluster de "baixa intensidade" é, na verdade, o <b>playmaker</b> de lateral, não um jogador limitado; <b>Kimmich</b> tem passe de p100 mas seu volume o joga para "motor", mostrando o limite de rotular jogadores únicos por um só cluster. <b>Conclusão prática:</b> os arquétipos servem como eixo, mas jogadores de elite são frequentemente <b>blends</b> — e os moldes da Fase 2 ganham precisão se ancorados também nestes refs validados, não só nos centroides.</p>
    {'<p class="disc">Fora do snapshot jun26 (lesão/transferência), sem dossiê: '+esc(', '.join(missing))+'.</p>' if missing else ''}
  </section>
  <section class="finding">
    <h2>Os dossiês</h2>
    <p class="sub">Radar = percentil vs. todos os titulares do mundo na posição. As barras mostram onde o jogador é elite; a marca roxa (▎) indica o percentil dentro da própria elite das 5 grandes ligas.</p>
    {sections}
  </section>
  <footer class="foot">
    <h3>Notas</h3>
    <ul>
      <li>Percentis calculados sobre todos os jogadores do mundo (≥ 900 min) na mesma posição de dados. Métricas "menor é melhor" (faltas, gols sofridos, tempo de arranque) são invertidas.</li>
      <li>A posição usada é a da base de dados. <b>Messi</b> aparece como extremo (classificação dos dados), embora o scout o liste como meia.</li>
      <li>O "% " ao lado do cluster é a confiança (cosseno) do enquadramento no arquétipo mais próximo do estudo — baixo = jogador é um blend entre arquétipos.</li>
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
 '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Dossiês · Referências Mundiais</title>'
 '<style>'+CSS+EXTRA+'</style></head><body>'+body+'</body></html>')
open('estudo/dossies_refs.html','w').write(full)
open('estudo/build/artifact_dossies.html','w').write('<style>\n'+CSS+EXTRA+'\n</style>\n<title>Dossiês · Referências Mundiais</title>\n'+body)
print('dossies dashboard bytes:',len(full),'| found:',R['meta']['found'],'| missing:',missing)
