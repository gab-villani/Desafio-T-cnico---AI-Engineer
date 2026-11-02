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

### Uso de assistentes de código

- Assistente utilizado para criar a estrutura inicial, arquivos de configuração e registrar decisões. As escolhas de arquitetura e a validação dos dados serão revisadas durante a implementação.
- Assistente utilizado para criar e executar o script de inspeção, consolidar o relatório dos CSVs brutos e registrar os achados. Nenhum dado foi modificado nesta etapa.
