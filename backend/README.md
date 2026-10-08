# Minha Agenda — Backend Python (fase 1)

Esta pasta é uma **fundação isolada** de autenticação e sincronização. A interface atual continua funcionando em GitHub Pages, com IndexedDB. Nenhum dado existente é migrado ou excluído automaticamente.

## Executar localmente

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export AGENDA_ALLOWED_ORIGINS=http://localhost:8000
export AGENDA_SECURE_COOKIES=0
python app.py
```

A API abre em `http://127.0.0.1:5000`. Para o frontend local, sirva a aplicação em `http://localhost:8000` e use `credentials: "include"`. O navegador pode restringir cookies entre origens; em produção, hospede a API sob HTTPS com configuração adequada de cookies.

## Endpoints

- `GET /api/health`
- `POST /api/auth/register` — JSON `{"email":"...","password":"..."}`
- `POST /api/auth/login` — mesma estrutura
- `GET /api/auth/me`
- `POST /api/auth/logout` — JSON `{}`
- `GET /api/sync/records` e `GET /api/sync/settings`
- `PUT /api/sync/{collection}/{id}` — JSON `{"base_revision":0,"data":{"id":"..."}}` para registros, ou `{"key":"..."}` para configurações.

**Revisões:** o primeiro envio exige `base_revision: 0`; alterações seguintes usam a revisão retornada. Se outra versão já existir, retorna `409` com a versão remota. **Nunca sobrescreva automaticamente em caso de conflito.**

**Segurança e limitações:** tokens de sessão aleatórios são armazenados no servidor apenas como hash SHA-256 e enviados em cookie HttpOnly. Senhas usam PBKDF2-HMAC com salt. A API restringe origens e exige JSON nas mutações. Antes de disponibilizar publicamente, são necessários rate limiting distribuído, proteção contra abuso, HTTPS, política de recuperação/verificação de e-mail, observabilidade, backups do servidor e revisão do fluxo de cookies entre GitHub Pages e a API. O SQLite é apropriado para prototipação, não uma escolha definitiva de produção multi-instância. O backend não oferece exclusão remota ainda, propositalmente.

## Próxima etapa

Implementar no frontend uma tela de login **opcional**, botão **Pré-visualizar migração** e confirmação explícita antes de enviar dados locais. Manter o IndexedDB como fonte local; armazenar revisões separadamente; nunca limpar stores. Implementar reconciliação e testes com duas sessões antes de ativar sincronização automática.
