---
name: refactor-arch
description: >
  Audita e refatora APIs web para o padrão MVC em 3 fases sequenciais: análise da
  stack, auditoria contra catálogo de anti-patterns (com confirmação do usuário) e
  refatoração validada. Agnóstica de tecnologia — detecta linguagem, framework e
  banco automaticamente. Use quando o usuário pedir para analisar, auditar ou
  refatorar a arquitetura de um projeto.
---

# refactor-arch — Auditoria e Refatoração Arquitetural

Refatoração arquitetural guiada por evidências. Funciona em qualquer stack (Python,
Node.js, etc.) e leva o projeto ao padrão MVC descrito em
`references/diretrizes-arquitetura.md`.

## Entrada

O alvo é o diretório de projeto passado como argumento. Sem argumento, use o
diretório atual. Nunca assuma a stack — ela é detectada na Fase 1.

## Regras invioláveis

1. As fases são **sequenciais**: 1 → 2 → 3. Nunca pule nem antecipe uma fase.
2. **Nenhum arquivo do projeto é modificado antes da confirmação explícita do
   usuário ao final da Fase 2.** As Fases 1 e 2 são somente leitura (exceto a
   gravação do relatório de auditoria).
3. O comportamento observável da API é preservado — mesmas rotas, mesmos contratos
   de request/response — exceto onde o relatório aprovado disser o contrário
   (ex.: remover senha do JSON de resposta é uma mudança de contrato aprovada).
4. Toda modificação da Fase 3 deve ser rastreável a um item do relatório aprovado.
   Não faça melhorias "de carona" que não foram aprovadas.

---

## Fase 1 — Análise

Leia `references/analise-projeto.md` e siga as heurísticas de lá.

1. Detecte linguagem, framework, banco de dados e gerenciador de dependências
   pelos arquivos de manifesto e imports — nunca por suposição.
2. Mapeie a arquitetura atual: quais camadas existem, qual a responsabilidade real
   de cada arquivo (não a sugerida pelo nome), e o fluxo de uma request da rota
   até o banco.
3. Registre o **baseline de execução**: comando para subir a aplicação, porta, e a
   lista de endpoints existentes (método + path). Esse baseline é o critério de
   validação da Fase 3.
4. Imprima o resumo no formato "Resumo da Fase 1" definido em
   `analise-projeto.md`.

Fase 1 é fotografia, não julgamento — não relate problemas ainda.

## Fase 2 — Auditoria

Leia `references/catalogo-antipatterns.md` e `references/template-relatorio.md`.

1. Varra o código-fonte cruzando com **cada** anti-pattern do catálogo, usando os
   sinais de detecção (grep pelos padrões + leitura dos arquivos suspeitos).
2. Para cada achado registre: severidade, `arquivo:linha`, evidência (trecho real
   do código), impacto e correção proposta (referenciando o padrão do playbook).
3. Gere o relatório no formato do template e salve como `audit-report.md` na raiz
   do projeto alvo.
4. **PARE AQUI.** Apresente o resumo por severidade e pergunte explicitamente ao
   usuário quais correções aplicar: todas, por severidade (ex.: só CRITICAL+HIGH)
   ou por item. Não prossiga para a Fase 3 sem resposta.

## Fase 3 — Refatoração

Leia `references/diretrizes-arquitetura.md` e `references/playbook-refatoracao.md`.

1. Planeje a ordem de execução: primeiro a reestruturação de pastas/camadas MVC
   (se aprovada), depois as correções em ordem de severidade (CRITICAL → LOW).
   Aplique **somente** o que foi aprovado na Fase 2.
2. Para cada correção, use o padrão de transformação correspondente do playbook.
3. Refatore em passos pequenos; após cada passo estrutural, confirme que a
   aplicação ainda importa/carrega sem erro.
4. **Validação obrigatória** ao final:
   - Subir a aplicação com o comando do baseline da Fase 1.
   - Exercitar os endpoints principais (ex.: `curl`) e comparar as respostas com
     o baseline — status code e formato do corpo.
   - Se o projeto tiver testes, rodá-los.
5. Se a validação falhar, corrija antes de declarar concluído — nunca entregue a
   aplicação quebrada.
6. Relate o resultado: o que mudou (mapeado aos itens do relatório), o que foi
   validado e o que ficou pendente.
