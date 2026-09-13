# Migração de Conta AWS — Frontend + Backend

## Por que migramos

A conta AWS original (`871341458526`) não conseguia:
1. Criar uma **CloudFront Distribution** (bloqueio da conta, nunca totalmente esclarecido)
2. Habilitar **modelos atuais do Bedrock** (Anthropic/Nova — resolvido à parte trocando a geração de IA pra API do Gemini, ver [`ia-generativa.md`](ia-generativa.md))

A migração foi feita em **três etapas**:
- **Parte 1 (frontend/CloudFront/DNS):** feita primeiro, com o backend ainda na conta antiga
- **Parte 2 (backend completo):** migrando ECS + RDS + S3 de documentos também pra conta nova, seguida da exclusão de tudo na conta antiga (`871341458526`)
- **Parte 3 (limpeza de uma terceira conta órfã):** durante a Parte 1, descobrimos que existia uma **terceira conta AWS** (`765607524508`), de uma tentativa de infraestrutura ainda mais antiga, com uma CloudFront Distribution esquecida segurando os domínios `brightedtech.com.br`/`www` (ver perrengue 1). Depois de resolvido o conflito de CNAME, voltamos nessa conta pra fazer a limpeza completa também.

Hoje, **tudo em produção** roda na conta nova (`818651033737`) — as outras duas contas antigas foram completamente desligadas (ver seção "Estado final").

---

## O que foi feito (visão geral, estado atual)

```
Domínio brightedtech.com.br (registro.br)
        │
        ▼ (nameservers apontando pra conta nova)
Route 53 Hosted Zone — conta NOVA (818651033737)
        │
        ├── brightedtech.com.br  ──┐
        ├── www.brightedtech.com.br ─┤──► CloudFront Distribution ──► S3 (bucket privado, OAC)
        │
        └── api.brightedtech.com.br  ──┐
            backend.brightedtech.com.br ─┤──► ALB ──► ECS Fargate ──► RDS PostgreSQL (privado)
                                                                   └─► S3 (documentos)
                                        (tudo na conta NOVA agora)

Acesso administrativo ao RDS: Client VPN (mesmo padrão de antes, recriado na conta nova)
```

---

## Parte 1 — Passo a passo (Frontend/CloudFront/DNS)

### 1. Acesso administrativo na conta nova

Em vez de dar `AdministratorAccess` direto a cada usuário, criamos um **IAM Group**:

1. IAM → User groups → `Administradores` → policy `AdministratorAccess` anexada
2. Cada pessoa (sócios inclusos) ganha um IAM User próprio, adicionado a esse grupo
3. Quem precisa de CLI gera uma Access Key e configura um profile local:
   ```bash
   aws configure --profile rootbrightedtech
   ```
4. Teste: `aws sts get-caller-identity --profile rootbrightedtech` deve retornar a conta `818651033737`

**Por quê:** único ponto de controle de permissão (tira/põe gente do grupo em vez de mexer em policy por usuário), e cada pessoa tem sua própria identidade (rastreável no CloudTrail).

---

### 2. Bucket S3 privado para o frontend

Criado via CloudFormation (não manual), reaproveitando o padrão já usado no projeto:
[`cloudformation/cf-bright-ed-tech-s3-front-cloudfront.yaml`](../cloudformation/cf-bright-ed-tech-s3-front-cloudfront.yaml)

- Bucket: `prod-brightedtech-frontend-cf-818651033737`
- **Block Public Access: ON** (diferente do bucket antigo, que era 100% público via website hosting) — esse é privado porque quem serve os arquivos é o CloudFront, não o S3 direto
- Deploy: CloudFormation console → Create stack → upload do template

**Por quê:** servir estático via CloudFront + Origin Access Control (OAC) é mais seguro (bucket não fica exposto na internet) e mais rápido (CDN com cache nas edge locations) que o bucket-website antigo.

Depois de criado: build do React (`npm run build`) enviado manualmente pro bucket via console (Upload).

---

### 3. Certificado ACM (`us-east-1`, obrigatório pro CloudFront)

1. Certificate Manager → Request certificate → Public
2. Domínios: `brightedtech.com.br` + `www.brightedtech.com.br`
3. Validação: DNS

**Por quê a região importa:** CloudFront só aceita certificados ACM emitidos em `us-east-1`, independente de onde a maioria dos outros recursos estiver.

---

### 4. Route 53 Hosted Zone na conta nova

1. Route 53 → Create hosted zone → `brightedtech.com.br` (Public)
2. Zone ID: `Z02019453CUZDPO3T5NKE`
3. Nameservers gerados:
   ```
   ns-283.awsdns-35.com
   ns-645.awsdns-16.net
   ns-1882.awsdns-43.co.uk
   ns-1507.awsdns-60.org
   ```

---

### 5. Registros criados **antes** de trocar o nameserver

Pra não derrubar o backend (que estava sendo testado ativamente pelo front no momento da migração), criamos primeiro, na zona nova:

| Registro | Tipo | Valor |
|---|---|---|
| `api.brightedtech.com.br` | CNAME | `prod-brightedtech-alb-2029409732.us-east-1.elb.amazonaws.com` |
| `backend.brightedtech.com.br` | CNAME | mesmo ALB acima |

E o CNAME de validação do certificado ACM (gerado automaticamente pelo pedido do passo 3).

**Por quê essa ordem importa:** o nameserver é trocado no registrador (fora da AWS) e a propagação não é instantânea nem controlável — no momento em que qualquer resolvedor de DNS pelo mundo passa a usar a zona nova, ela precisa **já ter todos os registros que estavam funcionando antes**, senão esses subdomínios somem do ar durante a transição.

---

### 6. Troca de nameserver no registro.br

No painel do registro.br, os 4 nameservers antigos (AWS, conta antiga) foram substituídos pelos 4 novos do passo 4. Propagação neste caso foi rápida (minutos, não as ~24-48h que o pior caso permite).

---

### 7. Validação do certificado

Assim que a zona nova ficou autoritativa, o CNAME de validação passou a ser visível publicamente e o ACM validou o certificado (`Issued`).

---

### 8. CloudFront Distribution

Criada via console (CLI esbarrou nos perrengues da seção abaixo):

- **Origin:** bucket S3 do passo 2, com **Origin Access Control (OAC)** — a opção "Grant CloudFront access to origin: Yes" já resolve a bucket policy automaticamente, sem precisar copiar/colar manual
- **Alternate domain names:** `brightedtech.com.br` + `www.brightedtech.com.br`
- **Certificado:** o do passo 3 (`Issued`)
- **Cache policy:** `CachingOptimized` (gerenciada pela AWS)
- **Security protections (WAF):** habilitado — vem **incluso sem custo adicional** no plano (só a proteção contra DDoS L7 é paga, e nem aparece disponível sem plano Business)
- **Default root object:** `index.html` (configurado depois da criação, via `update-distribution`)
- **Custom error responses:** `403` e `404` → `/index.html`, código `200` (fallback pra rotas do React Router — sem isso, dar refresh numa rota tipo `/dashboard` quebra)

Distribution final: `E1GZDEJADF7JN` → `d2udh2uianioem.cloudfront.net`

---

### 9. Registros finais de DNS

Na zona nova, registros tipo **A (Alias)** apontando pra CloudFront (zona fixa `Z2FDTNDATAQYW2`, é a mesma pra qualquer distribution CloudFront de qualquer conta):

| Registro | Tipo | Aponta pra |
|---|---|---|
| `brightedtech.com.br` (raiz) | A (Alias) | `d2udh2uianioem.cloudfront.net` |
| `www.brightedtech.com.br` | A (Alias) | mesma distribution |

---

## Parte 2 — Passo a passo (Backend completo: ECS + RDS + S3 documentos)

Feita depois da Parte 1, pra consolidar tudo numa única conta e poder desligar a antiga de vez.

### 1. Rede base na conta nova

Deploy do mesmo template já usado na conta antiga, sem alterações:
[`cloudformation/cf-bright-ed-tech-base-network-security.yaml`](../cloudformation/cf-bright-ed-tech-base-network-security.yaml)

Cria: VPC, subnets públicas/privadas, security groups (ALB/ECS/RDS), bucket S3 de documentos
(`prod-brightedtech-client-docs-818651033737`), IAM roles do ECS.

**Por quê reaproveitar o template:** já era testado e correto (RDS privado, `PubliclyAccessible: false`,
sem rota de internet na subnet privada, SG do RDS só aceita tráfego do SG do ECS) — não precisou de
nenhum ajuste.

### 2. Banco de dados (RDS)

Deploy de [`cloudformation/cf-bright-ed-tech-database.yaml`](../cloudformation/cf-bright-ed-tech-database.yaml)
com uma senha nova gerada (`DBPassword`, parâmetro `NoEcho`). Endpoint resultante:
`prod-brightedtech-postgres-db.cwna6y2m03nu.us-east-1.rds.amazonaws.com`

### 3. Client VPN na conta nova (acesso privado ao RDS)

Mesmo padrão de antes, documentado em [`referencia-rapida.md`](referencia-rapida.md) — reaproveitamos
os **mesmos certificados** (PKI local com `easy-rsa`) já gerados anteriormente, só reimportando no ACM
da conta nova (certificados ACM não são compartilhados entre contas, mesmo sendo o mesmo arquivo `.crt`):

1. Reimportar `server.crt`/`server.key`/`ca.crt` (servidor) e `ca.crt`/`ca.key` (raiz de confiança dos
   clientes) no ACM da conta nova
2. Deploy de [`cloudformation/cf-bright-ed-tech-client-vpn.yaml`](../cloudformation/cf-bright-ed-tech-client-vpn.yaml)
3. Exportar o `.ovpn` novo (`aws ec2 export-client-vpn-client-configuration`) e embutir o certificado/chave
   do cliente (o mesmo `client1.eric.crt/key` de antes — não precisa gerar cliente novo)
4. **Trocar a conexão no AWS VPN Client:** desconectar o perfil da conta antiga e conectar o novo — as
   duas VPCs usam o mesmo CIDR (`10.0.0.0/16`), então **não dá pra manter as duas VPNs conectadas ao
   mesmo tempo**

### 4. Aplicar o schema no banco novo

Com a VPN conectada, banco acessível só de dentro da VPC:
1. `CREATE ROLE api_brightedtech WITH LOGIN PASSWORD '...'` (senha nova gerada — o schema.sql não cria
   esse role, só dá `GRANT` pra ele, então precisa criar manualmente antes)
2. Rodar [`schema.sql`](../schema.sql) inteiro
3. Reaplicar os `GRANT`s (ver [`dados.md`](dados.md#permissões-usuário-de-aplicação))
4. Validar com um `INSERT`/`DELETE` de teste usando o usuário da aplicação

### 5. Corrigir credenciais hardcoded no código

**Achado importante:** `app/core/database.py` tem o usuário/senha do banco **hardcoded direto no código-fonte**
(não lê de variável de ambiente, ao contrário do que `DB_HOST`/`DB_NAME` fazem). Precisou editar o arquivo
pra trocar a senha antiga pela nova antes de buildar a imagem — senão o app na conta nova ia tentar
autenticar no RDS novo com a senha do RDS antigo.

> ⚠️ Fica como dívida técnica: o ideal é esse usuário/senha vir de `os.getenv("DB_USER")`/`os.getenv("DB_PASSWORD")`,
> igual já é feito com `DB_HOST`/`DB_NAME` — hoje, toda vez que a senha do banco mudar, precisa mexer no
> código e rebuildar a imagem.

### 6. Imagem Docker + ECR na conta nova

ECR é um serviço **por conta** — a imagem que já existia no ECR da conta antiga não é visível na conta
nova. Precisou:
1. Criar um novo repositório ECR (`brightedtech-api`, tag immutability ligada)
2. Rebuild local da imagem (com o `database.py` corrigido)
3. Login + push pro ECR da conta nova

### 7. Stack de computação (ECS + ALB) na conta nova

Deploy de [`cloudformation/cf-bright-ed-tech-compute.yaml`](../cloudformation/cf-bright-ed-tech-compute.yaml)
com os parâmetros apontando pra recursos da conta nova:
- `AppImage` → imagem no ECR da conta nova
- `AcmCertificateArn` → certificado novo, emitido especificamente pra `api.brightedtech.com.br` +
  `backend.brightedtech.com.br` (o certificado do frontend, da Parte 1, **não cobre** esses subdomínios)
- `HostedZoneId` → o Hosted Zone da conta nova (`Z02019453CUZDPO3T5NKE`)

O template também tem `DB_HOST`/`DB_NAME`/`S3_BUCKET_NAME` **hardcoded** nas variáveis de ambiente do
container (não são parâmetros) — precisaram ser editados no arquivo antes do deploy, pros valores da
conta nova.

### 8. Corte de DNS final

Depois do ECS/ALB novo saudável (`target group: healthy`), os registros `api.`/`backend.` (que na Parte 1
eram CNAME temporário pro ALB da conta antiga) foram apagados, e a própria stack de compute recriou os
registros definitivos (tipo A/Alias) apontando pro ALB novo — mesmo padrão que já existia.

### 9. Validação end-to-end

`GET /` (health check) + `POST /profile` (grava no banco) testados direto em `https://api.brightedtech.com.br`
— confirmando ECS novo → RDS novo funcionando de ponta a ponta antes de desligar a conta antiga.

---

## Parte 3 — Limpeza da terceira conta órfã (`765607524508`)

Essa conta era de uma tentativa de infraestrutura **ainda mais antiga** que a "conta antiga" principal
(recursos datados de maio/2026, contra setembro/2026 da outra). Achada só porque uma CloudFront
Distribution esquecida lá segurava a reserva global dos domínios `brightedtech.com.br`/`www` (perrengue 1
da Parte 1). Varredura completa encontrou:

- **CloudFront Distribution** — já tinha sido apagada pelo usuário antes dessa limpeza (resolvendo o
  conflito de CNAME)
- **Certificado ACM** wildcard `*.brightedtech.com.br`, sem uso → excluído
- **Cognito user pool** `bright-website-users` (id `us-east-1_VI9tx818s`, **5 usuários reais**, diferente
  do pool já excluído na Parte 2) → excluído, mesma decisão consciente de não preservar autenticação antiga
  - Tinha **deletion protection ativada** e um **domínio Cognito associado** — precisou desativar a
    proteção (`update-user-pool --deletion-protection INACTIVE`) e apagar o domínio
    (`delete-user-pool-domain`) antes de conseguir apagar o pool em si
- **CloudWatch Log Group** `/ecs/task-bright-edtech-backend` → excluído
- **SSM Parameters** `/brightedtech/rds/db_user` e `/brightedtech/rds/db_password` (`SecureString`) → excluídos.
  Esses batem exatamente com o trecho **comentado** em `app/core/database.py` (busca de credenciais via
  `ssm.get_parameters_by_path`) — confirma que essa conta era de uma arquitetura anterior que usava
  Parameter Store em vez de credencial hardcoded
- **IAM Roles** `ecsTaskExecutionRole` e `Role-App-BrightEdTech` → excluídas (precisou primeiro
  `detach-role-policy` de tudo que estava anexado — **as duas tinham `AdministratorAccess` anexado
  diretamente na role**, o que já era um sinal de que essa infra antiga tinha permissões bem mais amplas
  do que deveria)

Mantido de propósito (mesmo critério da Parte 2): usuários IAM (`eric.martins`,
`github-actions-deploy-backend`, `github-actions-deploy-front`, `joao.cavalcante`, `miguel.magalhaes`) e
grupo `Founders-Admin-Developers`.

---

## Estado final

| Recurso | Onde está |
|---|---|
| Frontend (S3 + CloudFront) | Conta nova (`818651033737`) |
| Backend (ECS + ALB) | Conta nova (`818651033737`) |
| Banco de dados (RDS) | Conta nova (`818651033737`) |
| S3 de documentos | Conta nova (`818651033737`) |
| Client VPN (acesso DBeaver) | Conta nova (`818651033737`) |
| DNS (Route 53 Hosted Zone) | Conta nova |
| Domínio (registro.br) | Nameservers apontando pra conta nova |
| Cognito (usuários) | **Excluído nas duas contas antigas** — decisão consciente de não migrar, dados de autenticação antigos foram perdidos |
| Conta antiga (`871341458526`) | **Desligada por completo.** Confirmado por varredura total (CloudFormation, S3, EC2, RDS, Lambda, ECR, ALB, ECS, VPC, Route 53, ACM, Cognito, Secrets Manager, SSM, EIPs — todos vazios). Restam apenas os **usuários/grupo IAM**, mantidos de propósito |
| Terceira conta órfã (`765607524508`) | **Desligada por completo** (Parte 3 acima). Mesma exceção: usuários/grupo IAM mantidos |

---

## Perrengues

### 1. CNAME já em uso — 3 contas envolvidas ao mesmo tempo
Ao tentar criar a distribution definitiva, o erro `CNAMEAlreadyExists` apareceu **duas vezes**, por motivos diferentes:
- Primeira vez: uma distribution de teste ("só pra ver se dava certo criar uma distribution") já existia **na própria conta nova**, já reservando os domínios mesmo sem ter `Aliases` visível na config atual (reserva "fantasma" que só some depois de deletar de verdade).
- Segunda vez: havia **uma terceira conta AWS** (`765607524508`, de uma tentativa ainda mais antiga) com uma distribution esquecida usando os mesmos domínios.

**Lição:** domínio alternativo (CNAME) de CloudFront é único **globalmente**, não só dentro de uma conta — qualquer distribution, em qualquer conta AWS que você já tenha mexido, pode estar segurando a reserva.

### 2. Não dava pra deletar a distribution de teste
```
An error occurred (PreconditionFailed) when calling the DeleteDistribution operation:
You can't delete this distribution while it's subscribed to a pricing plan.
```
O CloudFront moderno anexa automaticamente um **WAF (WebACL)** a toda distribution nova, o que cria uma espécie de "assinatura" que bloqueia a exclusão direta. A solução veio pelo console (o usuário encontrou o fluxo específico pra cancelar isso antes de excluir — a via CLI pura não resolveu de primeira).

### 3. Certificado ACM demorando pra validar
Mesmo com o CNAME de validação já resolvendo publicamente (confirmado via `nslookup` contra `8.8.8.8` e `1.1.1.1`), o certificado ficou em `PENDING_VALIDATION` por um tempo — o ACM revalida em ciclos automáticos, não a cada consulta.
**Solução aplicada:** deletar o certificado pendente e pedir um novo — a AWS reaproveitou exatamente o mesmo token de validação (já resolvendo), e o novo certificado saiu `Issued` quase na hora.

### 4. Comandos AWS CLI com caminho de arquivo no Git Bash
No Windows com Git Bash, o AWS CLI (binário Windows) não entende caminhos estilo Unix (`/c/Users/...`) passados via `file://`. Precisou converter pra caminho Windows (`C:\Users\...`) em todo `--change-batch`, `--distribution-config` etc.

### 5. Ordem de operações crítica pro backend não cair
Se os registros `api.`/`backend.` não tivessem sido criados na zona nova **antes** da troca de nameserver, o backend em produção (sendo testado ativamente pelo front) teria ficado fora do ar durante a janela de propagação.

### 6. Registro CNAME temporário conflitando com a própria stack (Parte 2)
Ao deployar a stack de compute na conta nova, ela falhou tentando criar os registros `api.`/`backend.`
tipo A/Alias:
```
RRSet of type A ... is not permitted because a conflicting RRSet of type CNAME
with the same DNS name already exists
```
Causa: os **próprios CNAMEs temporários da Parte 1** (criados pra não derrubar o backend durante a
troca de nameserver, apontando pro ALB da conta antiga) continuavam na zona. A stack de compute tenta
criar/possuir esses registros como recurso próprio (tipo A/Alias) — Route 53 não permite CNAME e A
coexistindo no mesmo nome. **Solução:** apagar os CNAMEs temporários antes de redeployar a stack —
isso causa um pequeno intervalo de indisponibilidade de `api.`/`backend.` até a stack recriar os
registros definitivos.

### 7. Certificado do frontend não cobre os subdomínios da API
O certificado ACM emitido na Parte 1 cobre só `brightedtech.com.br` + `www.brightedtech.com.br` — a
stack de compute precisa de um certificado que cubra `api.brightedtech.com.br` +
`backend.brightedtech.com.br`. Precisou emitir um **segundo certificado ACM** específico pra esses
subdomínios (mesmo fluxo de validação DNS de sempre).

### 8. Parâmetros do template com defaults da conta antiga
O `cf-bright-ed-tech-compute.yaml` tem `AcmCertificateArn` e `HostedZoneId` com valores **default**
apontando pra recursos da conta antiga (ARNs/IDs não são portáveis entre contas). O primeiro deploy na
conta nova falhou até esses dois serem passados explicitamente via `--parameter-overrides`.

### 9. Credenciais do banco hardcoded no código-fonte
Diferente de `DB_HOST`/`DB_NAME` (que vêm de variável de ambiente), o usuário/senha do PostgreSQL
estavam escritos direto em `app/core/database.py`. Passou despercebido até a aplicação tentar autenticar
no RDS novo com a senha do RDS antigo. Ver nota na Parte 2, passo 5 — fica registrado como dívida técnica.

### 10. "SG criado por fora" — não era bem isso
Suspeita inicial era de um security group criado manualmente (fora do CloudFormation) travando a
exclusão da VPC antiga. Na investigação, todos os SGs da VPC eram do CloudFormation — o bloqueio real
era o **RDS antigo ainda existir** (`available`, não deletado), com a ENI dele presa no
`RDSSecurityGroup`. `AWS::EC2::SecurityGroup` não pode ser excluído enquanto algo (mesmo que seja outro
recurso do próprio projeto) ainda estiver anexado a ele — e isso bloqueia a VPC inteira em cascata.
**Lição:** ao investigar falha de exclusão de VPC, checar ENIs ativas (`describe-network-interfaces`)
antes de suspeitar de recursos "escondidos" fora do IaC.

### 11. Stack de compute travada em `DELETE_IN_PROGRESS` mesmo com o ECS já `INACTIVE`
O recurso `AppService` (ECS Service) ficou reportando `DELETE_IN_PROGRESS` no CloudFormation por vários
minutos depois do serviço já estar `INACTIVE` no ECS — atraso de sincronização entre o ECS e o
CloudFormation. Só foi possível confirmar que realmente tinha terminado esperando
(`aws cloudformation wait stack-delete-complete`) — tentar excluir a stack de rede base antes disso falha
silenciosamente, porque o CloudFormation não deixa apagar uma stack cujos `Export`s ainda estão sendo
importados por outra stack (mesmo que essa outra já esteja no meio da própria exclusão).

### 12. RDS sem snapshot final = perda de dados permanente
A exclusão do RDS antigo foi feita com `--skip-final-snapshot` (decisão explícita, sem backup). Isso é
irreversível — qualquer dado que só existisse ali (e não tivesse sido migrado pro banco novo) foi perdido
de vez. Os backups automáticos diários anteriores (`rds:prod-brightedtech-postgres-private-*`) também
deixam de existir depois que a instância de origem é removida definitivamente após o período de retenção.

---

## Próximos passos (em aberto)

- [ ] Refazer o cadastro/onboarding dos usuários no Cognito da conta nova — o Cognito antigo foi excluído junto com o resto (usuários precisam se cadastrar de novo, autenticação não foi migrada)
- [ ] Mover `DB_USER`/`DB_PASSWORD` em `app/core/database.py` pra variável de ambiente (hoje hardcoded — ver perrengue 9)
- [ ] Revisar o WAF anexado à distribution nova (hoje sem custo, mas vale confirmar que não muda de plano no futuro)
- [ ] Revisar os usuários/grupo IAM remanescentes nas duas contas antigas (`eric.martins`, `github-actions-deployer`(s), `joao.cavalcante`, `miguel.magalhaes`, grupo `Founders-Admin-Developers`) — foram mantidos de propósito, mas as contas em si não têm mais nenhum recurso rodando; avaliar se faz sentido recriar esses acessos na conta nova e desativar de vez as antigas
- [x] Confirmar que a conta antiga (`871341458526`) foi totalmente desligada — feito em 2026-09-12, incluindo Cognito, snapshot manual do RDS e recursos residuais (bucket de templates do CloudFormation, ECR antigo, budget de monitoramento)
- [x] Confirmar que a terceira conta órfã (`765607524508`) foi totalmente desligada — feito em 2026-09-12 (Parte 3)

---

**Data da migração:** 2026-09-12 (Parte 1: frontend/CloudFront, Parte 2: backend completo, Parte 3: limpeza da terceira conta)
**Conta antiga:** `871341458526` (desligada)
**Terceira conta órfã:** `765607524508` (desligada)
**Conta nova:** `818651033737` (produção atual)
