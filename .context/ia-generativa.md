# IA Generativa — Histórico e Estado Atual (Bedrock vs Gemini)

> Serviço responsável: [`app/services/BedrockService.py`](../app/services/BedrockService.py). O nome da
> classe é histórico — hoje ela chama a **API do Gemini**, não o Bedrock (ver linha 1 do arquivo).

## Linha do tempo

### 1. Bedrock (Anthropic), conta antiga (`871341458526`)
Implementação original usava `boto3` + `bedrock-runtime`, com os modelos:
- `anthropic.claude-3-5-sonnet-20241022-v2:0` (resumos)
- `anthropic.claude-3-5-haiku-20241022-v1:0` (flashcards/quizzes)

**Quebrou em produção** (2026-09-11) com o erro:
```
ResourceNotFoundException: This model version has reached the end of its life.
```
Esses modelos 3.5 foram descontinuados pela AWS.

### 2. Tentativa de atualizar pros modelos Bedrock atuais
Trocamos pra `anthropic.claude-sonnet-5` e `anthropic.claude-haiku-4-5-20251001-v1:0`, mas a conta
antiga bloqueava **qualquer modelo atual** (não só Anthropic — testamos também `amazon.nova-lite-v1:0`
e deu o mesmo erro):
```
ValidationException: Operation not allowed
```
Investigando, o único jeito de destravar seria um **caso de suporte da AWS** (`create-foundation-model-agreement`
retornava `AccessDeniedException: You have not filled out the request form`), sem prazo garantido de resposta.

### 3. Solução aplicada: Gemini (produção atual)
Como havia urgência (front testando ativamente), restauramos a abordagem que o projeto já tinha usado
antes do Bedrock — havia um `GenerativeIAService.py` removido no commit `6b24391` que já fazia isso.

- Pacote: `google-genai` (voltou pro `requirements.txt`)
- Modelo: `gemini-3.6-flash` — o `gemini-2.5-flash` (que aparece listado na API) não está mais disponível
  pra contas novas (`This model is no longer available to new users`); `gemini-3.6-flash` foi confirmado
  funcionando via teste direto na API antes de integrar no código
- `GEMINI_API_KEY` está tanto no `.env` local quanto **hardcoded no `Default` do parâmetro `GeminiApiKey`**
  em [`cloudformation/cf-bright-ed-tech-compute.yaml`](../cloudformation/cf-bright-ed-tech-compute.yaml)
  — decisão consciente do time pra simplificar o deploy nessa fase, mesmo sabendo que normalmente uma
  secret não deveria ficar em texto puro num arquivo versionado
- Interface pública da classe (`gerar_resumo`, `gerar_flashcards`, `gerar_quiz`) foi mantida idêntica à
  versão Bedrock, então `ResumoService`, `FlashcardService` e `QuizService` não precisaram mudar nada

**Status:** ✅ em produção, validado ponta a ponta (`POST /documentos/{id}/flashcards` retornando `201`
com `modelo_ia: "gemini-3.6-flash"`).

### 4. Bedrock na conta nova (`818651033737`) — em andamento
Ao tentar habilitar o Bedrock na conta nova (818651033737, criada pra resolver o bloqueio de CloudFront —
ver [`migracao-conta-aws.md`](migracao-conta-aws.md)), o comportamento foi **diferente** do bloqueio
permanente da conta antiga:

1. Formulário de "use case details" da Anthropic foi preenchido com sucesso (diferente da conta antiga,
   que retornava `"Your account is not authorized... create a support case"` direto nesse formulário)
2. Modelo escolhido: **Claude Haiku 4.5**, via **Inference Profile "US Anthropic Claude Haiku 4.5"**
   (região `us-east-1`, não o profile "Global")
3. Ao testar no Playground, retornou:
   ```
   AccessDeniedException: Your account is currently being verified.
   Verification normally takes less than 2 hours...
   ```
   Essa é a verificação anti-fraude **padrão de contas AWS novas** — diferente do bloqueio estrutural
   da conta antiga. Expectativa é resolver sozinho em até ~2h; se persistir, contato é
   `aws-verification@amazon.com`.

**Status:** ⏳ aguardando a verificação da conta nova completar.

---

## ⚠️ Detalhe técnico se/quando voltar pro Bedrock

O modelo Claude Haiku 4.5 no Bedrock exige um **Inference Profile**, não aceita `InvokeModel` direto
com o ID puro do modelo. Isso muda o valor usado no código: em vez de
`anthropic.claude-haiku-4-5-20251001-v1:0`, o `modelId` passado pra `invoke_model` provavelmente
precisa ser o ID do profile, algo como `us.anthropic.claude-haiku-4-5-20251001-v1:0` (prefixo de
região). **Confirmar o ID exato do profile no console (Bedrock → Inference profiles) antes de trocar
o código de volta.**

Se um dia a conta nova estiver 100% liberada e a decisão for voltar pro Bedrock:
1. Confirmar o Inference Profile ID exato
2. Reverter `BedrockService.py` pra versão que usa `boto3` + `bedrock-runtime` (está no histórico do git,
   commit anterior a essa migração pro Gemini)
3. Atualizar `BEDROCK_MODEL_SUMMARY`/`BEDROCK_MODEL_EXTRACT` nas variáveis de ambiente da task ECS
4. Remover `google-genai` do `requirements.txt` e `GEMINI_API_KEY` do compute.yaml (ou manter os dois
   como fallback, se quiser redundância entre provedores)

---

**Última atualização:** 2026-09-12
