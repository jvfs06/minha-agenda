# Preparação para hospedagem (não publicada automaticamente)

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

- Fluxo de sessão entre domínios depende de política de cookies do navegador.
- Ainda faltam recuperação/verificação de e-mail, proteção robusta contra brute-force e testes integrados em PostgreSQL.
- O controle de revisão retorna 409 em conflito, mas a primeira gravação simultânea do mesmo ID precisa de teste de concorrência e tratamento de violação de chave única.
- A interface só envia cópias manualmente e não baixa dados da nuvem para IndexedDB.
- O frontend ainda exige informar manualmente a URL da API.

## Checklist obrigatório antes do merge e do uso real

- [ ] GitHub Actions verde em **unit**, **postgres** e **PWA checks** no último commit.
- [ ] Validar os cookies de sessão em Android Chrome com frontend em github.io e API em domínio externo; se bloqueados, projetar autenticação compatível antes de lançar.
- [ ] Trocar o rate limiter em memória por armazenamento compartilhado (Redis ou solução gerenciada), com políticas para login e cadastro e logs seguros.
- [ ] Adicionar recuperação e verificação de e-mail, fluxo de redefinição de senha e revogação de sessões.
- [ ] Testar concorrência de escrita de mesmo ID no PostgreSQL, inclusive inserção simultânea.
- [ ] Criar teste E2E de migração, retorno offline, duplicações, conflito, dados de configurações e exportação/recuperação de backup.
- [ ] Revisar implantação HTTPS, CORS, proxy e cookies; ativar backups automáticos do banco com teste de restauração.
- [ ] Revisar limites de armazenamento e paginação de sincronização; não há exclusão/tombstones nem download automático para IndexedDB.
- [ ] Validar UX mobile e acessibilidade da tela de conta.
- [ ] **Não publicar o frontend de login antes de uma API operacional e validada.**

## Solução adotada para cookies de terceiros

A interface experimental usa `Authorization: Bearer` e `credentials: "omit"`. O token aleatório é guardado **somente em memória JavaScript**; ao recarregar a página é necessário entrar novamente. Não use `localStorage` nem IndexedDB para armazenar o token sem revisão de segurança. O backend mantém cookies HttpOnly como compatibilidade, mas a interface não depende deles. Como a API aceita `Authorization`, o preflight CORS precisa permitir esse cabeçalho e origens restritas. Os tokens devem ser protegidos contra XSS; o frontend não pode injetar HTML não confiável. Para produção, adotar sessões de curta duração, rotação/renovação e revogação adequada.

**Ainda não liberar produção:** rate limiter atual é por processo (não compartilhado entre workers); faltam recuperação de senha e verificação de e-mail. Esses itens precisam de infraestrutura externa e validação antes de criar contas reais.
