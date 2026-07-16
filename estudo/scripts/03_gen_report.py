# -*- coding: utf-8 -*-
import json, os, statistics as st
SP='estudo/build/'
os.makedirs(SP,exist_ok=True)
R=json.load(open(SP+'results.json'))
M=json.load(open(SP+'master.json'))
PS=M['positions_summary']; PL=R['phys_label']
def lab(f): return PL.get(f,f)

# ---- archetype labels/notes keyed by group, in size-desc order (deterministic) ----
LABELS={
 'Zagueiro':[
  {'nome':'Marcador de área (stopper)','tag':'Físico/aéreo',
   'desc':'Duelo aéreo e bloqueios altos, passe longo, pouca corrida de alta intensidade — protege a área e não a linha.',
   'scout':'Na América do Sul: zagueiro alto, forte no jogo aéreo e no bloqueio, mesmo que lento — priorizar % de duelo aéreo e altura.'},
  {'nome':'Defensor de espaço (veloz)','tag':'Moderno',
   'desc':'Velocidade máxima e explosão altas, passe seguro, corre pouco em volume — defende o espaço nas costas com velocidade, não com posicionamento.',
   'scout':'Procurar PSV99/velocidade de ponta alta e aceleração; permite linha alta. Raro e valioso no mercado sul-americano jovem.'},
  {'nome':'Construtor (saída de bola)','tag':'Construtor',
   'desc':'Maior volume e qualidade de passe: passes para o terço final, progressivos, recebidos — o zagueiro que inicia o jogo. Maior índice do grupo.',
   'scout':'Volume de passe, passe progressivo e % de acerto sob pressão; conforto para receber virado. O arquétipo mais vendável.'},
  {'nome':'Zagueiro móvel (linha alta)','tag':'Box-to-box',
   'desc':'Máximo de alta intensidade, HSR e sprints do grupo, menos duelo aéreo — cobre muito campo, ideal para linha alta e pressão.',
   'scout':'Distância de alta intensidade e nº de sprints elevados; combina defesa avançada e recuperação. Perfil atlético jovem.'},
 ],
 'Lateral':[
  {'nome':'Lateral defensivo (conservador)','tag':'Defensivo',
   'desc':'Ações defensivas, passe para frente e duelo aéreo; baixo volume de corrida e ameaça ofensiva quase nula.',
   'scout':'Solidez defensiva e leitura; menos apoio. Menos escasso — só priorizar se o projeto pede equilíbrio.'},
  {'nome':'Ala ofensivo (explosivo)','tag':'Explosivo',
   'desc':'Distância em sprint, explosão e acelerações no topo do grupo — o lateral que ataca a profundidade e ultrapassa.',
   'scout':'Sprint e explosão altos; capacidade de ir à linha de fundo. Perfil de maior valorização (ala moderno).'},
  {'nome':'Motor incansável (volume)','tag':'Volume',
   'desc':'Maior distância total e metros/min, sem velocidade de ponta — sustenta o corredor os 90 minutos por repetição, não por explosão.',
   'scout':'Volume físico e capacidade aeróbica; ida-e-volta constante. Bom custo-benefício se o resto for decente.'},
  {'nome':'Lateral posicional (baixa intensidade)','tag':'Posicional',
   'desc':'Passe longo/para frente e desarme, baixíssima intensidade — muitas vezes zagueiro adaptado ou veterano de posse.',
   'scout':'Perfil de leitura e passe; pouco apelo físico para revenda de jovem.'},
 ],
 'Volante':[
  {'nome':'Regista posicional (metrônomo)','tag':'Posicional',
   'desc':'Passe de maior distância média, baixa intensidade física — controla o ritmo à frente da defesa sem cobrir muito campo.',
   'scout':'Qualidade e tempo de passe, inteligência posicional; físico secundário. Ex.: perfil Modrić/Parejo.'},
  {'nome':'Recuperador box-to-box (intensidade)','tag':'Box-to-box',
   'desc':'Máximo de alta intensidade, HSR e sprints, menos progressão de passe — o motor que recupera e cobre.',
   'scout':'Volume de alta intensidade e desarme; o perfil mais fácil de achar atleticamente na base sul-americana.'},
  {'nome':'Organizador (deep-lying playmaker)','tag':'Criador',
   'desc':'Passe em profundidade, para a área e progressivo no topo do grupo — dita o jogo desde trás. Maior índice do grupo.',
   'scout':'Passe entrelinhas e progressivo, visão; raro e caro. O mais vendável dos volantes.'},
 ],
 'Medio':[
  {'nome':'Médio de equilíbrio (aéreo)','tag':'Equilíbrio',
   'desc':'Forte no aéreo e no passe seguro, lento para o sprint — o meio-campista de ligação e cobertura.',
   'scout':'Equilíbrio defensivo, aéreo e passe simples confiável; físico de resistência.'},
  {'nome':'Box-to-box de intensidade','tag':'Intensidade',
   'desc':'Máximo de alta intensidade e HSR do grupo — chega à área e recompõe, o "motor" moderno.',
   'scout':'Alta intensidade repetida, chegada à área; perfil atlético de grande valorização.'},
  {'nome':'Condutor explosivo','tag':'Condutor',
   'desc':'Velocidade de ponta e explosão altas, baixo volume, mais drible — carrega a bola e quebra linhas conduzindo.',
   'scout':'Condução, explosão e 1v1; típico talento sul-americano jovem de alto teto.'},
  {'nome':'Organizador (criador)','tag':'Criador',
   'desc':'Passe em profundidade, progressivo e para a área no topo do grupo — o cérebro criativo do meio. Maior índice.',
   'scout':'Passe de ruptura e visão; escasso. O perfil premium de meio-campo.'},
 ],
 'Meia':[
  {'nome':'Meia de intensidade (2º atacante)','tag':'Intensidade',
   'desc':'Alta intensidade e corrida veloz, menos criação final — o meia que ataca o espaço e faz o gol, mais que a última assistência.',
   'scout':'Chegada, finalização e intensidade; perfil de meia-atacante moderno muito procurado.'},
  {'nome':'Armador clássico (camisa 10)','tag':'Armador',
   'desc':'Passe em profundidade, inteligente e progressivo no topo do grupo, baixa intensidade — cria com o passe, não com a corrida.',
   'scout':'Último passe, xA e visão; craque de organização. Raro e de alto valor.'},
  {'nome':'Condutor/driblador','tag':'Condutor',
   'desc':'Drible, condução progressiva e presença na área no topo do grupo — desequilibra no 1v1 e aparece para finalizar.',
   'scout':'Drible, condução e explosão; o arquétipo criativo sul-americano por excelência.'},
 ],
 'Extremo':[
  {'nome':'Motor vertical (profundidade)','tag':'Vertical',
   'desc':'Máximo de alta intensidade, HSR e mudanças de direção, pouca criação — ataca a profundidade e pressiona sem parar.',
   'scout':'Velocidade repetida e verticalidade; perfil de ponta de energia, de fácil valorização se ganhar decisão.'},
  {'nome':'Driblador de pé invertido (finalizador)','tag':'Driblador',
   'desc':'Drible e condução, baixo volume de corrida — o ponta que encara para dentro e finaliza, economizando fisicamente.',
   'scout':'Drible em 1v1, pé invertido e finalização; talento clássico sul-americano de revenda.'},
  {'nome':'Ponta associativo (não-veloz)','tag':'Associativo',
   'desc':'Muito volume de corrida mas sem velocidade de ponta — joga associado, de posse, combinando curto.',
   'scout':'Técnica e associação; menos apelo de revanda se faltar explosão.'},
  {'nome':'Craque criador de elite','tag':'Craque',
   'desc':'Presença na área, passe-chave, xA e explosão no topo — o ponta que dribla, cria e finaliza. Maior índice e valor (mediana ~36M€).',
   'scout':'O alvo de ouro: drible + criação + explosão + faro de área num jogador só. Ex.: Lamine Yamal, Olise.'},
 ],
 'Atacante':[
  {'nome':'Centroavante de área (fixo)','tag':'Área/aéreo',
   'desc':'Jogo aéreo e gols de cabeça, baixa intensidade e velocidade — o 9 de referência que vive na área.',
   'scout':'Presença de área, aéreo e finalização de primeira; físico/altura sobre mobilidade.'},
  {'nome':'Atacante de profundidade (velocista)','tag':'Velocista',
   'desc':'Velocidade máxima e explosão no topo, ataca as costas da defesa — o 9 que corre para o espaço.',
   'scout':'Velocidade de ponta e explosão + finalização; perfil sul-americano jovem de maior valorização (Mbappé/Vini).'},
  {'nome':'Atacante móvel (pressionador)','tag':'Móvel',
   'desc':'Muito volume de corrida, menos xG/conversão — o 9 que se movimenta, pressiona e associa mais do que finaliza.',
   'scout':'Trabalho sem bola, mobilidade e pressão; complementa sistema, valor médio.'},
  {'nome':'Falso-9 / atacante-criador','tag':'Criador',
   'desc':'Passe em profundidade, inteligente e xA muito acima, pouca velocidade — recua para criar e ligar o jogo. Maior índice e valor (mediana 20M€).',
   'scout':'Associação, último passe e finalização; raro. Ex.: Dembélé, Kane, Dybala.'},
 ],
 'Goleiro':[
  {'nome':'Goleiro reativo (menos jogo de pés)','tag':'Reativo',
   'desc':'Mais saídas, distribuição mais fraca e menos jogos sem sofrer — goleiro de linha/reação.',
   'scout':'Reflexo e saída; menos construção. Avaliar se o projeto exige jogo de pés.'},
  {'nome':'Goleiro de rendimento (defesas de elite)','tag':'Rendimento',
   'desc':'Taxa de defesa, gols evitados e jogos sem sofrer no topo — o goleiro que ganha pontos defendendo. Maior índice.',
   'scout':'Gols evitados (prevented goals) e taxa de defesa acima da média; o KPI que mais separa. Perfil premium.'},
  {'nome':'Goleiro construtor (jogo de pés)','tag':'Construtor',
   'desc':'Muito volume de passe e jogo com os pés, mas sofre mais — típico de time de posse com defesa frágil.',
   'scout':'Distribuição e conforto com a bola; separar mérito do goleiro do contexto do time.'},
 ],
}

GROUPS_ORDER=['Goleiro','Zagueiro','Lateral','Volante','Medio','Meia','Extremo','Atacante']
GROUP_FULL={'Goleiro':'Goleiros','Zagueiro':'Zagueiros','Lateral':'Laterais',
 'Volante':'Volantes','Medio':'Médios (meio-campo central)','Meia':'Meias (armadores)',
 'Extremo':'Extremos (pontas)','Atacante':'Atacantes (centroavantes)'}

# ---- between-position physical heatmap columns (curated) ----
PHEAT=[('total_distance_p90','Volume (dist. total)'),('m_min_otip','Intens. s/ posse'),
 ('hi_distance_p90','Alta intensidade'),('hsr_count_p90','Corridas velozes (HSR)'),
 ('n_sprints_p90','Sprints'),('psv99','Veloc. de ponta'),
 ('high_accel_p90','Acelerações fortes'),('cod_count_p90','Mudanças de direção'),
 ('explosive_accel_to_sprint','Explosão')]
POS_ORDER=['Goleiro','Zagueiro - Direita','Zagueiro - Esquerda','Lateral Direito','Lateral Esquerdo',
 'Volante','Medio','Meia','Extremo - Direita','Extremo - Esquerda','Atacante']
POS_SHORT={'Goleiro':'Goleiro','Zagueiro - Direita':'Zagueiro (D)','Zagueiro - Esquerda':'Zagueiro (E)',
 'Lateral Direito':'Lateral (D)','Lateral Esquerdo':'Lateral (E)','Volante':'Volante','Medio':'Médio',
 'Meia':'Meia','Extremo - Direita':'Extremo (D)','Extremo - Esquerda':'Extremo (E)','Atacante':'Atacante'}

heat=[]
for pos in POS_ORDER:
    row=R['between_phys'].get(pos,{})
    heat.append({'pos':POS_SHORT[pos],'vals':[round(row.get(k,0),2) for k,_ in PHEAT]})

# ---- differentials per position (merge L/R into group for narrative) ----
def clean_metric(m): return m
diff_by_pos={}
for pos,rows in R['diffs'].items():
    out=[]
    for r in rows[:8]:
        out.append({'m':r['metric'],'cat':('FÍSICO' if r['kind']=='fis' else r['cat']),
                    'p':round(r['eff']),'bp':(round(r['beff']) if r['beff'] is not None else None),
                    'wm':r['world_med'],'t5':r['top5_med']})
    diff_by_pos[pos]=out

# representative position per group for the differential panel
GROUP_REPPOS={'Goleiro':'Goleiro','Zagueiro':'Zagueiro - Direita','Lateral':'Lateral Direito',
 'Volante':'Volante','Medio':'Medio','Meia':'Meia','Extremo':'Extremo - Direita','Atacante':'Atacante'}

# ---- archetypes payload ----
arche={}
for g in GROUPS_ORDER:
    c=R['clusters'][g]
    labs=LABELS[g]
    cs=[]
    for i,cl in enumerate(c['clusters']):
        L=labs[i] if i<len(labs) else {'nome':f'Grupo {i+1}','tag':'','desc':'','scout':''}
        bars=[{'m':lab(f),'z':z} for f,z in (cl['hi'][:5])]
        bars+= [{'m':lab(f),'z':z} for f,z in (cl['lo'][:3])]
        ex=[{'n':e['name'],'t':e['team'],'l':e['league'],'ovr':e['overall'],'age':e['age'],'mv':e['mv']}
            for e in cl['ex_top'][:6]]
        cs.append({'nome':L['nome'],'tag':L['tag'],'desc':L['desc'],'scout':L['scout'],
                   'n':cl['n'],'ovr':cl['avg_overall'],'age':cl['avg_age'],'mv':cl['med_mv'],
                   'bars':bars,'ex':ex})
    arche[g]={'full':GROUP_FULL[g],'n':c['n'],'k':c['k'],'clusters':cs,
              'diff':diff_by_pos[GROUP_REPPOS[g]]}

payload={
 'meta':{'n_players':len(M['players']),'min_min':M['min_min'],
         'leagues':list(M['leagues'].values()),
         'var_between':R['var_decomp']['between_pct'],'var_within':R['var_decomp']['within_pct'],
         'n_var':R['var_decomp']['n']},
 'pheat_cols':[l for _,l in PHEAT],'heat':heat,
 'groups_order':GROUPS_ORDER,'arche':arche,
}
json.dump(payload,open(SP+'report.json','w'),ensure_ascii=False)
print('report.json written. groups:',len(arche),'players:',payload['meta']['n_players'])
for g in GROUPS_ORDER:
    print(' ',g,arche[g]['k'],'arquétipos, n=',arche[g]['n'])
