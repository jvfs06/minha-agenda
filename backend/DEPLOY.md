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
