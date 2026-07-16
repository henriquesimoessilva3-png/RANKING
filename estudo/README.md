# Estudo Top-5 · Perfis e Arquétipos

Estudo dos jogadores das **cinco grandes ligas europeias** (Premier League, La Liga,
Bundesliga, Serie A, Ligue 1) com **≥ 900 minutos** na temporada 2025/26, cruzando
métricas técnicas (114 KPIs) com dados físicos de rastreamento (SkillCorner).

Objetivo: mapear o padrão de elite **por posição** e **por arquétipo dentro da posição**,
para servir de gabarito na próxima fase — a busca de jovens sul-americanos com o mesmo DNA.

## O que abrir

- **`index.html`** — dashboard visual (self-contained, tema claro/escuro). Abra no navegador.
- **`data/arquetipos_top5.json`** — os "moldes" estruturados: cada arquétipo com seu
  centroide (z-score médio vs. a média da posição) no espaço de features, referências
  reais e alvo de scouting. É o insumo da fase de similaridade.

## Principais achados

1. **Posição explica menos da metade.** Da variação do perfil físico, ~47% está *entre*
   posições e **~53% está *dentro* de cada posição** — os arquétipos importam tanto
   quanto a posição.
2. **Assinaturas físicas nítidas por posição:** volantes/médios = volume + baixa
   velocidade; extremos/laterais = velocidade, sprint e aceleração; atacantes =
   explosivos mas econômicos; zagueiros = pouca corrida (com um subgrupo veloz).
3. **O diferencial das grandes ligas vs. o mundo** não é correr mais — é
   **envolvimento com a bola**, **retenção sob pressão** e **explosividade**. Entre a
   elite (top-10%), o salto vem da **progressão e criação**.
4. **29 arquétipos** em 8 grupos de posição. Os mais raros e caros são consistentemente
   os de **criação/progressão** e **velocidade pura** — os alvos de maior valorização.

## Reprodutibilidade

Pipeline em Python puro (sem dependências), a partir da raiz do repositório:

```bash
python3 estudo/scripts/01_build_master.py   # junta rankings+kpis_detail+skillcorner -> build/master.json
python3 estudo/scripts/02_analyze.py        # diferenciais, assinaturas, clusterização -> build/results.json
python3 estudo/scripts/03_gen_report.py     # payload do dashboard -> build/report.json
```

Fonte de dados: `data/jun26/` (rankings, kpis_detail, skillcorner). A pasta `estudo/build/`
é intermediária e não é versionada.

## Metodologia (resumo)

- **Amostra:** 1602 jogadores das 5 ligas com ≥ 900 min. Benchmark mundial: titulares
  (≥ 900 min) de 60+ ligas.
- **Arquétipos:** k-means sobre métricas padronizadas (z-score) dentro de cada grupo de
  posição; posições espelhadas (D/E) unidas para robustez amostral.
- **Leitura:** o "índice" é a nota composta do modelo (relativa). As silhouettes de
  cluster são baixas por natureza — estilos de jogo formam um contínuo; os arquétipos
  são polos interpretáveis, não fronteiras rígidas.
