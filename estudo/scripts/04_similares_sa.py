# -*- coding: utf-8 -*-
"""Fase 2 — pontua jovens sul-americanos por similaridade aos arquétipos das 5 grandes ligas.
Método: para cada jogador jovem (<=IDADE_MAX, >=MIN_MIN) de ligas SA com dados físicos,
computa o vetor z-score do seu perfil RELATIVO à média posicional sul-americana, e mede o
cosseno contra o centroide (z vs. média top-5) de cada arquétipo. Cosseno alto = mesmo
"formato" de perfil, controlando o nível de liga por padronização dentro do próprio contexto.
"""
import json, math, statistics as st, os
from collections import defaultdict

D='data/jun26/'
IDADE_MAX=23
MIN_MIN=600
os.makedirs('estudo/build',exist_ok=True)

rk=json.load(open(D+'rankings.json'))
recs=rk['records']
det=json.load(open(D+'kpis_detail.json'))
KPIS=det['_kpis']; DET=det['data']
sc=json.load(open(D+'skillcorner.json'))
ARQ=json.load(open('estudo/data/arquetipos_top5.json'))

PHYS=['total_distance_p90','running_distance_p90','hi_distance_p90','hi_actions_p90',
      'hsr_distance_p90','hsr_count_p90','sprint_distance_p90','n_sprints_p90',
      'psv99','top5_psv99','high_accel_p90','med_accel_p90','high_decel_p90','med_decel_p90',
      'explosive_accel_to_sprint','cod_count_p90','m_min','m_min_tip','m_min_otip',
      'top3_time_to_sprint','top3_time_to_hsr']

SA_LEAGUES={'Brasil A','Brasil B','Argentina A','Uruguai','Colombia A','Chile',
            'Equador A','Paraguai','Peru','Venezuela','Bolivia'}
FLAB={'total_distance_p90':'Distância total/90','running_distance_p90':'Dist. corrida/90',
 'hi_distance_p90':'Dist. alta intens./90','hi_actions_p90':'Ações alta intens./90',
 'hsr_distance_p90':'Dist. veloz (HSR)/90','hsr_count_p90':'Corridas HSR/90',
 'sprint_distance_p90':'Dist. sprint/90','n_sprints_p90':'Sprints/90',
 'psv99':'Veloc. de ponta (PSV99)','top5_psv99':'Veloc. máx (top5)',
 'high_accel_p90':'Acelerações fortes/90','med_accel_p90':'Acelerações méd./90',
 'high_decel_p90':'Desacel. fortes/90','med_decel_p90':'Desacel. méd./90',
 'explosive_accel_to_sprint':'Explosão (acel→sprint)','cod_count_p90':'Mudanças de direção/90',
 'm_min':'Metros/min','m_min_tip':'Metros/min c/ posse','m_min_otip':'Metros/min s/ posse',
 'top3_time_to_sprint':'Tempo até sprint','top3_time_to_hsr':'Tempo até HSR',
 'Defensive duels won, %':'Duelos defensivos ganhos %','Aerial duels won, %':'Duelos aéreos ganhos %',
 'PAdj Interceptions':'Interceptações (aj.)','Successful defensive actions per 90':'Ações defensivas/90',
 'Sliding tackles per 90':'Carrinhos/90','Shots blocked per 90':'Bloqueios/90',
 'Aerial duels per 90':'Duelos aéreos/90','Defensive duels per 90':'Duelos defensivos/90',
 'Passes per 90':'Passes/90','Accurate passes, %':'Acerto de passe %',
 'Progressive passes per 90':'Passes progressivos/90','Accurate long passes, %':'Acerto passe longo %',
 'Long passes per 90':'Passes longos/90','Forward passes per 90':'Passes p/ frente/90',
 'Passes to final third per 90':'Passes ao terço final/90','Average pass length, m':'Distância média de passe',
 'Received passes per 90':'Passes recebidos/90','Key passes per 90':'Passes decisivos/90',
 'Smart passes per 90':'Passes inteligentes/90','Through passes per 90':'Passes em profundidade/90',
 'xA per 90':'xA/90','Passes to penalty area per 90':'Passes à área/90',
 'Deep completions per 90':'Conduções/passes ao terço/90','Shot assists per 90':'Assist. p/ finalização/90',
 'Accurate crosses, %':'Acerto de cruzamento %','Crosses per 90':'Cruzamentos/90',
 'Second assists per 90':'Segundas assistências/90','Progressive runs per 90':'Conduções progressivas/90',
 'Successful dribbles per 90':'Dribles certos/90','Dribbles per 90':'Dribles/90',
 'Accelerations per 90':'Arranques/90','xG per 90':'xG/90','Non-penalty goals per 90':'Gols (s/ pênalti)/90',
 'Shots per 90':'Finalizações/90','Touches in box per 90':'Toques na área/90',
 'Goal conversion, %':'Conversão de gol %','Head goals per 90':'Gols de cabeça/90',
 'Deep completed crosses per 90':'Cruzamentos ao terço/90','Save rate, %':'Taxa de defesa %',
 'gk_prevented_goals_per_90':'Gols evitados/90','Exits per 90':'Saídas/90',
 'gk_accurate_passes_pct':'Acerto de passe (GR) %','Clean sheets':'Jogos sem sofrer',
 'Conceded goals per 90':'Gols sofridos/90'}
def flab(f): return FLAB.get(f,f)
GROUPS={'Zagueiro':['Zagueiro - Direita','Zagueiro - Esquerda'],
 'Lateral':['Lateral Direito','Lateral Esquerdo'],'Volante':['Volante'],'Medio':['Medio'],
 'Meia':['Meia'],'Extremo':['Extremo - Direita','Extremo - Esquerda'],
 'Atacante':['Atacante'],'Goleiro':['Goleiro']}
POS2GROUP={p:g for g,ps in GROUPS.items() for p in ps}

def kdict(pk):
    arr=DET.get(pk)
    if not arr: return {}
    return {KPIS[e['k']]:e['v'] for e in arr}

def physd(pk):
    s=sc.get(pk)
    if not s: return None
    m=s.get('metrics') or {}
    if m.get('total_distance_p90') is None: return None
    return {k:m.get(k) for k in PHYS if m.get(k) is not None}

def getf(kd,ph,f):
    if f in kd and kd[f] is not None: return kd[f]
    if ph and f in ph and ph[f] is not None: return ph[f]
    return None

# ---- build SA player table (all ages, with physical) for reference; flag young candidates
sa=[]
for r in recs:
    if r['league'] not in SA_LEAGUES: continue
    if (r.get('Minutes played') or 0)<MIN_MIN: continue
    pos=r['position_group_pt']
    if pos not in POS2GROUP: continue
    ph=physd(r['primary_key'])
    if ph is None: continue          # exige dados físicos (mesmo espaço dos moldes)
    kd=kdict(r['primary_key'])
    sa.append({'pk':r['primary_key'],'name':r.get('tm_nome') or r['Player'],
        'team':r['Team'],'league':r['league'],'pos':pos,'group':POS2GROUP[pos],
        'age':r.get('Age'),'mv':r.get('Market value'),'minutes':r.get('Minutes played'),
        'height':r.get('Height'),'foot':r.get('Foot'),'overall':r.get('overall'),
        'birth':r.get('Birth country'),'kd':kd,'ph':ph})

print('SA jogadores (todas idades, c/ físico):',len(sa))

# ---- per-group reference stats (mean/std over SA pool) on that group's feature set
results={'meta':{'idade_max':IDADE_MAX,'min_min':MIN_MIN,'ligas':sorted(SA_LEAGUES),
                 'metodo':'cosseno entre z-perfil (vs. média posicional SA) e centroide do arquétipo (z vs. média top-5)'},
         'grupos':{}}
candidate_best=[]  # per young candidate: best archetype

for g,gd in ARQ['grupos'].items():
    feats=gd['features']
    pool=[p for p in sa if p['group']==g]
    if len(pool)<12:
        print(' grupo',g,'pool pequeno',len(pool));
    # reference mean/std with median imputation
    med={}
    for f in feats:
        vals=[getf(p['kd'],p['ph'],f) for p in pool]
        vals=[v for v in vals if v is not None]
        med[f]=st.median(vals) if vals else 0.0
    mu={}; sd={}
    for f in feats:
        col=[ (getf(p['kd'],p['ph'],f) if getf(p['kd'],p['ph'],f) is not None else med[f]) for p in pool]
        mu[f]=st.mean(col) if col else 0.0
        sd[f]=(st.pstdev(col) if len(col)>1 else 0.0) or 1.0
    # young candidates: require >=70% real feature coverage
    cands=[]
    for p in pool:
        if (p['age'] or 99)>IDADE_MAX: continue
        real=sum(1 for f in feats if getf(p['kd'],p['ph'],f) is not None)
        if real/len(feats)<0.7: continue
        z={f:((getf(p['kd'],p['ph'],f) if getf(p['kd'],p['ph'],f) is not None else med[f])-mu[f])/sd[f] for f in feats}
        p['_z']=z; cands.append(p)
    # score each archetype
    arch_out=[]
    for a in gd['arquetipos']:
        c=a['centroide_z']
        cfeats=list(dict.fromkeys(f for f in feats if abs(c.get(f,0))>1e-9))
        cnorm=math.sqrt(sum(c[f]**2 for f in cfeats)) or 1.0
        scored=[]
        for p in cands:
            z=p['_z']
            dot=sum(z[f]*c.get(f,0) for f in cfeats)
            znorm=math.sqrt(sum(z[f]**2 for f in cfeats)) or 1.0
            cos=dot/(znorm*cnorm)
            scored.append((cos,p))
        # rank by cosine (fidelidade de formato); proj = intensidade ao longo do eixo do arquétipo
        scored2=[]
        for cos,p in scored:
            z=p['_z']; dot=sum(z[f]*c.get(f,0) for f in cfeats)
            proj=dot/cnorm
            scored2.append((cos,proj,p))
        scored2.sort(key=lambda x:-x[0])
        top=[]
        for cos,proj,p in scored2[:15]:
            # traços de destaque: features que o arquétipo valoriza e onde o jogador é forte
            cand_traits=[(f,p['_z'][f]) for f in cfeats if c.get(f,0)>0]
            zz=sorted(cand_traits,key=lambda kv:-kv[1])[:3]
            traits=[{'lab':flab(f),'v':getf(p['kd'],p['ph'],f),'z':round(p['_z'][f],2)} for f,_ in zz]
            top.append({'name':p['name'],'team':p['team'],'league':p['league'],
                'age':p['age'],'minutes':p['minutes'],'mv':p['mv'],'height':p['height'],
                'foot':p['foot'],'overall':p['overall'],
                'match':round(max(0,cos)*100,1),'intensidade':round(proj,2),
                'traits':traits})
        arch_out.append({'nome':a['nome'],'tag':a['tag'],'alvo':a['alvo_scouting'],
                         'referencias':a['referencias'],'top':top})
    results['grupos'][g]={'nome':gd['nome'],'n_cands':len(cands),'n_pool':len(pool),
                          'features':feats,'arquetipos':arch_out}
    # best-match per candidate
    for p in cands:
        best=None
        for a in gd['arquetipos']:
            c=a['centroide_z']; cfeats=list(dict.fromkeys(f for f in feats if abs(c.get(f,0))>1e-9))
            cnorm=math.sqrt(sum(c[f]**2 for f in cfeats)) or 1.0
            z=p['_z']; dot=sum(z[f]*c.get(f,0) for f in cfeats)
            znorm=math.sqrt(sum(z[f]**2 for f in cfeats)) or 1.0
            cos=dot/(znorm*cnorm)
            if best is None or cos>best[0]: best=(cos,a['nome'],a['tag'])
        candidate_best.append({'name':p['name'],'team':p['team'],'league':p['league'],
            'group':g,'pos':p['pos'],'age':p['age'],'minutes':p['minutes'],'mv':p['mv'],
            'overall':p['overall'],'best_arch':best[1],'best_tag':best[2],
            'match':round(max(0,best[0])*100,1)})

results['best_por_jogador']=sorted(candidate_best,key=lambda x:-x['match'])
json.dump(results,open('estudo/data/similares_sa.json','w'),ensure_ascii=False,indent=1)

# summary
print('\n== Resumo por grupo (candidatos jovens) ==')
for g,gd in results['grupos'].items():
    print(f"  {g:10s} cands={gd['n_cands']:3d} pool={gd['n_pool']:3d}")
print('\n== Exemplos: melhores matches por arquétipo (premium) ==')
for g in ['Zagueiro','Atacante','Extremo','Volante']:
    gd=results['grupos'][g]
    for a in gd['arquetipos']:
        if a['top']:
            t=a['top'][0]
            print(f"  {g} · {a['nome'][:28]:28s} -> {t['name']} ({t['league']}, {t['age']:.0f}a) match {t['match']}%")
