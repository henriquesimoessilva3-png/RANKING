# CONTEXTO — Caso Willian Pacho & Lições para o Sistema de Ranking

> Documento de contexto da sessão de análise (jul/2026). Consolida o estudo do caso Pacho,
> as decisões metodológicas tomadas, os resultados finais e as pendências.
> Base de dados: período **jun26** (temporada 2025/26).

---

## 1. O caso

**Pergunta original:** avaliação completa do Willian Pacho (PSG) + busca de zagueiros
brasileiros e sul-americanos similares.

**Pergunta final (após iterações):** *quem pode assumir a FUNÇÃO do Pacho* — defender e
correr como ele — com nível de liga crível e sem punir quem o supera.

### Perfil do Pacho (resumo)
- Zagueiro-esquerda (LCB), canhoto, 24 anos, 1,88 m, PSG, €35M, contrato 2029. 23j/2.094min.
- **Elite:** duelo defensivo (p93), acerto de passe (95,4% — p99,8), disciplina (p98, quase não
  comete faltas), agilidade (mudança de direção p87, PSV-99 p84, acel. explosiva p82).
- **Limitações:** jogo aéreo mediano (52,9% de aproveitamento = p31; 3,0 disputas/90; 0 gols de
  cabeça — mas 0 é normal na posição: média 0,29/temporada), sem passe longo (p3), não conduz
  (p13), distância total ABAIXO da mediana (p41) — intensidade, não quilometragem.

## 2. Evolução metodológica (as 6 versões do estudo)

| v | Régua | Problema encontrado |
|---|---|---|
| v1 | Estilo (27 KPIs não-físicos, método padrão da aba Similaridade) | Físico valia 0%; Ignácio/Jemmes lideravam mas têm motor oposto |
| v2 | Def+Fís bilateral (23 KPIs) | Validação: Marquinhos/Beraldo (PSG) no topo |
| v3 | Estudo em 4 partes + 3 notas (Completa/Def/Fís) | Completa = 45,5% bola → listas divergiam da expectativa |
| v4 | Nota final = Def (49,7%) + Fís (50,3%), bola 0% (decisão do usuário) | Betão (Brasil B) #1 — scouts não validam |
| v5 | — | Diagnóstico: bilateral pune quem SUPERA o Pacho; percentil não mede nível de liga |
| **v6 (FINAL)** | **Unilateral (só déficit penaliza) + tiers de liga + mín. 900 min** | Listas com validade de face ✓ |

### Régua final (v6)
- **23 KPIs**: 7 defesa (49,7% do peso) + 16 físicas SkillCorner (50,3%). Jogo com bola fora.
- **Distância unilateral**: só o que falta vs. Pacho penaliza; igualar/superar = sem desconto
  (mesma filosofia da aba "Similares Físicos" do app). Desempate: quem supera mais.
- **Tiers de liga**: T1 = top-5 Europa · T2 = Brasil A, Argentina A, Portugal A, México, Rússia,
  Turquia, Holanda, Bélgica A, MLS, Arábia A · T3 = a provar (radar).
- Pool: zagueiros sul-americanos (país de nascimento) com dado físico e ≥900 min → 552.
- Ranks sempre pela similaridade NÃO-arredondada (houve bug de empate por arredondamento).

## 3. Resultado final (v6)

**Prontos (T1-T2):**
1. **N. Marichal** (Dinamo Moscou, 25, 1,85m, D) — **97,1** (iguala/supera o Pacho em quase tudo)
2. **João Victor** (CSKA, 27, 1,87m, D) — 93,0 · 3. **Vítor Tormena** (Krasnodar, 30, 1,92m) — 92,1
4. **R. Hillen** (NAC Breda, 23, **canhoto**, 1,87m) — 91,4 · **Marquinhos (PSG) #10 = validação da régua**
- Jovens: David Sousa (Casa Pia, 24, E, 1,92m), M. Moreno (Levante, 22, 1,93m), L. Rivero (River, 22),
  Viery (Grêmio, 21, E — melhor doméstico).

**Radar (T3, monitorar):** Guasone (Cerro-URU, 1,97m, 93,2), Cañete (92,4), **Betão (90,8 —
formato certo, nível não comprovado, 951min)**, Villagra (89,8), Quintana (21).

**Achados estruturais:** correlação def×fís ≈ 0 no pool (defender e correr como o Pacho são
dons independentes); ninguém é clone (bilateral: teto ~82); métricas esparsas geram
percentis-artefato (ex.: 2ª assistência p95,6 com valor ~0).

## 4. Referências mundiais — métricas destaque

Relatório `referencias_metricas.html` (46 refs dos arquétipos do scanner): assinatura técnica +
física por referência. Destaques: Messi/TAA/Yamal são réguas puramente TÉCNICAS (físico p8–52);
Raphinha é o único ponta p100 técnico + p99 físico; GKs sem tracking físico SkillCorner.
Estêvão (Chelsea) e Musiala sem dados no jun26.

## 5. Lições para o produto (ranking :5053 · comparativo :5054)

1. **Presets de similaridade** (Estilo/Defensiva/Física/Função/Completa + modo **unilateral
   "reposição"**) — motor já suporta selCats; mostrar notas lado a lado + rank no pool.
2. **Tier de liga na base** — separar "prontos" de "radar" em qualquer lista de similares.
3. **Blocos como colunas de 1ª classe no ranking** (DEF/PAS/DGP/OFE/FIS + rank por bloco);
   overall composto esconde especialistas (Pacho: overall 54 vs. def 82).
4. **Físico**: badge de cobertura (38% do pool SA sem dado); liderar com intensidade
   (COD, PSV-99, ações AI), não distância total.
5. **Aéreo em dupla** (disputas/90 + % ganho) p/ zagueiros; altura/pé como colunas fixas.
6. **Métricas esparsas**: quando mediana da posição ≈ 0, mostrar valor bruto + badge, suprimir
   percentil de destaques.
7. **Referências internas fixáveis** no comparativo (Marquinhos/Beraldo provaram valor).
8. Ranks por valor bruto; faltas = "disciplina" (↓ melhor); Aerial duels per 90 no vetor.

## 6. Entregáveis

| Arquivo (nesta branch) | Conteúdo |
|---|---|
| `dossie_pacho.html` | Estudo em 4 partes (12 seções), versão final v6 |
| `comparativo_def_fis.html` | Comparativo defensivo-físico (radares/heatmaps) |
| `comparativo_pacho_destros_br.html` | Comparativo de estilo (v1, mantido como histórico) |
| `referencias_metricas.html` | Métricas destaque das 46 referências mundiais |
| `pacho.html` | Índice do caso |

Artifacts (claude.ai): dossiê `05c51e66-…3455b5` · comparativo def+fís `51cc6d91-…43e1` ·
estilo `8849ae28-…9f74d` · referências `f5ebf9f4-…40f2`. PDFs (claro/escuro) gerados via
Chromium headless (scripts recriáveis: print CSS embutido nos HTMLs).

## 7. Estado e pendências

- **PR #2** (branch `claude/willian-pacho-analysis-t0q6gs`): RASCUNHO por decisão do usuário
  ("só local por enquanto") — NÃO mesclar sem autorização. Sem CI no repo.
- Verificação: 3 rodadas de painel adversarial (números recalculados do zero: 100% exatos;
  ~40 findings de texto/design/paginação corrigidos).
- Pendências sugeridas (não iniciadas): implementar presets de similaridade no app estático;
  campo tier de liga na base; comparativos individuais Marichal/João Victor/Hillen vs. Pacho.
