# Modelos de Resumo Suportados

A API suporta nativamente **3 tipos de síntese** através de System Prompts injetados via Amazon Bedrock.

## 1. Resumo Executivo

### Objetivo
Tópicos diretos e bullet points para **leitura dinâmica e rápida**.

### Características
- ✅ Máximo 5-7 bullet points principais
- ✅ Linguagem concisa e objetiva
- ✅ Sem explicações verbosas
- ✅ Ideal para revisão rápida

### Exemplo de Output

```markdown
# Fotossíntese: Resumo Executivo

## Tópicos-Chave

- **Definição:** Processo biológico que converte luz em energia química (ATP e NADPH)
- **Localização:** Cloroplastos (algas e plantas), em duas fases:
  - **Fase luminosa** (tilacoides): Absorção de luz, quebra de água
  - **Fase escura** (estroma): Fixação de CO₂ → glicose (Ciclo de Calvin)
- **Reação global:** 6CO₂ + 6H₂O + luz → C₆H₁₂O₆ + 6O₂
- **Importância:** Base da cadeia alimentar, produção de oxigênio atmosférico
- **Fatores limitantes:** Intensidade luminosa, concentração de CO₂, temperatura

## Palavras-Chave
fotossíntese, clorofila, ATP, NADPH, Ciclo de Calvin, oxigênio
```

### System Prompt Injetado (Pseudocódigo)
```
System: Você é um especialista em síntese acadêmica. 
Seu objetivo é extrair os 5-7 tópicos MAIS IMPORTANTES do texto fornecido.

Regras:
1. Use bullet points concisos (máx. 2 linhas por ponto)
2. Evite detalhes desnecessários
3. Mantenha linguagem técnica mas acessível
4. Inclua uma seção "Palavras-Chave" ao final
5. Formato: Markdown

Texto: [CONTEÚDO DO PDF]

Output esperado: Bullet points em Markdown
```

---

## 2. Método Cornell

### Objetivo
Formato de **anotação estruturada** que equilibra Perguntas-Gatilho, Notas de Estudo e Sumário.

### Características
- ✅ Dividido em 3 seções:
  1. **Perguntas-Gatilho** (coluna esquerda): Questões que estimulam recall
  2. **Notas de Estudo** (coluna direita): Respostas e explicações
  3. **Sumário** (rodapé): Revisão geral dos conceitos
- ✅ Ideal para estudo ativo e autoteste
- ✅ Facilita geração de Flashcards

### Exemplo de Output

```markdown
# Mitose: Método Cornell

## Perguntas-Gatilho | Notas de Estudo

| Pergunta | Resposta |
|--|--|
| O que é mitose? | Divisão celular que resulta em duas células-filhas geneticamente idênticas à célula-mãe. |
| Quais são as 4 fases? | Prófase, Metáfase, Anáfase, Telófase. |
| O que ocorre na prófase? | Cromossomos se condensam, nucléolo desaparece, centríolos se movem para os polos. |
| Função do fuso acromático? | Alinha cromossomos no plano equatorial e os separa nas fases posteriores. |
| Resultado final? | Duas células-filhas com mesmo número cromossômico (2n), prontas para interfase. |

## Sumário

Mitose é essencial para crescimento, reparação e reprodução assexuada. Garante transmissão fiel do material genético.

---

## Conceitos Relacionados
- Intérfase (preparação)
- Meiose (divisão reducional)
- Ciclo celular
```

### System Prompt Injetado
```
System: Você é um professor de biologia criando notas no formato Cornell.

Estrutura:
1. Esquerda (Perguntas-Gatilho): 5-8 questões que testam compreensão
2. Direita (Notas de Estudo): Respostas concisas e explicativas
3. Rodapé (Sumário): 2-3 linhas resumindo os conceitos-chave

Use Markdown com tabela para organizar Pergunta | Resposta

Texto: [CONTEÚDO DO PDF]

Output esperado: Nota Cornell estruturada
```

---

## 3. Fichamento Acadêmico

### Objetivo
Formato **formal e rigoroso** para pesquisa acadêmica e trabalhos científicos. Inclui Citações Diretas, Metodologia e Apreciação Crítica.

### Características
- ✅ Extração de **citações diretas** (com aspas)
- ✅ Identificação de **metodologia** (se aplicável)
- ✅ **Apreciação crítica**: limitações, relevância, implicações
- ✅ Formato citável (ABNT/APA ready)
- ✅ Ideal para monografias e dissertações

### Exemplo de Output

```markdown
# A Evolução da Internet: Um Fichamento Acadêmico

## Referência
LEINER, B. M., et al. A Brief History of the Internet. 1997.

## Tema Central
História técnica e social da evolução da Internet, desde ARPANET até a Web.

## Citações Diretas

> "ARPANET, desenvolvida em 1969, foi o primeiro protótipo de uma rede de computadores de longa distância." (p. 3)

> "A Transmissão de Controle de Protocolo (TCP) e o Protocolo de Internet (IP) emergiram como padrões dominantes." (p. 8)

## Metodologia

O trabalho adota abordagem histórica-descritiva, entrevistando pioneiros e analisando documentação técnica original. Cronologia estruturada: 1960s-1990s.

## Conceitos-Chave
- ARPANET
- TCP/IP
- WWW (Tim Berners-Lee)
- Comercialização da Internet
- Escalabilidade de protocolo

## Apreciação Crítica

**Pontos Fortes:**
- Perspectiva abrangente (técnica + social)
- Fontes primárias de autoridade
- Narrativa clara e acessível

**Limitações:**
- Focado em contexto ocidental (EUA/Europa)
- Dados até 1997 (desatualizado para era atual)
- Menos foco em implicações sociais contemporâneas

**Relevância Atual:**
Essencial para compreensão histórica. Recomendado complementar com leituras recentes sobre arquitetura de redes modernas (5G, blockchain).

## Palavras-Chave
Internet, ARPANET, TCP/IP, história da tecnologia, protocolos

---

## Referências Cruzadas
- Ver também: "Redes de Computadores II"
- Conecta com: "Segurança em Redes"
```

### System Prompt Injetado
```
System: Você é um acadêmico criando um fichamento estruturado para pesquisa científica.

Seções obrigatórias:
1. Referência: Título, autor, ano
2. Tema Central: 1-2 linhas do foco principal
3. Citações Diretas: Extrair 3-5 trechos verbatim com página (em aspas)
4. Metodologia: Abordagem usada pelo autor
5. Conceitos-Chave: Lista de 5-7 conceitos
6. Apreciação Crítica:
   - Pontos Fortes (2-3)
   - Limitações (2-3)
   - Relevância Atual (1-2 sentenças)
7. Palavras-Chave para indexação

Formato: Markdown estruturado, pronto para ABNT/APA

Texto: [CONTEÚDO DO PDF]

Output esperado: Fichamento acadêmico completo
```

---

## Comparação Rápida

| Aspecto | Executivo | Cornell | Fichamento |
|--|--|--|--|
| **Tempo de leitura** | 3-5 min | 10-15 min | 15-20 min |
| **Ideal para** | Revisão rápida | Estudo ativo | Pesquisa formal |
| **Geração de Flashcards** | Moderada | Excelente | Moderada |
| **Complexidade** | Baixa | Média | Alta |
| **Uso acadêmico** | Não | Sim | Sim (citável) |
| **Público-alvo** | Qualquer | Estudantes | Pesquisadores |

---

## Configuração de Modelo

### No Perfil Global
```json
{
  "usuario_id": "abc-123",
  "estilo_preferido": "cornell",
  "formato_preferido": "markdown"
}
```

### No Documento
```json
{
  "documento_id": "xyz-789",
  "modelo_resumo_override": "fichamento_academico"
}
```

### No Bedrock Request
```python
{
  "max_tokens": 2048,
  "system": f"{SYSTEM_PROMPT[modelo]}",
  "messages": [
    {
      "role": "user",
      "content": conteudo_extraido_do_pdf
    }
  ]
}
```

---

## Fluxo de Seleção de Modelo

```
1. Usuário clica [+ Novo Resumo]
2. API verifica:
   ├─ Existe config no documento? (Use)
   ├─ Existe config na pasta? (Use)
   └─ Senão, usa config global

3. Frontend envia POST /api/resumos
   └─> Payload: { documento_id, modelo: "cornell" }

4. Backend:
   ├─ Extrai texto do PDF (S3)
   ├─ Injeta System Prompt correto
   ├─ Envia para Bedrock (Claude 3.5 Sonnet)
   └─ Salva resposta em S3 como .md

5. Frontend:
   ├─ Busca arquivo em S3
   ├─ Renderiza em TipTap
   └─ Exibe [Editar] [Salvar]
```

---

## Future Extensions

- **Resumo Visual:** Diagramas e mindmaps (Claude Vision)
- **Resumo Comparativo:** Lado-a-lado de múltiplos PDFs
- **Resumo Custom:** Usuário define seu próprio template
- **Resumo Multiidioma:** Tradução automática
