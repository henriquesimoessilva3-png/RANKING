# -*- coding: utf-8 -*-
"""Dashboard dos Alvos de Contratação — top-10 por posição, segmentado por mercado (buckets)."""
import json, html, os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(ROOT)
def esc(s): return html.escape(str(s))
R=json.loads(open('estudo/data/reco_botafogo.json',encoding='utf-8').read())
CSS=open('estudo/build/shared.css',encoding='utf-8').read()
GORD=R['grupos_ordem']; R2=R['recos']; BUCKETS=R['meta']['buckets']; BL=R['meta']['bucket_label']
GFULL={'Goleiro':'Goleiro','Zagueiro':'Zagueiro','Lateral':'Lateral','Volante':'Volante (1º volante)',
 'Medio':'Meio-campo','Meia':'Meia armador','Extremo':'Extremo (ponta)','Atacante':'Centroavante'}
BK_SHORT={'SUB23':'Sub-23 BR+SA','BR':'Brasileiros','SA':'Sul-americanos','IBER':'ESP·POR·ANG·A.Central','MUNDO':'Mundo'}
FLAG={'Brazil':'BRA','Argentina':'ARG','Uruguay':'URU','Colombia':'COL','Chile':'CHI','Ecuador':'EQU',
 'Paraguay':'PAR','Peru':'PER','Bolivia':'BOL','Venezuela':'VEN','Spain':'ESP','Portugal':'POR','Angola':'ANG',
 'France':'FRA','England':'ENG','Germany':'ALE','Italy':'ITA','Netherlands':'HOL','Belgium':'BEL','Mexico':'MEX'}
def flag(c): return FLAG.get(c, (c or '—')[:3].upper())
def mv(v): return (f'{v/1e6:.1f}M€'.replace('.0M','M') if v and v>=1e6 else '—')

def need_tag(inc):
    if not inc: return ('Sem titular fixo mapeado','need-hi')
    old=[i for i in inc if (i['age'] or 0)>=30]; top=inc[0]
    if old: return (f"Titular veterano ({old[0]['name']}, {old[0]['age']:.0f})",'need-hi')
    if (top['age'] or 0)>=27: return (f"{top['name']} ({top['age']:.0f}) — janela curta",'need-md')
    return (f"{top['name']} ({top['age']:.0f}) no elenco",'need-lo')

def scorebar(t):
    tip="Prontidão %.0f · Revenda %.0f" % (t['readiness'], t['resale'])
    w=max(4, t['score'])
    return ('<span class="scb" title="%s"><i style="width:%.0f%%"></i><b>%.0f</b></span>'
            % (tip, w, t['score']))

def row(i,t):
    teco='<span class="teco" title="Sem dados físicos — afinidade técnica-apenas">téc</span>' if t['tech_only'] else ''
    ref=esc(t['arch_refs'][0]) if t['arch_refs'] else ''
    return f'''<tr>
      <td class="rk">{i}</td>
      <td class="pl"><span class="pl-n">{esc(t['name'])} <span class="fl">{flag(t['birth'])}</span></span>
        <span class="pl-m">{esc(t['team'])} · {esc(t['league'])} · {t['age']:.0f}a · {t['minutes']}′ · {mv(t['mv'])}</span></td>
      <td class="ar"><span class="chip sm">{esc(t['arch'])}</span> <span class="arm">{t['arch_match']:.0f}%</span>{teco}
        <span class="arref">perfil {ref}</span></td>
      <td class="sc">{scorebar(t)}</td>
    </tr>'''

def bucket_table(g,b):
    lst=R2[g]['buckets'].get(b,[])
    if not lst:
        return f'<div class="bktable" data-bk="{b}"><p class="nolist">Sem candidato elegível neste mercado.</p></div>'
    rows=''.join(row(i+1,t) for i,t in enumerate(lst))
    return f'''<div class="bktable" data-bk="{b}">
      <table class="mkt"><thead><tr><th>#</th><th>Jogador</th><th>Arquétipo · afinidade</th><th>Score</th></tr></thead>
      <tbody>{rows}</tbody></table></div>'''

def block(g):
    r=R2[g]; nt,ncls=need_tag(r['incumbentes'])
    inc=', '.join(f"{i['name']} ({i['age']:.0f})" for i in r['incumbentes'][:3]) if r['incumbentes'] else '—'
    pills=''.join('<button data-bk="%s"%s>%s <em>%d</em></button>' % (
        b, (' class="on"' if b=="SUB23" else ''), esc(BK_SHORT[b]), len(r["buckets"].get(b,[]))) for b in BUCKETS)
    tables=''.join(bucket_table(g,b) for b in BUCKETS)
    return f'''<section class="posblock" id="g-{esc(g)}">
      <div class="pb-head"><h3>{esc(GFULL[g])}</h3><span class="need {ncls}">{esc(nt)}</span></div>
      <p class="pb-inc">Elenco atual: {esc(inc)}</p>
      <div class="bkpills">{pills}</div>
      <div class="bkwrap" data-active="SUB23">{tables}</div>
    </section>'''

# XI headline: melhor Sub-23 BR+SA por posição (núcleo de revenda)
xi=[]
for g in GORD:
    lst=R2[g]['buckets'].get('SUB23',[])
    if lst: xi.append((g,lst[0]))
xicards=''.join(f'''<div class="xic"><div class="pos">{esc(GFULL[g].split(" (")[0])}</div>
  <div class="nm">{esc(t['name'])} <span class="fl">{flag(t['birth'])}</span></div>
  <div class="mt">{esc(t['team'])} · {t['age']:.0f}a · {esc(t['league'])}</div>
  <div class="sc2">score {t['score']:.0f} · {esc(t['arch_tag'])}</div></div>''' for g,t in xi)

blocks=''.join(block(g) for g in GORD)
nav=''.join(f'<a href="#g-{esc(g)}">{esc(GFULL[g].split(" (")[0])}</a>' for g in GORD)

EXTRA='''
.posblock{border-top:1px solid var(--line);padding:22px 0}
.posblock:first-of-type{border-top:none}
.pb-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.pb-head h3{font-size:20px}
.need{font-size:11px;font-weight:660;padding:3px 10px;border-radius:20px}
.need-hi{color:#fff;background:var(--amber)}.need-md{color:var(--ink);background:color-mix(in srgb,var(--amber) 26%,transparent)}
.need-lo{color:var(--ink2);background:var(--surface2)}
.pb-inc{font-size:12px;color:var(--muted);margin:4px 0 12px}
.bkpills{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.bkpills button{font-family:inherit;font-size:11.5px;color:var(--ink2);background:var(--surface2);border:1px solid var(--line);
 padding:5px 11px;border-radius:20px;cursor:pointer;font-weight:600}
.bkpills button em{font-style:normal;color:var(--muted);font-size:10px}
.bkpills button.on{color:#fff;background:var(--accent);border-color:var(--accent)}
.bkpills button.on em{color:rgba(255,255,255,.75)}
.bktable{display:none}.bktable.show{display:block}
.tbl-wrap,.bkwrap{overflow-x:auto}
table.mkt{border-collapse:collapse;width:100%;min-width:640px}
.mkt th{font-size:10px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);font-weight:640;text-align:left;padding:7px 9px;border-bottom:1px solid var(--line)}
.mkt td{padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:middle;font-size:12.5px}
.mkt tr:last-child td{border-bottom:none}
.mkt .rk{color:var(--muted);font-weight:750;width:26px;text-align:center;font-variant-numeric:tabular-nums}
.pl-n{display:block;font-weight:640}
.fl{font-size:9px;font-weight:700;color:var(--accent);background:color-mix(in srgb,var(--accent) 12%,transparent);padding:1px 5px;border-radius:5px;letter-spacing:.03em;vertical-align:middle}
.pl-m{display:block;font-size:10.5px;color:var(--muted)}
.ar{max-width:230px}
.arm{font-size:11px;font-weight:680;color:var(--accent);font-variant-numeric:tabular-nums}
.arref{display:block;font-size:10px;color:var(--muted)}
.teco{font-size:8.5px;font-weight:700;color:var(--amber);border:1px solid color-mix(in srgb,var(--amber) 45%,var(--line));padding:0 4px;border-radius:4px;margin-left:4px;text-transform:uppercase}
.chip.sm{font-size:9px;padding:2px 7px}
.sc{width:120px}
.scb{display:flex;align-items:center;gap:7px}
.scb i{display:block;height:8px;border-radius:5px;background:linear-gradient(90deg,var(--accent),var(--accent2));min-width:6px}
.scb b{font-size:13px;font-variant-numeric:tabular-nums;font-weight:720}
.nolist{font-size:12.5px;color:var(--muted);padding:10px 0}
.xi{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:8px}
.xic{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px;box-shadow:var(--shadow)}
.xic .pos{font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:var(--accent);font-weight:700}
.xic .nm{font-size:15px;font-weight:700;margin:3px 0 1px}
.xic .mt{font-size:11px;color:var(--muted)}
.xic .sc2{font-size:12px;color:var(--ink2);margin-top:6px;font-weight:600}
.mkey{display:flex;flex-wrap:wrap;gap:12px;margin-top:10px;font-size:12px;color:var(--ink2)}
.mkey b{color:var(--ink)}
@media(max-width:760px){.xi{grid-template-columns:repeat(2,1fr)}.ar .arref{display:none}}
'''

body=f'''<div id="top"></div>
<header class="site"><div class="wrap site-in">
  <div class="brand"><span class="dot"></span> Alvos de Contratação · Botafogo</div>
  <nav class="jump">{nav}</nav><button id="theme">◐</button>
</div></header>
<main class="wrap">
  <section class="hero">
    <p class="eyebrow">Titular agora · revenda depois — por mercado</p>
    <h1>Alvos de contratação: top-10 por posição, em cada mercado</h1>
    <p class="lede">Para cada posição, os <b>10 melhores alvos em cada mercado de origem</b>, ranqueados por um score que combina <b>prontidão</b> (nível, minutos, força da liga) e <b>potencial de revenda</b> (afinidade a um arquétipo valorizado, juventude e velocidade). Universo: todas as ligas com ≥ {R['meta']['min_min']} minutos; atletas já do Botafogo excluídos.</p>
    <div class="mkey">
      <span><b>Mercados:</b></span>
      <span><b>Sub-23 BR+SA</b> — núcleo de revenda</span><span><b>Brasileiros</b></span><span><b>Sul-americanos</b></span>
      <span><b>ESP·POR·ANG·A.Central</b> — mercado lusófono/hispano</span><span><b>Mundo</b></span>
    </div>
    <h2 class="xih">XI Sub-23 BR+SA — o núcleo de revenda</h2>
    <div class="xi">{xicards}</div>
  </section>
  <section class="finding">
    <h2>Como o score é montado</h2>
    <p>{esc(R['meta']['formula'])} A revenda decai com a idade (jogador veterano não se revende com lucro). Cada mercado é ranqueado no seu próprio contexto (padronização por mercado × posição).</p>
  </section>
  <section class="finding">
    <h2>Posição por posição · escolha o mercado</h2>
    <p class="sub">Clique nos mercados para alternar a lista. O selo <span class="teco">téc</span> indica jogador sem dados de rastreamento físico (afinidade técnica-apenas, menor confiança).</p>
    {blocks}
  </section>
  <footer class="foot">
    <h3>Leitura & limites</h3>
    <ul>
      <li><b>Prontidão</b> = 45% nível (percentil do índice no mercado) + 25% minutos + 30% força da liga. <b>Revenda</b> = 50% afinidade ao arquétipo premium + 25% juventude + 25% velocidade, com decaimento por idade.</li>
      <li><b>Filtro de estilo + nível, não de viabilidade de contratação.</b> Aparecem perfis de elite (ex.: astros de clubes grandes) que servem de referência do mercado, não necessariamente contratáveis. Cruzar com valor, contrato e disposição de venda é passo obrigatório.</li>
      <li><b>Padronização por mercado × posição:</b> cada bucket é ranqueado no próprio contexto; os scores são comparáveis dentro do mercado, não necessariamente entre mercados de níveis muito diferentes.</li>
      <li>Sem dados físicos (<span class="teco">téc</span>): afinidade calculada só com métricas técnicas — menor confiança, sobretudo para arquétipos definidos por velocidade/intensidade.</li>
    </ul>
  </footer>
</main>
<script>
(function(){{
  var root=document.documentElement,btn=document.getElementById('theme');
  function set(t){{root.setAttribute('data-theme',t);try{{localStorage.setItem('e5t',t)}}catch(e){{}}}}
  var s;try{{s=localStorage.getItem('e5t')}}catch(e){{}}if(s)set(s);
  btn.onclick=function(){{var d=root.getAttribute('data-theme')==='dark'||(!root.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme:dark)').matches);set(d?'light':'dark')}};
  document.querySelectorAll('.posblock').forEach(function(pb){{
    var pills=pb.querySelectorAll('.bkpills button'), tables=pb.querySelectorAll('.bktable');
    function show(bk){{
      pills.forEach(function(p){{p.classList.toggle('on',p.getAttribute('data-bk')===bk)}});
      tables.forEach(function(t){{t.classList.toggle('show',t.getAttribute('data-bk')===bk)}});
    }}
    pills.forEach(function(p){{p.onclick=function(){{show(p.getAttribute('data-bk'))}}}});
    show('SUB23');
  }});
  var L=[].slice.call(document.querySelectorAll('.jump a')),S=L.map(function(a){{return document.querySelector(a.getAttribute('href'))}});
  function spy(){{var y=scrollY+120,c=-1;for(var i=0;i<S.length;i++)if(S[i]&&S[i].offsetTop<=y)c=i;L.forEach(function(a,i){{a.classList.toggle('on',i===c)}})}}
  addEventListener('scroll',spy,{{passive:true}});spy();
}})();
</script>'''

full=('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
 '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Alvos de Contratação · Botafogo</title>'
 '<style>'+CSS+EXTRA+'</style></head><body>'+body+'</body></html>')
open('estudo/reco_botafogo.html','w',encoding='utf-8').write(full)
open('estudo/build/artifact_botafogo.html','w',encoding='utf-8').write('<style>\n'+CSS+EXTRA+'\n</style>\n<title>Alvos de Contratação · Botafogo</title>\n'+body)
print('reco_botafogo.html bytes:',len(full),'| XI:',len(xi))
