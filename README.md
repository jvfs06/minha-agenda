# Minha Agenda Semanal — PWA

## Publicação no GitHub Pages
1. Crie um repositório **público** no GitHub (ex.: `minha-agenda`).
2. Envie **o conteúdo desta pasta** para a raiz do repositório (`index.html`, `manifest.webmanifest`, `service-worker.js` e a pasta `icons`).
3. Abra **Settings → Pages** e, em **Build and deployment**, escolha **Deploy from a branch**. Selecione `main` e `/ (root)`, depois **Save**.
4. Aguarde a publicação e abra `https://SEU-USUARIO.github.io/minha-agenda/`.
5. No Chrome do Android, abra o endereço e use o menu ⋮ → **Instalar app** (ou **Adicionar à tela inicial**).

## Notas
- O aplicativo funciona offline depois da primeira visita online, quando o cache é instalado.
- Marcações são locais ao navegador/aparelho e separadas por semana; não há sincronização nem login.
- Repositórios GitHub Pages públicos tornam o conteúdo publicado acessível a outras pessoas. Evite dados sensíveis.
- Atualizações no código podem levar algum tempo para aparecer no aparelho; feche e reabra o app ou atualize a página.
- A instalação PWA exige HTTPS ou localhost; abrir `index.html` pelo gerenciador de arquivos não ativa o service worker.
