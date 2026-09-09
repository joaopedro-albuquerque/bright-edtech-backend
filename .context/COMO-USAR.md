# Como Usar Esta Pasta de Contexto

Bem-vindo! Esta pasta (`.context/`) contém toda a documentação centralizada do Bright EdTech.

## 📚 Estrutura de Documentos

```
.context/
├── README.md                 ← COMECE AQUI (índice principal)
├── COMO-USAR.md             ← Este arquivo
│
├── visao-geral.md           ← O que é Bright EdTech?
├── arquitetura.md           ← Stack, infraestrutura, decisões
├── dados.md                 ← Schema PostgreSQL, hybrid DB+S3
├── ux-ui.md                 ← Interface, fluxos, componentes
├── modelos-resumo.md        ← 3 tipos de resumo (Executivo, Cornell, Fichamento)
├── glossario.md             ← Termos técnicos, acrônimos, definições
└── referencia-rapida.md     ← Cheat sheet para desenvolvimento
```

---

## 🎯 Entrando Rápido (Next 5 Minutes)

### Se você está...

**1. Novo no projeto**
   1. Leia `visao-geral.md` (2 min)
   2. Leia `arquitetura.md` § Stack (3 min)
   3. Pule para `referencia-rapida.md` e explore conforme necessário

**2. Desenvolvendo uma feature de API**
   1. Consulte `dados.md` para entender o schema
   2. Use `referencia-rapida.md` § Endpoints para rota base
   3. Veja `ux-ui.md` para entender o fluxo de usuário

**3. Ajustando resumos (IA/Prompts)**
   1. Vá direto a `modelos-resumo.md`
   2. Consulte `referencia-rapida.md` § Variables de Ambiente para Bedrock config

**4. Ajustando UI/UX**
   1. Consulte `ux-ui.md` § Layout, Componentes
   2. Veja `referencia-rapida.md` § Comandos Úteis (Frontend)

**5. Debugando um problema**
   1. Procure o termo em `glossario.md`
   2. Vá para o doc relevante (seções cross-linked)
   3. Consulte `referencia-rapida.md` § Comandos Úteis

---

## 🔍 Encontrando Informações Específicas

### Procurando informação sobre...

| Tópico | Documento | Seção |
|--|--|--|
| **O que é Bright EdTech?** | `visao-geral.md` | Tudo |
| **Stack/Infraestrutura** | `arquitetura.md` | Stack em Diagrama |
| **Endpoints da API** | `referencia-rapida.md` | Endpoints API Principais |
| **Schema de BD** | `dados.md` | Schema PostgreSQL Completo |
| **Modelos de Resumo** | `modelos-resumo.md` | Seções 1-3 |
| **Algoritmo SM-2** | `dados.md` | Fluxo de Dados (Daily Mix) |
| **Layout da UI** | `ux-ui.md` | Document Hub |
| **Configuração em Cascata** | `ux-ui.md` | Herança de Configuração |
| **Variáveis de Ambiente** | `referencia-rapida.md` | Variables de Ambiente (.env) |
| **Definição de um termo** | `glossario.md` | Procure alfabeticamente |
| **Fluxo completo (Upload→Revisão)** | `referencia-rapida.md` | Fluxo de Usuário (Happy Path) |
| **AWS/Docker/Frontend comandos** | `referencia-rapida.md` | Comandos Úteis |

---

## 🚀 Fluxo para Diferentes Tarefas

### Implementar um Novo Endpoint

```
1. Vá para referencia-rapida.md § Checklist: Novo Endpoint
2. Leia arquitetura.md § Fluxo de Processamento (relevante)
3. Consulte dados.md § Schema PostgreSQL para estruturas de BD
4. Implemente!
```

### Adicionar um Novo Tipo de Artefato (além de Resumos/Flashcards/Quizzes)

```
1. Leia ux-ui.md § Document Hub (entender containers)
2. Vá para dados.md e desenhe novo schema
3. Consulte modelos-resumo.md para padrão de System Prompt
4. Implemente backend + frontend
5. Use referencia-rapida.md § Checklist: Novo Recurso
```

### Debugar um Problema com SM-2 (Algoritmo não avança)

```
1. Vá para glossario.md e procure "SM-2"
2. Leia dados.md § Tabela cartoes (Spaced Repetition State)
3. Veja referencia-rapida.md § SM-2 Rápido
4. Verifique BD: SELECT * FROM cartoes WHERE proxima_revisao = ...
5. Valide lógica em backend
```

### Customizar a Geração de Resumos

```
1. Vá para modelos-resumo.md § Modelo relevante (ex: Cornell)
2. Veja o System Prompt injetado (pseudocódigo)
3. Localize arquivo em backend/app/prompts/{modelo}.txt
4. Edite o prompt
5. Teste em dev local com um PDF
```

### Implementar Notificação de Daily Mix

```
1. Leia referencia-rapida.md § Fluxo de Usuário (encontre "Daily Mix")
2. Vá para ux-ui.md § Daily Mix (Revisão Diária)
3. Consulte dados.md § Fluxo de Dados Exemplificado (revisão)
4. Implemente:
   - Backend: Lógica de envio de email/push
   - Frontend: Renderização de notificação
   - DB: Salvar timestamp de última notificação
5. Use referencia-rapida.md § Checklist: Novo Recurso
```

---

## 📖 Leitura Completa vs. Leitura Seletiva

### Leitura Completa (1-2 horas)
Recomendado se você é:
- Novo no projeto
- Planejando arquitetura importante
- Revisor de código (PR review)

**Ordem Sugerida:**
1. `visao-geral.md`
2. `arquitetura.md`
3. `dados.md`
4. `ux-ui.md`
5. `modelos-resumo.md`
6. `glossario.md`
7. `referencia-rapida.md`

### Leitura Seletiva (5-10 min)
Recomendado para:
- Tarefas pontuais
- Debugging
- Consultores de ad-hoc

Use a tabela acima "Procurando informação sobre..." para ir direto ao ponto.

---

## 🔗 Cross-Links e Referências

Cada documento é **independente**, mas temáticas relacionadas são linkadas internamente.

**Exemplos:**
- Lendo `ux-ui.md` § Daily Mix? Consulte `dados.md` § Fluxo de Dados (revisão) para entender o backend.
- Lendo `arquitetura.md` § Bedrock? Vá para `modelos-resumo.md` para ver exemplos de System Prompts.
- Lendo `dados.md` § SM-2? Consulte `glossario.md` para detalhes de termos.

---

## ⚠️ Informações NÃO Estão Aqui

Esta pasta de contexto **NÃO é um substituto para:**

- 📝 **Código-fonte** — Leia o código para implementação real
- 🔧 **Documentação de Bibliotecas** — FastAPI docs, PostgreSQL docs, AWS docs
- 📊 **Dados de Produção** — Logs, métricas, dashboards (CloudWatch, Datadog)
- 🐛 **Issues/Tickets** — GitHub Issues, Linear, Jira
- 💬 **Conversas do Time** — Slack, PRs, comentários

**Use isto para:**
✅ Entender visão geral do projeto
✅ Arquitetura e decisões de design
✅ Fluxos de usuário
✅ Schema de dados e endpoints
✅ Referência rápida de termos

---

## 🆘 Se Não Encontrar uma Resposta

1. **Procure em `glossario.md`** — Pode ser uma definição
2. **Use Ctrl+F em todo o `.context/`** — Busca por palavra-chave
3. **Consulte o código-fonte** — A verdade está lá
4. **Pergunte ao time** — Slack, Daily standup

---

## 📝 Mantendo Este Contexto Atualizado

### Quando Adicionar/Atualizar

- ✅ Novo modelo de resumo adicionado? Atualize `modelos-resumo.md`
- ✅ Stack mudou? Atualize `arquitetura.md`
- ✅ Novo termo técnico? Adicione a `glossario.md`
- ✅ Novo endpoint? Atualize `referencia-rapida.md` § Endpoints
- ✅ Fluxo de UI mudou? Atualize `ux-ui.md`

### Não Atualize Por

- ❌ Mudanças no código (versionadas via Git)
- ❌ Histórico de commits (use `git log`)
- ❌ Bugs/Issues específicos (use GitHub Issues)
- ❌ Dados de produção (use dashboards)

---

## 🎓 Sugestões de Estudo

### Semana 1: Fundamentals
- [ ] Leia `visao-geral.md`
- [ ] Leia `arquitetura.md`
- [ ] Rode localmente: `npm start` + `uvicorn app.main:app --reload`

### Semana 2: Backend Deep Dive
- [ ] Estude `dados.md` (schema completo)
- [ ] Explore `referencia-rapida.md` (endpoints)
- [ ] Faça um POST no seu endpoints local

### Semana 3: Frontend + UX
- [ ] Leia `ux-ui.md` (layout + fluxos)
- [ ] Inspeccione React components no browser
- [ ] Faça um teste com PDF real

### Semana 4: IA + Algoritmo
- [ ] Estude `modelos-resumo.md` (3 tipos de resumo)
- [ ] Estude SM-2 em `glossario.md` e `dados.md`
- [ ] Teste geração de resumo no local

### Semana 5: Integração Completa
- [ ] Faça um fluxo completo (upload → gerar resumo → revisar flashcard)
- [ ] Consulte `referencia-rapida.md` § Fluxo de Usuário
- [ ] Debug algum problema real do projeto

---

## 💡 Quick Tips

1. **Use Ctrl+F** para buscar em cada documento
2. **Abra em Markdown viewer** (VSCode, GitHub) para melhor leitura
3. **Imprima `referencia-rapida.md`** e coloque na mesa (sheet cheat)
4. **Atualize com o time** quando mudanças importantes acontecerem
5. **Link este `.context/`** em documentações de onboarding do projeto

---

**Última atualização:** 2026-09-09
**Versão:** 1.0
**Mantido por:** Contexto Documentação do Bright EdTech
