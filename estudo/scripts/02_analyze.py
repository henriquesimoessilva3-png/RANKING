import json, os, math, statistics as st
from collections import defaultdict

SP='estudo/build/'
os.makedirs(SP,exist_ok=True)
M=json.load(open(SP+'master.json'))
players=M['players']; PS=M['positions_summary']; catmap=M['catmap']
PHYS=M['phys_keys']

# direction: metrics where LOWER is better
LOWER={'Fouls per 90','Fouls','Yellow cards per 90','Yellow cards','Red cards',
       'Red cards per 90','Conceded goals','Conceded goals per 90','xG against',
       'xG against per 90','Shots against','Shots against per 90',
       'top3_time_to_sprint','top3_time_to_hsr'}

PHYS_LABEL={
 'total_distance_p90':'Distância total','running_distance_p90':'Dist. corrida',
 'hi_distance_p90':'Dist. alta intensidade','hi_actions_p90':'Ações alta intens.',
 'hsr_distance_p90':'Dist. corrida veloz (HSR)','hsr_count_p90':'Nº corridas HSR',
 'sprint_distance_p90':'Dist. em sprint','n_sprints_p90':'Nº de sprints',
 'psv99':'Velocidade máx (PSV99)','top5_psv99':'Vel. máx (top5)',
 'high_accel_p90':'Acelerações fortes','med_accel_p90':'Acelerações médias',
 'high_decel_p90':'Desacel. fortes','med_decel_p90':'Desacel. médias',
 'explosive_accel_to_sprint':'Explosão (acel→sprint)','cod_count_p90':'Mudanças de direção',
 'm_min':'Metros/min','m_min_tip':'Metros/min c/ posse','m_min_otip':'Metros/min s/ posse',
 'top3_time_to_sprint':'Tempo p/ atingir sprint','top3_time_to_hsr':'Tempo p/ atingir HSR'}

POS2GROUP={'Zagueiro - Direita':'Zagueiro','Zagueiro - Esquerda':'Zagueiro',
 'Lateral Direito':'Lateral','Lateral Esquerdo':'Lateral','Volante':'Volante',
 'Medio':'Medio','Meia':'Meia','Extremo - Direita':'Extremo',
 'Extremo - Esquerda':'Extremo','Atacante':'Atacante','Goleiro':'Goleiro'}
OUTPUT_EXTRA=['Non-penalty goals per 90','xG per 90','Assists per 90','xA per 90',
 'Goal conversion, %','Shots per 90','Touches in box per 90','Head goals per 90',
 'Progressive runs per 90','Successful dribbles per 90','Accelerations per 90',
 'Defensive duels won, %','Aerial duels won, %','PAdj Interceptions',
 'Successful defensive actions per 90','Sliding tackles per 90','Shots blocked per 90',
 'Progressive passes per 90','Accurate passes, %','Accurate long passes, %',
 'Passes to final third per 90','Key passes per 90','Smart passes per 90',
 'Through passes per 90','Passes to penalty area per 90','Deep completions per 90',
 'Accurate crosses, %','Crosses per 90','Received passes per 90','Forward passes per 90',
 'Accurate forward passes, %','Fouls per 90','Deep completed crosses per 90']

# ---------- 1. DIFFERENTIAL vs WORLD, per position ----------
def diffs():
    res={}
    for pos,s in PS.items():
        g=POS2GROUP[pos]
        if g=='Goleiro':
            relevant=set(GK)|{'Passes per 90','Average pass length, m','Long passes per 90'}
        else:
            relevant=set(FEAT[g])|set(OUTPUT_EXTRA)
        rows=[]
        for name,d in s['kpi'].items():
            if name not in relevant: continue
            if not d['top5'] or d['top5_med_pct'] is None: continue
            wstd=d['world'].get('std') if d['world'] else 0
            if not wstd or wstd<=0.001: continue
            if d['world']['med']==0 and d['top5']['med']==0: continue
            pct=d['top5_med_pct']; bpct=d.get('best_med_pct')
            # for lower-better metrics invert percentile meaning
            eff=100-pct if name in LOWER else pct
            beff=(100-bpct) if (bpct is not None and name in LOWER) else bpct
            rows.append({'metric':name,'cat':catmap.get(name,''),
                         'pct':pct,'eff':eff,'bpct':bpct,'beff':beff,
                         'world_med':d['world']['med'],'top5_med':d['top5']['med'],
                         'best_med':d['best']['med'] if d['best'] else None,
                         'kind':'tec'})
        for key,d in s['phys'].items():
            if not d['top5'] or d['top5_med_pct'] is None: continue
            pct=d['top5_med_pct']; bpct=d.get('best_med_pct')
            eff=100-pct if key in LOWER else pct
            beff=(100-bpct) if (bpct is not None and key in LOWER) else bpct
            rows.append({'metric':PHYS_LABEL.get(key,key),'raw':key,'cat':'FÍSICO',
                         'pct':pct,'eff':eff,'bpct':bpct,'beff':beff,
                         'world_med':d['world']['med'],'top5_med':d['top5']['med'],
                         'best_med':d['best']['med'] if d['best'] else None,'kind':'fis'})
        rows.sort(key=lambda r:-(r['eff'] if r['eff'] is not None else 0))
        res[pos]=rows
    return res

# ---------- 2. BETWEEN-POSITION physical signature (z vs pooled) ----------
def between_phys():
    # pooled mean/std across all top5 players per phys metric
    pool=defaultdict(list)
    for p in players:
        for k,v in p['phys'].items(): pool[k].append(v)
    stats={k:(st.mean(v),st.pstdev(v)) for k,v in pool.items() if len(v)>5 and st.pstdev(v)>0}
    sig={}
    for pos in PS:
        pl=[p for p in players if p['pos']==pos]
        row={}
        for k,(mu,sd) in stats.items():
            vals=[p['phys'][k] for p in pl if k in p['phys']]
            if vals: row[k]=round((st.mean(vals)-mu)/sd,2)
        sig[pos]=row
    return sig,list(stats.keys())

# ---------- clustering utils (pure python) ----------
def zmatrix(rows, feats):
    cols={f:[r[f] for r in rows] for f in feats}
    mu={f:st.mean(cols[f]) for f in feats}
    sd={f:(st.pstdev(cols[f]) or 1.0) for f in feats}
    X=[[ (r[f]-mu[f])/sd[f] for f in feats] for r in rows]
    return X,mu,sd

def dist2(a,b): return sum((x-y)**2 for x,y in zip(a,b))

def kmeans(X,k,seed=1,iters=60,restarts=8):
    n=len(X); d=len(X[0]); best=None
    rng=seed
    def rnd():
        nonlocal rng
        rng=(rng*1103515245+12345)&0x7fffffff
        return rng/0x7fffffff
    for rs in range(restarts):
        # kmeans++ init
        c0=int(rnd()*n); cents=[X[c0][:]]
        while len(cents)<k:
            ds=[min(dist2(x,c) for c in cents) for x in X]
            tot=sum(ds) or 1
            t=rnd()*tot; acc=0; pick=n-1
            for i,dd in enumerate(ds):
                acc+=dd
                if acc>=t: pick=i; break
            cents.append(X[pick][:])
        assign=[0]*n
        for _ in range(iters):
            newa=[min(range(k),key=lambda j:dist2(X[i],cents[j])) for i in range(n)]
            if newa==assign: assign=newa; break
            assign=newa
            for j in range(k):
                mem=[X[i] for i in range(n) if assign[i]==j]
                if mem: cents[j]=[sum(col)/len(mem) for col in zip(*mem)]
        inertia=sum(dist2(X[i],cents[assign[i]]) for i in range(n))
        if best is None or inertia<best[0]: best=(inertia,assign,cents)
    return best[1],best[2],best[0]

def silhouette(X,assign,k):
    n=len(X)
    if n>600: return None
    byc=defaultdict(list)
    for i,a in enumerate(assign): byc[a].append(i)
    if any(len(byc[j])<2 for j in range(k)): return -1
    s=[]
    for i in range(n):
        ai=assign[i]
        a=st.mean([math.sqrt(dist2(X[i],X[j])) for j in byc[ai] if j!=i])
        b=min(st.mean([math.sqrt(dist2(X[i],X[j])) for j in byc[c]])
              for c in byc if c!=ai)
        s.append((b-a)/max(a,b) if max(a,b)>0 else 0)
    return st.mean(s)

def pca2(X):
    n=len(X); d=len(X[0])
    mu=[sum(col)/n for col in zip(*X)]
    Xc=[[x-mu[j] for j,x in enumerate(row)] for row in X]
    # covariance
    C=[[0.0]*d for _ in range(d)]
    for row in Xc:
        for a in range(d):
            for b in range(a,d):
                C[a][b]+=row[a]*row[b]
    for a in range(d):
        for b in range(a,d):
            C[a][b]/=n; C[b][a]=C[a][b]
    def mv(v):
        return [sum(C[a][b]*v[b] for b in range(d)) for a in range(d)]
    def norm(v):
        m=math.sqrt(sum(x*x for x in v)) or 1; return [x/m for x in v]
    def power(deflate=None):
        v=norm([math.sin(i+1) for i in range(d)])
        for _ in range(200):
            w=mv(v)
            if deflate:
                dot=sum(w[i]*deflate[i] for i in range(d))
                w=[w[i]-dot*deflate[i] for i in range(d)]
            v=norm(w)
        return v
    p1=power(); p2=power(p1)
    proj=[[sum(row[j]*p1[j] for j in range(d)), sum(row[j]*p2[j] for j in range(d))] for row in Xc]
    return proj

# ---------- feature pools ----------
DEF=['Defensive duels won, %','Aerial duels won, %','PAdj Interceptions',
     'Successful defensive actions per 90','Sliding tackles per 90','Shots blocked per 90',
     'Aerial duels per 90','Defensive duels per 90']
BUILD=['Passes per 90','Accurate passes, %','Progressive passes per 90',
       'Accurate long passes, %','Long passes per 90','Forward passes per 90',
       'Passes to final third per 90','Average pass length, m','Received passes per 90']
CREA=['Key passes per 90','Smart passes per 90','Through passes per 90','xA per 90',
      'Passes to penalty area per 90','Deep completions per 90','Shot assists per 90',
      'Accurate crosses, %','Crosses per 90','Second assists per 90']
CARRY=['Progressive runs per 90','Successful dribbles per 90','Dribbles per 90',
       'Accelerations per 90']
SHOOT=['xG per 90','Non-penalty goals per 90','Shots per 90','Touches in box per 90',
       'Goal conversion, %','Head goals per 90']
GK=['Save rate, %','gk_prevented_goals_per_90','Exits per 90','gk_accurate_passes_pct',
    'Aerial duels won, %','Clean sheets','Passes per 90','Accurate long passes, %',
    'Conceded goals per 90']

FEAT={
 'Zagueiro':DEF+BUILD+CARRY[:1]+['Progressive runs per 90'],
 'Lateral':DEF[:5]+BUILD[:6]+CREA[:1]+['Crosses per 90','Accurate crosses, %','Deep completed crosses per 90']+CARRY+SHOOT[:2],
 'Volante':DEF+BUILD+CREA[:6]+CARRY,
 'Medio':BUILD+CREA+CARRY+SHOOT[:3]+DEF[:3],
 'Meia':CREA+SHOOT+CARRY+BUILD[:4],
 'Extremo':CARRY+CREA+SHOOT+['Crosses per 90','Accurate crosses, %'],
 'Atacante':SHOOT+CREA[:5]+CARRY[:2]+['Aerial duels won, %'],
 'Goleiro':GK,
}
GROUPS={
 'Zagueiro':['Zagueiro - Direita','Zagueiro - Esquerda'],
 'Lateral':['Lateral Direito','Lateral Esquerdo'],
 'Volante':['Volante'],'Medio':['Medio'],'Meia':['Meia'],
 'Extremo':['Extremo - Direita','Extremo - Esquerda'],
 'Atacante':['Atacante'],'Goleiro':['Goleiro'],
}
KCHOICE={'Zagueiro':4,'Lateral':4,'Volante':3,'Medio':4,'Meia':3,'Extremo':4,'Atacante':4,'Goleiro':3}

def getfeat(p,f):
    if f in p['kpi']: return p['kpi'][f]
    if f in p['phys']: return p['phys'][f]
    return None

def cluster_group(gname):
    poss=GROUPS[gname]
    pl=[p for p in players if p['pos'] in poss]
    base=[f for f in FEAT[gname]+PHYS]
    # keep features with <35% missing across group
    feats=[]
    for f in base:
        cov=sum(1 for p in pl if getfeat(p,f) is not None)/len(pl)
        if cov>=0.65: feats.append(f)
    # keep only players with all feats present (impute median otherwise)
    med={}
    for f in feats:
        vals=[getfeat(p,f) for p in pl if getfeat(p,f) is not None]
        med[f]=st.median(vals)
    rows=[{f:(getfeat(p,f) if getfeat(p,f) is not None else med[f]) for f in feats} for p in pl]
    X,mu,sd=zmatrix(rows,feats)
    # choose k
    kbest=KCHOICE[gname]; abest=None; cbest=None; sbest=None
    for k in range(3, min(6,KCHOICE[gname]+1)+1):
        a,c,inr=kmeans(X,k,seed=7)
        sil=silhouette(X,a,k)
        if k==KCHOICE[gname]:
            abest,cbest,kbest,sbest=a,c,k,sil
    assign,cents=abest,cbest
    proj=pca2(X)
    # characterize clusters
    k=kbest
    byc=defaultdict(list)
    for i,a in enumerate(assign): byc[a].append(i)
    clusters=[]
    for j in sorted(byc,key=lambda j:-len(byc[j])):
        idx=byc[j]
        mz={f:st.mean([X[i][fi] for i in idx]) for fi,f in enumerate(feats)}
        top=sorted(mz.items(),key=lambda kv:-kv[1])
        # exemplars: highest overall in cluster + closest to centroid
        mem=sorted(idx,key=lambda i:-(pl[i]['overall'] or 0))
        exl=[pl[i] for i in mem[:6]]
        cen=cents[j]
        near=sorted(idx,key=lambda i:dist2(X[i],cen))[:4]
        clusters.append({
          'id':j,'n':len(idx),
          'hi':[(f,round(mz[f],2)) for f,_ in top[:7] if mz[f]>0.15],
          'lo':[(f,round(mz[f],2)) for f,_ in top[::-1][:6] if mz[f]<-0.15],
          'ex_top':[{'name':e['name'],'team':e['team'],'league':e['league'],
                     'overall':e['overall'],'age':e['age'],'pos':e['pos'],'mv':e['mv']} for e in exl],
          'ex_near':[pl[i]['name'] for i in near],
          'avg_overall':round(st.mean([pl[i]['overall'] for i in idx if pl[i]['overall'] is not None]),1),
          'avg_age':round(st.mean([pl[i]['age'] for i in idx if pl[i]['age']]),1),
          'med_mv':int(st.median([pl[i]['mv'] for i in idx if pl[i]['mv']])) if any(pl[i]['mv'] for i in idx) else 0,
          'mean_z':mz,
        })
    return {'group':gname,'n':len(pl),'feats':feats,'k':k,'sil':round(sbest,3) if sbest else None,
            'clusters':clusters,'assign':assign,'proj':proj,
            'players':[{'name':p['name'],'overall':p['overall'],'pos':p['pos']} for p in pl]}

# ---------- variance decomposition between vs within position ----------
def variance_decomp(feature_scope='phys'):
    # use physical features common to all
    if feature_scope=='phys':
        feats=[f for f in PHYS if f not in ('top3_time_to_sprint','top3_time_to_hsr')]
        getv=lambda p,f: p['phys'].get(f)
    rows=[p for p in players if all(getv(p,f) is not None for f in feats)]
    X,mu,sd=zmatrix([{f:getv(p,f) for f in feats} for p in rows],feats)
    grand=[0.0]*len(feats)  # z-mean is 0
    sstot=sum(dist2(x,grand) for x in X)
    byp=defaultdict(list)
    for i,p in enumerate(rows): byp[p['pos']].append(i)
    ssb=0
    for pos,idx in byp.items():
        cen=[st.mean([X[i][fi] for i in idx]) for fi in range(len(feats))]
        ssb+=len(idx)*dist2(cen,grand)
    return {'scope':feature_scope,'n':len(rows),'between_pct':round(100*ssb/sstot,1),
            'within_pct':round(100*(sstot-ssb)/sstot,1),'feats':feats}

print('computing diffs...')
D=diffs()
print('computing between phys...')
BP,phys_used=between_phys()
print('clustering...')
CL={}
for g in GROUPS:
    CL[g]=cluster_group(g)
    c=CL[g]
    print(f'  {g:10s} n={c["n"]:4d} k={c["k"]} sil={c["sil"]} feats={len(c["feats"])} sizes={[cl["n"] for cl in c["clusters"]]}')
print('variance decomp...')
VD=variance_decomp('phys')
print('  physical between-position variance:',VD['between_pct'],'% within:',VD['within_pct'],'%')

json.dump({'diffs':D,'between_phys':BP,'phys_used':phys_used,'clusters':CL,
           'var_decomp':VD,'phys_label':PHYS_LABEL,'lower':list(LOWER)},
          open(SP+'results.json','w'))
print('saved results.json')
