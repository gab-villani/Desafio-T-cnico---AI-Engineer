# Empório da Música — Agente de Atendimento

Protótipo em Python de um agente de atendimento por texto para a loja fictícia Empório da Música, em Campo Grande/MS. O agente usa o Google Gemini para interpretar solicitações e ferramentas determinísticas em Python para consultar catálogo, pedidos, preços e políticas da loja.

> **Idioma:** este é o README de apoio em português. O README principal está em [README.md](./README.md), inteiramente em inglês.

## Requisitos

- Python 3.11 ou superior
- Uma chave de API do Google Gemini e um identificador de modelo disponível para sua conta
- Acesso à internet para enviar solicitações ao Gemini

## Preparação

Execute os comandos a partir da raiz do repositório.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do repositório com as credenciais do Gemini:

```dotenv
GEMINI_API_KEY=sua_chave_de_api
GEMINI_MODEL=um_modelo_gemini_disponivel
REFERENCE_DATE=2026-03-01
```

`GEMINI_API_KEY` e `GEMINI_MODEL` são obrigatórios. Escolha um modelo atualmente disponível para sua conta do Google AI Studio; a disponibilidade pode mudar. `REFERENCE_DATE` é opcional e, se omitida, usa `2026-03-01`. Ela é usada pelas regras de negócio do protótipo relacionadas a datas.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Crie o mesmo arquivo `.env` na raiz do repositório.

## Executar a aplicação

### Interface de linha de comando

Inicie uma conversa em português:

```bash
python src/cli.py
```

Inicie uma conversa em inglês:

```bash
python src/cli.py --idioma en
```

A CLI também aceita `--idioma pt-BR`. Digite uma mensagem e pressione Enter. Use `/salvar` para exportar a conversa atual como Markdown em `examples/`, ou `/sair` para encerrar. A CLI salva o histórico da sessão em `.session_history.json`.

### Interface web

Inicie o Streamlit a partir da raiz do repositório:

```bash
streamlit run ui/app.py
```

Abra o endereço local exibido pelo Streamlit. O seletor de idioma na barra lateral alterna entre português (`pt-BR`) e inglês (`en`); a interface começa em português. A UI permite iniciar uma conversa nova e carregar conversas salvas em `chat_history/`.

## Executar os testes focados nas regras de dados

O teste abaixo verifica o carregamento de dados e regras de negócio determinísticas sem chamar a API Gemini:

```bash
python -m unittest discover -s tests -p test_data_rules.py
```

Outros testes podem fazer chamadas reais ao Gemini e exigem credenciais válidas, acesso à rede e cota de API disponível.

## Estrutura do projeto

```text
src/
  agent.py       Orquestração do Gemini, contexto da conversa e loop de tools
  cli.py         Interface de terminal e histórico da sessão
  data_loader.py Leitura dos CSVs, normalização, campos derivados e validações
  prompts.py     Instruções do agente e contexto das políticas da loja
  tools.py       Tools determinísticas para catálogo, pedidos, pagamento e políticas
ui/
  app.py         Interface de chat Streamlit e conversas salvas
data/
  *.csv          Produtos, categorias, clientes, pedidos, itens e promoções
  politicas_da_loja.md
                 Manual de políticas da loja
examples/        Exemplos de conversa e exportações feitas pela CLI
tests/           Testes de dados, privacidade, idioma e interface
```

## Decisões técnicas

O agente usa function calling do Gemini para escolher entre operações explícitas. O Python executa as consultas, validações, verificações de identidade e cálculos. Os CSVs são carregados com pandas; o manual de políticas entra no contexto do sistema e também pode ser consultado por tópico. O projeto não usa banco vetorial nem text-to-SQL porque os dados fornecidos são pequenos, estruturados e disponíveis localmente.

Para a justificativa detalhada, os trade-offs e as suposições, consulte:

- [Decisões técnicas em português](./DECISOES_TECNICAS.md)
- [Technical decisions in English](./TECHNICAL_DECISIONS.md)

## Comportamentos e limitações importantes

- Um produto só é considerado disponível quando `status == "active"` e o estoque é maior que zero.
- Apenas promoções marcadas como ativas nos dados são consideradas vigentes; o CSV de promoções não tem datas de validade.
- Os cálculos de preço e parcelamento são feitos em Python. As regras implementadas não acumulam o desconto de PIX com uma promoção ativa.
- Os detalhes de um pedido só são retornados quando o e-mail ou telefone informado corresponde ao cliente associado ao pedido. Falhas de validação recebem uma resposta genérica.
- As ferramentas omitem descrições de produtos com inconsistências de catálogo e retornam um aviso.
- A fonte de políticas contém dados conflitantes de contato e garantia. O prompt instrui o agente a não resolver esses conflitos silenciosamente e a recomendar confirmação quando necessário.
- O agente depende da API externa do Gemini. Rede, limites de uso, disponibilidade de modelos e latência do provedor podem afetar as respostas. O código tenta novamente algumas falhas temporárias e limita o loop de tools, mas não garante disponibilidade ou baixa latência.
- Este é um protótipo, não um serviço de produção. Não há integração com estoque em tempo real, pagamentos, transportadora, registro de reclamações ou ERP.

## Declaração sobre assistentes de IA

Assistência de IA (Kiro/Claude) foi usada na estrutura inicial, inspeção dos dados, implementação, testes e depuração do projeto. Os resultados foram revisados e afirmações iniciais incorretas foram corrigidas. As notas e auditorias registram essas correções e as suposições ainda não aprovadas.

