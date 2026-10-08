# Nexus Folha Lab

Bancada **isolada e sem autoridade** para experimentar a Folha branca e interpretação em português. Não executa ferramentas do Windows, não acede ao Kernel/Host/Store/Creative/Canonical e não altera o repositório principal.

## Proveniência

Extração controlada de `PAPACREATOR/cerebro-parvo-`, branch `lab-e2e-frontdoor-20261004`: `nexus/frontdoor.py`, `nexus/frontdoor_rules.json`, `nexus/schemas/frontdoor_rules.json`. O mecanismo `correction_shadow` é uma extração do adaptador `nexus/adapters/languagetool.py` da mesma branch; a lógica de reconhecimento da Front Door mantém-se. Esta bancada não declara que a integração com o Host está pronta.

## Arranque local

Requer Python 3.10+ e `pip install jsonschema pytest`. Executar `python -m folha_lab.server` e abrir `http://127.0.0.1:8765`. Testar com `python -m pytest -q`.

O LanguageTool é **opcional**: o endpoint de laboratório aceita diagnósticos JSON fornecidos explicitamente, sem iniciar Java nem consultar serviços externos. A IA é uma futura integração opcional e **não está implementada**; em ambiguidade, a Folha pergunta ao humano. A bancada apenas simula interpretações: não executa processos reais.

## Segurança

Servidor só em loopback. Não enviar dados sensíveis; repositório atualmente público. Nenhuma interpretação autoriza ações. Sem execução automática nem promoção de conhecimento.
