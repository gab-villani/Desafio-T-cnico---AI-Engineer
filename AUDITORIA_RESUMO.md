# AUDITORIA - Resumo Executivo

**Data:** 2026-11-02  
**Solicitante:** Usuário (desconfiou do resumo inicial do Dia 1)

---

## 1. AUDITORIA DE VERACIDADE ✅ COMPLETA

### Afirmações Falsas Identificadas e Corrigidas

1. **"Preços como string"** → ❌ FALSO
   - CSV já tem `price_brl` como `float64`
   - Nenhum parsing necessário
   - Corrigido em NOTES.md

2. **"Promoções vencidas"** → ❌ FALSO
   - CSV tem apenas `is_active` (0 ou 1), SEM datas
   - Impossível determinar "vencido" sem colunas de data
   - Corrigido em NOTES.md

3. **Status "esgotado"** → ❌ PARCIALMENTE FALSO
   - Status reais: `active`, `discontinued`, `coming_soon`
   - "Esgotado" é `active` com `stock_quantity=0` (produto ID 96)
   - Corrigido em NOTES.md

### Documentação Criada
- ✅ `AUDITORIA.md` - Lista completa de afirmações falsas e suposições
- ✅ `NOTES.md` - Atualizado com informações precisas
- ✅ Commit: "docs: correção de afirmações falsas e documentação de suposições não aprovadas"

---

## 2. SMOKE TESTS REAIS ✅ COMPLETA

### Configuração
- **Modelo inicial:** `gemini-2.5-flash-lite` → ❌ Descontinuado (HTTP 404)
- **Modelo corrigido:** `gemini-3.5-flash-lite` → ✅ Funcional
- **API:** Google Gemini (gratuita)
- **Timeout:** 30s por chamada

### Resultados: 6/6 PASSARAM ✅

| # | Cenário | Latência | Status |
|---|---------|----------|--------|
| 1 | Busca violões até R$ 1000 | 47.66s | ✅ PASSOU |
| 2 | Preço do Takamine GD20 | 50.02s | ✅ PASSOU |
| 3 | Endereço e horário | 18.77s | ✅ PASSOU |
| 4 | Política de devolução | 69.82s | ✅ PASSOU |
| 5 | Corda de violão (fora de escopo) | 26.20s | ✅ PASSOU |
| 6 | Pedido com e-mail errado (LGPD) | 38.30s | ✅ PASSOU |

**Latência média:** 41.80s

### Evidências
- ✅ `SMOKE_TESTS_EVIDENCIAS.md` - Queries, tools chamadas, respostas completas
- ✅ `scripts/smoke_test_real.py` - Script de testes
- ✅ Commit: "test: smoke tests reais com API Gemini - todos os 6 cenários passaram"

### Verificações Específicas
- ✅ Consultou tools antes de informar preço/estoque
- ✅ Reconheceu fora de escopo sem consulta desnecessária
- ✅ LGPD: negou acesso sem revelar se pedido existe
- ✅ Cálculos feitos em Python, não pelo LLM

---

## 3. TESTES ADVERSARIAIS ⏳ EM ANDAMENTO

### Status
- **Iniciado:** 16:03 (02/11/2026)
- **Tempo decorrido:** ~2 minutos
- **Progresso:** 0/30 testes (arquivo de output ainda vazio)
- **Estimativa:** 30-60 minutos (30 testes × 20-70s cada)

### Categorias a Testar
- [ ] A) Identidade e LGPD (4 testes)
- [ ] B) Alucinação de preço (2 testes)
- [ ] C) Estoque (3 testes)
- [ ] D) Promoção e pagamento (3 testes)
- [ ] E) Políticas e prazos (3 testes)
- [ ] F) Escopo (3 testes)
- [ ] G) Prompt injection e segurança (3 testes)
- [ ] H) Reclamações (2 testes)
- [ ] I) Contradições do manual (2 testes)

### Arquivo de Saída
- `tests/test_adversarial.py` - Script criado
- `ADVERSARIAL_RESULTS.txt` - Será gerado ao término

---

## 4. CONVERSAS FINAIS (examples/) ⏳ PENDENTE

Aguardando término dos testes adversariais para:
1. Corrigir falhas encontradas
2. Gravar 4-5 conversas completas via `/salvar`
3. Garantir que pelo menos uma mostre tool calls visíveis

---

## 5. README ✅ COMPLETO

### Conteúdo
- ✅ Como rodar (instalação, execução, configuração)
- ✅ Decisões técnicas e justificativas
- ✅ Limitações conhecidas (7 itens)
- ✅ Suposições não aprovadas (6 itens)
- ✅ Uso de assistentes de código (honesto sobre correções)
- ✅ Estrutura de dados e colunas derivadas
- ✅ Referências aos arquivos de evidências

### Formato
- ✅ Um único arquivo: `README.md`
- ✅ Idioma: Português
- ✅ Removido: `README_PT.md` (duplicado)

### Commit
- ✅ "docs: README completo em português com decisões, limitações e suposições"

---

## SUPOSIÇÕES NÃO APROVADAS DOCUMENTADAS

1. **REFERENCE_DATE = 2026-03-01** - Data arbitrária para cálculos de prazo
2. **catalog_inconsistent omite descrição** - 6 produtos com marca divergente
3. **PIX não acumula com promoção** - Decisão de negócio sem validação
4. **Parcelas mínimas** - R$ 50/80/100 baseado em "padrão de mercado"
5. **Normalização de e-mail/telefone** - Flexibilidade para matching LGPD
6. **Tratamento de contradições do manual** - Apresentar ambos sem escolher

---

## COMMITS REALIZADOS

1. ✅ "docs: correção de afirmações falsas e documentação de suposições não aprovadas"
2. ✅ "test: smoke tests reais com API Gemini - todos os 6 cenários passaram"
3. ✅ "docs: README completo em português com decisões, limitações e suposições"

---

## PRÓXIMOS PASSOS

1. ⏳ Aguardar término dos testes adversariais (~30-60min)
2. ⏳ Analisar resultados e identificar falhas
3. ⏳ Corrigir falhas encontradas (commits separados)
4. ⏳ Gravar 4-5 conversas completas em examples/
5. ⏳ Testar limite de 10 iterações (forçar loop)
6. ✅ Documentação final (README completo)

---

## OBSERVAÇÕES

### Latências Altas
- System prompt: ~16.5k caracteres
- API gratuita: sem SLA de latência
- Média: 18-70s por resposta
- **Inviável para produção** (usuários esperam <3s)

### Modelo Gemini
- `gemini-2.5-flash-lite` descontinuado (HTTP 404)
- `gemini-3.5-flash-lite` funcional
- Verificar documentação oficial para modelos ativos

### Processo de Auditoria
- ✅ Evidências brutas fornecidas (não apenas afirmações)
- ✅ Testes com API real (sem mocks)
- ✅ Correções documentadas e commitadas
- ✅ Suposições explicitadas para aprovação retroativa
