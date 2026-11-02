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
- Todos os CSVs foram lidos corretamente em UTF-8. Não foram encontrados valores textuais de preço: `products.price_brl` é `float64`.
- Não há linhas integralmente duplicadas nem nulos em `products`, `categories`, `customers`, `order_items` ou `promotions`.
- `orders` possui 12 `tracking_code` e 12 `estimated_delivery` nulos; eles pertencem a pedidos `confirmed`, `pending` ou `cancelled`. O único pedido `shipped` e os 7 `delivered` possuem rastreio. Trataremos esses campos como opcionais, sem preenchimento artificial.
- Status de produto encontrados: 62 `active`, 2 `discontinued` e 1 `coming_soon`. O agente deverá considerar disponível somente um produto `active` com estoque positivo; não oferecerá produtos descontinuados ou futuros.
- Foram identificados 2 produtos com estoque zero: IDs 96 (`active`) e 113 (`discontinued`). Não há estoque negativo. O ID 96 exige atenção porque seu status ativo conflita com a indisponibilidade por estoque.
- Há 25 promoções: 4 ativas e 21 inativas. O arquivo não contém datas de vigência; portanto, o sistema não pode classificar promoções como vencidas por data e deve usar exclusivamente `is_active`.
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
- Foram identificados 6 produtos com marca divergente entre nome e descrição/specs (IDs 135, 137, 139, 140, 142 e 144), equivalentes a 9,2% do catálogo.
- Há um e-mail duplicado para dois clientes diferentes (`bruno.martins@jmail.com`), portanto a identidade é validada contra o cliente já associado ao pedido, e não por uma busca global de cliente.
- Os pedidos 3 e 20 divergem da soma com preços atuais. Como os itens não têm preço histórico, `orders.total_brl` será preservado como fonte de verdade do pedido.
- A janela de datas sugere `REFERENCE_DATE=2026-03-01` como data demonstrativa: há entrega estimada em 2026-02-28 dentro do prazo de 7 dias e entregas anteriores fora dele.

## Fase B/C — Regras aprovadas e implementação

- Disponibilidade: produto só é disponível quando `status == active` e `stock_quantity > 0`. Assim, o ID 96 permanece indisponível apesar de estar ativo; `coming_soon` não é vendido nem recebe promessa de prazo; `discontinued` não é disponível.
- Promoção válida: somente `is_active == 1`. A ausência de datas de vigência impede qualquer afirmação de validade temporal. PIX dá 5% apenas sobre preço de tabela sem promoção; desconto PIX e promoção não acumulam.
- `data_loader.py` cria, somente em memória, `is_available`, `active_promo_percent`, `final_price` e `catalog_inconsistent`. `final_price` representa o preço promocional ativo ou o preço de tabela, antes de uma eventual simulação de pagamento.
- Para os 6 produtos de catálogo inconsistente, tools deverão omitir a descrição e incluir aviso para não citar detalhes não confirmados. Por decisão aprovada, `specs` continua disponível e é tratada como confiável; nome, preço e estoque seguem como fonte de verdade operacional.
- `REFERENCE_DATE` é lida do `.env`, com padrão demonstrativo `2026-03-01`. Prazo de arrependimento usa 7 dias corridos a partir de `estimated_delivery` como proxy do recebimento, pois não há data real de entrega. Esta é uma suposição explícita.
- Identidade é normalizada em memória com `email_norm` (trim/lower) e `phone_norm` (somente dígitos). Telefones são comparados pelos últimos 10 ou 11 dígitos. A falha deve gerar resposta genérica, sem revelar a existência do pedido.
- Tracking e previsão de entrega ausentes são preservados como ausentes e nunca devem ser inventados.

### Uso de assistentes de código

- Assistente utilizado para criar a estrutura inicial, arquivos de configuração e registrar decisões. As escolhas de arquitetura e a validação dos dados serão revisadas durante a implementação.
- Assistente utilizado para criar e executar o script de inspeção, consolidar o relatório dos CSVs brutos e registrar os achados. Nenhum dado foi modificado nesta etapa.
- Assistente utilizado para implementar o carregador tipado, suas validações de dados e a limpeza mínima documentada acima. A execução foi verificada localmente com os CSVs fornecidos.
