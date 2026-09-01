# -*- coding: utf-8 -*-
"""Alvos de contratação Botafogo — top-10 por posição, segmentado por MERCADO/origem.
Buckets (por país de nascimento): SUB23 (BR+SA <=23), BR, SA, IBER (Espanha/Portugal/Angola/
América Central+México), MUNDO. Universo = todas as ligas, >=900', exclui atletas do Botafogo.
Score = Prontidão (nível/minutos/força da liga) x Revenda (afinidade a arquétipo premium +
juventude + velocidade). Afinidade = cosseno ao centroide do arquétipo, com o candidato
padronizado (z) DENTRO do seu (bucket x posição); usa físico quando há tracking, senão cai
para afinidade técnica-apenas (sinalizada)."""
import json, math, statistics as st, os, bisect
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(ROOT)
os.makedirs('estudo/build',exist_ok=True)
def rd(p): return open(p,encoding='utf-8').read()
D='data/jun26/'
IDADE_SUB23=23; MIN_MIN=900; TOPN=10

rk=json.loads(rd(D+'rankings.json')); recs=rk['records']
det=json.loads(rd(D+'kpis_detail.json')); KPIS=det['_kpis']; DET=det['data']
sc=json.loads(rd(D+'skillcorner.json'))
ARQ=json.loads(rd('estudo/data/arquetipos_top5.json'))

PHYS=set(['total_distance_p90','running_distance_p90','hi_distance_p90','hi_actions_p90','hsr_distance_p90',
 'hsr_count_p90','sprint_distance_p90','n_sprints_p90','psv99','top5_psv99','high_accel_p90','med_accel_p90',
 'high_decel_p90','med_decel_p90','explosive_accel_to_sprint','cod_count_p90','m_min','m_min_tip','m_min_otip',
 'top3_time_to_sprint','top3_time_to_hsr'])

SA_C={'Argentina','Uruguay','Colombia','Chile','Ecuador','Paraguay','Peru','Bolivia','Venezuela'}
CAM={'Costa Rica','Panama','Honduras','Guatemala','El Salvador','Nicaragua','Mexico'}
IBER_C={'Spain','Portugal','Angola'}|CAM
def bucket_of(r, age):
    c=r.get('Birth country')
    isbrsa = (c=='Brazil' or c in SA_C)
    b=[]
    if isbrsa and (age is not None and age<=IDADE_SUB23): b.append('SUB23')
    if c=='Brazil': b.append('BR')
    elif c in SA_C: b.append('SA')
    elif c in IBER_C: b.append('IBER')
    else: b.append('MUNDO')
    return b  # jogador pode estar em SUB23 + (BR|SA)
def bucket_of_wrap(p, age): return bucket_of({'Birth country':p['birth']}, age)

BUCKETS=['SUB23','BR','SA','IBER','MUNDO']
BUCKET_LABEL={'SUB23':'Sub-23 BR + Sul-americanos','BR':'Brasileiros','SA':'Sul-americanos',
 'IBER':'Espanha · Portugal · Angola · América Central','MUNDO':'Mundo'}
# frame de padronização por bucket: pool de referência (todas idades)
FRAME_MEMBER={
 'SUB23': lambda c: (c=='Brazil' or c in SA_C),   # jovens julgados vs. norma BR+SA
 'BR': lambda c: c=='Brazil',
 'SA': lambda c: c in SA_C,
 'IBER': lambda c: c in IBER_C,
 'MUNDO': lambda c: not (c=='Brazil' or c in SA_C or c in IBER_C),
}

LEAGUE_W={ # força da liga (prontidão)
 'Inglaterra A':1.00,'Espanha A':1.00,'Alemanha A':1.00,'Italia A':1.00,'França A':1.00,
 'Portugal A':0.90,'Holanda':0.90,'Belgica A':0.88,'Brasil A':0.90,'Argentina A':0.88,'Turquia':0.85,
 'França B':0.82,'Italia B':0.80,'Espanha B':0.80,'Inglaterra B':0.82,'Alemanha B':0.80,'EUA':0.78,'Mexico':0.80,'Arabia Saudita A':0.80,
 'Colombia A':0.75,'Chile':0.74,'Uruguai':0.74,'Grecia':0.76,'Escocia':0.76,'Austria':0.74,'Suiça':0.76,'Dinamarca':0.75,'Croacia':0.72,'Tcheca':0.72,'Russia':0.76,'Ucrania':0.72,
 'Brasil B':0.70,'Paraguai':0.70,'Equador A':0.70,'Peru':0.66,'Japao A':0.74,'Coreia A':0.72,'Noruega':0.72,'Suecia':0.72,'Polonia':0.72,'Servia':0.70,
}
def league_w(l): return LEAGUE_W.get(l,0.60)

def kdict(pk):
    arr=DET.get(pk); return {KPIS[e['k']]:e['v'] for e in arr} if arr else {}
def physd(pk):
    s=sc.get(pk)
    if not s: return {}
    m=s.get('metrics') or {}
    return {k:m.get(k) for k in PHYS if m.get(k) is not None}
def getf(kd,ph,f):
    v=kd.get(f); return v if v is not None else ph.get(f)

GROUPS={'Zagueiro':['Zagueiro - Direita','Zagueiro - Esquerda'],'Lateral':['Lateral Direito','Lateral Esquerdo'],
 'Volante':['Volante'],'Medio':['Medio'],'Meia':['Meia'],'Extremo':['Extremo - Direita','Extremo - Esquerda'],
 'Atacante':['Atacante'],'Goleiro':['Goleiro']}
POS2GROUP={p:g for g,ps in GROUPS.items() for p in ps}
PREMIUM={'Zagueiro':['Construtor','Defensor de espaço','móvel'],'Lateral':['ofensivo','Motor'],
 'Volante':['Organizador'],'Medio':['Organizador','Condutor','intensidade'],'Meia':['Armador','Condutor'],
 'Extremo':['Craque','Driblador'],'Atacante':['Falso-9','profundidade'],'Goleiro':['rendimento','Construtor']}
def is_prem(g,nome): return any(k.lower() in nome.lower() for k in PREMIUM.get(g,[]))

FLAB={'total_distance_p90':'volume de corrida','hi_distance_p90':'alta intensidade','sprint_distance_p90':'dist. sprint',
 'n_sprints_p90':'sprints','psv99':'velocidade de ponta','high_accel_p90':'acelerações','explosive_accel_to_sprint':'explosão',
 'cod_count_p90':'mudança de direção','hsr_count_p90':'corridas velozes','m_min':'intensidade (m/min)',
 'Defensive duels won, %':'duelo defensivo','Aerial duels won, %':'jogo aéreo','PAdj Interceptions':'interceptações',
 'Successful defensive actions per 90':'ações defensivas','Progressive passes per 90':'passe progressivo','Accurate passes, %':'acerto de passe',
 'Passes to final third per 90':'passe ao terço','Received passes per 90':'envolvimento','Key passes per 90':'passe decisivo',
 'Smart passes per 90':'passe inteligente','Through passes per 90':'passe em profundidade','xA per 90':'criação (xA)',
 'Passes to penalty area per 90':'passe à área','Deep completions per 90':'chegada ao terço','Accurate crosses, %':'cruzamento',
 'Crosses per 90':'cruzamentos','Progressive runs per 90':'condução progressiva','Successful dribbles per 90':'dribles certos',
 'Dribbles per 90':'dribles','xG per 90':'volume de chance (xG)','Non-penalty goals per 90':'gols','Shots per 90':'finalizações',
 'Touches in box per 90':'presença na área','Goal conversion, %':'conversão','Head goals per 90':'gol de cabeça',
 'Save rate, %':'taxa de defesa','gk_prevented_goals_per_90':'gols evitados','Exits per 90':'saídas','Long passes per 90':'passes longos'}
def flab(f): return FLAB.get(f,f)

# incumbentes Botafogo por grupo (contexto de necessidade)
incum={g:[] for g in GROUPS}
for r in recs:
    if r.get('isBotafogo'):
        g=POS2GROUP.get(r['position_group_pt'])
        if g: incum[g].append({'name':r['Player'],'age':r.get('Age'),'min':r.get('Minutes played')})
for g in incum: incum[g].sort(key=lambda x:-(x['min'] or 0))

# universo de candidatos
def natlabel(c): return c or '—'
univ=[]
for r in recs:
    if (r.get('Minutes played') or 0)<MIN_MIN or r.get('isBotafogo'): continue
    pos=r['position_group_pt']
    if pos not in POS2GROUP: continue
    kd=kdict(r['primary_key']); ph=physd(r['primary_key'])
    univ.append({'pk':r['primary_key'],'name':r.get('tm_nome') or r['Player'],'team':r['Team'],'league':r['league'],
        'pos':pos,'group':POS2GROUP[pos],'age':r.get('Age'),'mv':r.get('Market value'),'minutes':r.get('Minutes played'),
        'height':r.get('Height'),'foot':r.get('Foot'),'overall':r.get('overall'),'birth':r.get('Birth country'),
        'kd':kd,'ph':ph,'hasphys':bool(ph)})

def pctrank(sorted_vals,v):
    if not sorted_vals: return 0.5
    return bisect.bisect_right(sorted_vals,v)/len(sorted_vals)

recos={}
for g,gd in ARQ['grupos'].items():
    feats=gd['features']
    poss=GROUPS[g]
    grouppool=[p for p in univ if p['group']==g]
    # precompute per-bucket frame stats + level/speed arrays
    frames={}
    for b in BUCKETS:
        mem=[p for p in grouppool if FRAME_MEMBER[b](p['birth'])]
        med={}; mu={}; sd={}
        for f in feats:
            vals=[getf(p['kd'],p['ph'],f) for p in mem]; vals=[v for v in vals if v is not None]
            med[f]=st.median(vals) if vals else 0.0
            mu[f]=st.mean(vals) if vals else 0.0
            sd[f]=(st.pstdev(vals) if len(vals)>1 else 0.0) or 1.0
        overalls=sorted([p['overall'] for p in mem if p['overall'] is not None])
        psv=sorted([p['ph'].get('psv99') for p in mem if p['ph'].get('psv99') is not None])
        frames[b]={'mem':mem,'med':med,'mu':mu,'sd':sd,'overalls':overalls,'psv':psv,'n':len(mem)}
    # score candidato dentro de cada bucket a que pertence
    perb={b:[] for b in BUCKETS}
    for p in grouppool:
        age=p['age']
        for b in bucket_of_wrap(p,age):
            fr=frames[b]
            if fr['n']<12: continue
            # z do candidato no frame do bucket
            z={};
            for f in feats:
                v=getf(p['kd'],p['ph'],f)
                if v is None: v=fr['med'][f]
                z[f]=(v-fr['mu'][f])/fr['sd'][f]
            # afinidade a cada arquétipo (usa só features que o candidato tem de verdade OU técnica se sem físico)
            tech_only=not p['hasphys']
            def cos_to(a):
                c=a['centroide_z']
                cf=[f for f in feats if abs(c.get(f,0))>1e-9 and (not tech_only or f not in PHYS)]
                if not cf: return 0.0
                cn=math.sqrt(sum(c[f]**2 for f in cf)) or 1
                zn=math.sqrt(sum(z[f]**2 for f in cf)) or 1
                return sum(z[f]*c.get(f,0) for f in cf)/(zn*cn)
            affs=[(cos_to(a),a) for a in gd['arquetipos']]
            best=max(affs,key=lambda x:x[0])
            prem=[(cs,a) for cs,a in affs if is_prem(g,a['nome'])]
            bestp=max(prem,key=lambda x:x[0]) if prem else best
            q_level=pctrank(fr['overalls'],p['overall']) if p['overall'] is not None else 0.4
            q_min=min(1.0,(p['minutes'] or 0)/2400)
            lw=league_w(p['league'])
            readiness=0.45*q_level+0.25*q_min+0.30*lw
            q_prem=max(0.0,bestp[0])
            q_youth=max(0.0,min(1.0,(29-(age or 29))/12.0))
            q_speed=pctrank(fr['psv'],p['ph'].get('psv99')) if (not tech_only and p['ph'].get('psv99') is not None) else 0.5
            # revenda decai forte com a idade (jogador velho não se revende com lucro)
            age_decay=1.0 if (age is None or age<=26) else (0.75 if age<=28 else (0.45 if age<=30 else 0.2))
            resale=(0.50*q_prem+0.25*q_youth+0.25*q_speed)*age_decay
            score=0.5*readiness+0.5*resale
            cbest=bestp[1]['centroide_z']; cf=[f for f in feats if cbest.get(f,0)>0 and (not tech_only or f not in PHYS)]
            zz=sorted(((f,z[f]) for f in cf),key=lambda kv:-kv[1])[:3]
            perb[b].append({'name':p['name'],'team':p['team'],'league':p['league'],'birth':natlabel(p['birth']),
                'age':age,'minutes':p['minutes'],'height':p['height'],'foot':p['foot'],'mv':p['mv'],'overall':p['overall'],
                'arch':bestp[1]['nome'],'arch_tag':bestp[1]['tag'],'arch_match':round(q_prem*100,1),'arch_refs':bestp[1]['referencias'][:3],
                'readiness':round(readiness*100,1),'resale':round(resale*100,1),'score':round(score*100,1),
                'tech_only':tech_only,'traits':[flab(f) for f,_ in zz]})
    for b in BUCKETS:
        perb[b].sort(key=lambda x:-x['score'])
        perb[b]=perb[b][:TOPN]
    recos[g]={'nome':gd['nome'],'incumbentes':incum[g],'buckets':{b:perb[b] for b in BUCKETS},
              'frame_n':{b:frames[b]['n'] for b in BUCKETS}}

out={'meta':{'min_min':MIN_MIN,'topn':TOPN,'idade_sub23':IDADE_SUB23,'buckets':BUCKETS,'bucket_label':BUCKET_LABEL,
     'formula':'Score = 50% Prontidão (nível 45% + minutos 25% + força da liga 30%) + 50% Revenda (afinidade premium 50% + juventude 25% + velocidade 25%). Padronização por bucket×posição. Sem físico ⇒ afinidade técnica-apenas.'},
     'grupos_ordem':['Goleiro','Zagueiro','Lateral','Volante','Medio','Meia','Extremo','Atacante'],'recos':recos}
open('estudo/data/reco_botafogo.json','w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False,indent=1))

print('== Alvos por posição x bucket (top-1) ==')
for g in out['grupos_ordem']:
    print(f'\n### {g}  (frame n:', {b:recos[g]["frame_n"][b] for b in BUCKETS}, ')')
    for b in BUCKETS:
        lst=recos[g]['buckets'][b]
        if lst:
            t=lst[0]; to=' [téc]' if t['tech_only'] else ''
            print(f"   {b:6s} #1 score{t['score']:.0f} {t['name']} ({t['birth']}, {t['team']}/{t['league']}, {t['age']}a){to} -> {t['arch']} {t['arch_match']:.0f}%")
        else:
            print(f"   {b:6s} —")
