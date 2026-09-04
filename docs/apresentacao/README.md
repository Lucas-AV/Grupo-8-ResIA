# Apresentação do MelodIA

Este diretório reúne o material do Épico 11. O conteúdo foi escrito para ser
usado por quem vai apresentar e também por quem precisa avaliar o projeto sem
conhecer o código.

## Entregas

| Ticket | Entrega | Situação |
| --- | --- | --- |
| KAN-97 / 11.1 | `pitch/MelodIA_Pitch.pptx`, PDF e `ROTEIRO_PITCH.md` | Pronto para apresentar |
| KAN-98 / 11.2 | Pacote de gravação em `video/` | Gravação e publicação dependem da equipe |
| KAN-99 / 11.3 | `tecnica/MelodIA_Tecnica.pptx`, PDF e `ROTEIRO_TECNICO.md` | Pronto para apresentar |
| KAN-101 / 11.5 | `ENSAIO_GERAL.md` | Roteiro pronto; execução deve ser registrada pela equipe |
| KAN-102 / 11.6 | `video/ROTEIRO_VIDEO.md` | Pronto para gravação |

O resultado das verificações automáticas e visuais está em `VALIDACAO.md`.

## Ordem recomendada de uso

1. Ler o roteiro do pitch e atribuir as seis pessoas.
2. Rodar o ensaio técnico, incluindo notebook e demo do agente.
3. Gravar o clipe reserva de 45 segundos.
4. Gravar o vídeo de cinco minutos seguindo o roteiro cena a cena.
5. Fazer o ensaio geral pelo menos um dia antes da banca.

## Tempos de referência

- Pitch: 5 minutos, 14 slides.
- Apresentação técnica: 8 minutos, 10 slides.
- Vídeo: 5 minutos.
- Clipe reserva da demo: 45 segundos.

## Fontes principais

- `analise_mercado_streaming/RELATORIO.md`: mercado e argumento do pitch.
- `docs/PIPELINE_AGENTE_PROPOSTA_B.md`: arquitetura do agente.
- `analise_exploratoria.ipynb`: análises do conjunto de músicas.
- `data/analytics/dataset_profile.json`: contagens atuais do conjunto.

Os dados de mercado foram curados em agosto de 2026. O perfil do conjunto
processado representa a versão de setembro de 2026. Por isso, os materiais
tratam essas duas datas como fotografias diferentes do projeto.

## Como reconstruir os arquivos

No Windows com o ambiente do Codex instalado, execute na raiz do repositório:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/apresentacao/build_decks.ps1
```

O atalho localiza as dependências de apresentações do ambiente, gera os dois
PPTX, cria as prévias e monta os PDFs correspondentes. As prévias ficam na
pasta temporária de construção e não precisam ser versionadas. A lógica dos
decks está em `scripts/apresentacao/build_decks.mjs` e a montagem dos PDFs em
`scripts/apresentacao/build_pdfs.py`.

## Pendências que exigem pessoas

- O vídeo final ainda precisa ser gravado, revisado e publicado.
- O link final deve ser registrado em `video/GUIA_GRAVACAO.md`.
- O ensaio só pode ser considerado concluído depois que a equipe preencher o
  registro em `ENSAIO_GERAL.md`.
