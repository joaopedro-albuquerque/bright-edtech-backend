# Estrutura e Decisões de UX/UI

## 1. Onboarding e Soft Gating

### Fluxo
```
1. Página de Cadastro
   ├─> Email + Senha
   ├─> Verificação: OPCIONAL (soft-gate)
   └─> Acesso imediato (verificada = false)

2. Onboarding Guiado (1ª visita)
   ├─> "Qual é seu objetivo de estudo?"
   ├─> "Qual é seu ritmo preferido?"
   ├─> "Qual modelo de resumo prefere?"
   └─> Salva em `usuarios.estilo_preferido` etc.

3. Usuário pode usar 100% da plataforma
   └─> Verificação de email pode ser opcional/adiada
```

### Benefícios
- ✅ Reduz atrito de entrada (não força verificação)
- ✅ Coleta preferências úteis desde o início
- ✅ Permite AB-testing de onboarding

---

## 2. Herança de Configuração (3 Níveis)

Qualquer comportamento de IA respeita a ordem:

```
┌─────────────────────────────────────────────────┐
│ CONFIGURAÇÃO DO DOCUMENTO (maior prioridade)    │
│  └─> "Para este PDF, use Fichamento Acadêmico"  │
├─────────────────────────────────────────────────┤
│ CONFIGURAÇÃO DA PASTA (prioridade média)        │
│  └─> "Nesta pasta, use Resumo Cornell"         │
├─────────────────────────────────────────────────┤
│ CONFIGURAÇÃO GLOBAL (prioridade mínima)         │
│  └─> "Seu padrão é Resumo Executivo"           │
└─────────────────────────────────────────────────┘
```

### Exemplo de Uso
```
User: "Gere um resumo para meu PDF de Direito Constitucional"

API:
  1. Busca config do documento
  2. Se não houver, busca config da pasta
  3. Se não houver, busca config do perfil global
  4. Injeta modelo + estilo no System Prompt
  5. Envia para Bedrock
```

---

## 3. Document Hub (Workspace)

### Princípio Central
**Não há abas globais para listar/gerenciar artefatos isolados.**

Toda edição de artefatos acontece **estritamente dentro** do arquivo PDF de origem.

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  [📄 Nome do Documento.pdf]                   [Menu ⋮] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌────────────────────────────────┐  │
│  │              │  │  [📑 Resumos]                  │  │
│  │              │  │  [🎴 Flashcards]              │  │
│  │              │  │  [❓ Quizzes]                  │  │
│  │              │  │                                │  │
│  │  Visualizador│  │  ┌────────────────────────────┐│  │
│  │  de PDF      │  │  │ Conteúdo da aba ativa:   ││  │
│  │              │  │  │ - Editor WYSIWYG (resumo)││  │
│  │              │  │  │ - Visualizador (cards)   ││  │
│  │              │  │  │ - Quiz player (quiz)     ││  │
│  │              │  │  └────────────────────────────┘│  │
│  │              │  │                                │  │
│  │              │  │ [+ Novo Resumo] [⚙ Config]  │  │
│  │              │  │                                │  │
│  └──────────────┘  └────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Benefícios
- ✅ Contexto visual: sempre vê o PDF e artefato lado-a-lado
- ✅ Reduz navegação: tudo em um lugar
- ✅ Fluxo natural: lê → gera → estuda
- ❌ Trade-off: interface densa, não ideal para mobile

---

## 4. Editor Interativo (TipTap)

### Resumos em Markdown
```
Feature: WYSIWYG Editor para Resumos
- Conteúdo renderizado em tempo real
- Suporte para Bold, Italic, Links, Lists, Headings
- Syntax Highlighting para código (se houver)
- Botão [Salvar] atualiza arquivo em S3
- Histórico de versões (opcional, v2)

Fluxo:
  1. IA gera resumo.md inicial
  2. TipTap carrega e renderiza
  3. Usuário edita livremente
  4. Clica [Salvar]
  5. API valida e atualiza S3 (PUT /artifacts/...)
  6. Timestamp atualizado em BD
```

### Flashcards e Quizzes
```
Feature: Visualizador + Player
- Flashcard: Frente/Verso com flip animation
- Quiz: Pergunta + opções (múltipla escolha)
- Feedback instantâneo
- Progresso visual (X de Y itens revisados)

Não há edição inline (por enquanto).
Edição futura: abrir JSON em modal ou painel lateral.
```

---

## 5. Daily Mix (Revisão Diária) — Core Loop

### O Painel Unificado ("Túnel de Foco")

```
┌─────────────────────────────────────────────────────┐
│  🎯 Seu Túnel de Foco de Hoje                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ✅ Prontos para revisar: 12 itens                 │
│                                                     │
│  ┌──────────────────────────────────┐              │
│  │ [📑 Doc: Biologia Molecular]     │              │
│  │ Pergunta: "Qual é a estrutura..."│              │
│  │ [Ver Resposta] | [Skip]          │              │
│  └──────────────────────────────────┘              │
│                                                     │
│  ┌──────────────────────────────────┐              │
│  │ [🎴 Flashcard: História]         │              │
│  │ Frente: "Capital da França?"     │              │
│  │ [Virar Card]                     │              │
│  └──────────────────────────────────┘              │
│                                                     │
│  ... (mais itens)                                  │
│                                                     │
│  ├─ Prontos: 12  ├─ Revisados hoje: 3             │
│  └─ Tempo estimado: 15 min                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Fluxo de Revisão
```
1. Frontend: GET /api/daily-mix
   └─> API busca: flashcards.cartoes + quizzes.questoes 
       WHERE proxima_revisao <= TODAY

2. Frontend exibe cada item
   └─> Usuário lê e responde

3. Usuário: Clica numa das opções
   ├─ "Muito fácil" (5)   → Intervalo grande
   ├─ "Fácil" (4)         → Intervalo médio
   ├─ "Médio" (3)         → Intervalo pequeno
   ├─ "Difícil" (2)       → Volta para amanhã
   └─ "Muito difícil" (1) → Volta hoje à noite

4. Backend: POST /api/cartoes/{id}/responder
   └─> Aplica SM-2
   └─> UPDATE cartoes (proxima_revisao, fator_facilidade, ...)
   └─> Retorna próxima data

5. Frontend: Atualiza contador e passa pro próximo
   └─> Notificação: "Próxima revisão: em 3 dias"
```

---

## 6. Configuração Cascata (Documento > Pasta > Perfil)

### UI para Ajustes

```
Documento (PDF) > Menu ⋮ > Configurações
├─ Modelo de resumo: [Resumo Executivo ▼]
├─ Estilo de linguagem: [Técnico ▼]
├─ Idioma de síntese: [Português ▼]
└─ [Usar config da pasta] [Usar config global]

Pasta > Menu ⋮ > Configurações
├─ Modelo de resumo (padrão para docs desta pasta)
├─ Ritmo de repetição: [Normal ▼]
└─ [Usar config global]

Perfil > Configurações > Preferências Globais
├─ Modelo de resumo preferido
├─ Ritmo de estudo
├─ Notificações
└─ Privacidade
```

---

## 7. Componentes Principais

| Componente | Localização | Responsabilidade |
|--|--|--|
| `PDFViewer` | Document Hub (esquerda) | Renderização de PDF |
| `TabBar` | Document Hub (direita, topo) | Resumos / Flashcards / Quizzes |
| `SummaryEditor` | Aba Resumos | Editor TipTap + [Salvar] |
| `FlashcardPlayer` | Aba Flashcards | Flip cards + classificação (1-5) |
| `QuizPlayer` | Aba Quizzes | Pergunta + múltipla escolha |
| `DailyMixDashboard` | Home / Sidebar | Túnel de Foco |
| `DocumentTree` | Sidebar | Hierarquia Pastas > Documentos |
| `ConfigurationPanel` | Modal | Ajustes de cascata |

---

## 8. Fluxos de Erro

### PDF Upload
```
❌ Arquivo muito grande (>100MB)
   └─> Mensagem: "Limite é 100MB"

❌ Formato inválido (não é PDF)
   └─> Mensagem: "Apenas PDFs são suportados"

❌ Erro na extração de texto
   └─> Status em BD: 'erro'
   └─> Mensagem: "Falha ao processar. Tente novamente."
```

### Geração de Artefatos
```
❌ Bedrock falha (rate limit, timeout)
   └─> Retry automático (exponential backoff)
   └─> Após 3 tentativas: Mensagem ao usuário

❌ Usuário não tem quota
   └─> Mensagem: "Atingiu limite mensal. Upgrade para Premium?"
```

### Revisão (Daily Mix)
```
❌ Usuário não tem nenhum item para revisar
   └─> Mensagem: "Você está em dia! 🎉"
   └─> Sugestão: "Crie novos resumos/flashcards"

❌ Falha ao salvar resposta
   └─> Retry local (fallback offline)
   └─> Sync quando voltar online
```

---

## 9. Design System (Cores, Tipografia)

- **Tema:** Light / Dark (auto-detect via OS)
- **Cores Primárias:** Azul (#0066CC), Verde (#00AA44)
- **Tipografia:** Inter (sans-serif), JetBrains Mono (código)
- **Spacing:** 8px grid
- **Componentes:** Shadcn/ui (React) para consistência

---

## 10. Acessibilidade

- ✅ WCAG 2.1 AA compliance
- ✅ Keyboard navigation completa
- ✅ Screen reader support (ARIA labels)
- ✅ Alto contraste opcionalmente
- ✅ Redução de animação (prefers-reduced-motion)
