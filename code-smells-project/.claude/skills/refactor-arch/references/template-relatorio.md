# Relatório de Auditoria

Salvar como `audit-report.md` na raiz do projeto alvo. Preencher **todos** os
campos com evidência real do código — nunca placeholder genérico.

```markdown
# Relatório de Auditoria Arquitetural — <nome do projeto>

**Data:** <data ISO>
**Stack detectada:** <linguagem> / <framework> / <banco>
**Baseado na Fase 1:** ver "Resumo da Análise" acima

## Sumário executivo

<3-5 linhas: estado geral da arquitetura, principal risco, principal padrão de
duplicação/débito encontrado>

## Achados por severidade
| # | Severidade | Problema | Localização | Observações | Ação proposta |
|---|:----------:|---|---|---|---|
| 1 | CRITICAL | <nome do catálogo> | `arquivo:linha` | <observação se relevante> | <resumo curto da correção> |
| ... | | | | | |

## Detalhamento

### [CRITICAL-1] <Nome do anti-pattern>

- **Local:** `arquivo:linha`
- **Evidência:**
  ```<linguagem>
  <trecho real do código, não paráfrase>
  ```
- **Impacto:** <consequência concreta — o que pode dar errado e em que condição>
- **Correção proposta:** <padrão de transformação do playbook a aplicar,
  referenciando o nome exato da seção em playbook-refatoracao.md>
- **Risco da correção:** <baixo/médio/alto — ex. "muda contrato de resposta",
  "requer migração de dados">

<repetir para cada achado, agrupado por severidade: CRITICAL, HIGH, MEDIUM, LOW>

## Resumo por severidade

| Severidade | Quantidade |
|---|---|
| CRITICAL | N |
| HIGH | N |
| MEDIUM | N |
| LOW | N |

## Proposta de reestruturação MVC

<Se o projeto não segue MVC (ver diretrizes-arquitetura.md): estrutura de
pastas alvo, e para cada arquivo atual, o destino proposto. Se já segue MVC,
declare explicitamente e omita esta seção.>

## Pergunta de confirmação

Ao apresentar este relatório ao usuário, perguntar textualmente:

> Encontrei N problemas (C críticos, H altos, M médios, L baixos). Quais
> devo corrigir?
> 1. Todos
> 2. Apenas CRITICAL + HIGH
> 3. Selecionar itens específicos (informe os números)
> 4. Nenhum agora (só o relatório)

**Não prosseguir para a Fase 3 sem uma resposta explícita a esta pergunta.**
```

## Regras de preenchimento

- Cada achado referencia um item do `catalogo-antipatterns.md` pelo nome exato,
  para rastreabilidade entre catálogo → relatório → playbook.
- Evidência é sempre o código real lido do arquivo, nunca reescrito de memória.
- Achados que exigem decisão de produto (ex.: remover campo de senha da
  resposta muda o contrato consumido por um frontend) devem ter isso destacado
  em "Risco da correção" — o usuário decide se aceita a quebra de contrato.
- Ordene os achados por severidade decrescente; dentro da severidade, por
  facilidade de correção (mais simples primeiro), a menos que haja dependência
  entre eles (ex.: reestruturação de pastas precede correções pontuais que
  seriam refeitas de qualquer forma).
