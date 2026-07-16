# -*- coding: utf-8 -*-
"""Monta o DOSSIÊ ÚNICO (estudo/dossie_completo.html) juntando os materiais já prontos
num shell único (1 header, 1 nav em abas, 1 tema, 1 CSS):
  1. Ligas × Mundo            (estudo/index.html)
  2. Arquétipos               (renderizado de estudo/data/arquetipos_top5.json; placeholder p/ o :5064)
  3. Dossiê 42 referências    (estudo/dossies_refs.html)
  4. Alvos de Contratação     (estudo/reco_botafogo.html)

Extrai o <main> de cada HTML, remove header/nav/script individuais, deduplica o shared.css,
namespaceia os IDs por material (evita colisão) e envolve tudo em abas."""
import re, json, html, os
def esc(s): return html.escape(str(s))

SHARED=open('estudo/build/shared.css').read()

def extract(path):
    s=open(path).read()
    style=re.search(r'<style>(.*?)</style>', s, re.S).group(1)
    main=re.search(r'<main class="wrap">.*</main>', s, re.S).group(0)
    return style, main

def extra_of(style):
    """Retorna o bloco EXTRA = tudo após o shared.css (os 3 arquivos começam por ele)."""
    if style.startswith(SHARED):
        return style[len(SHARED):]
    # fallback: alinhar pelo fim do shared
    tail=SHARED[-40:]; i=style.find(tail)
    return style[i+len(tail):] if i!=-1 else style

def namespace(mainhtml, prefix):
    mainhtml=re.sub(r'id="([^"]+)"', lambda m: f'id="{prefix}-{m.group(1)}"', mainhtml)
    mainhtml=re.sub(r'href="#([^"]+)"', lambda m: f'href="#{prefix}-{m.group(1)}"', mainhtml)
    return mainhtml

st1,main1=extract('estudo/index.html')
st2,main2=extract('estudo/dossies_refs.html')
st3,main3=extract('estudo/reco_botafogo.html')
EXTRA_DOSSIES=extra_of(st2)
EXTRA_BOTA=extra_of(st3)

main1=namespace(main1,'m1')
main3=namespace(main3,'m3')       # alvos (ids g-*)
main2ns=namespace(main2,'m2b')    # dossiê (ids g-*)

# ---------- Aba 2: Arquétipos (dos nossos moldes) ----------
ARQ=json.load(open('estudo/data/arquetipos_top5.json'))
GORD=['Goleiro','Zagueiro','Lateral','Volante','Medio','Meia','Extremo','Atacante']
GFULL={'Goleiro':'Goleiros','Zagueiro':'Zagueiros','Lateral':'Laterais','Volante':'Volantes',
 'Medio':'Médios','Meia':'Meias','Extremo':'Extremos','Atacante':'Atacantes'}
def mvfmt(v): return (f'{v/1e6:.1f}M€'.replace('.0M','M') if v and v>=1e6 else '—')
def arq_cards(g):
    gd=ARQ['grupos'].get(g)
    if not gd: return ''
    cards=''
    for a in gd['arquetipos']:
        refs=', '.join(a['referencias'][:4])
        cards+=f'''<article class="acard">
          <div class="ac-h"><h4>{esc(a['nome'])}</h4><span class="chip">{esc(a['tag'])}</span></div>
          <p class="ac-desc">{esc(a['descricao'])}</p>
          <div class="ac-stats"><div><b>{a['n']}</b><span>jogadores</span></div>
            <div><b>{a['indice_medio']}</b><span>índice</span></div>
            <div><b>{a['idade_media']}</b><span>idade</span></div>
            <div><b>{mvfmt(a['valor_mediano_eur'])}</b><span>valor</span></div></div>
          <div class="ac-refs"><span>Referências</span>{esc(refs)}</div>
          <div class="ac-scout"><span>▸ Alvo na América do Sul</span>{esc(a['alvo_scouting'])}</div>
        </article>'''
    return f'''<section class="group"><div class="group-h"><h3>{esc(GFULL[g])}</h3>
      <span class="group-meta">{gd['n']} jogadores · {len(gd['arquetipos'])} arquétipos</span></div>
      <div class="acards">{cards}</div></section>'''

arq_sections=''.join(arq_cards(g) for g in GORD)
main2_arq=f'''<main class="wrap">
  <section class="hero">
    <p class="eyebrow">Os moldes do estudo · 29 arquétipos em 8 grupos</p>
    <h1>Arquétipos — o vocabulário de perfis por posição</h1>
    <p class="lede">Os {sum(len(ARQ['grupos'][g]['arquetipos']) for g in GORD)} arquétipos derivados das 5 grandes ligas (Fase 1), com referência real e alvo de scouting. Esta aba é o <b>ponto de encontro</b> com o card de arquétipos que roda em <code>localhost:5064</code>: na sessão local, este conteúdo pode ser substituído ou complementado por aquele material — ver <code>estudo/CONTEXT_UNIFICACAO.md</code> §5.</p>
    <div class="callout"><b>Placeholder de integração.</b> Cards renderizados a partir de <code>estudo/data/arquetipos_top5.json</code>. Para casar com o material do <code>:5064</code>, confirmar se são os mesmos 29 arquétipos (mesma nomenclatura) e então portar/regerar no mesmo estilo.</div>
  </section>
  <section class="finding"><h2>Arquétipos por posição</h2>{arq_sections}</section>
</main>'''

TABS=[('ligas','Ligas × Mundo',main1),
      ('arquetipos','Arquétipos',main2_arq),
      ('dossies','Dossiê · 42 referências',main2ns),
      ('alvos','Alvos de Contratação',main3)]

UNIFY_CSS='''
/* --- shell unificado --- */
.tabs{display:flex;gap:2px;overflow-x:auto;margin-left:auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tabs button{font-family:inherit;font-size:12.5px;color:var(--ink2);background:none;border:none;
 padding:7px 11px;border-radius:8px;white-space:nowrap;font-weight:600;cursor:pointer}
.tabs button:hover{background:var(--surface2);color:var(--ink)}
.tabs button.on{color:var(--accent);background:color-mix(in srgb,var(--accent) 12%,transparent)}
.material{display:none}
.material.active{display:block;animation:fade .25s ease}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.material>main{padding-top:6px}
/* cards de arquétipo (aba 2) */
.acards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin-top:8px}
.acard{background:var(--surface);border:1px solid var(--line);border-radius:15px;padding:16px;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:10px}
.ac-h{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.ac-h h4{font-size:16px}
.ac-desc{font-size:12.5px;color:var(--ink2);margin:0}
.ac-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;padding:9px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.ac-stats b{display:block;font-size:15px;font-variant-numeric:tabular-nums}
.ac-stats span{font-size:9.5px;color:var(--muted)}
.ac-refs{font-size:11.5px;color:var(--ink2)}
.ac-refs span,.ac-scout span{display:block;font-size:10px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);font-weight:660;margin-bottom:3px}
.ac-scout{font-size:11.5px;color:var(--ink2);background:var(--surface2);border-radius:10px;padding:10px;margin-top:auto}
.ac-scout span{color:var(--accent)}
.callout{margin-top:18px;background:color-mix(in srgb,var(--amber) 12%,transparent);border:1px solid color-mix(in srgb,var(--amber) 40%,var(--line));border-radius:12px;padding:14px 16px;font-size:13px;color:var(--ink2)}
code{font-family:var(--mono);font-size:.9em;background:var(--surface2);padding:1px 5px;border-radius:5px}
'''

tabbtns=''.join('<button data-t="%s"%s>%s</button>' % (k,(' class="on"' if i==0 else ''),esc(lbl)) for i,(k,lbl,_) in enumerate(TABS))
mats=''.join(f'<section class="material{" active" if i==0 else ""}" data-m="{k}">{body}</section>'
             for i,(k,lbl,body) in enumerate(TABS))

STYLE='<style>'+SHARED+EXTRA_DOSSIES+EXTRA_BOTA+UNIFY_CSS+'</style>'

body=f'''<header class="site"><div class="wrap site-in">
  <div class="brand"><span class="dot"></span> Dossiê Completo · Scouting Botafogo</div>
  <nav class="tabs">{tabbtns}</nav>
  <button id="theme" aria-label="Alternar tema">◐</button>
</div></header>
{mats}
<script>
(function(){{
  var root=document.documentElement,btn=document.getElementById('theme');
  function set(t){{root.setAttribute('data-theme',t);try{{localStorage.setItem('e5t',t)}}catch(e){{}}}}
  var s;try{{s=localStorage.getItem('e5t')}}catch(e){{}}if(s)set(s);
  btn.onclick=function(){{var d=root.getAttribute('data-theme')==='dark'||(!root.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme:dark)').matches);set(d?'light':'dark')}};
  var tabs=[].slice.call(document.querySelectorAll('.tabs button'));
  var mats=[].slice.call(document.querySelectorAll('.material'));
  function show(k){{
    tabs.forEach(function(b){{b.classList.toggle('on',b.getAttribute('data-t')===k)}});
    mats.forEach(function(m){{m.classList.toggle('active',m.getAttribute('data-m')===k)}});
    try{{history.replaceState(null,'','#'+k)}}catch(e){{}}
    window.scrollTo(0,0);
  }}
  tabs.forEach(function(b){{b.onclick=function(){{show(b.getAttribute('data-t'))}}}});
  var h=(location.hash||'').replace('#','');
  if(h&&tabs.some(function(b){{return b.getAttribute('data-t')===h}}))show(h);
}})();
</script>'''

full=('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
 '<meta name="viewport" content="width=device-width,initial-scale=1">'
 '<title>Dossiê Completo · Scouting Botafogo</title>'
 '<meta name="description" content="Ligas x mundo, arquétipos, dossiê das 42 referências mundiais e alvos de contratação do Botafogo.">'
 +STYLE+'</head><body>'+body+'</body></html>')
open('estudo/dossie_completo.html','w').write(full)
# versão artifact (sem doctype/head/body)
open('estudo/build/artifact_completo.html','w').write('<style>'+SHARED+EXTRA_DOSSIES+EXTRA_BOTA+UNIFY_CSS+'</style>\n<title>Dossiê Completo · Scouting Botafogo</title>\n'+body)
print('dossie_completo.html bytes:',len(full))
print('abas:',[k for k,_,_ in TABS])
print('EXTRA_DOSSIES ok:',bool(EXTRA_DOSSIES),'| EXTRA_BOTA ok:',bool(EXTRA_BOTA))
