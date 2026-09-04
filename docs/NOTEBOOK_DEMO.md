# Demonstração e publicação do notebook

O arquivo `analise_exploratoria.ipynb` é o material de demonstração da análise exploratória. Ele pode ser apresentado célula a célula ou aberto sem instalação local.

## Abrir online

- [Visualizar no GitHub](https://github.com/Lucas-AV/Grupo-8-ResIA/blob/main/analise_exploratoria.ipynb): leitura dos resultados já salvos no arquivo.
- [Abrir no Binder](https://mybinder.org/v2/gh/Lucas-AV/Grupo-8-ResIA/HEAD?labpath=analise_exploratoria.ipynb): ambiente temporário no navegador para executar as células. A primeira abertura pode levar alguns minutos enquanto o ambiente é preparado.

No Binder, selecione uma célula e use **Shift + Enter**. Para executar tudo, use o menu `Run` → `Run All Cells`.

## Rodar e conferir localmente

Na raiz do repositório:

```bash
pip install -r requirements.txt
python scripts/prepare_notebook_demo.py
python scripts/validate_notebook_demo.py
python scripts/run_notebook_demo.py
```

O primeiro script mantém o texto de abertura e o import do notebook alinhados à demonstração. A validação confere a estrutura; a execução roda todas as células em memória e falha se alguma célula apresentar erro. O notebook versionado não é sobrescrito durante esse último teste.
