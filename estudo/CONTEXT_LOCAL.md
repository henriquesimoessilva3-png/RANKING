# CONTEXTO PARA A SESSÃO LOCAL (rodar no computador)

> **Para o Claude que abrir DIRETO no computador do usuário** (com acesso aos arquivos e
> capacidade de rodar servidor local). Leia este arquivo primeiro; depois `estudo/CONTEXT.md`
> (handoff geral) e `estudo/CONTEXT_UNIFICACAO.md` (plano de fusão).
>
> Ambiente do usuário: **macOS** (usa `⌘`, `lsof`). Repositório: pasta **RANKING**.
> Branch de trabalho: **`claude/top-5-leagues-player-analysis-vqxqrh`** (PR #4, draft).
> Última entrega da sessão em nuvem: commit **`e3cf7de`**.

---

## 0. Por que a sessão é local
A sessão anterior rodou **na nuvem** e só conseguia commitar no repositório — não conseguia
iniciar/ver o servidor `localhost:5064` do usuário nem ler o app de arquétipos que roda nele.
Você, rodando **local**, pode: inspecionar o que serve o `:5064`, servir a pasta do repo,
e **fazer a fusão** do material de arquétipos (`:5064`) no dossiê único. Esse é o objetivo.

---

## 1. PRIMEIRO — destravar o `localhost:5064` (está servindo cópia velha)

Sintoma: no `:5064`, a aba **Alvos de Contratação** aparece na versão ANTIGA (card único
"A. Cañete + Alternativas", texto "a Europa compra esse perfil depois?", "Sem candidato
jovem elegível"). O repositório já tem a versão NOVA (top-10 por mercado, com pills). Ou seja,
o servidor entrega um arquivo desatualizado/cacheado, não o do repo.

Diagnóstico (rodar na pasta RANKING):
```bash
git status                                  # deve estar na branch claude/top-5-leagues-player-analysis-vqxqrh
git pull origin claude/top-5-leagues-player-analysis-vqxqrh
grep -c "top-10 por posição, em cada mercado" estudo/dossie_completo.html   # 1 = arquivo novo OK
lsof -i :5064                               # qual processo/porta serve o 5064 (veja o COMMAND/PID e a pasta)
```

Correção à prova de erro (serve a pasta do repo direto, sem cache):
```bash
lsof -ti :5064 | xargs kill                 # derruba o servidor atual
python3 -m http.server 5064 --directory estudo
# abrir http://localhost:5064/dossie_completo.html  (⌘+Shift+R)
```
Se o `:5064` for outro app (ex.: o app de arquétipos) e o usuário quiser mantê-lo, então a
cópia servida está noutra pasta — encontre e sobrescreva:
```bash
find ~ -name "dossie_completo.html" 2>/dev/null          # onde há cópias
cp estudo/dossie_completo.html <pasta_servida_pelo_5064>/
```
**Verificação de versão de qualquer arquivo:** `grep -c "top-10 por posição, em cada mercado" ARQ`
→ `1` novo, `0` velho.

---

## 2. Estado atual do trabalho (o que já existe)

Quatro materiais + um dossiê único, todos self-contained (abrem no navegador), tema claro/escuro:

| Material | Arquivo | Gerador |
|---|---|---|
| 1. Ligas × Mundo (padrão de elite + arquétipos) | `estudo/index.html` | `03_gen_report.py` |
| 2. Arquétipos (29 moldes) | seção do dossiê único / `data/arquetipos_top5.json` | `10_gen_unificado.py` |
| 3. Dossiê 42 referências mundiais (radar + reconciliação scout×cluster) | `estudo/dossies_refs.html` | `06`+`07` |
| 4. Alvos de Contratação — **top-10 por posição × mercado** | `estudo/reco_botafogo.html` | `08`+`09` |
| ★ Dossiê único (4 abas) | **`estudo/dossie_completo.html`** | `10_gen_unificado.py` |
| (extra) Similares SA jovens por arquétipo (Fase 2) | `estudo/similares_sa.html` | `04`+`05` |

Alvos (Fase 4) agora: universo mundial (≥900′, exclui Botafogo), 5 mercados por país de
nascimento — **Sub-23 BR+SA, Brasileiros, Sul-americanos, ESP·POR·ANG·A.Central(+México),
Mundo** — top-10 por posição em cada; afinidade técnica+física (ou técnica-apenas, selo `téc`,
quando falta rastreamento); revenda decai com a idade; padronização por mercado×posição.

---

## 3. Rodar / regenerar / servir localmente

Python puro, **sem dependências**, a partir da raiz do repo. (macOS já tem UTF-8; se algum dia
for Windows, `set PYTHONUTF8=1`.)
```bash
# Regenerar tudo, em ordem:
python3 estudo/scripts/01_build_master.py      # -> build/master.json
python3 estudo/scripts/02_analyze.py           # -> build/results.json
python3 estudo/scripts/03_gen_report.py        # -> build/report.json  (index.html é a saída da Fase 1)
python3 estudo/scripts/04_similares_sa.py       # -> data/similares_sa.json
python3 estudo/scripts/05_gen_sa_dashboard.py   # -> similares_sa.html
python3 estudo/scripts/06_dossies_refs.py       # -> data/dossies_refs.json
python3 estudo/scripts/07_gen_dossies.py        # -> dossies_refs.html
python3 estudo/scripts/08_reco_botafogo.py      # -> data/reco_botafogo.json
python3 estudo/scripts/09_gen_botafogo.py       # -> reco_botafogo.html
python3 estudo/scripts/10_gen_unificado.py      # -> dossie_completo.html (junta tudo)

# Servir (qualquer um):
python3 -m http.server 5064 --directory estudo  # abrir /dossie_completo.html
```
`build/shared.css` é extraído de `index.html` (os geradores 05/07/09/10 leem esse arquivo). Se
faltar: `python3 -c "import re;open('estudo/build/shared.css','w').write(re.search(r'<style>(.*?)</style>',open('estudo/index.html').read(),re.S).group(1))"` (ou rode `10` que já cuida). `estudo/build/` é gitignored.

---

## 4. TAREFA PRINCIPAL DA SESSÃO LOCAL — fundir o app de arquétipos (`:5064`) no dossiê único

Plano completo em `estudo/CONTEXT_UNIFICACAO.md §5`. Resumo do que fazer local:
1. **Descobrir o app do `:5064`**: qual comando o sobe e de qual pasta (`lsof -i :5064`, ler
   `package.json`/scripts). Ver stack (HTML puro? React/Vite?) e os arquivos-fonte dos cards.
2. **Ver os dados dele**: de onde os cards de arquétipo leem. Comparar com o nosso
   `estudo/data/arquetipos_top5.json` — são os mesmos 29 arquétipos (8 grupos)? Nomenclatura bate?
3. **Integrar** (preferência): portar o markup/estilo dos cards do `:5064` para a aba
   **Arquétipos** do `dossie_completo.html` (hoje um placeholder renderizado do nosso JSON),
   re-estilizando com os tokens do `shared.css`; OU regenerar os cards a partir do nosso JSON no
   mesmo estilo do `:5064`. Iframe só como último recurso. Editar `10_gen_unificado.py` (a aba
   Arquétipos é montada na função `arq_cards`/`main2_arq`) e regenerar.
4. Perguntar ao usuário se a **Fase 2** (`similares_sa`) deve entrar como 5ª aba.
5. (Opcional) Gerar **PDF do dossiê completo** empilhando as 4 abas (usar o truque `@media print`
   + Chromium headless, como as outras fases).
6. Commit + push na mesma branch (atualiza o PR #4).

---

## 5. Regras de trabalho no repo
- **Branch:** sempre `claude/top-5-leagues-player-analysis-vqxqrh`. Commitar e dar push ao concluir.
- **Arquivos grandes de dados históricos** (`data/2024|2025/kpis_detail.json`) estão no
  `.gitignore`; `data/jun26/` (o que a pipeline usa) está versionado.
- Dados de entrada em `data/jun26/`: `rankings.json` (identidade, posição, `overall`, flag
  `isBotafogo`, `Birth country`), `kpis_detail.json` (114 KPIs), `skillcorner.json` (físico),
  `scanner_refs.json` (as 48 referências do scout).

---

## 6. Ponteiros
- `estudo/CONTEXT.md` — handoff geral (objetivo de negócio, dados, metodologia, achados, limites).
- `estudo/CONTEXT_UNIFICACAO.md` — plano detalhado da fusão + como capturar/integrar o `:5064`.
- `estudo/README.md` — resumo público e reprodutibilidade.

Primeira frase sugerida para abrir a sessão local:
> "Leia estudo/CONTEXT_LOCAL.md e continue: primeiro conserta o localhost:5064 e depois vamos
> fundir o app de arquétipos no dossiê único."
