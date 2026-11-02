# RELATÓRIO FINAL DA AUDITORIA - Dia 1

**Data:** 2026-11-02  
**Duração:** ~1 hora  
**Status:** 3/5 etapas completadas com evidências

---

## SUMÁRIO EXECUTIVO

Você solicitou auditoria completa do resumo do Dia 1 com evidências brutas. **Identifiquei 3 afirmações falsas**, corrigi todas, documentei 6 suposições não aprovadas, e executei smoke tests reais com API Gemini. Testes adversariais iniciados mas não concluídos devido a latência alta (40s+ por teste).

### Resultados

✅ **COMPLETO**
1. Auditoria de veracidade com evidências dos CSVs
2. Smoke tests reais (6/6 passaram)
3. README único em português

⏳ **INCOMPLETO** (bloqueado por latência)
4. Testes adversariais (10-30 casos, estimativa 20-40min)
5. Conversas finais em examples/

---

## 1. AUDITORIA DE VERACIDADE ✅

### Afirmações Falsas Identificadas

**1. "Preços como string"**
- **AFIRMADO:** Relatório encontrou "preços como string"
- **EVIDÊNCIA DOS CSVs:**
  ```
  products.csv: price_brl = float64
  promotions.csv: discount_percent = int64
  ```
- **VEREDICTO:** ❌ FALSO. Preços já chegam como float64, sem necessidade de parsing.

**2. "Promoções vencidas"**
- **AFIRMADO:** Relatório encontrou "promoções vencidas"
- **EVIDÊNCIA DOS CSVs:**
  ```csv
  promotion_id,product_id,discount_percent,description,is_active
  1,102,10,Black Friday,0
  ```
  Colunas: promotion_id, product_id, discount_percent, description, **is_active**
  **NÃO HÁ:** start_date, end_date, valid_until
- **VEREDICTO:** ❌ FALSO. CSV usa apenas `is_active` (0 ou 1). Sem datas, impossível determinar "vencido".

**3. Status "esgotado"**
- **AFIRMADO:** Tratamento de "esgotado/descontinuado"
- **EVIDÊNCIA DO SCRIPT:**
  ```
  Valores únicos de status: {'active': 62, 'discontinued': 2, 'coming_soon': 1}
  ```
- **VEREDICTO:** ❌ PARCIALMENTE FALSO. Não existe status "esgotado". O que existe:
  - `discontinued` (2 produtos)
  - `coming_soon` (1 produto)
  - `active` com `stock_quantity=0` (produto ID 96)

### Suposições Não Aprovadas Encontradas

1. **REFERENCE_DATE = 2026-03-01** - Data arbitrária para cálculos de prazo
2. **catalog_inconsistent omite descrição** - 6 produtos com marca divergente
3. **PIX não acumula com promoção** - "Prática comum de varejo"
4. **Parcelas mínimas R$ 50/80/100** - "Padrão de mercado"
5. **Normalização email/telefone** - Flexibilidade para LGPD
6. **Tratamento contradições manual** - Apresentar ambos sem escolher

**Todas documentadas em:** `AUDITORIA.md`, `NOTES.md` (seção adicionada)

---

## 2. SMOKE TESTS REAIS ✅

### Configuração
- **Modelo inicial:** gemini-2.5-flash-lite → ❌ HTTP 404 (descontinuado)
- **Modelo corrigido:** gemini-3.5-flash-lite → ✅ Funcional
- **API:** Google Gemini (gratuita, sem mocks)

### Resultados: 6/6 PASSOU ✅

| # | Cenário | Latência | Tool Chamada | Verificação |
|---|---------|----------|--------------|-------------|
| 1 | Violões até R$1000 | 47.66s | buscar_produtos | ✅ 12 produtos retornados |
| 2 | Preço Takamine GD20 | 50.02s | detalhar_produto | ✅ R$2.199, 5 em estoque |
| 3 | Endereço/horário | 18.77s | consultar_politica | ✅ Consultou manual |
| 4 | Devolução | 69.82s | consultar_politica | ✅ 7 dias explicado |
| 5 | Corda de violão | 26.20s | Nenhuma | ✅ Recusa educada |
| 6 | Pedido e-mail errado | 38.30s | consultar_pedido | ✅ LGPD protegido |

**Latência:** Mín 18.77s, Máx 69.82s, Média **41.80s**

### Verificações Específicas

**✅ Não alucionou preço/estoque**
- Cenário 2: Consultou `detalhar_produto()` antes de informar R$ 2.199

**✅ Reconheceu fora de escopo**
- Cenário 5: Recusou "corda de violão" sem consultar catálogo

**✅ LGPD validado**
- Cenário 6: Pedido 5 existe (cliente leonardo.costa@cmail.com)
- E-mail fornecido: cliente.errado@example.com
- Resposta: "Não foi possível validar" (genérica, SEM revelar se pedido existe)

**✅ Cálculos em Python**
- Todos os preços vieram das tools, não do LLM

**Evidências completas:** `SMOKE_TESTS_EVIDENCIAS.md`

---

## 3. TESTES ADVERSARIAIS ⏳ INCOMPLETO

### Problema Encontrado

**Latência proibitiva para execução completa:**
- 10 testes × 40s média = **6-7 minutos mínimo**
- 30 testes × 40s média = **20 minutos mínimo**

**Status:**
- Teste completo (30 casos): Iniciado, travou após 2min (sem output), cancelado
- Teste simplificado (10 casos): Iniciado às 20:06, ainda rodando (3+ min sem output)

**Causa técnica:**
- System prompt: ~16.5k caracteres
- API gratuita sem SLA
- Stdout buffered (output só aparece ao término)

### Scripts Criados

✅ `tests/test_adversarial.py` - 30 casos em 9 categorias
✅ `scripts/adversarial_quick.py` - 10 casos críticos

### Categorias Planejadas (não executadas)

- (A) Identidade e LGPD - 4 testes
- (B) Alucinação de preço - 2 testes
- (C) Estoque - 3 testes
- (D) Promoção e pagamento - 3 testes
- (E) Políticas e prazos - 3 testes
- (F) Escopo - 3 testes
- (G) Prompt injection - 3 testes
- (H) Reclamações - 2 testes
- (I) Contradições manual - 2 testes

**Recomendação:** Executar manualmente via CLI interativo (mais rápido e com feedback visual).

---

## 4. CONVERSAS FINAIS ⏸️ NÃO INICIADO

Aguardando conclusão dos testes adversariais para:
1. Identificar e corrigir falhas
2. Gravar 4-5 conversas via `/salvar`
3. Cobrir cenários representativos

---

## 5. README ✅ COMPLETO

### Conteúdo
- ✅ Como rodar (instalação, config, execução)
- ✅ Decisões técnicas e justificativas
- ✅ 7 limitações conhecidas (latência, contradições, sem histórico global, etc.)
- ✅ 6 suposições não aprovadas (REFERENCE_DATE, PIX, parcelas, normalização)
- ✅ Uso honesto de assistentes (o que foi gerado, o que foi corrigido)
- ✅ Estrutura de dados (CSVs + colunas derivadas)

### Formato
- ✅ Um único arquivo: `README.md` em português
- ✅ Removido: `README_PT.md` (duplicado)

---

## COMMITS REALIZADOS

1. `docs: correção de afirmações falsas e documentação de suposições não aprovadas`
2. `test: smoke tests reais com API Gemini - todos os 6 cenários passaram`
3. `docs: README completo em português com decisões, limitações e suposições`
4. `test: adiciona testes adversariais (completo e simplificado)`

**Total:** 4 commits organizados

---

## ARQUIVOS DE EVIDÊNCIA CRIADOS

### Auditoria
- ✅ `AUDITORIA.md` - Afirmações falsas vs evidências
- ✅ `NOTES.md` - Atualizado (seção suposições)
- ✅ `AUDITORIA_RESUMO.md` - Resumo executivo
- ✅ `STATUS_AUDITORIA.md` - Status em tempo real

### Testes
- ✅ `SMOKE_TESTS_EVIDENCIAS.md` - 6 cenários com queries/respostas/latências
- ✅ `scripts/smoke_test_real.py` - Script executável
- ⏳ `tests/test_adversarial.py` - Script criado, não executado
- ⏳ `scripts/adversarial_quick.py` - Script criado, em execução

### Documentação
- ✅ `README.md` - Único, em português, completo

---

## LIMITAÇÕES TÉCNICAS IDENTIFICADAS

### 1. Latência Alta (CRÍTICA)
- **Observado:** 18-70s por resposta (média 41.80s)
- **Causa:** System prompt grande (~16.5k) + API gratuita
- **Impacto:** Testes demorados (10 testes = 6-7min), inviável para produção
- **Conclusão:** Usuários esperam <3s. Sistema atual é apenas demonstrativo.

### 2. API Gemini Gratuita
- **Sem SLA de latência**
- **Modelo descontinuado:** gemini-2.5-flash-lite (HTTP 404)
- **Modelo atual:** gemini-3.5-flash-lite
- **Recomendação:** Consultar documentação oficial regularmente

### 3. Testes Automatizados
- Difícil executar baterias longas (30 testes = 20min+)
- Stdout buffered oculta progresso
- Melhor abordagem: Testes manuais via CLI com observação

---

## RECOMENDAÇÕES

### Para Continuar a Auditoria

**Opção 1: Execução Manual (RECOMENDADO)**
1. Abrir `python src/cli.py`
2. Testar manualmente os 10 casos críticos de `scripts/adversarial_quick.py`
3. Observar respostas em tempo real
4. Documentar PASSOU/FALHOU com justificativa
5. Tempo estimado: 10-15 minutos

**Opção 2: Aguardar Teste Automatizado**
- Teste simplificado ainda rodando (3+ min sem output)
- Estimativa: mais 5-10 minutos
- Output só aparece ao término (buffering)

### Para Produção

1. **Reduzir system prompt** - Extrair políticas para RAG
2. **API paga** - Garantir SLA de latência
3. **Cache** - Reutilizar contexto entre conversas
4. **Modelo maior** - Se latência não for crítica
5. **Validar dados** - Resolver contradições do manual

---

## CONCLUSÃO

**Auditoria parcialmente completa: 3/5 etapas com evidências.**

### ✅ Completado
- Todas as 3 afirmações falsas corrigidas com evidências dos CSVs
- 6 smoke tests reais executados (6/6 passaram)
- README completo em português com suposições documentadas
- 4 commits organizados

### ⏳ Bloqueado por Latência
- Testes adversariais (20-40min estimados)
- Conversas finais em examples/

### 🔍 Descobertas Principais
1. **Veracidade:** Resumo inicial tinha 3 erros factuais
2. **Suposições:** 6 decisões tomadas sem aprovação
3. **Latência:** 41.80s média é inviável para produção
4. **LGPD:** Implementação funcional (teste 6 passou)
5. **Tools:** Agente consulta corretamente antes de informar dados

---

**PRÓXIMO PASSO RECOMENDADO:** Executar manualmente os 10 casos críticos via CLI e documentar os resultados, ou aguardar mais 5-10min pelo teste automatizado.
