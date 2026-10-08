# Preparação para hospedagem (não publicada automaticamente)

## Custos e aprovação (revisão de outubro de 2026)

**Nenhum serviço é criado automaticamente por este repositório.** Existem dois Blueprints:

- `render.preview.yaml`: API e PostgreSQL Free, **somente dados fictícios**. O banco gratuito expira após 30 dias e não deve ser usado como armazenamento permanente. A API Free pode hibernar e não permite SMTP de saída nas portas 25, 465 ou 587.
- `render.yaml`: configuração **paga** com web Starter e PostgreSQL Basic. Antes de importar, verificar o nome exato e preço do plano do banco no painel Render (a nomenclatura de planos mudou em 2026). A combinação de web Starter e Postgres Basic-256mb custa cerca de US$ 13/mês antes de extras, e o Blueprint agora fixa explicitamente `plan: basic-256mb` (nome legado aceito pelo Render). Não aprovar este Blueprint sem conferir a prévia de custos.

### Checklist antes de criar qualquer recurso

1. Escolher explicitamente **preview gratuito** ou **produção paga**; nunca usar dados reais no preview.
2. Abrir o Render Dashboard e conferir o plano Hobby (workspace) e o custo **por serviço e banco**, armazenamento, tráfego e minutos de build.
3. Conferir que a região do banco e da API é a mesma e que a variável `DATABASE_URL` usa a conexão interna.
4. Revisar os nomes dos recursos para evitar duplicar instâncias existentes e custos inesperados.
5. Conferir o caminho do Blueprint selecionado. O padrão `render.yaml` é **pago**.
6. Antes de habilitar produção: configurar SMTP por provedor compatível, verificar domínio/origens, habilitar backup e executar teste de restauração.
7. Após implantação **somente com autorização**, verificar `/api/health`, cadastrar conta fictícia e validar login, logout, recuperação, escrita e conflito de revisão.
8. **Não habilitar o script `auth-sync.js` no GitHub Pages**, nem importar registros do IndexedDB, até o teste completo e backup comprovado.

Documentação oficial: https://render.com/pricing e https://render.com/docs/free.


O `render.yaml` descreve um serviço web Flask/Gunicorn e um PostgreSQL gerenciado no Render. **Os planos definidos podem gerar cobrança**: confira preços e limites atuais no painel do provedor antes de criar os recursos.

## Passos de configuração

1. Revise o PR e aguarde os testes da GitHub Actions.
2. Conecte o repositório ao Render e revise o Blueprint. Não habilite implantação antes de confirmar os custos.
3. O Render injeta `DATABASE_URL` a partir do banco gerenciado. Não publique essa variável em GitHub Pages ou arquivos versionados.
4. Use HTTPS na API. `AGENDA_ALLOWED_ORIGINS` deve listar somente os frontends autorizados.
5. Verifique `GET /api/health` e os fluxos de autenticação com contas de teste.
6. **Não habilite o envio de dados reais** antes de revisar a autenticação cross-site: GitHub Pages (`github.io`) e Render (`onrender.com`) são sites distintos; cookies `SameSite=None; Secure` podem ser bloqueados por políticas de terceiros.
7. Configure backups e retenção do banco, recuperação de conta, rate limiting persistente e monitoramento antes de produção.

## Persistência

- `DATABASE_URL` definida: PostgreSQL com `psycopg`.
- `DATABASE_URL` ausente: SQLite local para desenvolvimento/testes.
- Dados do navegador (IndexedDB) continuam independentes e **nunca são apagados pela API**.

## Limitações conhecidas

- A interface experimental usa Bearer em memória; não depende de cookies de terceiros.
- Recuperação de senha exige SMTP real; verificação de e-mail ainda não foi implementada. Rate limiting usa banco compartilhado, mas requer revisão de abuso distribuído.
- O controle de revisão retorna 409 em conflito, mas a primeira gravação simultânea do mesmo ID precisa de teste de concorrência e tratamento de violação de chave única.
- A interface só envia cópias manualmente e não baixa dados da nuvem para IndexedDB.
- O frontend ainda exige informar manualmente a URL da API.

## Checklist obrigatório antes do merge e do uso real

- [ ] GitHub Actions verde em **unit**, **postgres** e **PWA checks** no último commit.
- [ ] Validar os cookies de sessão em Android Chrome com frontend em github.io e API em domínio externo; se bloqueados, projetar autenticação compatível antes de lançar.
- [x] Rate limiter compartilhado no banco; ainda avaliar proxy, IP real e mitigação de abuso distribuído.
- [x] Recuperação e revogação de sessões implementadas; [ ] configurar SMTP e verificação de e-mail.
- [ ] Testar concorrência de escrita de mesmo ID no PostgreSQL, inclusive inserção simultânea.
- [ ] Criar teste E2E de migração, retorno offline, duplicações, conflito, dados de configurações e exportação/recuperação de backup.
- [ ] Revisar implantação HTTPS, CORS, proxy e cookies; ativar backups automáticos do banco com teste de restauração.
- [ ] Revisar limites de armazenamento e paginação de sincronização; não há exclusão/tombstones nem download automático para IndexedDB.
- [ ] Validar UX mobile e acessibilidade da tela de conta.
- [ ] **Não publicar o frontend de login antes de uma API operacional e validada.**

## Solução adotada para cookies de terceiros

A interface experimental usa `Authorization: Bearer` e `credentials: "omit"`. O token aleatório é guardado **somente em memória JavaScript**; ao recarregar a página é necessário entrar novamente. Não use `localStorage` nem IndexedDB para armazenar o token sem revisão de segurança. O backend mantém cookies HttpOnly como compatibilidade, mas a interface não depende deles. Como a API aceita `Authorization`, o preflight CORS precisa permitir esse cabeçalho e origens restritas. Os tokens devem ser protegidos contra XSS; o frontend não pode injetar HTML não confiável. Para produção, adotar sessões de curta duração, rotação/renovação e revogação adequada.

**Ainda não liberar produção:** rate limiter já usa banco compartilhado; recuperação de senha exige SMTP e ainda falta verificação de e-mail. Esses itens precisam de infraestrutura externa e validação antes de criar contas reais.

## Teste de conectividade sem escrita

Após implantar o commit que contém esta rota, abra `https://minha-agenda-api-teste.onrender.com/api/health/db`.
- `200` e `{"status":"ok","database":"connected"}`: a API consegue consultar o banco configurado.
- `503` e `{"status":"error","database":"unavailable"}`: verificar os logs privados do Render, a variável `DATABASE_URL`, a região e o status do PostgreSQL.

A consulta usa apenas `SELECT 1`, sem criar usuários ou registros. **Ela verifica o banco configurado, mas não prova isoladamente que ele é PostgreSQL**: confirme no Render que `DATABASE_URL` aponta para a instância PostgreSQL correta. A nova rota só estará disponível depois de implantar o commit atualizado; um `404` antes disso é esperado.
