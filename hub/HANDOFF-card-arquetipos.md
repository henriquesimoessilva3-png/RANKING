# Briefing — adicionar o card "Arquétipos" ao Hub Botafogo (:5555)

> Cole este documento inteiro na sessão do Claude Code aberta **localmente** na pasta do hub.
> Ele tem todo o contexto pra executar sem precisar perguntar nada.

## Objetivo
Adicionar um card **ARQUÉTIPOS** na home do Hub Botafogo (localhost:5555), no mesmo
padrão dos cards existentes, apontando para a ferramenta de arquétipos que o app
RANKING já serve localmente. **Tudo local — não publicar nada na web / não fazer deploy.**

## Onde é o hub (fatos já confirmados)
- Servidor: `hub_botafogo.py` (Flask).
- Pasta: `/Users/henriquesimoessilva/Meu Drive/arquivos pessoais/fut/BOTA/Analytics/Portal Analise Individual - pos jogo/`
- A **home `/` é HTML inline** dentro do próprio `.py`, na variável `HTML = r"""..."""`
  (por volta da **linha 186**), servida por `@app.route("/")` (linha ~1134) via
  `render_template_string(HTML)`.
- **Os cards estão dentro dessa variável `HTML`.** É lá que o novo card deve entrar —
  não existe `index.html` separado para a home.
- Cards existentes apontam para apps locais em portas próprias (ex.: RANKING `:5053`,
  BOLAS PARADAS `:5057`, etc.), cada um com badge **ONLINE**.

## A ferramenta que o card vai abrir
- A "Arquétipos × Regiões" faz parte do repo **RANKING** (o mesmo que roda em `:5053`).
- Caminho dentro do RANKING: `arquetipos/index.html` (+ `data/`, `standalone.html`,
  `print.html`, `Arquetipos_Regioes_jun26.pdf`).
- Servida localmente em: **http://localhost:5053/arquetipos/index.html**
- Dossiê PDF: **http://localhost:5053/arquetipos/Arquetipos_Regioes_jun26.pdf**
- O que é: para cada **referência de arquétipo** do scanner (base **jun26 · 2025/26**),
  os **10 jogadores mais similares** em 5 buckets independentes — Brasileiros ·
  Sul-americanos · Jovens (≤23) · Am. Central/Caribe·Espanha·Portugal·Angola · Resto do
  mundo. Similaridade **Técnica + Física (SkillCorner) + Combinada** (seleção dos 10 pela
  combinada 60/40), com comparativo à referência em **dados puros e percentil**.
  São **47 arquétipos** (inclui o novo "Veloz agressivo" — W. Pacho).

## Passo 1 — garantir que o `/arquetipos` existe no RANKING local (:5053)
O trabalho novo está na branch do GitHub, ainda **não mergeada** em `main`:
- Repo: `henriquesimoessilva3-png/RANKING`
- Branch: `claude/player-archetypes-regional-0gj7sb` (PR #3, draft)

No repositório RANKING **local** (a pasta que o `:5053` serve), traga a branch:
```bash
git fetch origin claude/player-archetypes-regional-0gj7sb
git checkout claude/player-archetypes-regional-0gj7sb   # ou faça merge na branch que o :5053 já serve
```
Depois confirme no navegador que **http://localhost:5053/arquetipos/index.html** abre.
(Se o `:5053` servir só a `main` e você não quiser trocar de branch, uma alternativa é
copiar a pasta `arquetipos/` para dentro do que o `:5053` serve. Não faça deploy/push
para publicar — é só local.)

## Passo 2 — inserir o card no `hub_botafogo.py`
1. Abra `hub_botafogo.py` e localize a variável `HTML = r"""..."""` (~linha 186).
2. Ache o **grid de cards** e o markup de **um card existente** (ex.: o do RANKING `:5053`).
3. **Copie o padrão desse card** (as classes/estrutura são as do hub) e crie o card
   ARQUÉTIPOS igualzinho, mudando só conteúdo/links:
   - Ícone: `🧬`
   - Título: **ARQUÉTIPOS**
   - Descrição: `Referências × regiões — 10 mais similares por bucket (seleção combinada téc+físico), com dados puros e percentil vs. a referência`
   - Sub: `Brasil · Sul-América · Jovens (≤23) · Am.Central/Esp/Por/Angola · Resto · 47 arquétipos`
   - Porta/label: `:5053  /arquetipos`  · badge **ONLINE**
   - Link principal do card: `http://localhost:5053/arquetipos/index.html`
   - Botão de ação (se os outros cards tiverem barra de ações): `📄 DOSSIÊ PDF` →
     `http://localhost:5053/arquetipos/Arquetipos_Regioes_jun26.pdf`
4. Insira o card **perto do card RANKING** (são da mesma família).
5. Reinicie o `hub_botafogo.py` e confira em **http://localhost:5555/** que o card
   apareceu, com o mesmo visual dos outros, e que clicar abre a ferramenta.

### Card de referência (fallback, caso queira algo pronto)
Se preferir um card self-contido (traz o próprio CSS, então funciona mesmo sem as
classes do hub) — mas **dê preferência a espelhar o padrão dos cards existentes**:
```html
<div style="display:flex;flex-direction:column;background:#fff;border:1px solid #e2e2e2;border-radius:4px;overflow:hidden;font-family:'Space Mono','Courier New',monospace;box-shadow:0 1px 2px rgba(0,0,0,.04)">
  <a href="http://localhost:5053/arquetipos/index.html" style="display:block;padding:22px 22px 14px;text-decoration:none;color:#222">
    <div style="font-size:30px">🧬</div>
    <div style="color:#c19016;font-weight:700;font-size:17px;letter-spacing:.5px;text-transform:uppercase;margin:16px 0 12px;padding-bottom:12px;border-bottom:1px solid #ececec">Arquétipos</div>
    <div style="font-size:13px;line-height:1.5;color:#2b2b2b">Referências × regiões — 10 mais similares por bucket (seleção combinada téc+físico), com dados puros e percentil</div>
    <div style="font-size:12px;line-height:1.5;color:#8a8a8a;margin-top:12px">Brasil · Sul-América · Jovens (≤23) · Am.Central/Esp/Por/Angola · Resto · 47 arquétipos</div>
    <div style="display:flex;justify-content:space-between;margin-top:16px;font-size:12.5px;color:#8a8a8a"><span>:5053 /arquetipos</span><span><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#22c55e;margin-right:7px"></span>ONLINE</span></div>
  </a>
  <div style="display:flex;border-top:1px solid #ececec">
    <a href="http://localhost:5053/arquetipos/Arquetipos_Regioes_jun26.pdf" style="flex:1;text-align:center;padding:12px 8px;font-size:11.5px;font-weight:700;color:#c19016;text-decoration:none">📄 DOSSIÊ PDF</a>
  </div>
</div>
```
> Há também `hub/card-arquetipos.html` no repo RANKING com esse card e o CSS `.hubcard`
> separado, se quiser reaproveitar.

## Restrições
- **Local apenas.** Não fazer deploy, não publicar em GitHub Pages, não `git push` do hub.
- Preservar o estilo/estrutura dos cards existentes do hub (usar as classes do próprio hub).
- Não mexer em nada além do necessário para adicionar o card (e, no Passo 1, disponibilizar
  o `/arquetipos` local).

## Critérios de aceite
- [ ] `http://localhost:5053/arquetipos/index.html` abre localmente.
- [ ] Card **ARQUÉTIPOS** aparece no grid de `http://localhost:5555/`, visual igual aos demais.
- [ ] Clicar no card abre a ferramenta; badge ONLINE; botão do PDF funciona.
- [ ] Nada foi publicado na web (sem deploy/push do hub).
