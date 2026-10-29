# API Reference — Bright EdTech (Detalhada)

Documentação completa de todas as rotas da API, com exemplos reais de request e response, feita para ser colada direto num prompt de IA (ou lida por um dev) e gerar a integração do frontend sem precisar abrir o código do backend.

> Fonte de verdade: [`app/api/routers/`](../app/api/routers/) + [`app/schemas/`](../app/schemas/). Se algo aqui divergir do código, o código vence — mas este arquivo é atualizado junto com qualquer mudança de rota (ver checklist no fim).

---

## Convenções gerais

- **Base URL (dev local):** `http://localhost:8000`
- **Base URL (produção):** `https://api.bright-edtech.com` (ver `REACT_APP_API_URL`)
- **Content-Type:** `application/json` em todas as rotas, exceto onde indicado (`multipart/form-data` para upload de arquivo, `application/x-www-form-urlencoded` para os `PUT` de renomear).
- **Autenticação:** duas camadas, ambas obrigatórias (exceto no health-check `GET /` e na documentação automática `/docs`, `/openapi.json`):
  1. **`Authorization: Bearer <token>` (JWT do Cognito) — exigido em TODA requisição.** Um middleware global (`app/core/auth_middleware.py`) valida a assinatura (RS256, via JWKS do Cognito), o emissor e a expiração do token antes de a requisição alcançar qualquer rota. Token ausente, malformado, expirado ou de outro Client/User Pool → `401` imediatamente, sem executar a rota.
  2. **`X-User-Id` (header)** — usado pela maioria das rotas de domínio para identificar de qual usuário (UUID da tabela `usuarios`) são os dados solicitados. **Obrigatório** em toda rota marcada como "🔒 Auth: X-User-Id" abaixo, além do Bearer token do item 1. Se ausente → `401`. Se não for um UUID válido → `400`.
  - Em `GET /profile` o Bearer token também é usado para identificar o usuário diretamente (via claim `sub`), sem precisar de `X-User-Id`.
- **Erros padrão:**
  - `401 Unauthorized` — token ausente/inválido: `{"detail": "Cabeçalho 'Authorization: Bearer <token>' é obrigatório."}` ou `{"detail": "Token de acesso inválido ou expirado."}`; ou falta `X-User-Id`: `{"detail": "Cabeçalho X-User-Id é obrigatório"}`
  - `400 Bad Request` — `X-User-Id` não é um UUID: `{"detail": "X-User-Id inválido"}`
  - `403 Forbidden` — rotas `/profile/{user_id}*` e `/pastas/user/{user_id}*`: `{"detail": "Acesso negado"}` quando o `user_id` do path não bate com o `X-User-Id`
  - `404 Not Found` — recurso não encontrado: `{"detail": "Documento não encontrado"}` (mensagem varia por recurso)
  - `422 Unprocessable Entity` — corpo da requisição não bate com o schema (validação do Pydantic). Formato padrão do FastAPI:
    ```json
    {
      "detail": [
        {
          "type": "greater_than_equal",
          "loc": ["body", "quantidade"],
          "msg": "Input should be greater than or equal to 1",
          "input": 0,
          "ctx": { "ge": 1 }
        }
      ]
    }
    ```
- Todos os `id` são **UUID v4** em formato string (`"3fa85f64-5717-4562-b3fc-2c963f66afa6"`).
- Datas (`criado_em`, `atualizado_em`, `proxima_revisao`, etc.) são **ISO 8601** com timezone, ex: `"2026-09-11T14:32:00.123456Z"`.

---

## Índice

1. [Perfil / Usuário](#1-perfil--usuário)
2. [Pastas](#2-pastas)
3. [Documentos](#3-documentos)
4. [Resumos](#4-resumos-bedrock)
5. [Flashcards](#5-flashcards-bedrock)
6. [Quizzes](#6-quizzes-bedrock)
7. [Revisões / Daily Mix (SM-2)](#7-revisões--daily-mix-sm-2)

---

## 1. Perfil / Usuário

Base path: `/profile`

### 1.1 Criar usuário — `POST /profile`

Cadastro inicial (sem auth — normalmente chamado logo após o signup no Cognito).

**Request body** (`UsuarioBase`):
```json
{
  "email": "joao.silva@example.com",
  "nome": "João Silva",
  "estilo_preferido": "direta",
  "formato_preferido": "cornell",
  "objetivos_estudo": "Passar no vestibular de Medicina",
  "cognito_id": "us-east-1:1234abcd-56ef-78gh-90ij-klmnopqrstuv"
}
```
Campos: `email` (obrigatório, deve ser email válido), `nome`, `estilo_preferido`, `formato_preferido`, `objetivos_estudo`, `cognito_id` — todos opcionais exceto `email`.

**Response `201 Created`** (`Usuario`):
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "joao.silva@example.com",
  "nome": "João Silva",
  "estilo_preferido": "direta",
  "formato_preferido": "cornell",
  "objetivos_estudo": "Passar no vestibular de Medicina",
  "cognito_id": "us-east-1:1234abcd-56ef-78gh-90ij-klmnopqrstuv",
  "criado_em": "2026-09-11T10:00:00Z",
  "atualizado_em": "2026-09-11T10:00:00Z"
}
```

---

### 1.2 Buscar usuário pelo token (Cognito) — `GET /profile`

🔒 Auth: `Authorization: Bearer <jwt_do_cognito>` (**não** usa `X-User-Id` aqui).

**Request:** sem body.
```
GET /profile
Authorization: Bearer eyJraWQiOiJ...<jwt>...
```
O backend extrai o claim `sub` do JWT (sem verificar assinatura) e usa como `cognito_id` para buscar o usuário.

**Response `200 OK`** (`Usuario`): mesmo formato do item 1.1.

**Erros:**
- `401` se o token estiver malformado: `{"detail": "Token JWT inválido ou malformado."}`
- `404` se não existir usuário com esse `cognito_id`: `{"detail": "Usuário não encontrado no banco de dados."}`

---

### 1.3 Detalhe do usuário — `GET /profile/{user_id}`

🔒 Auth: `X-User-Id` (header) — precisa bater com `user_id` do path, senão `403`.

**Request:** sem body. `user_id` é UUID na URL.
```
GET /profile/3fa85f64-5717-4562-b3fc-2c963f66afa6
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`** (`Usuario`): mesmo formato do item 1.1.

**Erros:** `404` — `{"detail": "Usuário não encontrado"}`; `403` — `{"detail": "Acesso negado"}`.

---

### 1.4 Editar perfil completo — `PUT /profile/{user_id}`

🔒 Auth: `X-User-Id` (header) — precisa bater com `user_id` do path, senão `403`.

Substitui os campos editáveis do perfil (envia o objeto completo, não é PATCH parcial — mas os campos são opcionais, então pode reenviar os mesmos valores que já existiam para os que não quer alterar).

**Request body** (`UsuarioBase` — igual ao de criação):
```json
{
  "email": "joao.silva@example.com",
  "nome": "João Silva Santos",
  "estilo_preferido": "detalhada",
  "formato_preferido": "fichamento_academico",
  "objetivos_estudo": "Concurso público - área fiscal",
  "cognito_id": "us-east-1:1234abcd-56ef-78gh-90ij-klmnopqrstuv"
}
```
```
PUT /profile/3fa85f64-5717-4562-b3fc-2c963f66afa6
Content-Type: application/json
```

**Response `200 OK`** (`Usuario`):
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "joao.silva@example.com",
  "nome": "João Silva Santos",
  "estilo_preferido": "detalhada",
  "formato_preferido": "fichamento_academico",
  "objetivos_estudo": "Concurso público - área fiscal",
  "cognito_id": "us-east-1:1234abcd-56ef-78gh-90ij-klmnopqrstuv",
  "criado_em": "2026-09-11T10:00:00Z",
  "atualizado_em": "2026-09-11T15:42:11Z"
}
```

**Erro:** `404` — `{"detail": "Usuário não encontrado"}`

> ⚠️ Nota: `estilo_preferido` e `formato_preferido` aqui são `str` livres (não validados contra um enum neste endpoint — diferente do onboarding, item 1.6, que usa enum fechado). Recomenda-se o front sempre enviar os mesmos valores usados no onboarding (`direta`/`detalhada`/`brincalhona` e `resumo_executivo`/`cornell`/`fichamento_academico`) para manter consistência.

---

### 1.5 Deletar conta — `DELETE /profile/{user_id}`

🔒 Auth: `X-User-Id` (header) — precisa bater com `user_id` do path, senão `403`.

**Request:** sem body.
```
DELETE /profile/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response:** `204 No Content` (sem corpo).

**Erro:** `404` — `{"detail": "Usuário não encontrado"}`

---

### 1.6 Onboarding — `POST /profile/{user_id}/perfil`

🔒 Auth: `X-User-Id` (header) — precisa bater com `user_id` do path, senão `403`.

Salva as preferências do onboarding (estilo, formato, objetivos). Diferente do 1.4: aqui os campos são validados contra enums fechados.

**Request body** (`OnboardingRequest`):
```json
{
  "estilo_preferido": "brincalhona",
  "formato_preferido": "resumo_executivo",
  "objetivos_estudo": "Reforço escolar - Ensino Médio"
}
```
- `estilo_preferido`: `"direta" | "detalhada" | "brincalhona"` (opcional)
- `formato_preferido`: `"resumo_executivo" | "cornell" | "fichamento_academico"` (opcional)
- `objetivos_estudo`: string livre (opcional)

**Response `200 OK`** (`Usuario`): mesmo formato do item 1.1, com os campos atualizados.

**Erro:** `404` — `{"detail": "Usuário não encontrado"}`

---

### 1.7 Dashboard do usuário — `GET /profile/{user_id}/dashboard`

🔒 Auth: `X-User-Id` (header), além do Bearer token global — `user_id` do path precisa bater com o `X-User-Id`, senão `403`.

**Request:** sem body.
```
GET /profile/3fa85f64-5717-4562-b3fc-2c963f66afa6/dashboard
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`** (`DashboardResponse`):
```json
{
  "ultimos_flashcards": [
    { "id": "a1b2c3d4-0000-0000-0000-000000000001", "titulo": "Flashcards - Revolução Francesa", "criado_em": "2026-09-10T09:00:00Z" }
  ],
  "ultimos_resumos": [
    { "id": "a1b2c3d4-0000-0000-0000-000000000002", "nome": "Resumo - Fotossíntese", "criado_em": "2026-09-09T18:20:00Z" }
  ],
  "ultimos_quizzes": [
    { "id": "a1b2c3d4-0000-0000-0000-000000000003", "titulo": "Quiz - Leis de Newton", "criado_em": "2026-09-08T11:15:00Z" }
  ],
  "documentos_recentes": [
    { "id": "a1b2c3d4-0000-0000-0000-000000000004", "nome": "Capítulo 1 - Introdução.pdf", "criado_em": "2026-09-10T09:00:00Z" }
  ],
  "total_flashcards": 12,
  "total_resumos": 5,
  "total_quizzes": 8
}
```
`documentos_recentes` traz os últimos 10 documentos do usuário (todas as pastas, sem filtro), pra alimentar um atalho de "gerar resumo" direto do dashboard.

**Erro:** `403` — `{"detail": "Acesso negado"}` se `user_id` do path não for o mesmo do `X-User-Id`.

---

## 2. Pastas

Base path: `/pastas`

### 2.1 Criar pasta — `POST /pastas`

🔒 Auth: `X-User-Id` (header) — `usuario_id` **não** é mais aceito no body, vem sempre do header.

**Request body** (`PastaCreateRequest`):
```json
{
  "nome": "Biologia - 3º Ano",
  "pasta_pai_id": null
}
```
`pasta_pai_id` é `null`/omitido para pasta raiz, ou o UUID da pasta pai para subpasta.

**Response `201 Created`:** objeto da pasta criada (formato equivalente a `Pasta`, ver 2.5).

---

### 2.2 Listar pastas raiz do usuário — `GET /pastas/user/{user_id}`

🔒 Auth: `X-User-Id` (header) — precisa bater com `user_id` do path, senão `403`.

**Query params:** `limit` (int, padrão 50, 1–100), `offset` (int, padrão 0, ≥0).
```
GET /pastas/user/3fa85f64-5717-4562-b3fc-2c963f66afa6?limit=20&offset=0
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`** (`list[PastaListagemResponse]`):
```json
[
  { "id": "b1000000-0000-0000-0000-000000000001", "nome": "Biologia - 3º Ano", "criada_em": "2026-09-01T12:00:00Z" },
  { "id": "b1000000-0000-0000-0000-000000000002", "nome": "Matemática - ENEM", "criada_em": "2026-09-03T08:30:00Z" }
]
```

---

### 2.3 Listar todas as pastas do usuário (árvore completa) — `GET /pastas/user/{user_id}/todas`

🔒 Auth: `X-User-Id` (header) — precisa bater com `user_id` do path, senão `403`.

**Request:** sem query params.
```
GET /pastas/user/3fa85f64-5717-4562-b3fc-2c963f66afa6/todas
```

**Response `200 OK`** (`list[PastaListagemResponse]`): mesmo formato do 2.2, mas inclui subpastas de todos os níveis (não só raiz). Cada item traz também `pasta_pai_id` (UUID da pasta superior; `null` nas pastas raiz), que o front usa para montar a árvore de pastas.

---

### 2.4 Conteúdo de uma pasta (subpastas + documentos) — `GET /pastas/{pasta_id}/conteudo`

🔒 Auth: `X-User-Id` (header). Retorna `404` se a pasta não existir ou não pertencer ao usuário.

**Query params:** `limit` (padrão 50, 1–100), `offset` (padrão 0).
```
GET /pastas/b1000000-0000-0000-0000-000000000001/conteudo?limit=50&offset=0
```

**Response `200 OK`** (`PastaConteudoResponse`):
```json
{
  "subpastas": [
    { "id": "b2000000-0000-0000-0000-000000000001", "nome": "Genética", "criada_em": "2026-09-02T10:00:00Z" }
  ],
  "arquivos": [
    { "id": "c1000000-0000-0000-0000-000000000001", "nome": "Capitulo1.pdf", "status": "pronto", "resumo": null }
  ],
  "total_arquivos": 1,
  "pagina_atual": 0,
  "tem_mais_paginas": false
}
```
`status` do documento pode ser algo como `"processando"` ou `"pronto"` (ver 3. Documentos).

---

### 2.5 Renomear pasta — `PUT /pastas/{pasta_id}`

🔒 Auth: `X-User-Id` (header). ⚠️ **Não é JSON** — é `multipart/form-data` (via `Form(...)` no FastAPI).

**Request:**
```
PUT /pastas/b1000000-0000-0000-0000-000000000001
Content-Type: multipart/form-data
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6

nome=Biologia - Terceirão
```
Exemplo com `fetch`:
```js
const formData = new FormData();
formData.append("nome", "Biologia - Terceirão");
await fetch(`/pastas/${pastaId}`, { method: "PUT", body: formData });
```

**Response `200 OK`** (`Pasta`):
```json
{
  "id": "b1000000-0000-0000-0000-000000000001",
  "nome": "Biologia - Terceirão",
  "usuario_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "pasta_pai_id": null,
  "criada_em": "2026-09-01T12:00:00Z"
}
```

**Erro:** `404` — `{"detail": "Pasta não encontrada"}`

---

### 2.6 Deletar pasta — `DELETE /pastas/{pasta_id}`

🔒 Auth: `X-User-Id` (header).

**Request:** sem body.

**Response:** `204 No Content`.

**Erro:** `404` — `{"detail": "Pasta não encontrada"}`

---

## 3. Documentos

Base path: `/documentos`

### 3.1 Upload de PDF — `POST /documentos/upload`

🔒 Auth: `X-User-Id` (header) — `user_id` **não** é mais aceito no form, vem sempre do header. ⚠️ **`multipart/form-data`** (upload de arquivo + campos de formulário juntos).

**Campos do form:**
- `documento` — arquivo (PDF)
- `pasta_id` — UUID (form field)
- `nome_documento` — string (form field)

Exemplo com `fetch`:
```js
const formData = new FormData();
formData.append("documento", fileInput.files[0]); // File object
formData.append("pasta_id", "b1000000-0000-0000-0000-000000000001");
formData.append("nome_documento", "Capítulo 1 - Introdução");

await fetch("/documentos/upload", {
  method: "POST",
  headers: { "X-User-Id": "3fa85f64-5717-4562-b3fc-2c963f66afa6" },
  body: formData,
});
// NÃO defina Content-Type manualmente — o browser define o boundary do multipart automaticamente
```

Exemplo `curl`:
```bash
curl -X POST http://localhost:8000/documentos/upload \
  -H "X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6" \
  -F "documento=@capitulo1.pdf" \
  -F "pasta_id=b1000000-0000-0000-0000-000000000001" \
  -F "nome_documento=Capítulo 1 - Introdução"
```

**Response `201 Created`:** objeto do documento criado (id, nome, status inicial, etc — status normalmente começa como `"processando"` até o upload/parse terminar).

**Validações do upload** (todas antes de gravar no banco ou no S3):
- `400` / `1003` — não é PDF; `1004` — acima de 5 MB (as duas podem vir juntas na lista de violações); `1006` — PDF corrompido ou ilegível; `1008` — PDF com mais de 100 páginas.
- `422` / `1005` — conteúdo impróprio na moderação (feita sobre uma amostra de páginas: início, meio e fim, texto e imagens).
- `503` / `9004` — moderação indisponível (falha fechada: o upload é recusado).
- PDFs escaneados (só imagem) são **aceitos**: o modelo lê as páginas como imagem.

---

### 3.2 URL pré-assinada para visualização — `GET /documentos/{documento_id}/url-visualizacao`

🔒 Auth: `X-User-Id` (header).

```
GET /documentos/c1000000-0000-0000-0000-000000000001/url-visualizacao
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`:**
```json
{ "url": "https://bright-bucket.s3.amazonaws.com/uploads/user-3fa85.../doc-c1000...pdf?X-Amz-Signature=..." }
```
Essa URL do S3 é temporária (pré-assinada) — usar direto num `<iframe>`/`<embed>` ou visualizador de PDF no front.

**Erros:**
- `404` se o documento não existir/não pertencer ao usuário: `{"detail": "<mensagem>"}`
- `500` se falhar ao gerar a URL: `{"detail": "<mensagem>"}`

---

### 3.3 Renomear documento — `PUT /documentos/{documento_id}`

🔒 Auth: `X-User-Id` (header). ⚠️ **`multipart/form-data`**, igual ao 2.5 (form field `nome`).

```js
const formData = new FormData();
formData.append("nome", "Capítulo 1 - Revisado");
await fetch(`/documentos/${documentoId}`, {
  method: "PUT",
  headers: { "X-User-Id": "3fa85f64-5717-4562-b3fc-2c963f66afa6" },
  body: formData,
});
```

**Response `200 OK`:** documento atualizado.

**Erro:** `404` — `{"detail": "Documento não encontrado"}`

---

### 3.4 Deletar documento — `DELETE /documentos/{documento_id}`

🔒 Auth: `X-User-Id` (header).

```
DELETE /documentos/c1000000-0000-0000-0000-000000000001
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response:** `204 No Content`. Apaga o original e tudo que foi gerado dele (resumos, flashcards e quizzes), no S3 e no banco.

**Erro:** `404` — `{"detail": "Documento não encontrado"}`

---

### 3.5 Buscar documentos por nome — `GET /documentos`

🔒 Auth: `X-User-Id` (header). Busca em todas as pastas do usuário, sem diferenciar maiúsculas nem acentos.

**Query params:** `q` (termo; vazio lista todos; até 100 caracteres), `limit` (padrão 20, 1–50), `offset` (padrão 0).
```
GET /documentos?q=sono&limit=20&offset=0
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`:**
```json
{
  "itens": [
    {
      "id": "c1000000-0000-0000-0000-000000000001",
      "nome": "A Importância do Sono para a Saúde Mental",
      "pasta_nome": "Hábitos Saudáveis",
      "pasta_caminho": "Saúde Mental › Hábitos Saudáveis",
      "criado_em": "2026-10-29T10:00:00"
    }
  ],
  "total": 1,
  "tem_mais": false
}
```
Ordenado do mais recente para o mais antigo. `pasta_caminho` é o caminho completo da pasta (separado por ` › `) e vem `null` se o documento estiver sem pasta. `limit` fora de 1–50 ou `offset` negativo retornam `422`.

---

### 3.6 PDF original (bytes) — `GET /documentos/{documento_id}/arquivo`

🔒 Auth: `X-User-Id` (header). Devolve o próprio PDF (`Content-Type: application/pdf`, `Content-Disposition: inline`, `Cache-Control: private, no-store`). É a rota usada pelo visualizador de PDF do front (o bucket não tem CORS, então não dá para ler direto do S3 no navegador).

**Erro:** `404` se o documento não existir ou não pertencer ao usuário.

---

## 4. Resumos (Bedrock)

### 4.1 Gerar resumo — `POST /documentos/{documento_id}/resumos`

🔒 Auth: `X-User-Id` (header). Chama o Bedrock — pode demorar alguns segundos.

**Request body** (`ResumoCreateRequest`):
```json
{
  "nivel_conhecimento": 3,
  "formato": "cornell",
  "tom": "descontraído e direto ao ponto"
}
```
- `nivel_conhecimento`: int, `0` a `10` (0 = iniciante total, 10 = avançado)
- `formato`: enum — `"resumo_executivo" | "cornell" | "fichamento_academico"`
- `tom`: string livre (ex: `"formal"`, `"descontraído"`, `"como se fosse para uma criança"`)

```
POST /documentos/c1000000-0000-0000-0000-000000000001/resumos
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
Content-Type: application/json
```

**Response `201 Created`** (`ResumoResponse`):
```json
{
  "id": "d1000000-0000-0000-0000-000000000001",
  "documento_id": "c1000000-0000-0000-0000-000000000001",
  "titulo": "Resumo - Capítulo 1 - Introdução",
  "formato": "cornell",
  "nivel_conhecimento": 3,
  "tom": "descontraído e direto ao ponto",
  "s3_chave": "usuarios/user-3fa85.../doc-c1000.../resumo-d1000....md",
  "tokens_utilizados": 2450,
  "modelo_ia": "claude-3-5-sonnet-20241022",
  "criado_em": "2026-09-11T16:00:00Z"
}
```
> O conteúdo real do resumo (markdown) fica em S3 na `s3_chave` — não vem embutido nesta resposta. Para ler o conteúdo, use o item 4.2 abaixo.

**Erro:** `404` — documento não encontrado: `{"detail": "<mensagem>"}`

---

### 4.2 Listar resumos de um documento — `GET /documentos/{documento_id}/resumos`

🔒 Auth: `X-User-Id` (header). Usado para o "Document Hub": abrir um documento e ver todos os resumos já gerados para ele.

```
GET /documentos/c1000000-0000-0000-0000-000000000001/resumos
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`** (`list[ResumoResponse]`): array no mesmo formato do item 4.1 (metadados apenas, sem `conteudo`), ordenado do mais recente para o mais antigo.

---

### 4.3 Ler conteúdo de um resumo — `GET /resumos/{resumo_id}/conteudo`

🔒 Auth: `X-User-Id` (header). Baixa o markdown do S3 e retorna já pronto pra renderizar.

```
GET /resumos/d1000000-0000-0000-0000-000000000001/conteudo
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`** (`ResumoConteudoResponse`):
```json
{
  "id": "d1000000-0000-0000-0000-000000000001",
  "titulo": "Resumo - Capítulo 1 - Introdução",
  "conteudo": "# Capítulo 1 — Introdução\n\n## Notas\n..."
}
```
`conteudo` é markdown puro (string) — renderizar com uma lib de markdown-to-html no front.

**Erro:** `404` — `{"detail": "Resumo não encontrado ou não pertence ao usuário."}`

---

### 4.3b PDF do resumo (bytes) — `GET /resumos/{resumo_id}/pdf`

🔒 Auth: `X-User-Id` (header). Devolve o PDF do resumo (`application/pdf`, `inline`). Se o PDF ainda não existir, é gerado a partir do markdown, gravado no S3 e devolvido. Usado pelo visualizador de PDF do front. `404` se o resumo não existir ou não pertencer ao usuário.

### 4.3c URL de download do PDF — `GET /resumos/{resumo_id}/download`

🔒 Auth: `X-User-Id` (header). Retorna `{"url": "<URL pré-assinada, válida por 5 minutos>"}` para baixar o PDF do resumo.

---

### 4.4 Renomear resumo — `PUT /resumos/{resumo_id}`

🔒 Auth: `X-User-Id` (header).

**Request body** (`ResumoRenomearRequest`):
```json
{ "titulo": "Resumo revisado - Capítulo 1" }
```

**Response `200 OK`** (`ResumoResponse`): mesmo formato do item 4.1, com `titulo` atualizado.
**Erro:** `404` — `{"detail": "Resumo não encontrado"}`

---

### 4.5 Deletar resumo — `DELETE /resumos/{resumo_id}`

🔒 Auth: `X-User-Id` (header).

**Response:** `204 No Content`.
**Erro:** `404` — `{"detail": "Resumo não encontrado"}`

---

## 5. Flashcards (Bedrock)

### 5.1 Gerar flashcards — `POST /documentos/{documento_id}/flashcards`

🔒 Auth: `X-User-Id` (header).

**Request body** (`FlashcardCreateRequest`):
```json
{ "quantidade": 15 }
```
`quantidade`: int, `1` a `50`, **padrão 10 se omitido** (pode enviar `{}` como body).

**Response `201 Created`** (`FlashcardResponse`):
```json
{
  "id": "e1000000-0000-0000-0000-000000000001",
  "documento_id": "c1000000-0000-0000-0000-000000000001",
  "titulo": "Flashcards - Capítulo 1 - Introdução",
  "s3_chave": "usuarios/user-3fa85.../doc-c1000.../flashcard-e1000....json",
  "tokens_utilizados": 3100,
  "modelo_ia": "claude-3-5-haiku-20241022",
  "criado_em": "2026-09-11T16:05:00Z"
}
```

**Erro:** `404` — `{"detail": "<mensagem>"}`

### 5.2 Listar flashcards (sets) de um documento — `GET /documentos/{documento_id}/flashcards`

🔒 Auth: `X-User-Id` (header). Lista os *sets* de flashcards gerados para o documento (não os cartões individuais).

```
GET /documentos/c1000000-0000-0000-0000-000000000001/flashcards
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`** (`list[FlashcardResponse]`): array no mesmo formato do 5.1, ordenado do mais recente para o mais antigo.

### 5.3 Ler conteúdo de um set de flashcards — `GET /flashcards/{flashcard_id}/conteudo`

🔒 Auth: `X-User-Id` (header). Retorna **todos** os cartões do set, independente de estarem atrasados ou não (diferente do `/revisoes/*`, que só traz o que venceu).

```
GET /flashcards/e1000000-0000-0000-0000-000000000001/conteudo
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`** (`FlashcardConteudoResponse`):
```json
{
  "id": "e1000000-0000-0000-0000-000000000001",
  "titulo": "Flashcards - Capítulo 1 - Introdução",
  "cartoes": [
    {
      "id": "g1000000-0000-0000-0000-000000000001",
      "item_ref": "flashcard-1",
      "fator_facilidade": 2.5,
      "intervalo_atual": 0,
      "repeticoes": 0,
      "proxima_revisao": "2026-09-11T16:05:00Z",
      "conteudo": { "pergunta": "O que é fotossíntese?", "resposta": "Processo pelo qual plantas convertem luz em energia química." }
    }
  ]
}
```

**Erro:** `404` — `{"detail": "Flashcard não encontrado ou não pertence ao usuário."}`

### 5.4 Renomear flashcard — `PUT /flashcards/{flashcard_id}`

🔒 Auth: `X-User-Id`. **Body:** `{ "titulo": "Novo título" }`. **Response `200 OK`**: mesmo formato do item 5.1. **Erro:** `404` — `{"detail": "Flashcard não encontrado"}`

### 5.5 Deletar flashcard — `DELETE /flashcards/{flashcard_id}`

🔒 Auth: `X-User-Id`. **Response:** `204 No Content`. **Erro:** `404` — `{"detail": "Flashcard não encontrado"}`

---

## 6. Quizzes (Bedrock)

### 6.1 Gerar quiz — `POST /documentos/{documento_id}/quizzes`

🔒 Auth: `X-User-Id` (header).

**Request body** (`QuizCreateRequest`):
```json
{ "quantidade": 10 }
```
`quantidade`: int, `1` a `50`, padrão 10.

**Response `201 Created`** (`QuizResponse`):
```json
{
  "id": "f1000000-0000-0000-0000-000000000001",
  "documento_id": "c1000000-0000-0000-0000-000000000001",
  "titulo": "Quiz - Capítulo 1 - Introdução",
  "s3_chave": "usuarios/user-3fa85.../doc-c1000.../quiz-f1000....json",
  "tokens_utilizados": 2800,
  "modelo_ia": "claude-3-5-sonnet-20241022",
  "criado_em": "2026-09-11T16:10:00Z"
}
```

**Erro:** `404` — `{"detail": "<mensagem>"}`

### 6.2 Listar quizzes de um documento — `GET /documentos/{documento_id}/quizzes`

🔒 Auth: `X-User-Id` (header). Lista os quizzes gerados para o documento.

```
GET /documentos/c1000000-0000-0000-0000-000000000001/quizzes
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`** (`list[QuizResponse]`): array no mesmo formato do 6.1, ordenado do mais recente para o mais antigo.

### 6.3 Ler conteúdo de um quiz — `GET /quizzes/{quiz_id}/conteudo`

🔒 Auth: `X-User-Id` (header). Retorna **todas** as questões do quiz, independente de estarem atrasadas ou não.

```
GET /quizzes/f1000000-0000-0000-0000-000000000001/conteudo
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`** (`QuizConteudoResponse`):
```json
{
  "id": "f1000000-0000-0000-0000-000000000001",
  "titulo": "Quiz - Capítulo 1 - Introdução",
  "questoes": [
    {
      "id": "h1000000-0000-0000-0000-000000000001",
      "item_ref": "quiz-1",
      "fator_facilidade": 2.5,
      "intervalo_atual": 0,
      "repeticoes": 0,
      "proxima_revisao": "2026-09-11T16:10:00Z",
      "conteudo": { "pergunta": "Qual lei descreve F=ma?", "alternativas": ["1ª Lei de Newton", "2ª Lei de Newton", "3ª Lei de Newton"], "resposta_correta": "2ª Lei de Newton" }
    }
  ]
}
```

**Erro:** `404` — `{"detail": "Quiz não encontrado ou não pertence ao usuário."}`

### 6.4 Renomear quiz — `PUT /quizzes/{quiz_id}`

🔒 Auth: `X-User-Id`. **Body:** `{ "titulo": "Novo título" }`. **Response `200 OK`**: mesmo formato do item 6.1. **Erro:** `404` — `{"detail": "Quiz não encontrado"}`

### 6.5 Deletar quiz — `DELETE /quizzes/{quiz_id}`

🔒 Auth: `X-User-Id`. **Response:** `204 No Content`. **Erro:** `404` — `{"detail": "Quiz não encontrado"}`

---

## 7. Revisões / Daily Mix (SM-2)

Base path: `/revisoes`. Todas as rotas exigem 🔒 `X-User-Id`.

### 7.1 Daily Mix consolidado — `GET /revisoes/hoje`

```
GET /revisoes/hoje
X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response `200 OK`** (`DailyMixResponse`):
```json
{
  "cartoes": [
    {
      "id": "g1000000-0000-0000-0000-000000000001",
      "origem_id": "e1000000-0000-0000-0000-000000000001",
      "item_ref": "card_001",
      "fator_facilidade": 2.5,
      "intervalo_atual": 1,
      "repeticoes": 0,
      "proxima_revisao": "2026-09-11T00:00:00Z",
      "conteudo": { "item_ref": "card_001", "pergunta": "O que é fotossíntese?", "resposta": "Processo pelo qual plantas convertem luz em energia química." }
    }
  ],
  "questoes": [
    {
      "id": "h1000000-0000-0000-0000-000000000001",
      "origem_id": "f1000000-0000-0000-0000-000000000001",
      "item_ref": "q_001",
      "fator_facilidade": 2.5,
      "intervalo_atual": 1,
      "repeticoes": 0,
      "proxima_revisao": "2026-09-11T00:00:00Z",
      "conteudo": { "item_ref": "q_001", "pergunta": "Qual lei descreve F=ma?", "alternativas": ["1ª Lei de Newton", "2ª Lei de Newton", "3ª Lei de Newton", "4ª Lei de Newton"], "resposta_correta": "2ª Lei de Newton" }
    }
  ],
  "total": 2
}
```
`item_ref` identifica o item dentro do JSON gerado (ex: `"card_001"`, `"q_001"`) — usado para casar o registro do banco com o conteúdo correspondente no S3. `conteudo` é o payload já resolvido a partir do S3, pronto pra renderizar: **flashcard usa `pergunta`/`resposta`**; **quiz usa `pergunta`/`alternativas`/`resposta_correta`** (a comparação da resposta escolhida é feita no front — não existe validação no backend).

---

### 7.2 Só cartões pendentes — `GET /revisoes/flashcards`

Mesmo formato de item de `cartoes` acima, mas em `list[ItemRevisaoResponse]` (array direto, sem envelope):
```json
[
  {
    "id": "g1000000-0000-0000-0000-000000000001",
    "origem_id": "e1000000-0000-0000-0000-000000000001",
    "item_ref": "card_001",
    "fator_facilidade": 2.5,
    "intervalo_atual": 1,
    "repeticoes": 0,
    "proxima_revisao": "2026-09-11T00:00:00Z",
    "conteudo": { "item_ref": "card_001", "pergunta": "...", "resposta": "..." }
  }
]
```

### 7.3 Só questões pendentes — `GET /revisoes/quizzes`

Mesmo formato do 7.2, mas para questões de quiz — `conteudo` vem como `{ "item_ref": "...", "pergunta": "...", "alternativas": [...], "resposta_correta": "..." }`.

---

### 7.3b Todos os cartões (atrasados + em dia) — `GET /revisoes/flashcards/todos`

Mesmo formato do 7.2, mas **sem filtro de `proxima_revisao`** — traz todo o histórico de cartões do usuário (até 500), não só o que venceu. Usado pra montar a lista "em dia" ao lado da lista "atrasados" (a mesma comparação `proxima_revisao <= hoje`, já feita no front pra marcar atraso, separa os dois grupos a partir desta única resposta).

### 7.3c Todas as questões (atrasadas + em dia) — `GET /revisoes/quizzes/todos`

Mesmo formato do 7.3b, para questões de quiz.

---

### 7.4 Avaliar cartão (flashcard) — `PUT /revisoes/cartoes/{cartao_id}/avaliar`

🔒 Auth: `X-User-Id`. `cartao_id` é o `id` do item retornado no Daily Mix (não é o `flashcard_id` direto — é o `id` da tabela `cartoes`).

**Request body** (`AvaliarRequest`):
```json
{ "qualidade": 4 }
```
`qualidade`: int, `1` a `5` — nota que o usuário dá após ver a resposta (1-2 = errou/difícil, 3+ = acertou). Regras completas do SM-2 em [`referencia-rapida.md`](referencia-rapida.md#sm-2-rápido).

**Response `200 OK`** (`AvaliarResponse`):
```json
{
  "id": "g1000000-0000-0000-0000-000000000001",
  "fator_facilidade": 2.6,
  "intervalo_atual": 6,
  "repeticoes": 1,
  "proxima_revisao": "2026-09-17T00:00:00Z"
}
```

**Erro:** `404` — `{"detail": "<mensagem>"}` (cartão não encontrado / não pertence ao usuário)

---

### 7.5 Avaliar questão (quiz) — `PUT /revisoes/questoes/{questao_id}/avaliar`

Idêntico ao 7.4, mesmo body (`{"qualidade": 1-5}`) e mesma resposta (`AvaliarResponse`), mas para a tabela `questoes`.

---

## Exemplos prontos (cURL) para colar num teste rápido

```bash
# Criar usuário
curl -X POST http://localhost:8000/profile \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@example.com","nome":"João Silva"}'

# Editar perfil
curl -X PUT http://localhost:8000/profile/3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@example.com","nome":"João Silva Santos","estilo_preferido":"detalhada"}'

# Gerar resumo (rota autenticada)
curl -X POST http://localhost:8000/documentos/c1000000-0000-0000-0000-000000000001/resumos \
  -H "X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6" \
  -H "Content-Type: application/json" \
  -d '{"nivel_conhecimento":3,"formato":"cornell","tom":"direto"}'

# Avaliar um cartão de revisão
curl -X PUT http://localhost:8000/revisoes/cartoes/g1000000-0000-0000-0000-000000000001/avaliar \
  -H "X-User-Id: 3fa85f64-5717-4562-b3fc-2c963f66afa6" \
  -H "Content-Type: application/json" \
  -d '{"qualidade":4}'
```

---

## Checklist: manter este arquivo atualizado

- [ ] Novo endpoint? Adicione aqui: método, path, auth, body de exemplo, response de exemplo, erros.
- [ ] Campo novo/removido em um schema (`app/schemas/*.py`)? Atualize o JSON de exemplo correspondente.
- [ ] Mudou uma regra de validação (`Field(ge=..., le=...)`, enum novo)? Atualize a descrição do campo.

---

**Última atualização:** 2026-09-22
**Fonte:** `app/api/routers/*.py` + `app/schemas/*.py` + `app/core/auth_middleware.py` (lidos diretamente do código nesta data)
