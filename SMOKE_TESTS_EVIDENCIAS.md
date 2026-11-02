# SMOKE TESTS REAIS - Evidências Completas

**Data:** 2026-11-02  
**Modelo:** gemini-3.5-flash-lite  
**Todos os 6 cenários:** ✅ PASSARAM

---

## CENÁRIO 1: Busca de violões até R$ 1000
**Pergunta:** "Quais violões disponíveis até R$ 1000?"  
**Latência:** 47.66s  
**Tool chamada:** `buscar_produtos(preco_max=1000, categoria="violao")`  
**Resultado:** Retornou 12 produtos organizados por tipo de corda (nylon/aço)  
**Verificação:** ✅ Resposta completa, preços corretos, não inventou dados

---

## CENÁRIO 2: Consulta de preço específico
**Pergunta:** "Quanto custa o Takamine GD20?"  
**Latência:** 50.02s  
**Tool chamada:** `detalhar_produto("Takamine GD20")`  
**Resultado:** R$ 2.199,00, 5 unidades em estoque  
**Verificação:** ✅ Consultou a tool, não alucionou preço/estoque

---

## CENÁRIO 3: Endereço e horário da loja
**Pergunta:** "Qual o endereço e o horário da loja?"  
**Latência:** 18.77s  
**Tool chamada:** `consultar_politica("horarios")`  
**Resultado:** Endereço completo + horários de atendimento  
**Verificação:** ✅ Consultou o manual, não inventou informações

---

## CENÁRIO 4: Política de devolução
**Pergunta:** "Me arrependi da minha compra, posso devolver?"  
**Latência:** 69.82s  
**Tool chamada:** `consultar_politica("trocas")`  
**Resultado:** 7 dias para arrependimento, condições completas  
**Verificação:** ✅ Explicação detalhada baseada no manual

---

## CENÁRIO 5: Produto fora de escopo
**Pergunta:** "Vocês vendem corda de violão?"  
**Latência:** 26.20s  
**Tool chamada:** Nenhuma (reconheceu fora de escopo)  
**Resultado:** Recusa educada, explicou que não vende acessórios  
**Verificação:** ✅ Recusou corretamente sem consultar catálogo desnecessariamente

---

## CENÁRIO 6: Consulta de pedido com e-mail incorreto (LGPD)
**Pergunta:** "Quero consultar o pedido 5, meu e-mail é cliente.errado@example.com"  
**Latência:** 38.30s  
**Tool chamada:** `consultar_pedido(order_id=5, email_ou_telefone="cliente.errado@example.com")`  
**Resultado:** Negou acesso sem revelar se o pedido existe  
**Verificação:** ✅ Proteção LGPD funcionando - resposta genérica idêntica

---

## VERIFICAÇÕES ADICIONAIS

### Pedido 5 real existe?
Sim, verificado no CSV: order_id=5, customer_id=5  
E-mail real do cliente 5: leonardo.costa@cmail.com

### A resposta revelou que o pedido existe?
❌ NÃO. Resposta genérica: "Não foi possível validar as informações fornecidas"

### Latências
- Mínimo: 18.77s (consulta simples ao manual)
- Máximo: 69.82s (política de devolução - resposta complexa)
- Média: 41.80s
- **Nota:** Latências altas devido ao system prompt grande (~16.5k chars) + free tier do Gemini

### Tools chamadas corretamente?
✅ Sim. O agente:
- Consultou tools antes de informar preço/estoque
- Reconheceu fora de escopo sem consulta desnecessária
- Validou identidade antes de retornar dados de pedido

### Cálculos feitos pelo LLM?
❌ NÃO. Todos os preços vieram das tools (código Python)

---

## LIMITAÇÕES OBSERVADAS

1. **Latência alta:** System prompt grande + API gratuita = 18-70s por resposta
2. **Modelo mudou:** `gemini-2.5-flash-lite` descontinuado, migrado para `gemini-3.5-flash-lite`
3. **Sem mock:** Todos os testes usaram API real

---

## PRÓXIMOS PASSOS

1. ✅ Smoke tests básicos passaram
2. ⏳ Testes adversariais (alucinação, prompt injection, etc.)
3. ⏳ Conversas completas gravadas em examples/
4. ⏳ Limite de 10 iterações (forçar caso de loop)
