# Logistica de rede da demo (ticket 0.5)

Tres opcoes consideradas, seguindo PIPELINE_AGENTE_PROPOSTA_B.md secao 1.1:

1. **Mesma Wi-Fi** — laptop com backend + Ollama numa rede, celulares/outros
   laptops acessando via IP local. Depende da rede do local da apresentacao
   nao bloquear trafego entre dispositivos (Wi-Fi corporativo/de evento as
   vezes isola clientes entre si — "client isolation").
2. **Tunel publico** (ngrok/Cloudflare Tunnel) — expoe o backend local via
   URL publica. Funciona em qualquer rede, mas depende do tunel nao cair no
   meio da demo (ver edge case documentado em PIPELINE_AGENTE_PROPOSTA_B.md
   secao 7).
3. **Tudo na mesma maquina** — quem apresenta roda backend, Ollama e abre o
   frontend no proprio navegador. Zero dependencia de rede externa.

## Achado real (maquina de desenvolvimento, 2026-09-02)

Rodando o modelo disponivel localmente (`glm-4.7-flash:latest`, 19GB — nao
e o modelo alvo da Proposta B) via `ollama ps`:

```
NAME                    SIZE     PROCESSOR          CONTEXT
glm-4.7-flash:latest    19 GB    79%/21% CPU/GPU     4096
```

79% do processamento caiu pra CPU (GPU nao segura o modelo inteiro na
VRAM) — primeira resposta demorou mais de 30s pra carregar o modelo em
memoria antes de comecar a gerar texto. Isso e maior que qualquer timeout
razoavel de UI (a extracao via LLM, ticket 2.2, usa timeout de ~8s).

**Implicacao pratica:** o modelo alvo (`qwen2.5:7b-instruct-q4_K_M`, ~4.7GB)
e bem menor e deve caber inteiro na VRAM de uma GPU dedicada — mas isso
*precisa* ser validado no hardware real de quem for rodar a demo (ticket
0.1) antes do dia. Se o hardware nao aguentar o modelo alvo com folga de
tempo de resposta, a opcao 3 (tudo na mesma maquina) fica ainda mais
arriscada, porque o mesmo processo que roda o LLM tambem roda o
backend/frontend.

## Recomendacao

**Opcao 3 (tudo na mesma maquina)** como default, com dois requisitos
obrigatorios antes do ensaio (ticket 7.6):

- Modelo alvo baixado e "aquecido" (rodar um prompt trivial) *antes* de
  abrir a demo pro publico — evita o custo de cold-start de 30s+ no meio
  da apresentacao.
- Fallback pronto: `LLM_BACKEND=claude` configurado e testado com uma
  chave valida (ticket 0.3), pra trocar de backend via variavel de
  ambiente sem reiniciar o fluxo da conversa caso o modelo local nao
  performe bem ao vivo.

Tunel publico (opcao 2) fica como alternativa se quem apresenta precisar
que outras pessoas acessem de dispositivos proprios durante a demo — mas
so deve ser ensaiado com antecedencia (nunca testado pela primeira vez no
dia, conforme o plano de testes em PIPELINE_AGENTE_PROPOSTA_B.md secao 10).

**Status:** proposta registrada aqui; falta validar com o hardware real de
quem vai apresentar e marcar como decidido (criterio de aceite do ticket
0.5 ainda em aberto).
