# Gates de validação da Folha — trabalho em ciclos

Estado: **PENDENTE de execução e evidência**. Não declarar concluído só porque os testes existem.

## Modelo e isolamento

Usar o mesmo endpoint/modelo local que o Nexus já configura, através de adaptador opcional e isolado. Não copiar pesos, segredos ou configurações privadas para este repositório público. O adaptador de IA só recebe uma pergunta delimitada quando o parser determinístico e a correção auxiliar não resolvem a intenção. A saída é uma **sugestão sem autoridade**, sujeita a validação determinística e confirmação humana. Sem modelo disponível, pedir esclarecimento humano e continuar funcional. Não instalar nem exigir Ollama.

## Matriz bidirecional

1. Texto original → intenção/estado → proposta visível → correspondência fiel com o texto original; preservar original byte-a-byte no limite UTF-8.
2. Ambiguidade → pergunta de esclarecimento → nova resposta → interpretação revista; nunca escolher silenciosamente.
3. Intenção resolvida → proposta específica → confirmação humana explícita → **apenas simulação no laboratório**. Sem confirmação, rejeição, expiração ou mudança de parâmetros → nenhuma execução.
4. Correção LanguageTool → shadow → nova interpretação; original intocado. Timeout, indisponibilidade ou resposta inválida → fallback seguro.
5. IA opcional → sugestão → validação → pergunta ao humano quando necessário. Erros, injeção de prompt, saída inválida ou divergência → fallback seguro.
6. Repetição, reinício e chamadas concorrentes → nenhuma confirmação reutilizada para outro pedido; nenhuma operação real.
7. Casos PT-PT: instruções positivas/negativas, citações, homónimos, erros, pontuação, espaços, Unicode, frases longas, contradições e entradas hostis.

## Ciclo obrigatório

Reproduzir FAIL → criar teste → correção mínima → regressão → E2E → publicar evidência (SHA, ambiente, número PASS/FAIL/SKIP e casos não resolvidos) → repetir. Não usar contagens sintéticas como substituto de diversidade semântica. O ciclo decorre em sessões efetivas de trabalho; o GitHub não executa autonomamente correções só porque este ficheiro existe.

## Conclusão

Folha abre e funciona realmente; sem seleção técnica manual; interpreta ou esclarece; exige confirmação para todas as propostas; não executa no laboratório; IA opcional segura e compatível com a configuração do Nexus; testes Windows e E2E verificados. Só então marcar TERMINADO. Não alterar o repositório principal.
