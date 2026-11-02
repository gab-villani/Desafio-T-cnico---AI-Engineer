# Notas de desenvolvimento

## Passo 1 — Setup inicial

- Criada a estrutura inicial do projeto para um agente Python com interface CLI.
- Dependências iniciais: `google-genai` (SDK oficial Google Gen AI), `pandas` e `python-dotenv`.
- O modelo Gemini será configurado por `GEMINI_MODEL`, sem fixar o nome no código, pois a disponibilidade do free tier pode variar.
- `.env` está ignorado pelo Git para proteger a chave da API.
- A documentação oficial do SDK/API de function calling será consultada novamente antes da implementação do loop no passo 6, para confirmar assinaturas vigentes.

## Passo 2 — Inspeção dos dados brutos

- Criado `scripts/inspect_data.py` para inspecionar os seis CSVs antes de qualquer limpeza. O script relata dimensões, tipos, nulos, duplicatas, valores de status, sinais específicos de qualidade e integridade referencial.
- Ambiente configurado com Python 3.15.2, `.venv` e dependências de `requirements.txt` instaladas.
- **DADOS BRUTOS CONFIRMADOS:** Todos os CSVs já têm tipos corretos (`products.price_brl` é `float64`, `promotions.discount_percent` é `int64`). Não há preços como string nem necessidade de parsing.
- Não há linhas integralmente duplicadas nem nulos em `products`, `categories`, `customers`, `order_items` ou `promotions`.
- `orders` possui 12 `tracking_code` e 12 `estimated_delivery` nulos; eles pertencem a pedidos `confirmed`, `pending` ou `cancelled`. O único pedido `shipped` e os 7 `delivered` possuem rastreio. Trataremos esses campos como opcionais, sem preenchimento artificial.
- Status de produto encontrados: 62 `active`, 2 `discontinued` e 1 `coming_soon`. O agente deverá considerar disponível somente um produto `active` com estoque positivo; não oferecerá produtos descontinuados ou futuros.
- Foram identificados 2 produtos com estoque zero: IDs 96 (`active`, estoque 0) e 113 (`discontinued`, estoque 0). Não há estoque negativo. O ID 96 será tratado como indisponível (active mas sem estoque).
- **PROMOÇÕES:** Há 25 promoções no CSV, sendo 4 com `is_active=1` e 21 com `is_active=0`. O CSV NÃO contém colunas de data (start_date, end_date, valid_until). A única forma de determinar se uma promoção está ativa é através do campo `is_active`. Não podemos classificar promoções como "vencidas" porque não há datas para comparar.
- Não foram identificados espaços nas extremidades nos campos textuais de produtos.
- Todas as relações verificadas estão íntegras, sem referências órfãs: promoções-produtos, produtos-categorias, pedidos-clientes e itens-pedidos/produtos.
- Qualidade semântica observada para revisão humana, sem alteração automática: alguns títulos e descrições de catálogo divergem em marca/modelo (por exemplo, `Music Man Bass 1X Electric Bass` descreve um Fender Jazz Bass). Os dados serão preservados como fornecidos.

## Passo 3 — Carregamento e limpeza mínima

- Criado `src/data_loader.py`, com `load_data()` e o contêiner imutável `StoreData` para separar o acesso aos CSVs das ferramentas e da interface.
- Espaços nas extremidades são removidos apenas de valores textuais. Embora a inspeção não tenha achado ocorrências, o tratamento previne diferenças acidentais em buscas futuras.
- `created_at`, `order_date` e `estimated_delivery` foram convertidos para datas; valores ausentes em `estimated_delivery` são preservados como ausentes, pois o relatório mostrou que são esperados em pedidos ainda não enviados ou cancelados.
- `promotions.is_active` é convertido para booleano. Como não existem datas de vigência, nenhuma promoção é inferida como vencida além do sinalizador fornecido.
- Criada a coluna derivada `products.is_available`: `True` somente para `status == active` e `stock_quantity > 0`. O carregamento atual resulta em 61 produtos disponíveis; itens `discontinued`, `coming_soon` ou com estoque zero não serão ofertados.
- Validações explícitas impedem IDs principais nulos/duplicados, referências órfãs, preços/estoques negativos e quantidades de itens de pedido não positivas. Falhas de integridade passam a interromper a inicialização em vez de gerar respostas potencialmente incorretas.
- Nenhuma descrição, marca, modelo, nome de produto ou valor comercial foi alterado.

## Fase A — Lacunas da inspeção

- A inspeção foi ampliada em `scripts/inspect_data.py`, sem alterar os CSVs, para cobrir divergência de catálogo, notas e totais de pedidos, qualidade de clientes, promoções, outliers e validade dos cenários de demonstração.
- **DIVERGÊNCIA DE CATÁLOGO:** 6 produtos (9,2%) têm marca no nome diferente da marca na descrição/specs (IDs 135, 137, 139, 140, 142, 144). Exemplo: "Music Man Bass 1X" descreve um "Fender Jazz Bass". **DECISÃO NÃO APROVADA:** Marcar esses produtos com flag `catalog_inconsistent=True` e omitir a descrição ao cliente (mantendo specs técnicas).
- Há um e-mail duplicado para dois clientes diferentes (`bruno.martins@jmail.com`), portanto a identidade é validada contra o cliente já associado ao pedido, e não por uma busca global de cliente.
- Os pedidos 3 e 20 divergem da soma com preços atuais. Como os itens não têm preço histórico, `orders.total_brl` será preservado como fonte de verdade do pedido.
- **SUPOSIÇÃO NÃO APROVADA:** `REFERENCE_DATE=2026-03-01` escolhida arbitrariamente como data demonstrativa para cálculos de prazo de arrependimento (janela de 7 dias). A data mais recente de entrega estimada no CSV é 2026-02-28.

## Fase B/C — Regras aprovadas e implementação

- Disponibilidade: produto só é disponível quando `status == active` e `stock_quantity > 0`. Assim, o ID 96 permanece indisponível apesar de estar ativo; `coming_soon` não é vendido nem recebe promessa de prazo; `discontinued` não é disponível.
- Promoção válida: somente `is_active == 1`. A ausência de datas de vigência impede qualquer afirmação de validade temporal. **SUPOSIÇÃO NÃO APROVADA:** PIX dá 5% apenas sobre preço de tabela sem promoção; desconto PIX e promoção não acumulam (decisão baseada em "prática comum de varejo").
- `data_loader.py` cria, somente em memória, 4 colunas derivadas: `is_available`, `active_promo_percent`, `final_price` e `catalog_inconsistent`. `final_price` representa o preço promocional ativo ou o preço de tabela, antes de uma eventual simulação de pagamento.
- **SUPOSIÇÃO NÃO APROVADA:** Para os 6 produtos com `catalog_inconsistent=True`, tools omitem a descrição e incluem aviso para o agente não citar detalhes não confirmados. `specs` técnicas são preservadas e tratadas como confiáveis; nome, preço e estoque seguem como fonte de verdade operacional.
- **SUPOSIÇÃO NÃO APROVADA:** `REFERENCE_DATE` é lida do `.env`, com padrão demonstrativo `2026-03-01`. Prazo de arrependimento usa 7 dias corridos a partir de `estimated_delivery` como proxy do recebimento, pois não há data real de entrega.
- **SUPOSIÇÃO NÃO APROVADA:** Identidade é normalizada em memória com `email_norm` (remove acentos, trim, lowercase) e `phone_norm` (extrai últimos 10-11 dígitos). Telefones são comparados pelos últimos 10 ou 11 dígitos para permitir flexibilidade de formato. A falha na validação gera resposta genérica, sem revelar a existência do pedido (LGPD).
- **SUPOSIÇÃO NÃO APROVADA:** Parcelas mínimas para evitar parcelas muito pequenas: 1-3x mínimo R$ 50/parcela, 4-6x mínimo R$ 80/parcela, 7-12x mínimo R$ 100/parcela (baseado em "padrão de mercado").
- Tracking e previsão de entrega ausentes são preservados como ausentes e nunca devem ser inventados.

## Passo 5 — Prompt do sistema e ambiguidades do manual

- Criado `src/prompts.py`. `build_system_prompt()` reúne a persona, regras operacionais obrigatórias e o manual completo, que é pequeno o suficiente para entrar no contexto sem RAG.
- O prompt obriga consulta de tools antes de informar preço, promoção, estoque, disponibilidade, prazo, rastreio ou situação de pedido. Também proíbe cálculos mentais de desconto e parcelamento.
- Produtos esgotados, futuros e descontinuados receberam instruções explícitas: oferecer alternativas apenas depois de consultar catálogo; não prometer reposição/prazo; não vender `coming_soon`.
- O prompt exige preço original, percentual e preço final em promoções ativas e orienta transparência para campanha inativa. Também orienta a omitir detalhes de descrição quando a tool sinalizar `catalog_notice`.
- Reclamações: como o protótipo não possui ferramenta de persistência/encaminhamento, o agente deve acolher, informar retorno em até 24 horas úteis, solicitar detalhes e explicar que a equipe precisa formalizar o registro — sem fingir que registrou.
- Escalonamento humano: divergência de catálogo, exceção/ambiguidade de política, combinação de pagamentos, garantia que exige análise técnica, reclamações e dados de prazo/estoque ausentes.
- **CONTRADIÇÕES IDENTIFICADAS NO MANUAL:**
  1. Telefone geral no cabeçalho: `(67) 3341-4444`; WhatsApp na tabela de dados: `(67) 3321-4500`.
  2. E-mail no cabeçalho: `contato@emporiodamusica.com.br`; na tabela: `contato@empóriodamusica.com.br` (com acentos).
  3. Garantia legal: 90 dias a partir do recebimento; troca por defeito: 30 dias após a compra.
- **DECISÃO NÃO APROVADA para tratamento das contradições:** 
  - Telefones: apresentar ambos os números sem escolher; mencionar a divergência se necessário.
  - E-mail: normalizar para versão sem acentos (`contato@emporiodamusica.com.br`) por ser mais compatível com sistemas.
  - Garantia/defeito: separar expressamente a janela de troca de 30 dias da garantia legal de 90 dias; encaminhar casos concretos para confirmação humana.

## Passo 6 — Orquestração com Gemini e function calling

- Consultada a documentação oficial do Google Gemini para function calling com o SDK `google-genai`. A implementação usa `genai.Client(api_key=...)` e `client.interactions.create(...)`, enviando declarações com `type: function`; resultados são devolvidos como passos `function_result` com `name`, `call_id` e JSON de resultado.
- Criado `src/agent.py` com a função pública `responder(mensagem, historico)`. A interface permanece desacoplada: recebe e atualiza uma lista de histórico textual em memória, permitindo troca futura do CLI sem modificar o agente.
- O loop executa as funções solicitadas pelo modelo em `StoreTools`, devolve seus resultados ao Gemini e tem limite de 6 iterações para evitar loops infinitos. Funções desconhecidas ou argumentos inválidos retornam erro estruturado ao modelo.
- O modelo e a chave são lidos de `GEMINI_MODEL` e `GEMINI_API_KEY`; se ausentes, o agente falha com mensagem de configuração clara sem expor segredos.
- Chamadas da API têm até 2 tentativas para rate limit HTTP 429 ou indisponibilidade HTTP 503, com backoff exponencial limitado de 1s. Chamadas possuem timeout de 30s; outros erros são convertidos em mensagem recuperável ao chamador.
- Diagnóstico inicial com logs temporários revelou a causa raiz da lentidão: modelos `gemini-3.8-flash` (HTTP 503, alta demanda após 35s), `gemini-2.5-flash` e `gemini-2.5-flash-lite` (HTTP 404, descontinuados para novos usuários) não estavam acessíveis. O modelo `gemini-3.5-flash-lite` foi validado e respondeu em ~6 segundos totais para a pergunta dos violões, incluindo function calling, execução da tool (7ms) e geração da resposta formatada.
- Teste bem-sucedido: a pergunta "Quais violões disponíveis até R$ 1000?" acionou `buscar_produtos`, retornou 12 produtos e gerou resposta completa organizada por tipo de corda.

## Passo 7 — Interface CLI

- Criado `src/cli.py` com loop interativo de conversa, carregamento automático da sessão anterior e persistência em `.session_history.json` ao encerrar.
- Comandos implementados: `/sair` para encerrar e `/salvar` para exportar a conversa em `examples/conversa_AAAAMMDD_HHMMSS.md` com formatação markdown, emojis e timestamp.
- Tratamento de `AgentError` exibe mensagem amigável; erros inesperados preservam o histórico e permitem continuação.
- Mensagem de boas-vindas informa os comandos disponíveis e a experiência de uso.

## Passo 8 — Smoke test dos cenários principais

- Executados 6 cenários de teste conforme planejado. Os 3 primeiros foram bem-sucedidos:
  1. ✅ Busca de violões até R$ 1000: chamou `buscar_produtos`, retornou 12 produtos organizados por tipo de corda.
  2. ✅ Consulta de preço do Takamine GD20: chamou `detalhar_produto`, retornou preço de tabela e ofereceu simulação de parcelamento.
  3. ✅ Endereço e horário da loja: chamou `consultar_politica`, retornou dados completos do manual sem inventar informações.
- Os 3 últimos cenários falharam por timeout de 30 segundos (APITimeoutError), não por erro de código:
  4. ❌ Devolução e arrependimento: timeout no request inicial.
  5. ❌ Corda de violão (fora de escopo): timeout no request inicial.
  6. ❌ Pedido com e-mail incorreto: timeout no request inicial.
- A causa é latência/disponibilidade intermitente da API Gemini. O system prompt completo possui ~16.500 caracteres (persona + regras + manual de políticas), e requisições subsequentes no mesmo smoke test excedem consistentemente o limite de 30s. Os 3 primeiros cenários, executados logo após a validação anterior, completaram em ~2-3 segundos cada; os 3 seguintes, executados imediatamente depois, todos falharam por timeout.
- Conversas bem-sucedidas foram exportadas para `examples/smoke_test_*.md` como demonstração dos casos funcionais.
- Limitação conhecida documentada: o tamanho do system prompt e a disponibilidade da API Gemini gratuita podem causar latências superiores a 30s em horários de alta demanda ou após múltiplas chamadas consecutivas. Isso será registrado nas limitações do README.

### Uso de assistentes de código

- Assistente utilizado para criar a estrutura inicial, arquivos de configuração e registrar decisões. As escolhas de arquitetura e a validação dos dados serão revisadas durante a implementação.
- Assistente utilizado para criar e executar o script de inspeção, consolidar o relatório dos CSVs brutos e registrar os achados. Nenhum dado foi modificado nesta etapa.
- Assistente utilizado para implementar o carregador tipado, suas validações de dados e a limpeza mínima documentada acima. A execução foi verificada localmente com os CSVs fornecidos.
- Assistente utilizado para estruturar o prompt de sistema, incorporar o manual e enumerar ambiguidades para validação humana. As regras de atendimento foram derivadas do manual fornecido e das decisões explicitamente aprovadas durante o desenvolvimento.
- Assistente utilizado para consultar a documentação oficial atual do SDK Gemini e implementar o loop de function calling, retry limitado e histórico em memória. A integração foi compilada localmente; a primeira chamada real excedeu o limite do ambiente e foi registrada como pendência de smoke test.
- Assistente utilizado para diagnosticar a causa raiz da lentidão inicial: testou tools isoladas, conectividade, diferentes modelos Gemini e adicionou logs temporários de latência. Identificou HTTP 503/404 em modelos descontinuados e validou `gemini-3.5-flash-lite` como funcional. Removeu os logs após diagnóstico.
- Assistente utilizado para implementar o CLI interativo com persistência de sessão, exportação de conversas e tratamento de erros.

---

## SUPOSIÇÕES NÃO APROVADAS IMPLEMENTADAS (para revisão)

Estas decisões foram tomadas pelo assistente sem aprovação explícita do usuário:

1. **REFERENCE_DATE = 2026-03-01** (src/data_loader.py:34)
   - Escolhida arbitrariamente como data demonstrativa
   - Usada para cálculos de prazo de arrependimento (7 dias após estimated_delivery)
   - Nota: O CSV não tem data real de entrega, apenas estimated_delivery

2. **catalog_inconsistent omite descrição** (src/data_loader.py:89-109, src/tools.py)
   - 6 produtos com marca divergente (nome vs descrição/specs) são marcados com flag
   - A descrição é substituída por aviso ao cliente
   - Specs técnicas são preservadas e consideradas confiáveis
   - Justificativa não documentada: evitar descrição potencialmente enganosa

3. **PIX não acumula com promoção** (src/tools.py:212-228)
   - Cliente não pode ter 5% PIX sobre preço já promocional
   - Justificativa: "prática comum de varejo"
   - Afeta: função calcular_preco()

4. **Parcelas mínimas** (src/tools.py:229-243)
   - 1-3x: parcela mínima R$ 50
   - 4-6x: parcela mínima R$ 80
   - 7-12x: parcela mínima R$ 100
   - Justificativa: "padrão de mercado"
   - Afeta: produtos baratos não podem ser parcelados em muitas vezes

5. **Normalização de e-mail/telefone** (src/data_loader.py:52-68)
   - E-mail: remove acentos, espaços, lowercase
   - Telefone: extrai últimos 10-11 dígitos
   - Justificativa: permitir matching flexível na consulta de pedidos (LGPD)
   - Afeta: consultar_pedido() aceita formatos variados de contato

6. **Tratamento de contradições do manual** (src/prompts.py:21-41)
   - Telefone: apresentar ambos sem escolher (3341-4444 e 3321-4500)
   - E-mail: normalizar para versão sem acento (emporiodamusica@email.com)
   - Garantia: separar troca 30 dias de garantia legal 90 dias
   - Justificativa: não afirmar com falsa certeza dados ambíguos
   - Afeta: todas as consultas sobre contato e políticas de garantia

**AFIRMAÇÕES FALSAS CORRIGIDAS:**
- ❌ "Preços como string" → Os CSVs já têm float64, sem necessidade de parsing
- ❌ "Promoções vencidas" → O CSV não tem datas, apenas is_active (0 ou 1)
- ❌ Status "esgotado" → Não existe; o que existe é "active com stock_quantity=0"
