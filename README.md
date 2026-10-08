# Minha Agenda 4.1 — PWA

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

## Novidades da versão 3

Na aba **Extras 3.0**: medidas físicas, cronômetro de descanso, calendário de consistência, flashcards de inglês, simulado demonstrativo da CNH, Pomodoro, tarefas da faculdade e tema claro/escuro.

Os dados continuam no banco IndexedDB **minha-agenda-v2** para preservar registros existentes. O backup exportado agora usa a versão 3, e a importação aceita backups 2 e 3. Os flashcards usam intervalos simples de 1, 3 ou 7 dias. As perguntas da CNH são exemplos didáticos, não um banco oficial. Cronômetros dependem de manter o aplicativo ativo; não há notificações em segundo plano.

**Antes de atualizar:** exporte seu backup JSON na aba Dados. Após atualizar, teste a importação e exportação. A aplicação não sincroniza dispositivos.

## Versão 4.0 — redesign mobile-first

- Navegação inferior em telas pequenas, cartões renovados, atalhos no dashboard, tipografia e cores consistentes.
- Mantém todas as páginas, formulários, ferramentas 3.0 e a estrutura IndexedDB `minha-agenda-v2` sem migração de dados.
- Importação/exportação JSON continuam com compatibilidade v2/v3 (formato de backup 3).
- Cache offline atualizado para incluir `v4.css` e `v4.js`.
- **Validação necessária antes do merge:** testar em celular e desktop, temas, navegação, treinos, estudos, ferramentas, backup JSON e uso offline. Exporte um backup antes de atualizar.

## Versão 4.1 — relatórios, calendário e qualidade

- Gráficos locais dos últimos 7 dias: exercícios registrados e minutos estudados.
- Dashboard configurável: treinos, estudo acumulado, último peso e prazos futuros; preferência salva em IndexedDB.
- Calendário mensal com compromissos próprios e prazos das tarefas da faculdade. Toque no dia para preencher a data do compromisso.
- Compromissos usam o novo tipo de registro `event`, incluído no backup JSON versão 3. O banco existente `minha-agenda-v2` permanece inalterado.
- Testes estáticos com `node --test tests/smoke.test.mjs`, executados automaticamente pelo GitHub Actions.

**Antes de publicar:** exporte o backup JSON. Valide manualmente as telas no celular, a importação/exportação, os temas e o uso offline. Os testes de fumaça não substituem testes completos de navegador.

## Versão 4.2 — banco CNH

- 35 questões educativas autorais em cinco temas, sorteio sem repetição no mesmo simulado, escolha de tema e de 5/10/20/35 perguntas (limitado ao tema).
- Feedback imediato com resposta correta e revisão dos erros; pontuação salva como estudo CNH no mesmo IndexedDB e backup existente.
- Conteúdo de prática **não oficial**, sem garantia de refletir a prova ou todas as atualizações normativas do DETRAN. Conferir fontes oficiais antes de estudar para a prova.
- Nenhuma alteração na versão do banco IndexedDB ou no formato do backup.

### Expansão para 100 questões

- Banco com 100 questões autorais em cinco temas; simulados de 30 perguntas; histórico de acertos por assunto, inclusive em simulados mistos.
- Resultados continuam em registros `study` no IndexedDB, exportados no backup JSON existente.
- Questões **não oficiais**, educativas e de revisão geral. Não substituem a legislação vigente, materiais do DETRAN ou questões reais do exame.

## Versão 4.3 — CNH ilustrada (Pernambuco)

- 50 questões **autorais** adicionais (total de 150), com seis ilustrações SVG didáticas originais e reutilizáveis, com texto alternativo. Não são imagens nem questões oficiais.
- Links de referência temática para os Manuais Brasileiros de Sinalização de Trânsito da SENATRAN. Os links **não** comprovam validação individual de cada questão; revisão pedagógica e normativa ainda necessária.
- Filtros: banco completo, somente ilustradas e revisão de questões erradas em simulados anteriores. Os erros são salvos no mesmo registro `study` em `cnhMistakeIds` e incluídos no backup existente.
- Ilustrações e scripts incluídos no cache offline. Nenhuma migração ou exclusão de dados.
- Para a prova em Pernambuco, conferir também as orientações atuais do DETRAN-PE. Nenhum item foi apresentado como questão oficial do DETRAN.

Fonte temática: https://www.gov.br/transportes/pt-br/assuntos/transito/senatran/manuais-brasileiros-de-sinalizacao-de-transito
