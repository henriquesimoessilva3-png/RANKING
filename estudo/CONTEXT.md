# CONTEXTO DA SESSÃO — Estudo de Scouting (retomar aqui)

> Handoff para continuar o trabalho em outra sessão (local ou web). Lê este arquivo
> primeiro. Tudo está commitado na branch **`claude/top-5-leagues-player-analysis-vqxqrh`**
> (PR **#4**, draft, aberto e mergeable). Data da última sessão: 2026-07-16.

---

## 1. Objetivo de negócio (a pergunta que guia tudo)

> **Por posição, quem o Botafogo deve contratar** que (a) possa ser **titular e entregar
> resultado/títulos já** e (b) possa ser **revendido com lucro** para o mercado europeu.

A lógica em 4 camadas, todas construídas:
1. **Fase 1** — o padrão de elite das 5 grandes ligas europeias (o perfil que a Europa compra).
2. **Fase 3** — dossiês dos jogadores-referência mundiais do ranking (a régua por arquétipo).
3. **Fase 2** — jovens sul-americanos que batem esses moldes (o upside de revenda).
4. **Fase 4** — a síntese: recomendação de contratação por posição (prontidão × revenda).

---

## 2. Onde estão os dados (entrada)

Pasta `data/jun26/` (período mais recente; há histórico em `data/2018..2025`, `abr26`).
Arquivos-chave:

- **`rankings.json`** — `{periodo, total, leagues[], positions[], records[]}`. 18.296 jogadores
  de 64 ligas. Cada record: identidade (`Player`, `tm_nome`, `Team`, `league`, `Age`,
  `Height`, `Foot`, `Market value`, `Minutes played`, `Birth country`), posição
  (`position_group_pt` = uma das 11), notas do modelo (`overall`, `overall_offensive`,
  `overall_deffensive`, `overall_pass`, `overall_dgp`, `phy_score`), `rank*`, e a flag
  **`isBotafogo`** (elenco atual do clube).
- **`kpis_detail.json`** (89 MB) — `{_kpis[114], _cats[12], data{}}`. `data[primary_key]`
  = lista de `{k:idx_kpi, c:idx_cat, v:valor_do_jogador, a:média_posição, m:máx_posição, w:peso}`.
  `primary_key` = `"Player - Team - League"`. É a base técnica (114 KPIs Wyscout por 90').
- **`skillcorner.json`** (15 MB) — dados físicos de rastreamento por `primary_key`:
  `metrics{total_distance_p90, hi_distance_p90, sprint_distance_p90, n_sprints_p90, psv99,
  top5_psv99, high_accel_p90, cod_count_p90, m_min_tip/otip, explosive_accel_to_sprint,
  top3_time_to_sprint, ...}`. **Cobre bem as 5 grandes ligas e as 1ªs divisões SA; é NULO
  em reservas/2ªs divisões** (Argentina Reservas/B, Colômbia B, Venezuela, Brasil C, etc.).
- **`scanner_refs.json`** — a **lista de referências mundiais validada com o scout**: 9 posições,
  ~5 jogadores cada (48 no total), com `archetype` (rótulo do scout), `key`, `nome`, `n_temporadas`.
- Outros: `scanner.json` (metadados do scanner SA), `similaridade.json`, `fisico_classificacao.json`.

Ligas das 5 grandes nos dados: **Alemanha A, Espanha A, França A, Inglaterra A, Italia A**.
11 posições: Goleiro, Zagueiro-Dir/Esq, Lateral-Dir/Esq, Volante, Medio, Meia,
Extremo-Dir/Esq, Atacante.

---

## 3. Pipeline (tudo em `estudo/scripts/`, Python puro, SEM dependências)

> **Não há numpy/pandas/sklearn no ambiente.** Tudo (z-score, KMeans, PCA, radar SVG,
> cosseno) é implementado à mão. Rodar **da raiz do repo**. Intermediários vão para
> `estudo/build/` (gitignored).

```bash
# Fase 1 — padrão de elite + arquétipos
python3 estudo/scripts/01_build_master.py     # join -> build/master.json (1602 jogadores top-5 >=900')
python3 estudo/scripts/02_analyze.py          # diferenciais, assinaturas, KMeans -> build/results.json
python3 estudo/scripts/03_gen_report.py       # payload -> build/report.json  (o index.html foi gerado a partir daqui)

# Fase 2 — similares jovens SA
python3 estudo/scripts/04_similares_sa.py     # afinidade cosseno -> data/similares_sa.json
python3 estudo/scripts/05_gen_sa_dashboard.py # -> similares_sa.html

# Fase 3 — dossiês dos refs mundiais
python3 estudo/scripts/06_dossies_refs.py     # percentis + reconciliação -> data/dossies_refs.json
python3 estudo/scripts/07_gen_dossies.py      # -> dossies_refs.html  (lê build/shared.css)

# Fase 4 — recomendação Botafogo
python3 estudo/scripts/08_reco_botafogo.py    # score prontidão x revenda -> data/reco_botafogo.json
python3 estudo/scripts/09_gen_botafogo.py     # -> reco_botafogo.html
```

Dependência de ordem: 01 gera `build/master.json` (usado por 02, 06). Os geradores de HTML
(05, 07, 09) leem `estudo/build/shared.css` — extraído de `estudo/index.html` com:
`python3 -c "import re;s=open('estudo/index.html').read();open('estudo/build/shared.css','w').write(re.search(r'<style>(.*?)</style>',s,re.S).group(1))"`.

PDFs foram gerados com o Chromium headless (`/opt/pw-browsers/chromium --headless
--print-to-pdf=...`), injetando um bloco `@media print` antes de `</head>`.

---

## 4. Metodologia (decisões importantes)

- **Arquétipos (Fase 1):** KMeans (k=3–4) sobre features técnicas+físicas padronizadas
  (z-score) DENTRO de cada grupo de posição. Posições espelhadas (Dir/Esq) unidas → **8 grupos**,
  **29 arquétipos**. Silhouettes baixas por natureza (estilos são um contínuo).
- **Moldes (`data/arquetipos_top5.json`):** cada arquétipo = **centroide z-score** no espaço
  de features + referências + alvo de scouting. É o insumo das fases 2 e 4.
- **Similaridade (Fase 2/4):** o jovem SA vira vetor z **relativo à média da sua posição na
  América do Sul**; afinidade = **cosseno** com o centroide do arquétipo. Controla o nível de
  liga por padronização no próprio contexto. **Filtro de estilo, não previsão de rendimento.**
- **Score Botafogo (Fase 4):** `0.5·Prontidão + 0.5·Revenda`.
  Prontidão = 0.45·nível(percentil do `overall`) + 0.25·minutos + 0.30·força_da_liga
  (Brasil A=1.00, Argentina A=0.92, … Bolívia=0.50).
  Revenda = 0.50·afinidade_a_arquétipo_premium + 0.25·juventude + 0.25·velocidade(psv99).
  Exclui `isBotafogo`; candidatos ≤ 23 anos, ≥ 900'.
- **Reconciliação (Fase 3):** o rótulo do scout bate com o cluster nos casos claros (valida a
  Fase 1); divergências são nuance (ex.: Militão é "defensor de espaço veloz", não "balanceado").

---

## 5. Principais achados

1. **Posição explica < metade:** ~47% da variância física é entre posições, **~53% é dentro**
   (o arquétipo importa tanto quanto a posição).
2. **Diferencial das grandes ligas vs. mundo** não é correr mais — é envolvimento com a bola,
   retenção sob pressão e explosividade; na elite (top-10%) o salto vem de progressão/criação.
3. **Recomendação Botafogo (nº1 por posição):** Zaga **A. Cañete** (PAR, 22); Lateral **A. Fretes**
   (PAR, 20) [alt. K. Amaro, URU]; Volante **S. Vasquez** (EQU, 22); Meio **M. Peralta** (URU, 20);
   Meia **N. Wunsch** (URU, 22, fraco); Ponta **A. Gómez** (Vasco/Brasil A, 23, 85% craque);
   Centroavante **J. Torres** (COL, 21, 85% falso-9); **Goleiro sem alvo elegível**.
   Necessidades reais no elenco: LB (Alex Telles 33), zaga (Barboza 31), ponta-D (Edenílson 36).

---

## 6. Limitações conhecidas (e por quê)

- **Ligas sem rastreamento físico ficaram de fora** da Fase 2/4 (reservas, 2ªs divisões) —
  o match usa físico. Grande pool argentino (Reservas/B) não avaliado.
- **Goleiros jovens:** amostra insuficiente com físico → sem recomendação.
- **Meia armador:** escassez real de perfil jovem no pool SA (afinidades baixas).
- **Valor de mercado** frequentemente ausente nas bases SA.
- `overall` é nota relativa do modelo, não medida absoluta; comparabilidade cross-liga imperfeita.

---

## 7. PRÓXIMOS PASSOS em aberto (escolher onde continuar)

1. **Re-ancorar os moldes nos refs do scout** (não só nos centroides dos clusters) — deve
   melhorar diretamente a precisão do ranking de alvos. *(sugerido como maior alavanca)*
2. **Match técnico-apenas** para cobrir as ligas SEM físico (destrava Argentina Reservas/B etc.).
3. **Frentes fracas:** rodada dedicada a **meia** e **goleiro** (outra faixa etária/base).
4. **Fichas individuais** dos finalistas (radar do jovem sobreposto ao molde + ao ref mundial).
5. Cruzar com **contrato/idade/valor** para priorizar custo-benefício de revenda.

---

## 8. Estado de entrega

Branch `claude/top-5-leagues-player-analysis-vqxqrh`, PR #4 (draft, mergeable).
Dashboards no repo (abrir no navegador):
`estudo/index.html` (Fase 1), `estudo/similares_sa.html` (Fase 2),
`estudo/dossies_refs.html` (Fase 3), `estudo/reco_botafogo.html` (Fase 4).
Dados estruturados em `estudo/data/*.json`. Ver `estudo/README.md` para o resumo público.

Para continuar localmente:
```bash
git fetch origin claude/top-5-leagues-player-analysis-vqxqrh
git checkout claude/top-5-leagues-player-analysis-vqxqrh
# reproduzir a pipeline: ver seção 3 acima
```
