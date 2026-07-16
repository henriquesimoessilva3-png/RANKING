# CONTEXTO DE UNIFICAÇÃO — juntar os materiais num dossiê único

> **Objetivo desta sessão futura (no seu computador, com acesso aos arquivos locais):**
> juntar num **material único e navegável** os 3 entregáveis já prontos + o card de
> arquétipos que roda em **`localhost:5064`**.
>
> Leia também `estudo/CONTEXT.md` (handoff geral). Tudo está na branch
> **`claude/top-5-leagues-player-analysis-vqxqrh`** (PR #4). Este arquivo foca **só na fusão**.

---

## 1. Os materiais a unir

| # | Material | Arquivo (abre no navegador) | Dados que consome | Gerador |
|---|----------|------------------------------|-------------------|---------|
| 1 | **Ligas × Mundo** (padrão de elite + arquétipos das 5 grandes) | `estudo/index.html` | `build/report.json` | `03_gen_report.py` |
| 2 | **Dossiê das 42 referências mundiais** | `estudo/dossies_refs.html` | `data/dossies_refs.json` | `07_gen_dossies.py` |
| 3 | **Alvos de contratação (Botafogo)** | `estudo/reco_botafogo.html` | `data/reco_botafogo.json` | `09_gen_botafogo.py` |
| 4 | **Cards de arquétipos** *(externo, do usuário)* | **`localhost:5064`** — não está neste repo ainda | a definir (ver §5) | app local do usuário |

> Existe ainda um 5º material relacionado — **`estudo/similares_sa.html`** (jovens SA por
> arquétipo, Fase 2). Não foi pedido na fusão, mas encaixa naturalmente como uma aba extra.
> Decidir com o usuário se entra.

---

## 2. O que já facilita a fusão

**Os 3 materiais compartilham o MESMO sistema de design** (`estudo/build/shared.css`), então
unir é sobretudo criar **um shell + uma navegação únicos** em volta dos corpos já prontos.

- **Tokens** (claro/escuro via `:root` + `[data-theme]` + `@media prefers-color-scheme`):
  `--bg, --surface, --surface2, --ink, --ink2, --muted, --line, --accent, --accent2,
  --amber, --teal, --purple, --shadow, --sans, --mono, --maxw`.
- **Componentes reutilizados** (mesmas classes em todos): `.site/.wrap/.hero/.eyebrow/.kpis/.kpi`,
  `.finding/.group/.group-h`, `.pbar` (barra de percentil com marca), `.chip`, `.card`,
  e no material 2 o **radar SVG** (`.radar` + `svg` gerado em `07_gen_dossies.py`).
- Cada material tem **header próprio** (`.site` com `.brand`, `.jump` nav e botão de tema `#theme`)
  e um `<script>` de tema + scroll-spy quase idêntico. **Na fusão, isso vira UM só.**

---

## 3. Arquitetura recomendada para o material único

**Opção A (recomendada) — documento único com abas/seções e um shell só.**
Um arquivo `estudo/dossie_completo.html` (self-contained) com:
- **1 header fixo** com navegação de topo entre as 4–5 seções + **1 botão de tema**.
- Cada material entra como uma `<section>` (reaproveitando o `body` interno de cada HTML,
  removendo o `.site`/nav/script individuais de cada um).
- **1 CSS** = `shared.css` + os blocos `EXTRA` de cada gerador (radar, tabelas, barras de score),
  concatenados e deduplicados.
- **1 script** de tema + scroll-spy no fim.
- Ordem sugerida (funil): **Ligas×Mundo → Arquétipos(5064) → Dossiê 42 refs → Alvos Botafogo**.

**Como gerar de forma limpa (não copiar/colar à mão):** criar
`estudo/scripts/10_gen_unificado.py` que:
1. Lê os payloads (`build/report.json`, `data/dossies_refs.json`, `data/reco_botafogo.json`).
2. Reusa as funções de render de cada gerador (importar de 03/07/09 ou refatorar as funções
   de card/section para um módulo comum `estudo/scripts/_render.py`).
3. Emite as `<section>` de cada material + o shell único + `shared.css`+EXTRA unificado.
4. Injeta a seção de arquétipos (material 4) conforme §5.

> **Refactor sugerido:** extrair as funções de render (`radar`, `strbar`, `pbar`, `card`, …)
> para `estudo/scripts/_render.py` e fazer 03/07/09/10 importarem de lá — evita divergência.

**Opção B — hub com iframes.** Um `index` que embute cada material num `<iframe>`. Mais rápido,
mas perde header/tema unificados e não integra o 5064 se ele for outra origem (CORS). Só usar
se o tempo for curto.

---

## 4. Passo a passo da fusão (para a sessão local)

1. `git checkout claude/top-5-leagues-player-analysis-vqxqrh` e rodar a pipeline (ver
   `CONTEXT.md` §3) para garantir `build/report.json`, `data/dossies_refs.json`,
   `data/reco_botafogo.json` atualizados e `build/shared.css` presente.
2. Refatorar os renders para `_render.py` (ou, no mínimo, importar as funções existentes).
3. Escrever `10_gen_unificado.py` → `estudo/dossie_completo.html` (Opção A).
4. Adicionar a seção **Arquétipos (5064)** — ver §5.
5. Conferir tema claro/escuro, navegação, e quebras de página se for gerar PDF único
   (mesmo truque `@media print` + Chromium headless das outras fases).
6. Commit + push na mesma branch (atualiza o PR #4).

---

## 5. Integrar o material de arquétipos do `localhost:5064` (fazer no computador)

Este material **não está no repositório** — está rodando localmente. Quando abrir a sessão
local (com acesso aos arquivos), **capture primeiro estas informações** e me passe:

- **Como é servido:** que comando sobe o `:5064`? (ex.: `python -m http.server 5064`,
  `npm run dev`, Vite/Next, etc.) e **a partir de qual pasta**.
- **Stack:** é HTML/CSS/JS puro, ou React/Vue/framework? (define se dá para portar o markup
  direto ou se precisa buildar/estático).
- **Arquivo(s)-fonte:** caminho do HTML/JS/componentes que renderizam os cards de arquétipo.
- **Dados:** de onde os cards leem os dados? É algum `arquetipos*.json`? **Se for, comparar com
  o nosso `estudo/data/arquetipos_top5.json`** (mesmos 29 arquétipos? nomes batem? há campos a
  reconciliar?). O ideal é os dois falarem do MESMO conjunto de arquétipos.
- **Visual:** print/prints da tela para eu casar o estilo com o `shared.css` (cores, tipografia).

**Caminhos de integração (escolher conforme o achado):**
- **(a) Portar** o markup/CSS dos cards para uma `<section>` nativa do `dossie_completo.html`,
  re-estilizando com nossos tokens → integração perfeita, tema unificado. *(preferível)*
- **(b) Regerar** os cards a partir do nosso `arquetipos_top5.json` no mesmo estilo das outras
  seções (se o 5064 for só uma view dos mesmos dados) → elimina duplicação.
- **(c) Embutir via iframe** apontando para o build estático do 5064 → rápido, mas tema/origem
  à parte; último recurso.

**Ponto de reconciliação importante:** verificar se os arquétipos do 5064 são os mesmos 29
(8 grupos) do estudo. Se forem listas diferentes, alinhar nomenclatura antes de juntar, senão
o material fica com dois vocabulários de arquétipo.

---

## 6. Resumo de conteúdo de cada material (para escrever transições/índice)

- **Ligas × Mundo:** amostra (1602 jogadores, 5 grandes, ≥900'); decomposição de variância
  (47% entre / 53% dentro); mapa físico das 11 posições (heatmap divergente); diferencial
  top-5 vs mundo; 29 arquétipos em 8 grupos (cards com assinatura + referências + alvo SA).
- **Dossiê 42 refs:** por posição, cada referência mundial com radar de percentis vs mundo,
  no que é elite (barras técnico/físico), e reconciliação **arquétipo do scout ↔ cluster do estudo**.
- **Alvos Botafogo:** por posição, o alvo jovem SA nº1 (score prontidão × revenda), com barras
  de componentes, arquétipo europeu espelhado + jogador-referência, destaques e alternativas;
  leitura da necessidade pela idade do elenco atual (flag `isBotafogo`).

Fio condutor do material único: **"o que a elite é" → "como os arquétipos se definem" →
"quem são as referências mundiais de cada um" → "quem contratar que aponta para esse teto".**

---

## 6b. Nota de ambiente (Windows)

Os scripts escrevem HTML com caracteres especiais (€, ▸, ·, acentos). O `10_gen_unificado.py`
já força `encoding='utf-8'` em todo I/O e roda de qualquer diretório (ancora na raiz via
`__file__`). Os scripts `01`–`09` usam o encoding padrão da plataforma — no **Windows**,
rode com UTF-8 forçado para evitar `UnicodeEncodeError`:

```bat
set PYTHONUTF8=1        &:: (ou: python -X utf8 estudo/scripts/XX.py)
```

---

## 7. Checklist rápido ao abrir a sessão local

- [ ] Branch `claude/top-5-leagues-player-analysis-vqxqrh` em dia (fetch/checkout).
- [ ] Pipeline rodada; `build/shared.css` e os 3 JSONs presentes.
- [ ] Info do `:5064` capturada (§5): comando, stack, arquivos, dados, prints.
- [ ] Decidir Opção A (portar/reGerar) vs C (iframe) para os arquétipos.
- [ ] Decidir se a Fase 2 (`similares_sa`) entra como aba.
- [ ] Gerar `estudo/dossie_completo.html` + (opcional) PDF único; commit/push.
