# Minha Agenda 2.0 — PWA

## Publicar no GitHub Pages

1. Crie um repositório no GitHub. No plano gratuito, o GitHub Pages requer repositório público.
2. Envie **o conteúdo desta pasta** à raiz do repositório (index.html, app.js, style.css, manifest.webmanifest, service-worker.js e a pasta icons).
3. Vá a Settings → Pages → Deploy from a branch → main → /(root) → Save.
4. Abra `https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/` no Chrome Android e use o menu Instalar aplicativo.
5. Atualizações: substitua os arquivos no repositório e recarregue o app quando estiver online.

## Executar localmente

Dentro desta pasta: `python3 -m http.server 8000` e abra http://localhost:8000/. Não abra via file://, pois recursos da PWA e IndexedDB podem ter restrições.

## Armazenamento e backup

Registros ficam apenas no IndexedDB do navegador/dispositivo. Não sincronizam com outros aparelhos. Use a aba **Dados → Exportar backup JSON** periodicamente. Na reinstalação, abra **Importar backup JSON**. O backup contém dados pessoais, guarde-o com cuidado.

## Migração da versão 1

A versão 2 usa um banco IndexedDB novo. Marcações da versão anterior que estavam em localStorage **não são importadas automaticamente**. Faça backup antes de substituir o aplicativo, se precisar preservar o histórico antigo.

## Treinos

Os exercícios seguem o plano de treino fornecido. Priorize técnica, descanso e atenção a desconforto no punho. Os horários são estimativas: se a sessão ultrapassar 30 min, não sacrifique a segurança.
