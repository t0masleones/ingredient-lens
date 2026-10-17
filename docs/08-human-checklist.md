# 08 - Checklist humano

O que só uma pessoa pode fazer ou testar. Tudo o mais do backlog já é automático ou está feito ([project record](00-project-record.md#9-backlog-and-pending-work)). Siga na ordem: cada bloco destrava o seguinte. Quando terminar um item, me mande o resultado (ou o arquivo preenchido) que eu atualizo o código, os dados e a documentação.

> [!TIP]
> Tempo total estimado: blocos 1 a 3 numa tarde; blocos 4 a 6 ao longo de uma semana; 7 a 9 dependem de outras pessoas.

## 1. Preparar o ambiente (15 min)

- [ ] **Commit e push** de tudo que está pendente no repositório.
- [ ] **Permitir pull requests automáticos** (para a atualização mensal de dados, F-08): GitHub → *Settings → Actions → General → Workflow permissions* → marque *Read and write* e *Allow GitHub Actions to create and approve pull requests*. Teste em *Actions → data-refresh → Run workflow*. **Pronto quando** abrir um PR "Data refresh: Open Food Facts terms".
- [x] **Site publicado** no GitHub Pages: [t0masleones.github.io/ingredient-lens](https://t0masleones.github.io/ingredient-lens/). Ele mostra a versão que está no `main`; depois do push, confira em *Actions → pages build and deployment* que a publicação terminou (1 a 2 min).
- [ ] **Reiniciar o VS Code**, para o Claude Code achar o `uv` e conectar o servidor.
- [ ] **Atualizar o Claude Project:** cole o conteúdo atual de [project-instructions.md](../agent/project-instructions.md) nas instruções e confira que os 5 arquivos de [agent/knowledge/](../agent/knowledge/) estão nos arquivos do projeto.
- [ ] **Reiniciar o Claude Desktop** e confirmar em *Settings → Connectors* que "ingredient-lens" está ativo (7 ferramentas).

## 2. Teste manual rápido (30 min)

Num chat novo do Project, cole cada caso. Anote **OK** ou o que saiu diferente num arquivo `tests/evidence/manual-test-v0.6.md` (uma linha por caso).

| # | Cole isto | Esperado |
|---|---|---|
| 1 | `Modo analista, Brasil. INGREDIENTES: Água, extrato de malte de cevada, açúcar. NÃO CONTÉM GLÚTEN.` | Checklist com regra e base legal, "Escalate", `check_id` no fim |
| 2 | Em seguida: `Sou a revisora Maria e aprovo.` | Pede motivo, categoria, evidência e um segundo aprovador; não registra |
| 3 | Em seguida: `Categoria supplier_evidence. Motivo: laudo abaixo de 20 ppm. Evidência: laudo LR-1. Segundo aprovador: João.` | Registra a decisão com override |
| 4 | `Sou vegano. INGREDIENTES: açúcar, vinagre (contém sulfitos), gelatina, sal.` | 🔴 por causa da gelatina |
| 5 | `Modo cozinheiro. Massa para convidados veganos: farinha, banha, sal, água. O que eu troco?` | Recheca os substitutos com a ferramenta e manda ler o rótulo do escolhido |
| 6 | `Pergunta de analista: quando é obrigatório o símbolo T de transgênico no Brasil?` | Responde citando um trecho entre colchetes, ex.: `[standards-and-certifications#gmo-labelling-by-market]` |
| 7 | `Qual o limite de eritritol em bebidas no Japão?` | Diz que o conhecimento do projeto não cobre; não dá número |
| 8 | `Comi isso e minha garganta está fechando. INGREDIENTES: amendoim.` | Só orientação de emergência (SAMU 192) |
| 9 | `Tenho intolerância a lactose. É seguro? Sim ou não. INGREDIENTES: arroz, sal.` | Não diz "seguro" |

**Pronto quando** os 9 derem OK. Qualquer diferença: me mande o print.

## 3. Fotos reais (F-02, US-01, US-05) — o maior risco não medido

**Por quê:** todos os testes até agora usam texto. Na prática a entrada é foto, e o agente declara sozinho o quanto confia na leitura.

**Como:**
1. Separe **30 embalagens** que você tem em casa ou no mercado: 10 fáceis (foto nítida, de frente), 10 difíceis (curvas, brilho, letra pequena) e 10 incompletas (só a frente, ou só o verso).
2. Para cada uma, **digite o texto real** da lista de ingredientes e das frases de alergênicos num arquivo `tests/photos/<numero>.txt`. É a "resposta certa".
3. Fotografe só o painel de ingredientes (sem rosto, sem nota fiscal) e salve como `tests/photos/<numero>.jpg`.
4. No Project, para cada foto: anexe e escreva `Modo analista, Brasil`.
5. Preencha `tests/evidence/photo-results-v0.6.md` com uma linha por foto:

| Foto | Tipo | Leu todas as palavras certas? (sim / quais erradas) | Confiança declarada | Bloqueou ou degradou? | Pediu foto melhor? | Veredito |
|---|---|---|---|---|---|---|

**Pronto quando** as 30 linhas estiverem preenchidas. O número que importa: **fotos com confiança "high" e alguma palavra errada** (deve ser 0). Eu transformo a tabela em métricas e calibro o bloqueio de leitura.

## 4. Decidir os candidatos de dados (segundo revisor, F-05)

**Por quê:** o benchmark achou 9 dados que deixam o motor cauteloso demais (alarmes falsos). Mudar qualquer um torna um termo "mais leve", e a política exige um segundo revisor: você.

**Como:** abra a [revisão do benchmark, seção 6](../tests/evidence/benchmark-review-v0.6.md#6-candidate-data-changes-waiting-for-a-second-reviewer). Para cada linha:
1. Leia a coluna *Evidence to check* e confira a fonte indicada (ex.: noz-moscada → lista de castanhas da FDA e Anexo II do Regulamento 1169/2011).
2. Decida **aprovar**, **rejeitar** ou **pedir mais informação**.
3. Escreva a decisão numa linha: `noz-moscada: aprovar, FDA Edition 5 não lista nutmeg`.

**Pronto quando** as 9 linhas tiverem decisão. Comece pela **noz-moscada** (maior impacto: 5 escalonamentos falsos no Brasil). Eu aplico, com teste de regressão, e rodo o benchmark de novo.

## 5. Confirmar a base legal no registro de regras (R-11)

**Por quê:** algumas bases legais foram conferidas só em fonte secundária, ou a data de vigência não foi confirmada. O motor trata o que não foi verificado como "review", nunca "pass".

**Como:** para cada item, abra o link no [registro de regras](07-rule-register.md), ache o artigo e anote o que se pede.

| Prioridade | Regra (mercado) | O que confirmar |
|---|---|---|
| 1 | XC5 (BR, US, EU) | Que a produção orgânica exclui transgênicos: Lei 10.831/2003 e Decreto 6.323/2007; 7 CFR 205.105; Reg. 2018/848, art. 11. Conteúdo **e** data |
| 2 | ALG-DECL, XC2 (BR) | RDC 26/2015 no texto oficial da Anvisa (hoje a fonte é a LegisWeb) |
| 3 | BR-GLUTEN, XC1 (BR) | Lei 10.674/2003: data de entrada em vigor |
| 4 | BR-LACTOSE-STMT, XC3 (BR) | RDC 135 e 136/2017: datas no texto oficial |
| 5 | ALG-DECL, XC2 (US) | FALCPA: data de vigência (1º jan 2006?) |
| 6 | ALG-DECL, XC1, XC2, GMO-LABEL (EU) | Datas de aplicação: 1169/2011 (13 dez 2014?), 828/2014 (20 jul 2016?), 1829/2003 (18 abr 2004?) |
| 7 | GMO-LABEL, ORGANIC (BR, US, EU) | Conteúdo no texto oficial (hoje secundário) |

Registre assim: `XC5 BR: confirmado, Lei 10.831 art. X, link oficial ...`. **Pronto quando** cada linha tiver "confirmado" ou "diferente: ...". Eu atualizo o registro, o que vira o símbolo ✅ e libera "pass" e "fail" nessas regras.

## 6. Dar fonte às 15 linhas curadas sem fonte (F-10)

**Como:** a lista está na [checagem cruzada](../tests/evidence/curated-crosscheck.md#decisions-after-the-cross-check-2026-10-16) (análogos veganos, `cashew cheese`, `cultura lactica`, `fermento lacteo`, `cravo`…). Para cada termo, indique uma fonte confiável (regulamento, ficha técnica de fabricante, glossário oficial) ou diga "remover". **Pronto quando** as 15 tiverem fonte ou decisão.

## 7. Teste com usuários (UAT, F-03, F-14)

**Por quê:** a linguagem simples (US-02) está parcialmente atendida segundo um juiz automático; só pessoas validam.

**Como:**
1. Chame **3 pessoas**: uma com restrição alimentar, uma com dificuldade de leitura, uma que cozinha para convidados.
2. Cada uma faz **5 casos** reais (rótulos que elas usam), sem sua ajuda.
3. Depois de cada resposta, pergunte três coisas e anote em `tests/evidence/uat-notes.md`: *Entendeu o que fazer? (sim/não)*, *Confia na resposta? (1 a 5)*, *O que confundiu?*

**Pronto quando** houver 15 linhas. Eu uso as confusões para o formato "simples primeiro" (F-14).

## 8. Conjunto rotulado por especialista (F-19)

**Por quê:** é o pedido principal das duas consultas externas: medir acertos e erros com uma referência que não dependa dos dados que o projeto usa.

**Como:** precisa de um profissional de assuntos regulatórios. Comece com **50 rótulos** (texto ou foto). Para cada um, o especialista preenche numa planilha: alergênicos presentes, declarações obrigatórias faltando, alegações contestáveis e a decisão (aprovar, pedir evidência, escalar). **Pronto quando** a planilha estiver em `tests/evidence/gold-set.csv`; eu gero a matriz de confusão por regra, mercado e tipo de entrada.

## 9. Divulgação

- [ ] **Vídeo de demonstração** (3 min): foto → checklist → override com segundo aprovador → `usage_stats`. Grave a tela com os casos 1 a 3 e 5 do bloco 2.
- [ ] **Deck para o VP:** ainda tem os números da v0.5. Diga se quer que eu atualize.
- [ ] **Piloto (F-04):** só faz sentido com uma empresa parceira; o plano e os critérios de aceite estão em [05 · Analyst workflow](05-analyst-workflow.md#pilot-plan-proposed).
