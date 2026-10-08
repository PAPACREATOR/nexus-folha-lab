# Nexus Folha Lab

Bancada **isolada e sem autoridade** para experimentar a Folha branca e interpretação em português. Não executa ferramentas do Windows, não acede ao Kernel/Host/Store/Creative/Canonical e não altera o repositório principal.

## Proveniência

Extração controlada de `PAPACREATOR/cerebro-parvo-`, branch `lab-e2e-frontdoor-20261004`: `nexus/frontdoor.py`, `nexus/frontdoor_rules.json`, `nexus/schemas/frontdoor_rules.json`. O mecanismo `correction_shadow` é uma extração do adaptador `nexus/adapters/languagetool.py` da mesma branch; a lógica de reconhecimento da Front Door mantém-se. Esta bancada não declara que a integração com o Host está pronta.

## Arranque local

Requer Python 3.10+ e `pip install jsonschema pytest`. Executar `python -m folha_lab.server` e abrir `http://127.0.0.1:8765`. Testar com `python -m pytest -q`.

O LanguageTool é **opcional**: a Folha aceita diagnósticos JSON fornecidos explicitamente ou, quando `FOLHA_LOCAL_LT=1`, consulta um servidor LanguageTool já existente em `http://127.0.0.1:8081/v2/check` (português europeu). Nunca inicia Java nem consulta serviços externos. Sem servidor, a Folha pergunta ao humano. A IA opcional está implementada apenas para propor **perguntas de esclarecimento** quando a interpretação determinística falha. Nunca decide uma intenção, executa operações ou concede autorização. Requer a configuração explícita `FOLHA_LOCAL_AI=1` e o serviço **já instalado pelo Nexus** em `127.0.0.1:18081`, com o alias `nexus-qwen3-1.7b` via API compatível com llama.cpp. Não inclui pesos nem instala Ollama. Sem serviço ou em caso de erro, faz perguntas determinísticas ao humano. A bancada apenas simula interpretações: não executa processos reais.

## Segurança

Servidor só em loopback. Não enviar dados sensíveis; repositório atualmente público. Nenhuma interpretação autoriza ações. Sem execução automática nem promoção de conhecimento.

## Usar a Folha no Codespaces

O projeto inclui `.devcontainer/devcontainer.json`, que instala as dependências ao criar/reconstruir o Codespaces, inicia a Folha e encaminha **privadamente** a porta 8765. No Codespaces já existente é necessário reconstruir o contentor para aplicar essa configuração; **não é necessário abrir outro repositório**. A interface expõe **Interpretar → Confirmar interpretação / Não, reformular**. Confirmar só regista a compreensão na própria página e **não executa nada**.

## IA local isolada — apenas se necessária

A Folha não chama IA para pedidos resolvidos, comandos de prefixos nem entradas bloqueadas. Para um pedido ambíguo, pode consultar o mesmo servidor local de linguagem do Nexus, mas somente quando ativado pelo utilizador com a variável de ambiente `FOLHA_LOCAL_AI=1`. O adaptador limita tamanho, tempo e resposta, desativa proxies e redirecionamentos e nunca usa serviços remotos. A resposta aceite é apenas uma pergunta curta; a interpretação permanece `UNRESOLVED` até o humano esclarecer. Em GitHub Codespaces o modelo do PC **não está acessível**, pelo que continua a funcionar com perguntas determinísticas.

## Gates

O GitHub Actions executa testes Python no Windows e Linux com Python 3.12/3.13, testes HTTP bidirecionais e, num job dedicado com Chromium real, testes da interface (confirmar, rejeitar, reformular, invalidação de propostas antigas, negações, segurança). A bateria de variações linguísticas verifica resultados e preservação do original; não substitui testes reais do modelo nem garante compreensão de qualquer frase. Só declarar PASS para o SHA e os jobs efetivamente verificados.

## Limites

Não há execução nem integração operacional com o Host neste laboratório. O LanguageTool pode receber diagnósticos JSON explícitos ou consultar um **servidor LanguageTool local** previamente iniciado e autorizado, usando uma *shadow*. Não inicia Java automaticamente, nem altera o original. O teste contra a instalação LanguageTool real no PC ainda requer prova adicional. O modelo real instalado no Windows exige prova adicional nesse ambiente.
