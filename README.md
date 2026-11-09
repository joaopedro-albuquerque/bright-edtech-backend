<div align="center">

# Bright EdTech API

**API que sustenta a plataforma de estudo: organização de PDFs, geração de material com IA e agendamento de revisões.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-ECS%20%7C%20RDS%20%7C%20S3%20%7C%20Cognito-FF9900?logo=amazonaws&logoColor=white)
![Testes](https://img.shields.io/badge/testes-592%20passando-2EA44F)
![Cobertura](https://img.shields.io/badge/cobertura-100%25-2EA44F)

[Acessar a plataforma](https://brightedtech.com.br) · [Repositório do front-end](https://github.com/joaopedro-albuquerque/bright-edtech-frontend) · [Referência da API](.context/api-reference.md)

<img src="docs/img/demo.gif" alt="Demonstração da plataforma: pastas, busca, revisão e estudo de flashcards" width="860">

</div>

## Índice

- [Sobre](#sobre)
- [O que a API oferece](#o-que-a-api-oferece)
- [Como funciona](#como-funciona)
- [Arquitetura](#arquitetura)
- [Modelagem de dados](#modelagem-de-dados)
- [Revisão espaçada](#revisão-espaçada)
- [Endpoints](#endpoints)
- [Segurança](#segurança)
- [Tecnologias](#tecnologias)
- [Qualidade](#qualidade)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Executando localmente](#executando-localmente)
- [Documentação técnica](#documentação-técnica)

## Sobre

A Bright EdTech é uma plataforma para quem estuda a partir de documentos. O estudante envia um PDF e recebe resumos, flashcards e quizzes do próprio material, com as revisões agendadas por repetição espaçada.

Este repositório contém o **back-end**: as rotas HTTP, as regras de negócio, a integração com IA e a infraestrutura como código. A interface está no [repositório do front-end](https://github.com/joaopedro-albuquerque/bright-edtech-frontend).

## O que a API oferece

| Recurso | Descrição |
|---|---|
| Documentos | Envio de PDFs com verificação de formato, tamanho e conteúdo; organização em pastas e subpastas; busca por nome; visualização do arquivo |
| Resumos | Três formatos: Executivo, Cornell e Fichamento acadêmico, com download em PDF |
| Flashcards e quizzes | Geração a partir do documento, com quantidade e dificuldade configuráveis |
| Revisão espaçada | Agenda cada item pelo algoritmo SM-2 e lista o que está atrasado, agrupado por documento |
| Perfil e conta | Cadastro, onboarding, aceite dos termos e exclusão completa da conta |

## Como funciona

```mermaid
flowchart LR
  A["Upload do PDF"] --> B["Verificação<br/>formato, tamanho e conteúdo"]
  B --> C["Arquivo no S3<br/>registro no PostgreSQL"]
  C --> D["Geração por IA<br/>resumo, flashcards ou quiz"]
  D --> E["Conteúdo no S3<br/>estado de revisão no PostgreSQL"]
  E --> F["Revisão espaçada"]
```

O banco de dados guarda os metadados e o estado de revisão de cada item. O conteúdo textual dos materiais gerados fica no S3 e é combinado com o estado de revisão na hora de responder, por meio de um identificador de item (`item_ref`).

## Arquitetura

O back-end é uma aplicação FastAPI executada em contêiner no Amazon ECS (Fargate), atrás de um Application Load Balancer. O front-end é estático, servido por CloudFront a partir de um bucket S3 privado.

```mermaid
flowchart LR
  U["Navegador<br/>SPA React"] -->|"HTTPS"| CF["CloudFront"]
  CF --> FS[("S3 privado<br/>front-end")]
  U -->|"login"| CG["Amazon Cognito"]
  U -->|"JWT"| ALB["Application<br/>Load Balancer"]
  ALB --> API["API FastAPI<br/>ECS Fargate"]
  API --> DB[("PostgreSQL<br/>Amazon RDS")]
  API --> DS[("S3<br/>documentos e conteúdo gerado")]
  API --> IA["IA generativa"]
  API --> SSM["Parameter Store<br/>credenciais"]
```

A aplicação segue uma arquitetura em camadas:

```mermaid
flowchart TB
  M["Middlewares<br/>identificador de requisição, CORS e autenticação JWT"] --> R["Routers<br/>rotas REST por domínio"]
  R --> S["Services<br/>regras de negócio, IA, SM-2 e geração de PDF"]
  S --> P["Repositories<br/>acesso ao PostgreSQL"]
  S --> X["Integrações<br/>S3 e IA generativa"]
```

A infraestrutura é descrita em CloudFormation (`cloudformation/`) e implantada por workflows manuais do GitHub Actions.

## Modelagem de dados

```mermaid
erDiagram
  USUARIOS ||--o{ PASTAS : possui
  PASTAS ||--o{ PASTAS : "contém subpastas"
  PASTAS ||--o{ DOCUMENTOS : agrupa
  USUARIOS ||--o{ DOCUMENTOS : envia
  DOCUMENTOS ||--o{ RESUMOS : gera
  DOCUMENTOS ||--o{ FLASHCARDS : gera
  DOCUMENTOS ||--o{ QUIZZES : gera
  FLASHCARDS ||--o{ CARTOES : contém
  QUIZZES ||--o{ QUESTOES : contém

  USUARIOS {
    uuid id PK
    string email
    string cognito_id
    boolean tour_concluido
    timestamp termos_aceitos_em
  }
  PASTAS {
    uuid id PK
    uuid usuario_id FK
    uuid pasta_pai_id FK
    string nome
  }
  DOCUMENTOS {
    uuid id PK
    uuid usuario_id FK
    uuid pasta_id FK
    string nome
    string status
  }
  RESUMOS {
    uuid id PK
    uuid documento_id FK
    string titulo
    string modelo_ia
  }
  FLASHCARDS {
    uuid id PK
    uuid documento_id FK
    string titulo
  }
  CARTOES {
    uuid id PK
    uuid flashcard_id FK
    string item_ref
    int intervalo_atual
    int repeticoes
    timestamp proxima_revisao
  }
  QUIZZES {
    uuid id PK
    uuid documento_id FK
    string titulo
  }
  QUESTOES {
    uuid id PK
    uuid quiz_id FK
    string item_ref
    int intervalo_atual
    int repeticoes
    timestamp proxima_revisao
  }
```

Todas as tabelas de conteúdo também referenciam `usuario_id`, o que permite filtrar cada consulta pelo dono do recurso. O esquema completo está em [`schema.sql`](schema.sql).

## Revisão espaçada

Cada cartão e cada questão guarda o fator de facilidade, o intervalo atual, o número de repetições e a data da próxima revisão. O algoritmo SM-2 recalcula esses valores a cada avaliação.

```mermaid
flowchart LR
  A["Itens com revisão vencida"] --> B["Avaliação<br/>de 1 a 5"]
  B --> C{"Lembrou?"}
  C -- "sim" --> D["Intervalo cresce"]
  C -- "não" --> E["Intervalo reinicia"]
  D --> F["Agenda a próxima revisão"]
  E --> F
  F --> A
```

## Endpoints

A documentação interativa (Swagger) fica em `/docs`. A referência completa, com exemplos, está em [`.context/api-reference.md`](.context/api-reference.md).

| Grupo | Exemplos |
|---|---|
| Perfil | `POST /profile`, `GET /profile`, `PUT /profile/{id}`, `DELETE /profile/{id}` |
| Pastas | `POST /pastas`, `GET /pastas/user/{id}`, `GET /pastas/{id}/conteudo` |
| Documentos | `POST /documentos/upload`, `GET /documentos`, `GET /documentos/{id}/url-visualizacao` |
| Resumos | `POST /documentos/{id}/resumos`, `GET /resumos/{id}/conteudo`, `GET /resumos/{id}/pdf` |
| Flashcards | `POST /documentos/{id}/flashcards`, `GET /flashcards/{id}/conteudo` |
| Quizzes | `POST /documentos/{id}/quizzes`, `GET /quizzes/{id}/conteudo` |
| Revisões | `GET /revisoes/hoje`, `GET /revisoes/lotes`, `PUT /revisoes/cartoes/{id}/avaliar` |

## Segurança

- **Autenticação:** cadastro e login pelo Amazon Cognito; o token JWT é validado em todas as rotas.
- **Isolamento por usuário:** toda consulta é filtrada pelo dono do recurso, e o identificador informado na requisição é conferido com o do token.
- **Verificação do conteúdo enviado:** o arquivo é validado e analisado antes de ser aceito.
- **Dados:** arquivos em bucket privado com criptografia, banco em sub-rede privada sem endereço público e credenciais no Parameter Store.
- **Exclusão de conta:** remove os dados do banco e os arquivos armazenados.

## Tecnologias

| Área | Tecnologias |
|---|---|
| Linguagem e framework | Python 3.12, FastAPI, Pydantic v2 |
| Banco de dados | PostgreSQL (Amazon RDS) |
| IA generativa | Modelos de linguagem via serviço gerenciado |
| Autenticação | Amazon Cognito |
| Infraestrutura | ECS Fargate, RDS, S3, CloudFront, CloudFormation |
| CI/CD | GitHub Actions |
| Testes | pytest, pytest-cov, pytest-mock |

## Qualidade

A suíte tem 592 testes automatizados, com 100% de cobertura de linhas e de ramos. As dependências externas (banco, S3 e IA) são simuladas, então os testes rodam sem credenciais.

```bash
pip install -r requirements-dev.txt
pytest
```

## Estrutura do projeto

```
app/
├── api/           # rotas HTTP e middlewares
├── core/          # configuração, banco, autenticação e exceções
├── services/      # regras de negócio, IA, S3, SM-2 e geração de PDF
├── repositories/  # acesso ao PostgreSQL
├── schemas/       # modelos de entrada e saída
└── main.py
cloudformation/    # infraestrutura como código
tests/             # testes automatizados
schema.sql         # esquema do banco
.context/          # documentação técnica
```

## Executando localmente

Requisitos: Python 3.12 e PostgreSQL com o [`schema.sql`](schema.sql) aplicado.

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

# crie um .env na raiz com as credenciais do banco, do S3 e da IA
uvicorn app.main:app --reload --port 8000
```

A documentação interativa fica em `http://localhost:8000/docs`.

## Documentação técnica

- [Visão geral do produto](.context/visao-geral.md)
- [Arquitetura](.context/arquitetura.md)
- [Modelo de dados](.context/dados.md)
- [Referência da API](.context/api-reference.md)

---

<sub>Projeto acadêmico do curso de Análise e Desenvolvimento de Sistemas do Instituto Federal de São Paulo (IFSP). Conteúdos gerados por inteligência artificial podem conter imprecisões e devem ser conferidos com o material original.</sub>
