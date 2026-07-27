# Análise de Projeto — Heurísticas de Detecção

Objetivo: identificar a stack e mapear a arquitetura real do projeto **por
evidência**, nunca por suposição. Toda conclusão deve citar o arquivo que a
sustenta.

## 1. Detecção de linguagem e gerenciador de dependências

Procure arquivos de manifesto na raiz do projeto (nesta ordem de confiança):

| Arquivo | Linguagem | Gerenciador |
|---|---|---|
| `package.json` | JavaScript/TypeScript | npm/yarn/pnpm (confirme pelo lockfile) |
| `requirements.txt`, `pyproject.toml`, `Pipfile` | Python | pip/poetry/pipenv |
| `go.mod` | Go | go modules |
| `pom.xml`, `build.gradle` | Java/Kotlin | maven/gradle |
| `Gemfile` | Ruby | bundler |
| `composer.json` | PHP | composer |

Se houver mais de um manifesto, o projeto é poliglota — trate cada parte
separadamente. Confirme a linguagem contando as extensões dos arquivos-fonte
(`.py`, `.js`, `.ts`, ...), ignorando `node_modules/`, `venv/`, `dist/`,
`__pycache__/`.

## 2. Detecção de framework

Leia as dependências do manifesto e os imports dos arquivos de entrada:

| Sinal | Framework |
|---|---|
| `from flask import` / `Flask(__name__)` | Flask |
| `from fastapi import` | FastAPI |
| `from django` / `manage.py` | Django |
| `require('express')` / `import express` | Express |
| `@nestjs/` | NestJS |
| `require('fastify')` | Fastify |

## 3. Detecção de banco de dados e camada de acesso

| Sinal | Banco / Camada |
|---|---|
| `sqlite3.connect(...)`, `require('sqlite3')` | SQLite, acesso direto (sem ORM) |
| `SQLAlchemy`, `db.Model`, `db.Column` | ORM SQLAlchemy |
| `sequelize`, `prisma`, `typeorm` | ORM Node.js |
| `psycopg2`, `pg`, `mysql2` | Postgres/MySQL, driver direto |
| `pymongo`, `mongoose` | MongoDB |
| String de conexão em config (`DATABASE_URI`, `:memory:`) | anote a origem dos dados |

Registre também **onde** o schema é criado: migrations, `create_all()`, DDL
inline no código (sinal de problema para a Fase 2, mas aqui apenas registre).

## 4. Mapeamento de arquitetura

Para cada arquivo-fonte, registre a responsabilidade **real** (lendo o
conteúdo), não a sugerida pelo nome. Um `models.py` pode conter SQL, regra de
negócio e formatação de resposta ao mesmo tempo.

Classifique cada arquivo nas camadas:

- **Rotas/HTTP** — registro de endpoints, parsing de request, status codes
- **Controller** — orquestração entre HTTP e domínio
- **Serviço/Domínio** — regra de negócio
- **Acesso a dados** — queries, ORM, conexão
- **Config/Bootstrap** — inicialização, variáveis, CORS
- **Misto** — mais de uma das anteriores (anote quais)

Trace o fluxo de 1–2 endpoints representativos: rota → função → query →
resposta. Isso revela o acoplamento real entre camadas.

## 5. Baseline de execução

Registre (será usado na validação da Fase 3):

1. Comando para subir a aplicação (`python app.py`, `npm start`, ...) — confirme
   no manifesto (`scripts.start`) ou no `if __name__ == "__main__"`.
2. Porta e host.
3. Lista completa de endpoints: método HTTP + path + função handler.
4. Dependência de estado: precisa de seed? O banco é em memória (dados se perdem
   no restart)?

## Resumo da Fase 1 (formato de saída)

```markdown
## Resumo da Análise — <nome do projeto>

- **Linguagem:** <linguagem + versão se detectável>
- **Framework:** <framework>
- **Banco:** <banco + forma de acesso (ORM/driver direto/concatenação)>
- **Execução:** `<comando>` (porta <n>)

### Arquitetura atual
| Arquivo | Camada(s) | Responsabilidade observada |
|---|---|---|
| ... | ... | ... |

### Endpoints (<total>)
| Método | Path | Handler |
|---|---|---|
| ... | ... | ... |

### Observações estruturais
- <camadas ausentes, arquivos mistos, fluxo request→banco>
```
