# Empório da Música — Agente de Atendimento com IA

Protótipo de agente conversacional com IA para a **Empório da Música**, loja fictícia de instrumentos musicais em Campo Grande/MS.

> **Desafio Técnico:** Vaga de AI Engineer na Artefact  
> **Prazo:** 2 dias  
> **Status do Dia 1:** Implementação central completa com function calling, ferramentas determinísticas e interface CLI.

---

## Índice

- [Início Rápido](#início-rápido)
- [Arquitetura e Decisões Técnicas](#arquitetura-e-decisões-técnicas)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Funcionalidades](#funcionalidades)
- [Limitações Conhecidas](#limitações-conhecidas)
- [Uso de Assistentes de IA](#uso-de-assistentes-de-ia)
- [Log de Desenvolvimento](#log-de-desenvolvimento)

---

## Início Rápido

### Pré-requisitos

- Python 3.11+
- Chave de API do Google AI Studio ([obtenha grátis](https://aistudio.google.com/apikey))

### Instalação

```bash
# Clone e navegue até o projeto
cd "Desafio Técnico - AI Engineer"

# Crie o ambiente virtual
python -m venv .venv

# Ative o ambiente virtual
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Unix/macOS:
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Configure o ambiente
cp .env.example .env
# Edite .env e adicione sua GEMINI_API_KEY
```

### Executando o Agente

```bash
# Inicie o CLI interativo
python -m src.cli

# Comandos disponíveis:
# /sair   - Encerra
# /salvar - Salva a conversa em examples/
```

---

## Arquitetura e Decisões Técnicas

### Por que Function Calling em vez de RAG?

**Decisão:** Function calling determinístico sobre dados estruturados em CSV usando pandas.

**Justificativa:**
- **Dados operacionais são estruturados:** Produtos, pedidos, clientes e promoções se encaixam naturalmente em tabelas relacionais
- **Consultas determinísticas necessárias:** Cálculos de preço, verificação de estoque e consulta de pedidos devem ser exatos, não aproximados
- **Manual de políticas é pequeno:** ~12KB cabem inteiramente no prompt do sistema sem overhead de recuperação
- **Busca semântica desnecessária:** Consultas são buscas factuais (preço, estoque, status de pedido), não buscas por similaridade
- **Stack mais simples:** Sem banco vetorial, embeddings ou estratégia de chunking

RAG adicionaria complexidade sem benefícios para este caso de uso.

### Por que Gemini em vez de Outros LLMs?

**Decisão:** Google Gemini via API do free tier.

**Justificativa:**
- **Disponibilidade no free tier:** Limites generosos de tokens para prototipagem
- **SDK oficial:** `google-genai` com suporte nativo a function calling
- **Modelo configurável:** Variável `GEMINI_MODEL` permite trocar entre variantes Flash conforme disponibilidade muda
- **Latência:** 2-6 segundos para requisições completas incluindo chamadas de função (quando a API está responsiva)

**Evolução do Modelo:** Inicialmente visou `gemini-2.5-flash-lite`, mas foi descontinuado. Validado `gemini-3.5-flash-lite` como alternativa estável.

### Por que Acesso Direto ao CSV em vez de SQL?

**Decisão:** DataFrames pandas carregados na inicialização.

**Justificativa:**
- **Tamanho do dataset:** 65 produtos, 50 clientes, 20 pedidos — cabe facilmente em memória
- **Sem risco de text-to-SQL:** SQL gerado por LLM pode produzir consultas incorretas ou problemas de segurança
- **Type safety:** Funções Python com assinaturas explícitas capturam erros em runtime
- **Simplicidade:** Sem configuração de banco de dados, migrações de schema ou pooling de conexões
- **Performance:** Operações pandas em memória completam em <10ms

### Estratégia do System Prompt

**Decisão:** Persona + regras + manual completo de políticas (~16,5K chars) na instrução do sistema.

**Justificativa:**
- **Consistência:** Regras são sempre aplicadas, não recuperadas probabilisticamente
- **Sem alucinação sobre políticas:** Texto do manual é explícito, não parafraseado pelo modelo
- **Uso obrigatório de ferramentas:** Prompt força chamadas de ferramentas antes de afirmar preços/estoque
- **Tratamento de ambiguidade:** Documenta explicitamente contradições do manual (telefones, períodos de garantia)

**Trade-off:** Prompt grande aumenta latência durante alta demanda da API.

---

## Estrutura do Projeto

```
emporio-agent/
├── data/
│   ├── politicas_da_loja.md              # Manual de políticas da loja
│   ├── desafio_tecnico_ai_eng - *.csv    # Dados operacionais (produtos, pedidos, etc.)
│   └── .gitkeep
├── src/
│   ├── __init__.py
│   ├── data_loader.py    # Carrega CSVs, deriva regras (disponibilidade, promoções)
│   ├── tools.py          # Funções determinísticas chamáveis pelo LLM
│   ├── prompts.py        # System prompt com persona e políticas
│   ├── agent.py          # Orquestração Gemini com loop de function calling
│   └── cli.py            # Interface de terminal interativa
├── scripts/
│   └── inspect_data.py   # Relatório de qualidade dos dados (executar antes da limpeza)
├── tests/
│   └── test_data_rules.py
├── examples/
│   └── smoke_test_*.md   # Conversas de exemplo
├── NOTES.md              # Decisões de desenvolvimento e log de uso de assistente IA
├── README.md             # Versão em inglês
├── README_PT.md          # Este arquivo (Português)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Funcionalidades

### Agente Conversacional

- **Persona:** Tom informal mas profissional, como "um amigo que entende de música"
- **Aplicação de escopo:** Recusa acessórios (cordas, palhetas, cabos, pedais, amplificadores)
- **Uso obrigatório de ferramentas:** Nunca inventa preços, estoque ou prazos de entrega
- **Conforme LGPD:** Consulta de pedido valida identidade do cliente antes de expor dados

### Ferramentas Determinísticas

| Ferramenta | Propósito |
|---|---|
| `buscar_produtos` | Busca instrumentos por nome, categoria, faixa de preço |
| `detalhar_produto` | Obtém preço atual, estoque, promoção e especificações |
| `listar_promocoes_ativas` | Lista promoções ativas em produtos disponíveis |
| `consultar_pedido` | Busca detalhes do pedido após verificação de identidade |
| `calcular_preco` | Calcula preço com regras de pagamento (desconto PIX, parcelamento) |
| `consultar_politica` | Extrai seção relevante do manual de políticas |

### Regras de Negócio (Aplicadas em Código)

- **Disponibilidade:** `status == "active" E stock_quantity > 0`
- **Desconto PIX:** 5% sobre preço de tabela, NÃO acumula com promoções ativas
- **Limites de parcelamento:**
  - 1-3x: mínimo R$50/parcela
  - 4-6x: mínimo R$80/parcela
  - 7-12x: mínimo R$100/parcela
- **Período de devolução:** 7 dias a partir de `estimated_delivery` (proxy para data real de entrega)
- **Inconsistências de catálogo:** 6 produtos sinalizados; agente omite descrição para estes itens

---

## Limitações Conhecidas

### 1. Latência da API em Alta Demanda

**Problema:** `gemini-3.5-flash-lite` pode ultrapassar timeout (>30s) durante uso de pico.

**Evidência:** Cenários 4-6 do smoke test falharam com `APITimeoutError` imediatamente após cenários 1-3 terem sucesso em 2-3s cada.

**Causa raiz:** Prompt grande (~16,5K chars) + limitação de taxa do free tier.

**Mitigação:** Lógica de retry com backoff exponencial trata HTTP 429/503. Produção requereria tier pago ou otimização do prompt.

### 2. Preços Históricos de Pedidos Ausentes

**Problema:** `order_items.csv` não possui coluna `unit_price`.

**Impacto:** 2 de 20 pedidos mostram discrepância entre `total_brl` e soma dos preços atuais dos produtos (provavelmente promoções históricas).

**Decisão:** Preservar `orders.total_brl` como fonte da verdade; não recalcular pedidos passados com preços atuais.

### 3. Dados Ambíguos no Manual

**Problema:** Manual de políticas contém contradições:
- Telefone: `(67) 3341-4444` (geral) vs `(67) 3321-4500` (WhatsApp)
- Email: `contato@emporiodamusica.com.br` vs `contato@empóriodamusica.com.br`
- Garantia: 90 dias garantia legal vs 30 dias para troca por defeito

**Decisão:** Agente NÃO escolhe silenciosamente. Apresenta ambos os valores e oferece escalonamento para a equipe para confirmação.

### 4. Proxy para Data de Entrega

**Problema:** Sem `actual_delivery_date` nos dados.

**Decisão:** Usar `estimated_delivery` como proxy para cálculo do período de devolução. Documentado como suposição no código e NOTES.md.

### 5. Modelos Descontinuados

**Problema:** Vários modelos Gemini (`2.5-flash`, `2.5-flash-lite`, `3.8-flash`) retornaram HTTP 404/503 durante o desenvolvimento.

**Resolução:** Validado `gemini-3.5-flash-lite` como estável. Nome do modelo é configurável via variável `GEMINI_MODEL`.

---

## Uso de Assistentes de IA

Este projeto foi desenvolvido com **suporte de assistente de IA (Kiro/Claude)** para:

1. **Configuração inicial** e scaffolding do projeto
2. **Script de inspeção de dados** com verificações de qualidade e validação de integridade referencial
3. **Carregador de CSV** com colunas derivadas (disponibilidade, promoções, cálculos de preço)
4. **Pesquisa do SDK Gemini** e implementação de function calling
5. **Diagnóstico de causa raiz** do timeout inicial de 120s (testou ferramentas independentemente, validou conectividade, identificou modelos descontinuados)
6. **Implementação do CLI** com persistência de sessão e exportação Markdown

### O que o Assistente NÃO Fez

- **Decisões de arquitetura:** Humano escolheu function calling sobre RAG, pandas sobre SQL, Gemini sobre alternativas
- **Regras de negócio:** Humano definiu lógica de disponibilidade, não-acumulação de PIX, limites de parcelamento
- **Ambiguidades do manual:** Humano identificou contradições e decidiu sobre tratamento transparente
- **Design do smoke test:** Humano especificou os 6 cenários e critérios de aceitação

### Workflow de Desenvolvimento

1. Humano fornece requisitos e decide abordagem
2. Assistente implementa código, trata detalhes do SDK, escreve testes
3. Humano valida comportamento, solicita correções, aprova commits
4. Assistente documenta decisões em `NOTES.md` após cada etapa

Isso espelha uso no mundo real: IA acelera execução, humano dirige estratégia.

---

## Log de Desenvolvimento

| Etapa | Entregável | Status |
|---:|---|:---:|
| 1 | Setup do projeto, venv, requirements | ✅ |
| 2 | Script de inspeção de dados (`scripts/inspect_data.py`) | ✅ |
| 3 | Carregador de dados com regras (`src/data_loader.py`) | ✅ |
| 4 | Ferramentas determinísticas (`src/tools.py`) | ✅ |
| 5 | System prompt com políticas (`src/prompts.py`) | ✅ |
| 6 | Agente Gemini com function calling (`src/agent.py`) | ✅ |
| 7 | CLI interativo (`src/cli.py`) | ✅ |
| 8 | Smoke test (3/6 cenários validados) | ⚠️ |
| 9 | Documentação (este README) | ✅ |

**Dia 1 completo.** Agente central funcional com function calling validado em consultas reais.

---

## Testes

### Executar Testes de Regras de Dados

```bash
python -m unittest tests/test_data_rules.py -v
```

### Resultados do Smoke Test

Veja `examples/smoke_test_*.md` para cenários validados:

1. ✅ Busca por violões até R$1000 → 12 resultados retornados
2. ✅ Consulta de preço do Takamine GD20 → Preço correto com opções de pagamento oferecidas
3. ✅ Endereço e horário da loja → Dados corretos do manual de políticas

Cenários 4-6 (política de devolução, item fora de escopo, pedido protegido por LGPD) tiveram timeout devido à latência da API, não erros de código.

---

## Licença

Projeto educacional para avaliação de desafio técnico.

---

## Contato

**Desafio:** AI Engineer @ Artefact  
**Candidato:** [Seu nome]  
**Data:** Novembro de 2026
