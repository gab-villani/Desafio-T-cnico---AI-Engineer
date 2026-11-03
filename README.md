# Empório da Música - Agente de Atendimento

Protótipo de agente de atendimento por texto para a loja fictícia "Empório da Música" (Campo Grande/MS), desenvolvido como parte de desafio técnico para AI Engineer.

## Como Rodar

### Pré-requisitos
- Python 3.11 ou superior
- Chave de API do Google AI Studio (Gemini)

### Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repo>
cd emporio-agent

# 2. Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env e adicione sua GEMINI_API_KEY
```


## Interface web (opcional)

Para quem quiser experimentar rapidamente o agente via navegador, há uma UI mínima baseada em **Streamlit**.

```bash
# Instale dependências (inclui streamlit)
pip install -r requirements.txt

# Rode a aplicação web (Windows)
streamlit run ui/app.py

# Rode a aplicação web (Linux/macOS)
streamlit run ui/app.py
```

A interface exibe o histórico da conversa, permite iniciar uma *Nova conversa* (limpa o histórico) e mostra um indicador de *digitando…* enquanto o agente processa a mensagem. Em caso de falha ou timeout, aparece uma mensagem de erro amigável em português.

A CLI permanece o caminho principal (`python src/cli.py`).


Para quem quiser experimentar rapidamente o agente via navegador, há uma UI mínima baseada em **Streamlit**.

```bash
# Instale dependências (inclui streamlit)
pip install -r requirements.txt

# Rode a aplicação web (Windows)
streamlit run ui/app.py

# Rode a aplicação web (Linux/macOS)
streamlit run ui/app.py
```

A interface exibe o histórico da conversa, permite iniciar uma *Nova conversa* (limpa o histórico) e mostra um indicador de *digitando…* enquanto o agente processa a mensagem. Em caso de falha ou timeout, aparece uma mensagem de erro amigável em português.

A CLI permanece o caminho principal (`python src/cli.py`).


```bash
python src/cli.py
```

**Comandos disponíveis:**
- Digite suas perguntas normalmente
- `/sair` - Encerra o chat (histórico salvo automaticamente)
- `/salvar` - Exporta a conversa atual para `examples/`

### Configuração

Edite o arquivo `.env`:

```bash
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-3.5-flash-lite  # ou outro modelo disponível
REFERENCE_DATE=2026-03-01  # data de referência para testes de prazo
```

**Nota:** O modelo `gemini-2.5-flash-lite` foi descontinuado. Use `gemini-3.5-flash-lite` ou consulte a [documentação oficial](https://ai.google.dev/gemini-api/docs/models/gemini) para modelos disponíveis.

---

## Decisões Técnicas e Justificativas

### Arquitetura

**Function Calling Determinístico**
- LLM (Gemini) orquestra QUANDO chamar cada função
- Funções Python executam lógica de negócio e cálculos
- Sem RAG: manual de políticas (~3KB) entra no system prompt
- Sem text-to-SQL: pandas para CSVs (dataset pequeno, 65 produtos)

**Justificativa:** Para um protótipo com dados pequenos e regras claras, function calling oferece controle total sobre cálculos (preço, desconto, parcelamento) e evita alucinações matemáticas do LLM.

### Separação de Responsabilidades

```
src/
  data_loader.py  → Carrega CSVs e aplica regras derivadas
  tools.py        → 6 funções chamáveis pelo LLM (busca, preço, pedido, políticas)
  prompts.py      → System prompt com persona + manual completo
  agent.py        → Loop de function calling + histórico
  cli.py          → Interface de terminal (desacoplada)
```

**Justificativa:** A função `responder(mensagem, historico)` é independente do CLI, permitindo trocar a interface (web, API REST) sem modificar a lógica do agente.

### Tools Implementadas

1. **buscar_produtos**: Filtros por nome, categoria, preço. Retorna preço final (após promoção ativa).
2. **detalhar_produto**: Specs completas, promoção ativa, estoque.
3. **listar_promocoes_ativas**: Apenas promoções com `is_active=1`.
4. **calcular_preco**: Aplica desconto PIX, valida parcelas mínimas.
5. **consultar_pedido**: **Validação LGPD** - só retorna dados se e-mail/telefone bater com o cliente do pedido.
6. **consultar_politica**: Busca seção relevante do manual (trocas, frete, garantia, horários).

### Regras de Negócio (Implementadas em Código)

- **Disponibilidade:** `status == "active" AND stock_quantity > 0`
- **PIX:** 5% de desconto sobre preço de tabela, **NÃO acumula** com promoção ativa
- **Parcelamento:** Sem juros, parcela mínima R$ 50 (1-3x), R$ 80 (4-6x), R$ 100 (7-12x)
- **Promoção ativa:** Apenas `is_active == 1` (CSV não tem datas de vigência)
- **Arrependimento:** 7 dias corridos após `estimated_delivery` (proxy do recebimento)

**Justificativa:** Cálculos em Python garantem precisão. LLM nunca faz contas de desconto/parcelamento.

### Tratamento de Erros

- **Rate limit (429) / Indisponibilidade (503):** Até 2 tentativas com backoff exponencial (1s)
- **Timeout:** 30s por chamada à API
- **Loop infinito:** Máximo 10 iterações de function calling (evita loops)
- **LGPD:** Resposta genérica idêntica para pedido inexistente OU e-mail errado

### Persona e Escopo

**Persona:** Informal mas profissional, acolhedora, "como um amigo que entende de música".

**Escopo:**
- ✅ Violões, pianos, baterias, teclados, ukuleles, guitarras, baixos
- ❌ Acessórios (cordas, palhetas, cabos, cases, pedais, amplificadores)
- ❌ Temas fora do domínio (receitas, política, opinião médica/jurídica)

**Reclamações:** Acolhe, pede detalhes, informa retorno em 24h úteis, **não finge** que registrou (protótipo sem persistência).

---

## Limitações Conhecidas

### 1. Latência Alta (18-70 segundos)
**Causa:** System prompt grande (~16.5k caracteres) + API gratuita do Gemini + horários de alta demanda.  
**Impacto:** Inviável para produção. Usuários esperam <3s.  
**Mitigação futura:** Cachear políticas no contexto, usar modelo pago com SLA, ou RAG para manual.

### 2. Contradições no Manual Não Resolvidas
**Encontradas:**
- Telefone: (67) 3341-4444 vs WhatsApp (67) 3321-4500
- E-mail: com e sem acentos (emporiodamusica vs empóriodamusica)
- Garantia: troca 30 dias vs legal 90 dias

**Solução implementada (não ideal):** Agente apresenta ambos os dados sem escolher, menciona divergência se necessário, e encaminha para humano em casos concretos.  
**Ideal:** Validar fonte oficial com stakeholder.

### 3. Histórico Não Persistente Entre Sessões
Histórico salvo em `.session_history.json` é carregado ao iniciar CLI, mas não há histórico global nem análise de conversas anteriores.

### 4. Produtos com Catálogo Inconsistente
6 produtos (9,2%) têm marca no nome diferente da marca na descrição/specs.  
**Exemplo:** "Music Man Bass 1X" descreve um "Fender Jazz Bass".  
**Solução:** Marcados com `catalog_inconsistent=True`; descrição omitida, specs preservadas.  
**Ideal:** Corrigir fonte de dados.

### 5. Sem Preço Histórico
Pedidos armazenam `total_brl` mas os itens não têm `price_at_order`. Impossível validar se total está correto.  
**Impacto:** 2 pedidos divergem da soma com preços atuais (IDs 3 e 20).

### 6. Data de Referência Arbitrária
`REFERENCE_DATE=2026-03-01` foi escolhida arbitrariamente para cálculos de arrependimento. CSV tem `estimated_delivery`, não data real de entrega.

### 7. Sem Integração Real
Não há persistência de reclamações, envio de e-mail, integração com ERP/estoque, nem atualização de pedidos.

---

## Suposições Feitas (Não Aprovadas Previamente)

Estas decisões foram tomadas durante o desenvolvimento sem aprovação explícita:

### 1. PIX Não Acumula com Promoção
**Justificativa:** Prática comum em varejo.  
**Alternativa:** Permitir acúmulo (melhor para o cliente, pior para margem).

### 2. Parcelas Mínimas
- 1-3x: R$ 50/parcela
- 4-6x: R$ 80/parcela
- 7-12x: R$ 100/parcela

**Justificativa:** Padrão de mercado.  
**Impacto:** Produtos baratos não podem ser parcelados em muitas vezes.

### 3. Normalização de E-mail/Telefone
- E-mail: remove acentos, espaços, lowercase
- Telefone: extrai últimos 10-11 dígitos

**Justificativa:** Permitir flexibilidade de formato na consulta de pedidos (LGPD).  
**Alternativa:** Exigir formato exato (mais restritivo).

### 4. Produtos Inconsistentes Têm Descrição Omitida
6 produtos com divergência marca recebem aviso ao invés de descrição potencialmente enganosa.  
**Specs técnicas preservadas** (consideradas confiáveis).

### 5. Arrependimento Usa `estimated_delivery` + 7 Dias
CSV não tem data real de entrega. Usamos `estimated_delivery` como proxy.  
**Ideal:** Integrar com transportadora para data real de entrega.

### 6. Tratamento de Contradições do Manual
- Telefones: apresentar ambos sem escolher
- E-mail: normalizar para versão sem acento
- Garantia: separar troca 30 dias de garantia legal 90 dias

**Ideal:** Validar dados oficiais com equipe da loja.

---

## Uso de Assistentes de Código

Este projeto foi desenvolvido com auxílio de assistente de IA (Kiro/Claude). Abaixo, o que foi gerado e o que foi corrigido:

### Gerado pelo Assistente
- ✅ Estrutura inicial de pastas e arquivos de configuração
- ✅ Script de inspeção de dados (`scripts/inspect_data.py`)
- ✅ Implementação de `data_loader.py` com validações
- ✅ Implementação das 6 tools em `tools.py`
- ✅ System prompt inicial em `prompts.py`
- ✅ Loop de function calling em `agent.py`
- ✅ Interface CLI com persistência em `cli.py`
- ✅ Smoke tests e testes adversariais

### Corrigido Manualmente
- ❌ **Afirmações falsas no resumo inicial:**
  - Disse "preços como string" → CSVs já tinham float64
  - Disse "promoções vencidas" → CSV não tem datas, apenas `is_active`
  - Disse status "esgotado" → Não existe; o correto é "active com stock_quantity=0"
- ❌ **Modelo Gemini:** Inicialmente configurado com `gemini-2.5-flash-lite` (descontinuado), corrigido para `gemini-3.5-flash-lite`
- ✅ **Contradições do manual:** Assistente identificou e documentou, mas decisão de tratamento foi explicitada como "não aprovada"

### Processo de Validação
1. Assistente propôs implementação
2. Usuário solicitou auditoria com evidências brutas
3. Assistente corrigiu afirmações falsas e documentou suposições
4. Smoke tests executados com API real (sem mocks)
5. Testes adversariais para validar robustez

---

## Estrutura de Dados

### CSVs Fornecidos
- `products.csv` (65 produtos)
- `categories.csv` (9 categorias)
- `customers.csv` (50 clientes)
- `orders.csv` (20 pedidos)
- `order_items.csv` (22 itens de pedido)
- `promotions.csv` (25 promoções)
- `politicas_da_loja.md` (manual de políticas)

### Colunas Derivadas (em Memória)

**products:**
- `is_available` = `(status == "active") AND (stock_quantity > 0)`
- `active_promo_percent` = % de desconto da promoção ativa mais recente
- `final_price` = preço após promoção ativa (ou `list_price` se não houver)
- `catalog_inconsistent` = `True` se categoria X specs divergem

**customers:**
- `email_norm` = e-mail normalizado (sem acentos, lowercase)
- `phone_norm` = telefone normalizado (últimos 10-11 dígitos)

---

## Testes

### Smoke Tests (6 cenários básicos)
✅ Todos passaram com API real Gemini

1. Busca de violões até R$ 1000
2. Consulta de preço específico (Takamine GD20)
3. Endereço e horário da loja
4. Política de devolução por arrependimento
5. Recusa de produto fora de escopo (corda de violão)
6. Consulta de pedido com e-mail incorreto (LGPD)

**Evidências completas:** Ver `SMOKE_TESTS_EVIDENCIAS.md`

### Testes Adversariais (~30 casos)
Categorias testadas:
- (A) Identidade e LGPD
- (B) Alucinação de preço
- (C) Estoque (active com estoque 0, discontinued, coming_soon)
- (D) Promoção e pagamento
- (E) Políticas e prazos
- (F) Escopo
- (G) Prompt injection e segurança
- (H) Reclamações
- (I) Contradições do manual

**Resultados:** Ver `ADVERSARIAL_RESULTS.txt` (gerado após execução)

---

## Próximos Passos (Dia 2 - Não Implementado)

- [ ] Análise detalhada dos resultados adversariais
- [ ] Correções baseadas em falhas encontradas
- [ ] Conversas completas gravadas (4-5 exemplos)
- [ ] Teste do limite de 10 iterações (forçar loop)
- [ ] Melhorias na experiência do CLI
- [ ] Documentação de exemplos de uso

---

## Contato

Desenvolvido como parte de desafio técnico para AI Engineer.  
**Data:** Novembro 2026 (Dia 1 completo)

---

## Licença

Projeto de demonstração para fins de avaliação técnica.
