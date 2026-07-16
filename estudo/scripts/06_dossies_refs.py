# -*- coding: utf-8 -*-
"""Dossiês individuais dos jogadores-referência OFICIAIS (scanner_refs.json, validados com o scout).
Para cada um: percentis vs. o mundo na sua posição (técnico + físico), no que é 'top', e mapeia
ao arquétipo estatístico do estudo (Fase 1). Também reconcilia o rótulo do scout com o do cluster."""
import json, math, unicodedata, statistics as st, os, bisect
os.makedirs('estudo/build',exist_ok=True)
D='data/jun26/'
def norm(s):
    s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower()
    return ''.join(c for c in s if c.isalnum() or c==' ').strip()

rk=json.load(open(D+'rankings.json')); recs=rk['records']
det=json.load(open(D+'kpis_detail.json')); KPIS=det['_kpis']; DET=det['data']
sc=json.load(open(D+'skillcorner.json'))
REFS=json.load(open(D+'scanner_refs.json'))
ARQ=json.load(open('estudo/data/arquetipos_top5.json'))
MAS=json.load(open('estudo/build/master.json'))  # top-5 players (Fase 1)

PHYS=['total_distance_p90','running_distance_p90','hi_distance_p90','hi_actions_p90',
 'hsr_distance_p90','hsr_count_p90','sprint_distance_p90','n_sprints_p90','psv99','top5_psv99',
 'high_accel_p90','med_accel_p90','high_decel_p90','med_decel_p90','explosive_accel_to_sprint',
 'cod_count_p90','m_min','m_min_tip','m_min_otip','top3_time_to_sprint','top3_time_to_hsr']
LOWER={'Fouls per 90','Fouls','Yellow cards per 90','Conceded goals per 90','xG against per 90',
 'Shots against per 90','top3_time_to_sprint','top3_time_to_hsr'}
POSMAP={'ATA':'Atacante','PE':'Extremo','PD':'Extremo','MEI':'Meia','CMF':'Medio','VOL':'Volante',
 'LAT':'Lateral','ZAG':'Zagueiro','GOL':'Goleiro'}
GROUPS={'Zagueiro':['Zagueiro - Direita','Zagueiro - Esquerda'],'Lateral':['Lateral Direito','Lateral Esquerdo'],
 'Volante':['Volante'],'Medio':['Medio'],'Meia':['Meia'],'Extremo':['Extremo - Direita','Extremo - Esquerda'],
 'Atacante':['Atacante'],'Goleiro':['Goleiro']}
POS2GROUP={p:g for g,ps in GROUPS.items() for p in ps}
# overrides p/ desambiguar homônimos (time correto)
OVR={'militao':'Real Madrid','kvara':'PSG','martinelli':'Arsenal','neves':'PSG','rodri':'Manchester City',
 'ederson':'Fenerbah','caicedo':'Chelsea','vini':'Real Madrid','raphinha':'Barcelona','alisson':'Liverpool',
 'julian':'Atlético','endrick':'Lyon','doku':'Manchester City','saka':'Arsenal','olise':'Bayern',
 'palmer':'Chelsea','rice':'Arsenal','camavinga':'Real Madrid','vitinha':'PSG','hakimi':'PSG','nuno':'PSG',
 'kimmich':'Bayern','gabriel':'Arsenal','ruben':'Manchester City','saliba':'Arsenal','cubarsi':'Barcelona',
 'courtois':'Real Madrid','oblak':'Atlético','donnarumma':'Manchester City','haaland':'Manchester City',
 'mbappe':'Real Madrid','bellingham':'Borussia Dortmund','enzo':'Bayer','valverde':'Real Madrid',
 'yamal':'Barcelona','doue':'PSG','szoboszlai':'Liverpool','nico':'Como','pedri':'Barcelona','messi':'Inter Miami'}

def kdict(pk):
    arr=DET.get(pk)
    return {KPIS[e['k']]:e['v'] for e in arr} if arr else {}
def physd(pk):
    s=sc.get(pk)
    if not s: return {}
    m=s.get('metrics') or {}
    return {k:m.get(k) for k in PHYS if m.get(k) is not None}

KNOWN_MISSING={'estevao','musiala'}  # fora do snapshot jun26 (lesão/transferência); homônimos gerariam ruído
def resolve(x,group):
    if x['key'] in KNOWN_MISSING: return None
    sur=norm(x['nome']).split()[-1]
    hint=OVR.get(x['key'])
    cands=[]
    for r in recs:
        pl=norm(r['Player']); fn=norm(r.get('tm_nome') or '')
        if sur in pl.split() or sur in fn.split():
            cands.append(r)
    if not cands: return None
    def score(r):
        g=POS2GROUP.get(r['position_group_pt'])
        s=0
        if hint and hint.lower() in norm(r['Team']): s+=1000
        if g==group: s+=100
        if r['league'] in ('Alemanha A','Espanha A','França A','Inglaterra A','Italia A','EUA','Arabia Saudita A','Turquia'): s+=20
        s+=min(30,(r.get('Minutes played') or 0)/120)
        return s
    cands.sort(key=score,reverse=True)
    return cands[0]

# ---- world pools per position (>=900, todas ligas) ----
MEANING=['Defensive duels won, %','Aerial duels won, %','PAdj Interceptions','Successful defensive actions per 90',
 'Sliding tackles per 90','Shots blocked per 90','Passes per 90','Accurate passes, %','Progressive passes per 90',
 'Accurate long passes, %','Long passes per 90','Forward passes per 90','Accurate forward passes, %',
 'Passes to final third per 90','Received passes per 90','Key passes per 90','Smart passes per 90',
 'Through passes per 90','xA per 90','Passes to penalty area per 90','Deep completions per 90',
 'Shot assists per 90','Accurate crosses, %','Crosses per 90','Deep completed crosses per 90',
 'Second assists per 90','Progressive runs per 90','Successful dribbles per 90','Dribbles per 90',
 'Accelerations per 90','xG per 90','Non-penalty goals per 90','Goals per 90','Shots per 90',
 'Touches in box per 90','Goal conversion, %','Head goals per 90','Assists per 90',
 'Save rate, %','gk_prevented_goals_per_90','Exits per 90','gk_accurate_passes_pct','Clean sheets',
 'Conceded goals per 90']+PHYS
WMIN=900
world={}  # pos -> metric -> sorted list
for r in recs:
    if (r.get('Minutes played') or 0)<WMIN: continue
    pos=r['position_group_pt']; world.setdefault(pos,{})
    kd=kdict(r['primary_key']); ph=physd(r['primary_key'])
    for m in MEANING:
        v=kd.get(m);
        if v is None: v=ph.get(m)
        if v is not None: world[pos].setdefault(m,[]).append(v)
for pos in world:
    for m in world[pos]: world[pos][m].sort()
def pct(pos,m,v):
    arr=world.get(pos,{}).get(m)
    if not arr or v is None: return None
    i=bisect.bisect_right(arr,v); p=100*i/len(arr)
    return round(100-p,1) if m in LOWER else round(p,1)

# top-5 cohort arrays (Fase 1) for elite percentile
top5={}
for p in MAS['players']:
    pos=p['pos']; top5.setdefault(pos,{})
    for m in MEANING:
        v=p['kpi'].get(m)
        if v is None: v=p['phys'].get(m)
        if v is not None: top5[pos].setdefault(m,[]).append(v)
for pos in top5:
    for m in top5[pos]: top5[pos][m].sort()
def pct5(pos,m,v):
    arr=top5.get(pos,{}).get(m)
    if not arr or v is None or len(arr)<10: return None
    i=bisect.bisect_right(arr,v); p=100*i/len(arr)
    return round(100-p,1) if m in LOWER else round(p,1)

FLAB=json.load(open('estudo/build/flab.json')) if os.path.exists('estudo/build/flab.json') else {}
# labels (reaproveita nomes amigáveis)
import importlib.util
LAB={'total_distance_p90':'Volume de corrida','running_distance_p90':'Dist. em corrida',
 'hi_distance_p90':'Dist. alta intensidade','hi_actions_p90':'Ações alta intensidade',
 'hsr_distance_p90':'Dist. corrida veloz','hsr_count_p90':'Corridas velozes','sprint_distance_p90':'Dist. em sprint',
 'n_sprints_p90':'Volume de sprints','psv99':'Velocidade de ponta','top5_psv99':'Velocidade máx.',
 'high_accel_p90':'Acelerações fortes','med_accel_p90':'Acelerações','high_decel_p90':'Freadas fortes',
 'med_decel_p90':'Freadas','explosive_accel_to_sprint':'Explosão','cod_count_p90':'Mudança de direção',
 'm_min':'Intensidade (m/min)','m_min_tip':'Intensidade c/ posse','m_min_otip':'Intensidade s/ posse',
 'top3_time_to_sprint':'Arranque até sprint','top3_time_to_hsr':'Arranque até corrida veloz',
 'Defensive duels won, %':'Duelos defensivos','Aerial duels won, %':'Jogo aéreo','PAdj Interceptions':'Interceptações',
 'Successful defensive actions per 90':'Ações defensivas','Sliding tackles per 90':'Desarmes (carrinho)',
 'Shots blocked per 90':'Bloqueios','Passes per 90':'Volume de passe','Accurate passes, %':'Acerto de passe',
 'Progressive passes per 90':'Passe progressivo','Accurate long passes, %':'Passe longo (acerto)',
 'Long passes per 90':'Passes longos','Forward passes per 90':'Passe para frente','Accurate forward passes, %':'Passe p/ frente (acerto)',
 'Passes to final third per 90':'Passe ao terço final','Received passes per 90':'Envolvimento (passes recebidos)',
 'Key passes per 90':'Passe decisivo','Smart passes per 90':'Passe inteligente','Through passes per 90':'Passe em profundidade',
 'xA per 90':'Criação (xA)','Passes to penalty area per 90':'Passe para a área','Deep completions per 90':'Chegada ao terço',
 'Shot assists per 90':'Assist. p/ finalização','Accurate crosses, %':'Cruzamento (acerto)','Crosses per 90':'Cruzamentos',
 'Deep completed crosses per 90':'Cruzamento ao terço','Second assists per 90':'Segunda assistência',
 'Progressive runs per 90':'Condução progressiva','Successful dribbles per 90':'Dribles certos','Dribbles per 90':'Dribles',
 'Accelerations per 90':'Arranques','xG per 90':'Volume de chance (xG)','Non-penalty goals per 90':'Gols (s/ pênalti)',
 'Goals per 90':'Gols','Shots per 90':'Finalizações','Touches in box per 90':'Presença na área',
 'Goal conversion, %':'Conversão','Head goals per 90':'Gol de cabeça','Assists per 90':'Assistências',
 'Save rate, %':'Taxa de defesa','gk_prevented_goals_per_90':'Gols evitados','Exits per 90':'Saídas do gol',
 'gk_accurate_passes_pct':'Passe (acerto)','Clean sheets':'Jogos sem sofrer','Conceded goals per 90':'Gols sofridos'}
def lab(m): return LAB.get(m,m)

# relevant metric subset per group para "top em" (evita ruído)
REL={'Zagueiro':['Defensive duels won, %','Aerial duels won, %','PAdj Interceptions','Successful defensive actions per 90',
  'Shots blocked per 90','Progressive passes per 90','Accurate passes, %','Accurate long passes, %','Passes to final third per 90',
  'Received passes per 90','Progressive runs per 90','psv99','top5_psv99','hi_distance_p90','high_accel_p90','explosive_accel_to_sprint'],
 'Lateral':['Defensive duels won, %','Successful defensive actions per 90','Accurate crosses, %','Crosses per 90',
  'Deep completed crosses per 90','xA per 90','Progressive runs per 90','Successful dribbles per 90','Accurate passes, %',
  'Passes to final third per 90','n_sprints_p90','psv99','sprint_distance_p90','high_accel_p90','total_distance_p90','explosive_accel_to_sprint'],
 'Volante':['Defensive duels won, %','PAdj Interceptions','Successful defensive actions per 90','Sliding tackles per 90',
  'Accurate passes, %','Progressive passes per 90','Passes to final third per 90','Through passes per 90','Key passes per 90',
  'xA per 90','Received passes per 90','total_distance_p90','hi_distance_p90','hsr_count_p90'],
 'Medio':['Accurate passes, %','Progressive passes per 90','Through passes per 90','Smart passes per 90','Key passes per 90',
  'xA per 90','Passes to penalty area per 90','Deep completions per 90','Progressive runs per 90','Successful dribbles per 90',
  'Non-penalty goals per 90','xG per 90','total_distance_p90','hi_distance_p90','n_sprints_p90'],
 'Meia':['Key passes per 90','xA per 90','Through passes per 90','Smart passes per 90','Passes to penalty area per 90',
  'Deep completions per 90','Non-penalty goals per 90','xG per 90','Shots per 90','Successful dribbles per 90',
  'Touches in box per 90','Progressive runs per 90','Accelerations per 90','explosive_accel_to_sprint'],
 'Extremo':['Successful dribbles per 90','Dribbles per 90','Progressive runs per 90','xA per 90','Key passes per 90',
  'Passes to penalty area per 90','Non-penalty goals per 90','xG per 90','Shots per 90','Touches in box per 90',
  'Accurate crosses, %','psv99','top5_psv99','explosive_accel_to_sprint','n_sprints_p90'],
 'Atacante':['Non-penalty goals per 90','xG per 90','Shots per 90','Goal conversion, %','Touches in box per 90',
  'Head goals per 90','Aerial duels won, %','xA per 90','Key passes per 90','Successful dribbles per 90',
  'psv99','explosive_accel_to_sprint','n_sprints_p90','hi_distance_p90'],
 'Goleiro':['Save rate, %','gk_prevented_goals_per_90','Clean sheets','Conceded goals per 90','Passes per 90',
  'gk_accurate_passes_pct','Accurate long passes, %','Long passes per 90','Exits per 90','Aerial duels won, %']}

# radar axes (8) por grupo — percentil vs mundo
AXES={
 'Goleiro':['Save rate, %','gk_prevented_goals_per_90','Clean sheets','Conceded goals per 90','Passes per 90','gk_accurate_passes_pct','Accurate long passes, %','Exits per 90'],
 'Zagueiro':['Defensive duels won, %','Aerial duels won, %','PAdj Interceptions','Successful defensive actions per 90','Progressive passes per 90','Accurate passes, %','psv99','hi_distance_p90'],
 'Lateral':['Successful defensive actions per 90','Aerial duels won, %','Accurate crosses, %','xA per 90','Progressive runs per 90','Accurate passes, %','n_sprints_p90','psv99'],
 'Volante':['Successful defensive actions per 90','PAdj Interceptions','Accurate passes, %','Progressive passes per 90','Through passes per 90','xA per 90','total_distance_p90','hi_distance_p90'],
 'Medio':['Accurate passes, %','Progressive passes per 90','Through passes per 90','Key passes per 90','xA per 90','Progressive runs per 90','Non-penalty goals per 90','hi_distance_p90'],
 'Meia':['Key passes per 90','xA per 90','Through passes per 90','Smart passes per 90','Non-penalty goals per 90','xG per 90','Successful dribbles per 90','Touches in box per 90'],
 'Extremo':['Successful dribbles per 90','Progressive runs per 90','xA per 90','Key passes per 90','Non-penalty goals per 90','Touches in box per 90','psv99','explosive_accel_to_sprint'],
 'Atacante':['Non-penalty goals per 90','xG per 90','Shots per 90','Goal conversion, %','Touches in box per 90','xA per 90','Aerial duels won, %','psv99']}

# ---- cluster (Fase 1) frame: group mean/std sobre features do arquétipo ----
def group_frame(g):
    feats=ARQ['grupos'][g]['features']
    poss=GROUPS[g]; pl=[p for p in MAS['players'] if p['pos'] in poss]
    med={}
    for f in feats:
        vals=[(p['kpi'].get(f) if p['kpi'].get(f) is not None else p['phys'].get(f)) for p in pl]
        vals=[v for v in vals if v is not None]
        med[f]=st.median(vals) if vals else 0.0
    mu={}; sd={}
    for f in feats:
        col=[]
        for p in pl:
            v=p['kpi'].get(f);
            if v is None: v=p['phys'].get(f)
            col.append(v if v is not None else med[f])
        mu[f]=st.mean(col); sd[f]=(st.pstdev(col) if len(col)>1 else 0)or 1.0
    return feats,med,mu,sd
FRAMES={g:group_frame(g) for g in GROUPS}
def my_archetype(g,kd,ph):
    feats,med,mu,sd=FRAMES[g]
    z={}
    for f in feats:
        v=kd.get(f);
        if v is None: v=ph.get(f)
        if v is None: v=med[f]
        z[f]=(v-mu[f])/sd[f]
    best=None
    for a in ARQ['grupos'][g]['arquetipos']:
        c=a['centroide_z']; cf=list(dict.fromkeys(f for f in feats if abs(c.get(f,0))>1e-9))
        cn=math.sqrt(sum(c[f]**2 for f in cf))or 1; zn=math.sqrt(sum(z[f]**2 for f in cf))or 1
        cos=sum(z[f]*c.get(f,0) for f in cf)/(zn*cn)
        if best is None or cos>best[0]: best=(cos,a['nome'],a['tag'])
    return best

# ---- build dossiers ----
dossies=[]; seen=set()
for grp in REFS:
    g=POSMAP[grp['pos']]
    for x in grp['refs']:
        if x['key'] in seen: continue
        seen.add(x['key'])
        r=resolve(x,g)
        if not r:
            dossies.append({'key':x['key'],'nome':x['nome'],'grupo':g,'arq_scout':x['archetype'],'found':False}); continue
        pos=r['position_group_pt']; kd=kdict(r['primary_key']); ph=physd(r['primary_key'])
        rel=REL[g]
        tops=[]
        for m in rel:
            v=kd.get(m);
            if v is None: v=ph.get(m)
            p=pct(pos,m,v)
            if p is None: continue
            tops.append({'m':m,'lab':lab(m),'v':round(v,2),'pct':p,'pct5':pct5(pos,m,v),
                         'kind':'fis' if m in PHYS else 'tec'})
        tops.sort(key=lambda t:-t['pct'])
        myb=my_archetype(g,kd,ph)
        radar=[{'ax':lab(m),'pct':pct(pos,m,(kd.get(m) if kd.get(m) is not None else ph.get(m)))}
               for m in AXES[g]]
        radar=[a for a in radar if a['pct'] is not None]
        dossies.append({'key':x['key'],'nome':x['nome'],'grupo':g,'pos':pos,'found':True,'radar':radar,
          'arq_scout':x['archetype'],'arq_meu':myb[1],'arq_meu_tag':myb[2],'arq_meu_match':round(max(0,myb[0])*100,1),
          'team':r['Team'],'league':r['league'],'age':r.get('Age'),'height':r.get('Height'),
          'foot':r.get('Foot'),'minutes':r.get('Minutes played'),'mv':r.get('Market value'),
          'overall':r.get('overall'),'n_temporadas':x.get('n_temporadas'),
          'top':tops[:10],'all':{t['m']:t['pct'] for t in tops}})

out={'meta':{'n':len(dossies),'found':sum(1 for d in dossies if d.get('found'))},
     'grupos_ordem':['Goleiro','Zagueiro','Lateral','Volante','Medio','Meia','Extremo','Atacante'],
     'dossies':dossies}
json.dump(out,open('estudo/data/dossies_refs.json','w'),ensure_ascii=False,indent=1)
print('dossies:',len(dossies),'| found:',out['meta']['found'])
for d in dossies:
    if not d.get('found'): print('  MISSING',d['nome']); continue
for g in out['grupos_ordem']:
    print(f'\n### {g}')
    for d in dossies:
        if d['grupo']!=g or not d.get('found'): continue
        t=d['top'][0]
        print(f"  {d['nome']:22s} scout='{d['arq_scout']}' | meu='{d['arq_meu']}' ({d['arq_meu_match']}%) | top: {d['top'][0]['lab']} p{d['top'][0]['pct']:.0f}, {d['top'][1]['lab']} p{d['top'][1]['pct']:.0f}")
