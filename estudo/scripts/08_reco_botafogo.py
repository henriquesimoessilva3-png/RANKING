# -*- coding: utf-8 -*-
"""Recomendação Botafogo: por posição, o alvo jovem sul-americano que (a) já pode ser
titular e entregar resultado e (b) tem upside de revenda ao mercado europeu.
Score = Prontidão (nível/minutos/força da liga) x Revenda (afinidade a arquétipo premium,
juventude, ferramentas físicas premium). Exclui atletas já do Botafogo."""
import json, math, statistics as st, os, bisect
os.makedirs('estudo/build',exist_ok=True)
D='data/jun26/'
IDADE_MAX=23
MIN_MIN=900

rk=json.load(open(D+'rankings.json')); recs=rk['records']
det=json.load(open(D+'kpis_detail.json')); KPIS=det['_kpis']; DET=det['data']
sc=json.load(open(D+'skillcorner.json'))
ARQ=json.load(open('estudo/data/arquetipos_top5.json'))

PHYS=['total_distance_p90','running_distance_p90','hi_distance_p90','hi_actions_p90','hsr_distance_p90',
 'hsr_count_p90','sprint_distance_p90','n_sprints_p90','psv99','top5_psv99','high_accel_p90','med_accel_p90',
 'high_decel_p90','med_decel_p90','explosive_accel_to_sprint','cod_count_p90','m_min','m_min_tip','m_min_otip',
 'top3_time_to_sprint','top3_time_to_hsr']
SA_LEAGUES={'Brasil A','Brasil B','Argentina A','Uruguai','Colombia A','Chile','Equador A','Paraguai','Peru','Venezuela','Bolivia'}
LEAGUE_W={'Brasil A':1.00,'Argentina A':0.92,'Colombia A':0.78,'Chile':0.75,'Uruguai':0.76,'Paraguai':0.72,
 'Equador A':0.72,'Peru':0.66,'Brasil B':0.70,'Venezuela':0.55,'Bolivia':0.50}
GROUPS={'Zagueiro':['Zagueiro - Direita','Zagueiro - Esquerda'],'Lateral':['Lateral Direito','Lateral Esquerdo'],
 'Volante':['Volante'],'Medio':['Medio'],'Meia':['Meia'],'Extremo':['Extremo - Direita','Extremo - Esquerda'],
 'Atacante':['Atacante'],'Goleiro':['Goleiro']}
POS2GROUP={p:g for g,ps in GROUPS.items() for p in ps}
PREMIUM={'Zagueiro':['Construtor','Defensor de espaço','móvel'],'Lateral':['ofensivo','Motor'],
 'Volante':['Organizador'],'Medio':['Organizador','Condutor','intensidade'],'Meia':['Armador','Condutor'],
 'Extremo':['Craque','Driblador'],'Atacante':['Falso-9','profundidade'],'Goleiro':['rendimento','Construtor']}
def is_prem(g,nome): return any(k.lower() in nome.lower() for k in PREMIUM.get(g,[]))

def kdict(pk):
    arr=DET.get(pk); return {KPIS[e['k']]:e['v'] for e in arr} if arr else {}
def physd(pk):
    s=sc.get(pk)
    if not s: return {}
    m=s.get('metrics') or {}
    return {k:m.get(k) for k in PHYS if m.get(k) is not None}
def getf(kd,ph,f):
    v=kd.get(f); return v if v is not None else ph.get(f)

# incumbentes atuais do Botafogo por grupo (contexto de necessidade)
incum={g:[] for g in GROUPS}
for r in recs:
    if r.get('isBotafogo'):
        g=POS2GROUP.get(r['position_group_pt'])
        if g: incum[g].append({'name':r['Player'],'age':r.get('Age'),'min':r.get('Minutes played'),'pos':r['position_group_pt']})
for g in incum: incum[g].sort(key=lambda x:-(x['min'] or 0))

# pool SA c/ físico (todas idades p/ referência); candidatos jovens não-Botafogo
sa=[]
for r in recs:
    if r['league'] not in SA_LEAGUES or (r.get('Minutes played') or 0)<600: continue
    pos=r['position_group_pt']
    if pos not in POS2GROUP: continue
    ph=physd(r['primary_key'])
    if not ph: continue
    sa.append({'pk':r['primary_key'],'name':r.get('tm_nome') or r['Player'],'team':r['Team'],'league':r['league'],
        'pos':pos,'group':POS2GROUP[pos],'age':r.get('Age'),'mv':r.get('Market value'),'minutes':r.get('Minutes played'),
        'height':r.get('Height'),'foot':r.get('Foot'),'overall':r.get('overall'),'bota':bool(r.get('isBotafogo')),
        'kd':kdict(r['primary_key']),'ph':ph})

def pctrank(arr,v):
    if not arr: return 0.5
    i=bisect.bisect_right(sorted(arr),v); return i/len(arr)

recos={}
for g,gd in ARQ['grupos'].items():
    feats=gd['features']
    pool=[p for p in sa if p['group']==g]
    if not pool: recos[g]={'cands':[],'incumbentes':incum[g],'n_pool':0}; continue
    # z-frame vs média SA da posição
    med={f:(st.median([v for v in (getf(p['kd'],p['ph'],f) for p in pool) if v is not None]) or 0.0) for f in feats}
    mu={}; sd={}
    for f in feats:
        col=[getf(p['kd'],p['ph'],f) if getf(p['kd'],p['ph'],f) is not None else med[f] for p in pool]
        mu[f]=st.mean(col); sd[f]=(st.pstdev(col) if len(col)>1 else 0) or 1.0
    overalls=[p['overall'] for p in pool if p['overall'] is not None]
    minutes=[p['minutes'] for p in pool]
    psv=[p['ph'].get('psv99') for p in pool if p['ph'].get('psv99') is not None]
    cands=[]
    for p in pool:
        if p['bota']: continue
        if (p['age'] or 99)>IDADE_MAX: continue
        if (p['minutes'] or 0)<MIN_MIN: continue
        real=sum(1 for f in feats if getf(p['kd'],p['ph'],f) is not None)
        if real/len(feats)<0.7: continue
        z={f:((getf(p['kd'],p['ph'],f) if getf(p['kd'],p['ph'],f) is not None else med[f])-mu[f])/sd[f] for f in feats}
        # afinidade a cada arquétipo
        affs=[]
        for a in gd['arquetipos']:
            c=a['centroide_z']; cf=list(dict.fromkeys(f for f in feats if abs(c.get(f,0))>1e-9))
            cn=math.sqrt(sum(c[f]**2 for f in cf))or 1; zn=math.sqrt(sum(z[f]**2 for f in cf))or 1
            cos=sum(z[f]*c.get(f,0) for f in cf)/(zn*cn)
            affs.append((cos,a))
        best=max(affs,key=lambda x:x[0])
        prem=[(cos,a) for cos,a in affs if is_prem(g,a['nome'])]
        best_prem=max(prem,key=lambda x:x[0]) if prem else best
        # componentes
        q_level=pctrank(overalls,p['overall']) if p['overall'] is not None else 0.4
        q_min=min(1.0,(p['minutes'] or 0)/2200)
        lw=LEAGUE_W.get(p['league'],0.6)
        readiness=0.45*q_level+0.25*q_min+0.30*lw
        q_prem=max(0.0,best_prem[0])
        q_youth=max(0.0,min(1.0,(24-(p['age'] or 24))/6.0))
        q_speed=pctrank(psv,p['ph'].get('psv99')) if p['ph'].get('psv99') is not None else 0.5
        resale=0.50*q_prem+0.25*q_youth+0.25*q_speed
        score=0.5*readiness+0.5*resale
        # destaques (features premium onde é forte)
        c=best_prem[1]['centroide_z']; cf=[f for f in feats if c.get(f,0)>0]
        zz=sorted(((f,z[f]) for f in cf),key=lambda kv:-kv[1])[:3]
        cands.append({'name':p['name'],'team':p['team'],'league':p['league'],'age':p['age'],'minutes':p['minutes'],
            'height':p['height'],'foot':p['foot'],'mv':p['mv'],'overall':p['overall'],
            'arch':best_prem[1]['nome'],'arch_tag':best_prem[1]['tag'],'arch_match':round(q_prem*100,1),
            'arch_refs':best_prem[1]['referencias'][:3],'best_any':best[1]['nome'],
            'readiness':round(readiness*100,1),'resale':round(resale*100,1),'score':round(score*100,1),
            'q_level':round(q_level*100),'q_min':round(q_min*100),'league_w':lw,
            'q_youth':round(q_youth*100),'q_speed':round(q_speed*100),
            'traits':[{'lab':f,'z':round(z[f],2)} for f,_ in zz]})
    cands.sort(key=lambda x:-x['score'])
    recos[g]={'nome':gd['nome'],'cands':cands,'incumbentes':incum[g],'n_pool':len(pool)}

out={'meta':{'idade_max':IDADE_MAX,'min_min':MIN_MIN,'ligas':sorted(SA_LEAGUES),'league_w':LEAGUE_W,
     'formula':'Score = 50% Prontidão (nível 45% + minutos 25% + força da liga 30%) + 50% Revenda (afinidade premium 50% + juventude 25% + velocidade 25%)'},
     'grupos_ordem':['Goleiro','Zagueiro','Lateral','Volante','Medio','Meia','Extremo','Atacante'],'recos':recos}
json.dump(out,open('estudo/data/reco_botafogo.json','w'),ensure_ascii=False,indent=1)

print('== RECOMENDAÇÃO BOTAFOGO — nº1 por posição ==')
for g in out['grupos_ordem']:
    r=recos[g]; inc=', '.join(f"{i['name']}({i['age']:.0f})" for i in r['incumbentes'][:2]) if r['incumbentes'] else '—'
    if not r['cands']:
        print(f"\n{g:9s} | elenco atual: {inc}\n   (sem candidato jovem elegível na base com físico)"); continue
    t=r['cands'][0]
    print(f"\n{g:9s} | elenco atual: {inc}")
    for t in r['cands'][:3]:
        print(f"   score {t['score']:.0f} (pront {t['readiness']:.0f}/rev {t['resale']:.0f}) {t['name']} ({t['team']}, {t['league']}, {t['age']:.0f}a, {t['minutes']}min) -> {t['arch']} {t['arch_match']:.0f}% [{', '.join(t['arch_refs'][:2])}]")
