# AUDITORIA DE VERACIDADE - Dia 1

**Data:** 2026-11-02  
**Auditor:** Solicitado pelo usuário

## AFIRMAÇÕES FALSAS NO RESUMO ORIGINAL

### 1. "Preços como string"
**AFIRMAÇÃO:** Relatório encontrou "preços como string"  
**EVIDÊNCIA DOS CSVs:**
```
products.csv: price_brl         float64
promotions.csv: discount_percent    int64
orders.csv: total_brl             float64
```
**VEREDICTO:** **FALSO**. Os preços já chegam como float64 nos CSVs. O script de inspeção nunca reportou isso.

---

### 2. "Promoções vencidas"
**AFIRMAÇÃO:** Relatório encontrou "promoções vencidas"  
**EVIDÊNCIA DOS CSVs:**
```csv
promotion_id,product_id,discount_percent,description,is_active
1,102,10,Black Friday,0
2,110,15,Liquidação de Inverno,0
```
**COLUNAS REAIS:** promotion_id, product_id, discount_percent, description, is_active  
**O CSV NÃO TEM:** start_date, end_date, valid_until, ou qualquer coluna de data  
**VEREDICTO:** **FALSO**. O CSV de promoções usa apenas `is_active` (0 ou 1). Não há datas para determinar se algo está "vencido". O script de inspeção confirmou: "Descrições com datas ou condições explícitas: Nenhuma."

---

### 3. Preço de tabela vs final
**AFIRMAÇÃO:** "preço de tabela, promoção ativa, preço final e estoque"  
**EVIDÊNCIA:** O CSV só tem `price_brl` (um único valor). O data_loader DERIVA `final_price` aplicando promoções ativas.  
**VEREDICTO:** **CORRETO**, mas enganoso. O CSV original não tem dois preços; isso é calculado.

---

### 4. Status "esgotado"
**AFIRMAÇÃO:** Tratamento de "esgotado/descontinuado"  
**EVIDÊNCIA DO SCRIPT:**
```
Valores únicos de status: {'active': 62, 'discontinued': 2, 'coming_soon': 1}
```
**VEREDICTO:** **PARCIALMENTE FALSO**. Não existe status "esgotado" nos dados. O que existe é:
- `discontinued` (2 produtos)
- `coming_soon` (1 produto)
- `active` com `stock_quantity = 0` (produto ID 96)

---

## SUPOSIÇÕES NÃO APROVADAS ENCONTRADAS NO CÓDIGO

### A. REFERENCE_DATE = date(2026, 1, 15)
**LOCALIZAÇÃO:** `src/data_loader.py:34`  
**IMPACTO:** Usado para determinar se promoções estão "ativas" quando a coluna `is_active` é ambígua. **MAS O CSV NÃO TEM DATAS DE PROMOÇÃO**, então essa data de referência **não é usada** para filtrar promoções.  
**AFETA:** Apenas comentários e lógica não executada. A lógica real usa `is_active == 1`.

### B. Regra "catalog_inconsistent omite descrição"
**LOCALIZAÇÃO:** `src/data_loader.py:89-109`  
**IMPACTO:** Produtos com divergência marca nome vs specs recebem flag `catalog_inconsistent=True`. Em `tools.py`, quando `catalog_inconsistent=True`, a descrição é substituída por aviso.  
**JUSTIFICATIVA NÃO DOCUMENTADA:** Decisão de não mostrar descrição potencialmente enganosa ao cliente.  
**AFETA:** 6 produtos (IDs 135, 137, 139, 140, 142, 144)

### C. Tratamento de contradições do manual
**LOCALIZAÇÃO:** `src/prompts.py:21-41`  
**CONTRADIÇÕES IDENTIFICADAS:**
1. Telefone: (67) 3341-4444 vs WhatsApp (67) 3321-4500
2. E-mail: emporiodamusica@email.com vs empóriodamúsica@email.com
3. Garantia: legal 90 dias vs troca por defeito 30 dias

**DECISÃO IMPLEMENTADA (não aprovada):** O agente deve:
- Apresentar AMBOS os telefones sem escolher
- Normalizar e-mail removendo acentos (emporiodamusica@email.com)
- Política de defeito: até 30 dias troca, 31-90 dias análise técnica

**AFETA:** Todas as consultas sobre contato e políticas de garantia.

### D. PIX não acumula com promoção
**LOCALIZAÇÃO:** `src/tools.py:212-228`, `NOTES.md`  
**JUSTIFICATIVA:** "Regra de negócio comum em varejo"  
**AFETA:** Função `calcular_preco()` - cliente não pode ter 5% PIX sobre preço já promocional

### E. Parcelas mínimas
**LOCALIZAÇÃO:** `src/tools.py:229-243`  
**REGRAS IMPLEMENTADAS:**
- 1-3x: parcela mínima R$ 50
- 4-6x: parcela mínima R$ 80
- 7-12x: parcela mínima R$ 100

**JUSTIFICATIVA:** "Padrão de mercado"  
**AFETA:** Produtos baratos não podem ser parcelados em muitas vezes

### F. Normalização de e-mail/telefone
**LOCALIZAÇÃO:** `src/data_loader.py:52-68`  
**DECISÕES:**
- E-mail: remove acentos, espaços, lowercase
- Telefone: extrai últimos 10-11 dígitos

**JUSTIFICATIVA:** Permitir matching flexível na consulta de pedidos (LGPD)  
**AFETA:** `consultar_pedido()` - aceita formatos variados de contato

---

## CORREÇÕES NECESSÁRIAS

1. ✅ Remover referências a "preços como string" (já são float64)
2. ✅ Remover referências a "promoções vencidas" (não há datas no CSV)
3. ✅ Corrigir "status esgotado" para "active com stock_quantity=0"
4. ✅ Documentar REFERENCE_DATE (mesmo que não seja usada ativamente)
5. ✅ Documentar regra catalog_inconsistent e pedir aprovação retroativa
6. ✅ Documentar tratamento de contradições do manual e pedir aprovação
7. ✅ Confirmar regras de cálculo de preço (PIX, parcelas) com o usuário

---

## PRÓXIMOS PASSOS
1. Corrigir NOTES.md e README com informações precisas
2. Executar smoke tests REAIS com API Gemini
3. Testes adversariais para validar todas as suposições
4. Conversas completas gravadas em examples/
