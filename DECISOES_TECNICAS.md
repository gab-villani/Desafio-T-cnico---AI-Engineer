# Decisões Técnicas e Justificativas

Este documento explica por que o projeto usa os métodos e tecnologias atuais, quais alternativas foram consideradas e quais suposições devem ser revistas antes de qualquer uso em produção.

## 1. Arquitetura do agente: function calling do Gemini com ferramentas determinísticas em Python

O Gemini interpreta a solicitação do cliente e decide se deve chamar uma das ferramentas declaradas. A aplicação executa a função Python escolhida e devolve o resultado ao modelo, que então prepara a resposta destinada ao cliente.

Essa divisão foi escolhida porque a compreensão de linguagem natural se beneficia de um LLM, enquanto preço, disponibilidade, consulta de pedidos e validação de identidade devem vir dos dados e das regras fornecidas. Manter essas operações no Python torna o comportamento inspecionável e testável e evita pedir ao modelo que invente ou calcule informações operacionais.

O conjunto de ferramentas é explícito e limitado a busca de produtos, detalhes de produto, promoções ativas, cálculo de preço, consulta de pedido e consulta de políticas. A consulta de pedido exige que e-mail ou telefone corresponda ao cliente vinculado ao pedido; a falha retorna uma mensagem genérica que não confirma se o pedido existe.

O loop é limitado a seis iterações de chamada de ferramentas. Erros selecionados de limite de uso ou indisponibilidade temporária (429/503) recebem no máximo duas tentativas pela aplicação, com um pequeno backoff exponencial; cada solicitação ao Gemini tem timeout de 60 segundos. Esses limites são medidas de resiliência, não uma garantia de disponibilidade.

### Por que não um agente ReAct totalmente autônomo?

O protótipo tem um conjunto pequeno e conhecido de operações de atendimento. Um esquema explícito de funções e uma orquestração limitada tornam as ações permitidas mais fáceis de avaliar do que um planejador aberto com ações escolhidas dinamicamente.

## 2. Provedor e SDK do modelo: Google Gemini via `google-genai`

A API do Gemini e o SDK oficial `google-genai` foram escolhidos para oferecer um modelo hospedado com suporte a function calling. A credencial do provedor e o identificador do modelo são configurações, não constantes no código-fonte, permitindo trocar o modelo sem editar a implementação do agente.

A escolha também evita exigir hardware para modelos locais ou infraestrutura própria para este protótipo de avaliação. Em contrapartida, há dependências externas: chave de API, rede, cota, disponibilidade do provedor e latência potencialmente variável. Antes de escolher um provedor e modelo para produção, devem ser avaliados custo, privacidade, retenção de dados, latência e níveis de serviço.

## 3. Dados estruturados: arquivos CSV carregados com pandas

Os dados operacionais fornecidos são um conjunto pequeno e finito de tabelas estruturadas em CSV. O pandas permite filtragens e junções diretas sem introduzir um serviço de banco de dados ou uma camada de geração de consultas.

`data_loader.py` centraliza a leitura e o preparo em memória. Remove espaços das extremidades do texto, converte colunas de data, deriva campos de disponibilidade e preço promocional, normaliza valores de contato para comparação e valida identificadores, referências e restrições numéricas básicas. Os arquivos CSV de origem não são regravados.

### Por que não text-to-SQL ou banco de dados?

O conjunto é pequeno e já foi fornecido em CSV; carregá-lo localmente é simples e evita erros de geração de consultas, configuração de banco e infraestrutura desnecessária. Se o volume crescer, os dados mudarem frequentemente ou houver necessidade de escrita concorrente, um banco de dados com controle explícito de acesso e migrações seria uma fonte da verdade mais adequada.

### Por que não RAG ou banco vetorial para as políticas?

O manual de políticas é um documento Markdown compacto. Ele pode ser incluído diretamente no contexto do sistema, enquanto `consultar_politica` extrai uma seção nomeada para uma consulta direcionada. Para esse volume e conteúdo, embeddings e um banco vetorial acrescentariam complexidade sem benefício de recuperação demonstrado. Uma base de conhecimento maior ou atualizada frequentemente poderia justificar um sistema de recuperação com citações de fonte e avaliação.

## 4. Regras de negócio implementadas no código

As ferramentas Python calculam preços e parcelas, aplicam filtros de disponibilidade, validam entradas de pagamento e verificam a identidade para consulta de pedidos. O modelo recebe os resultados e os explica; suas instruções proíbem calcular descontos ou parcelas mentalmente ou apresentar informações operacionais sem um resultado de ferramenta.

Esse desenho mantém os cálculos reproduzíveis e coloca as regras em funções que podem ser cobertas por testes unitários. Isso não torna as suposições atuais regras oficiais: decisões como acumular ou não promoções e definir valores mínimos de parcelas devem ser confirmadas pela loja antes de uso real.

## 5. Prompt e ambiguidades das políticas

`prompts.py` combina uma persona estável e instruções operacionais com o manual de políticas da loja. O prompt exige uso de ferramenta para preços, estoque, status de pedido, entrega, promoções e dúvidas sobre políticas. Também aborda solicitações fora de escopo, inconsistências do catálogo, privacidade, reclamações e afirmações conflitantes no manual.

As informações conflitantes sobre telefone, e-mail e garantia não são resolvidas silenciosamente pelo agente. Quando a fonte é ambígua, o comportamento esperado é ser transparente e oferecer confirmação com uma pessoa da equipe. O prompt não substitui a correção do manual de origem; os dados oficiais devem ser confirmados pela empresa.

## 6. Interfaces e persistência

A função central `responder` é independente das interfaces. Assim, CLI e UI Streamlit usam o mesmo comportamento do agente sem duplicar regras de negócio.

- **CLI:** adequada a um fluxo mínimo e direto de avaliação. O histórico da sessão é salvo localmente em `.session_history.json`; `/salvar` exporta a conversa para `examples/`.
- **Streamlit:** oferece chat simples no navegador, seletor de idioma, criação de nova conversa e carregamento de conversas salvas. Os arquivos da UI ficam localmente em `chat_history/`.

Esses mecanismos de persistência são próprios de um protótipo local, não de armazenamento multiusuário. Não oferecem autenticação, controle de acesso, garantias de criptografia em repouso, política de retenção nem coordenação entre usuários concorrentes.

## 7. Salvaguardas de qualidade de dados e suposições explícitas

- Disponibilidade exige status ativo e estoque positivo. Um produto ativo sem estoque não é oferecido como disponível.
- As promoções dependem do campo `is_active` porque o CSV não possui datas de início ou fim.
- Foram identificados seis itens do catálogo com divergência entre o nome do produto e seu texto descritivo. O carregador os sinaliza e as ferramentas omitem a descrição, retornando um aviso. Essa é uma escolha conservadora de apresentação, não uma correção dos dados de origem.
- `estimated_delivery` não comprova o recebimento real. Orientações de devolução baseadas nela são, portanto, aproximadas.
- A comparação de e-mail e telefone normaliza a formatação para tornar a validação prática. A resposta genérica em caso de falha reduz a divulgação da existência do pedido, mas este protótipo não é um sistema completo de autenticação.
- Na implementação, o desconto PIX não acumula com promoção. Os mínimos de parcela são R$ 50 para 1–3 parcelas, R$ 80 para 4–6 e R$ 100 para 7–12. Essas suposições precisam de aprovação da empresa; o próprio manual contém regras de pagamento que se sobrepõem.
- `REFERENCE_DATE` tem padrão `2026-03-01` para comportamentos relacionados a datas. Defina-a explicitamente para avaliações reproduzíveis; não trate o padrão como relógio atual.

## 8. Resumo das tecnologias

| Área | Escolha | Motivo |
|---|---|---|
| Linguagem | Python | Exigência do desafio e adequada a dados e integrações. |
| LLM | Google Gemini | Modelo hospedado com capacidade de function calling. |
| SDK | `google-genai` | Integração Python oficial com a API Gemini. |
| Dados tabulares | pandas e CSV | Processamento local simples para o conjunto pequeno fornecido. |
| Configuração | `python-dotenv` | Carrega credenciais e configurações de execução de `.env`. |
| Interface web | Streamlit | Chat web mínimo sem uma stack de frontend separada. |
| Consulta de políticas | Markdown no prompt e extração por tópico | Suficiente para um manual compacto e estável. |
| Persistência de conversa | Arquivos JSON locais | Persistência simples para protótipo; não voltada à produção multiusuário. |

## 9. Melhorias antes de produção

Antes de qualquer uso em produção, é preciso confirmar as suposições comerciais e resolver as contradições da fonte de políticas; substituir arquivos locais por dados operacionais aprovados e com controle de acesso; implementar autenticação e autorização adequadas para dados de clientes; adicionar observabilidade e logs que preservem a privacidade; avaliar qualidade do modelo e resiliência contra prompt injection; e definir requisitos de latência, custo, retenção e disponibilidade.

