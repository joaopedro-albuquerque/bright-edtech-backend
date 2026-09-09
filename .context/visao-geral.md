# Visão Geral do Produto

## O que é Bright EdTech?

Bright EdTech é uma plataforma SaaS educacional ("Smart EdTech") focada em **aprendizagem ativa e retenção de longo prazo**. Diferencia-se de leitores de PDFs genéricos ou chats de IA ao funcionar como um **copiloto de estudos** inteligente.

## Proposta de Valor

### Automatização de Artefatos de Revisão
A plataforma gera automaticamente, via IA, três tipos de artefatos a partir de documentos:
1. **Resumos** — Síntese inteligente do conteúdo (3 modelos suportados)
2. **Flashcards** — Cartões de revisão para retenção
3. **Quizzes** — Questões para auto-avaliação

### Otimização do Aprendizado
Utiliza um algoritmo de **Repetição Espaçada (Spaced Repetition / SM-2)** que:
- Determina quando cada item deve ser revisado
- Ajusta dificuldade com base na performance do usuário
- Maximiza retenção com custo cognitivo mínimo

## Fluxo de Usuário Principal

```
1. Cadastro + Onboarding
   └─> Perfil Global (objetivo, estilo, ritmo)

2. Upload de PDF
   └─> IA gera Resumos, Flashcards, Quizzes
   └─> Artefatos salvos em S3

3. Daily Mix (Revisão Diária)
   └─> Sistema busca itens para revisar hoje
   └─> Usuário responde e classifica dificuldade
   └─> Algoritmo recalcula próxima revisão

4. Repeat
   └─> Engajamento contínuo via notificações e dashboard
```

## Objetivos de Negócio

- ✅ Aumentar retenção de conhecimento (vs. leitura passiva)
- ✅ Reduzir tempo de estudo efetivo
- ✅ Criar hábitos de revisão sustentáveis
- ✅ Gerar receita via SaaS (modelo freemium → premium)

## Usuários-Alvo

- Estudantes de cursos online
- Profissionais em certificações
- Alunos de graduação/pós-graduação
- Qualquer pessoa que estude com PDFs
