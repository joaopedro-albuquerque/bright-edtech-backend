# Contexto do Projeto - Plataforma EdTech

Este documento serve como base de contexto para a inteligência artificial, detalhando o escopo do projeto, funcionalidades, páginas e fluxos de usuário mapeados na arquitetura (referência: `bright-edtech.jpg`).

---

## 1. Status de Desenvolvimento (Checklist)
> **Instrução:** Marque com `[x]` o que já foi desenvolvido e deixe `[ ]` para o que falta ser desenvolvido antes de enviar este documento para a próxima etapa ou para a IA.

### Módulo de Identidade e Acesso
- [ ] **Landing Page**: Página única de vendas do produto.
- [ ] **Login e Cadastro**: Via e-mail/senha ou Google Auth (Página de cadastro em pop-up).
- [ ] **Esqueci a senha**: Fluxo de recuperação.
- [ ] **Onboarding / Captura de Perfil (1º acesso)**: Formulário interativo (ex: "O que você está estudando hoje?") para "ensinar" a IA sobre o perfil do estudante. Os dados devem ser salvos no banco para contexto.
- [ ] **Gestão da conta do usuário**: Tela para trocar senha, trocar e-mail e deletar conta.

### Dashboard / Página Principal (Visão Geral)
- [ ] Visualização dos 5 últimos resumos gerados.
- [ ] Visualização dos 5 últimos conjuntos de flashcards criados.
- [ ] Seção "Pontos de Atenção" baseada nas dificuldades detectadas pela IA.
- [ ] Atalho (pop-up) para subir documentos rapidamente.
- [ ] Barra lateral de navegação e atalho para o perfil.

### Gestão de Documentos e Criação de Resumos
- [ ] **Geração de resumos**: A partir de PDF (ex: aula via Drag and Drop) ou de um tema fornecido à IA.
- [ ] **Geração de questionários**: A partir de um resumo, PDF ou tema fornecido.
- [ ] Definição de nomenclatura do documento, seção e subseções/blocos de estudo.
- [ ] **Galeria de Estudos / Gestão de Diretórios**: Área de visualização centralizada para todos os resumos e questionários.

### Módulo de Flashcards
- [ ] **Geração de flashcards**: A partir de um resumo, PDF ou tema.
- [ ] Listagem dos últimos flashcards criados e botão "Criar novo".
- [ ] Seleção de nome do deck e atrelamento de documentos base (máx. 2 por deck).
- [ ] **Visualização de Flashcards**: Interface de interação para estudos (UI do Flashcard).

---

## 2. Detalhamento dos Fluxos de Usuário (Referência Visual)

*   **Onboarding & 1º Acesso:** Landing Page $ightarrow$ Pop-up de Cadastro $ightarrow$ Captura de Informações (Formulário) $ightarrow$ Salvar no banco $ightarrow$ Visão Geral.
*   **Página Principal:** O usuário tem acesso rápido aos últimos 5 resumos e flashcards, além de poder iniciar o fluxo de upload de documentos (pop-up) diretamente do dashboard.
*   **Gestão de Documentos:** Acessado via barra lateral $ightarrow$ Página de geração (Drag & Drop ou IA) $ightarrow$ Preenchimento de metadados (nome, diretório) $ightarrow$ Criação finalizada e visível nos diretórios.
*   **Criação de Flashcards:** Acessado via barra lateral $ightarrow$ Listagem $ightarrow$ Criar novo $ightarrow$ Definir Deck e documentos base $ightarrow$ Cartões gerados $ightarrow$ UI de Estudo.
*   **Gestão da Conta:** Acessado pelo ícone de perfil no canto superior direito $ightarrow$ Opções de edição de credenciais ou exclusão da conta.

