# Contrato de integração futura — Folha → Nexus

Estado: **proposta de contrato para testes; não está integrado nem aprovado como alteração ao Kernel**.

## Fronteira

A Folha produz uma proposta de interpretação, nunca um pedido de execução autorizado. Preserva sempre o texto original. O adaptador de integração futuro deverá receber a saída `ParsedInput.as_dict()` de `nexus/frontdoor.py` e verificar a validade do contrato antes de chamar a API **existente** do Host. Não criar segundo Host, Store, runner ou Kernel neste laboratório.

## Envelope sugerido (somente bancada)

```json
{
  "version": "folha-intent-v1",
  "status": "RESOLVED",
  "intent": "trabalhar",
  "original": "Corrige este texto",
  "content": "Corrige este texto",
  "parser": "eliza-rules-v1",
  "explicit": false,
  "shadow": null,
  "execution": "SIMULATED_ONLY"
}
```

A presença de `RESOLVED` **não autoriza** uma ação. O campo `execution` é exclusivo do laboratório e não deve ser enviado ao Host como privilégio.

## Comportamento

1. Frase livre → parser determinístico (prefixos explícitos têm precedência).
2. Em `UNRESOLVED`, correção auxiliar LanguageTool, quando disponível, sem substituir `original`; reinterpretar.
3. Se continuar `UNRESOLVED` ou houver várias intenções, perguntar em português claro na mesma Folha; não apresentar `process_id` ou botões de seleção técnica.
4. Se `RESOLVED`, consultar uma **tabela de correspondências autorizadas** no adaptador de integração futuro. A tabela não existe no laboratório; sete intenções não equivalem automaticamente aos dez processos do runner.
5. Uma sugestão de IA opcional pode ajudar a formular a pergunta ou sugerir uma intenção; não cria nem altera correspondências autorizadas e não executa nada.
6. Só o Host do Nexus pode validar permissões, executar em confinamento e gerir Creative/Human Gate/Canonical.

## Gates antes de integração

- Testes unitários e de propriedades do parser, preservação do original e correções.
- Conjunto de frases PT-PT novas, independentes das regras, com avaliação de acertos, recusas e falsos positivos.
- Testes de ambiguidade, negação, Unicode, anexos, falha LanguageTool, entradas adversariais e perguntas ao humano.
- Testes de contrato Folha ↔ adaptador de integração; sem modificar Kernel/Store/M1–M14.
- E2E real no repositório Nexus, **no mesmo SHA**, incluindo Host, Creative, aprovação humana, Canonical e reinício. Os testes simulados deste laboratório não substituem esse gate.

## Proveniência

Fonte: `PAPACREATOR/cerebro-parvo-`, branch `lab-e2e-frontdoor-20261004`, especialmente `nexus/frontdoor.py`, `nexus/frontdoor_rules.json`, `nexus/schemas/frontdoor_rules.json` e `nexus/adapters/languagetool.py`.

O repositório principal mantém-se intocado. A integração futura deve ser proposta, revista e testada no repositório principal, não copiada automaticamente.
