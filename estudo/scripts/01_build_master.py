import json, os, statistics as st
from collections import defaultdict

DATA='data/jun26/'
TOP5={'Alemanha A':'Bundesliga','Espanha A':'La Liga','França A':'Ligue 1',
      'Inglaterra A':'Premier League','Italia A':'Serie A'}
MINMIN=900

rk=json.load(open(DATA+'rankings.json'))
recs=rk['records']
det=json.load(open(DATA+'kpis_detail.json'))
KPIS=det['_kpis']; CATS=det['_cats']; DET=det['data']
sc=json.load(open(DATA+'skillcorner.json'))

PHYS=['total_distance_p90','running_distance_p90','hi_distance_p90','hi_actions_p90',
      'hsr_distance_p90','hsr_count_p90','sprint_distance_p90','n_sprints_p90',
      'psv99','top5_psv99','high_accel_p90','med_accel_p90','high_decel_p90','med_decel_p90',
      'explosive_accel_to_sprint','cod_count_p90','m_min','m_min_tip','m_min_otip',
      'top3_time_to_sprint','top3_time_to_hsr']

def kdict(pk):
    """return {kpi_name: value} for a player from detail"""
    arr=DET.get(pk)
    if not arr: return {}
    out={}
    for e in arr:
        out[KPIS[e['k']]]=e['v']
    return out

# index rankings by pk
recmap={r['primary_key']:r for r in recs}

# ---- World pools per position (all leagues, >=900 min) ----
world_pos=defaultdict(list)   # pos -> list of pk
for r in recs:
    if (r.get('Minutes played') or 0)>=MINMIN:
        world_pos[r['position_group_pt']].append(r['primary_key'])

def pctile_rank(sorted_vals, x):
    # fraction of world <= x
    import bisect
    if not sorted_vals: return None
    i=bisect.bisect_right(sorted_vals,x)
    return round(100*i/len(sorted_vals),1)

def quant(sorted_vals,q):
    if not sorted_vals: return None
    if len(sorted_vals)==1: return sorted_vals[0]
    idx=q*(len(sorted_vals)-1)
    lo=int(idx); hi=min(lo+1,len(sorted_vals)-1)
    return sorted_vals[lo]+(sorted_vals[hi]-sorted_vals[lo])*(idx-lo)

# world KPI arrays per position
world_kpi=defaultdict(lambda: defaultdict(list))
for pos,pks in world_pos.items():
    for pk in pks:
        kd=kdict(pk)
        for name,v in kd.items():
            if v is not None:
                world_kpi[pos][name].append(v)
    for name in list(world_kpi[pos]):
        world_kpi[pos][name].sort()

# world physical arrays per position
world_phys=defaultdict(lambda: defaultdict(list))
for pos,pks in world_pos.items():
    for pk in pks:
        s=sc.get(pk)
        if not s: continue
        m=s.get('metrics') or {}
        for key in PHYS:
            v=m.get(key)
            if v is not None:
                world_phys[pos][key].append(v)
    for key in list(world_phys[pos]):
        world_phys[pos][key].sort()

# ---- Build top5 player records ----
players=[]
for r in recs:
    if r['league'] in TOP5 and (r.get('Minutes played') or 0)>=MINMIN:
        pk=r['primary_key']; pos=r['position_group_pt']
        kd=kdict(pk)
        s=sc.get(pk); phys={}
        if s:
            m=s.get('metrics') or {}
            for key in PHYS:
                if m.get(key) is not None: phys[key]=m[key]
        players.append({
            'pk':pk,'name':r.get('tm_nome') or r['Player'],'short':r['Player'],
            'team':r['Team'],'league':TOP5[r['league']],'pos':pos,
            'age':r.get('Age'),'height':r.get('Height'),'weight':r.get('Weight'),
            'foot':r.get('Foot'),'mv':r.get('Market value'),'minutes':r.get('Minutes played'),
            'overall':r.get('overall'),'off':r.get('overall_offensive'),
            'defe':r.get('overall_deffensive'),'pass':r.get('overall_pass'),
            'dgp':r.get('overall_dgp'),'phy':r.get('phy_score'),
            'rank':r.get('rank'),'birth':r.get('Birth country'),
            'kpi':kd,'phys':phys,
        })

# ---- Position-level KPI/phys summary ----
def summarr(a):
    if not a: return None
    return {'mean':round(st.mean(a),3),'med':round(quant(a,.5),3),
            'p10':round(quant(a,.1),3),'p90':round(quant(a,.9),3),
            'std':round(st.pstdev(a),4) if len(a)>1 else 0.0,'n':len(a)}

pos_summary={}
for pos in world_pos:
    top5_pl=[p for p in players if p['pos']==pos]
    # top decile by overall within top5
    ov=sorted([p for p in top5_pl if p['overall'] is not None],key=lambda p:-p['overall'])
    best=ov[:max(3,len(ov)//10)]
    ks={}
    for name in world_kpi[pos]:
        wv=world_kpi[pos][name]
        t5=[p['kpi'].get(name) for p in top5_pl if p['kpi'].get(name) is not None]
        bs=[p['kpi'].get(name) for p in best if p['kpi'].get(name) is not None]
        ks[name]={'world':summarr(wv),'top5':summarr(t5),'best':summarr(bs),
                  'cat':None,
                  'top5_med_pct':pctile_rank(wv,quant(sorted(t5),.5)) if t5 else None,
                  'best_med_pct':pctile_rank(wv,quant(sorted(bs),.5)) if bs else None}
    ps={}
    for key in world_phys[pos]:
        wv=world_phys[pos][key]
        t5=[p['phys'].get(key) for p in top5_pl if p['phys'].get(key) is not None]
        bs=[p['phys'].get(key) for p in best if p['phys'].get(key) is not None]
        ps[key]={'world':summarr(wv),'top5':summarr(t5),'best':summarr(bs),
                 'top5_med_pct':pctile_rank(wv,quant(sorted(t5),.5)) if t5 else None,
                 'best_med_pct':pctile_rank(wv,quant(sorted(bs),.5)) if bs else None}
    pos_summary[pos]={'n_world':len(world_pos[pos]),'n_top5':len(top5_pl),
                      'n_best':len(best),'kpi':ks,'phys':ps}

# kpi category map
catmap={}
for pos,pks in world_pos.items():
    for pk in pks[:1]:
        arr=DET.get(pk) or []
        for e in arr: catmap[KPIS[e['k']]]=CATS[e['c']]
        break

out={'positions_summary':pos_summary,'players':players,'phys_keys':PHYS,
     'kpi_list':KPIS,'catmap':catmap,'leagues':TOP5,'min_min':MINMIN}
json.dump(out,open('estudo/build/master.json','w'))
print('players',len(players))
print('positions',len(pos_summary))
for pos,s in sorted(pos_summary.items()):
    print(f'  {pos:22s} world={s["n_world"]:4d} top5={s["n_top5"]:3d} best={s["n_best"]}')
EOF_MARKER=1
