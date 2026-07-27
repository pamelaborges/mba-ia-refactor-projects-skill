# Guidelines de Arquitetura — Padrão MVC Alvo

Padrão de destino da Fase 3, adaptado para APIs web (sem view HTML — "View" é a
camada de rotas/serialização HTTP). Agnóstico de linguagem: os nomes de pasta
mudam por convenção da stack, as responsabilidades não.

## Camadas e responsabilidades

### Routes/Views — camada HTTP

**Responsabilidade única:** mapear método+path para um handler, extrair dados
do request (params/query/body) e devolver a resposta HTTP (status + corpo).

**Não deve conter:**
- Regra de negócio (cálculo, decisão condicional de domínio)
- Acesso direto a banco (SQL, sessão de ORM)
- Validação de regra de negócio (validação de *formato* de input é aceitável
  aqui — ex. "campo obrigatório presente"; validação de *regra* não —
  ex. "estoque suficiente")

**Convenção por stack:** Flask → Blueprints (`routes/*.py`); Express → Router
(`routes/*.js`); Django → `urls.py` + views finas.

### Controllers — orquestração

**Responsabilidade única:** receber dados já extraídos da camada HTTP, chamar o
serviço/domínio apropriado, traduzir o resultado (ou exceção) em uma resposta
apropriada. É a cola entre HTTP e domínio — não decide regra de negócio, decide
*como reportar* o resultado da regra.

**Não deve conter:** SQL, cálculo de negócio, efeito colateral direto (envio de
email real deve ser chamado através de um serviço, não implementado inline).

Em frameworks onde rota e controller costumam colapsar em uma função só (Flask
simples, Express simples), a separação mínima aceitável é: a função da rota
delega para uma função/classe de serviço testável sem HTTP; ela mesma só
traduz o retorno em `jsonify`/`res.json` + status code.

### Models — domínio e acesso a dados

Duas responsabilidades que **devem estar isoladas uma da outra** quando o
projeto crescer, mas no mínimo nunca misturadas com HTTP:

- **Modelo de domínio:** estrutura de dados + regras invariantes do próprio
  objeto (ex.: `is_overdue()`, `validate_priority()`). Não sabe o que é HTTP.
- **Acesso a dados (repository/DAO):** única camada autorizada a montar
  queries. Toda query usa parâmetros bindados — nunca concatenação de string
  com valor de request.

**Serviço/domínio (camada extra quando necessário):** regra de negócio que
orquestra mais de um model ou tem lógica não trivial (cálculo de desconto,
decisão de aprovação de pagamento, envio de notificação) vive aqui — não no
controller, não no model de dados puro.

## Regras de dependência (o que pode chamar o quê)

```
Routes  →  Controllers  →  Services/Domain  →  Models (data access)
```

- Uma camada só pode chamar a camada imediatamente abaixo (ou ela mesma).
  Routes não chamam Models diretamente; Models não chamam Controllers (sem
  dependência invertida).
- Segredos e configuração (chaves, connection string) vivem em variável de
  ambiente, lidos uma vez no bootstrap — nunca literal dentro de Models,
  Controllers ou Routes.

## Estrutura de pastas de referência

```
project/
├── app.py | app.js            # bootstrap: cria app, registra rotas, config
├── config.py | config.js       # lê variáveis de ambiente
├── routes/                     # uma por domínio (produtos, usuarios, pedidos)
├── controllers/                # uma por domínio, espelha routes/
├── services/                   # regra de negócio que não é 1:1 com um model
├── models/                     # um arquivo por entidade de domínio
│   └── <entidade>_repository   # acesso a dados, se separado do model
└── database.py | database.js   # conexão/pool, nunca lógica de negócio
```

Divisão "um arquivo por entidade" substitui um único `models.py`/model
monolítico contendo produtos+usuários+pedidos — cada entidade vira seu próprio
módulo, o que resolve diretamente o anti-pattern de baixa coesão do catálogo.

## Critérios de conformidade (checklist para a Fase 3)

- [ ] Nenhum arquivo de rota contém SQL ou regra de negócio de mais de uma
      linha de decisão
- [ ] Toda query usa parâmetros bindados
- [ ] Toda regra de negócio não trivial está em uma função/classe testável sem
      subir HTTP nem banco real (mock/stub aceitável)
- [ ] Segredos vêm de variável de ambiente
- [ ] Um domínio = um arquivo de model (não um arquivo com N domínios)
- [ ] O fluxo de dependência (Routes → Controllers → Services → Models) não
      tem atalhos nem ciclos

## O que **não** mudar sem aprovação explícita

Reestruturar pastas e mover código é refatoração estrutural aprovada por
default junto com o relatório. Mudanças de **contrato observável** (formato de
resposta, remoção de campo, novo código de status) exigem que o item do
relatório tenha sido explicitamente aprovado — ver `template-relatorio.md`.
