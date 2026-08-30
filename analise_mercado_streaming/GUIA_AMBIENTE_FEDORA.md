# Guia Completo: Ambiente Julia no Fedora 43

Guia passo a passo para rodar a análise do mercado de streaming (`analise_mercado.jl` + os CSVs em `data/`) no seu Fedora 43, do jeito mais correto e reprodutível possível.

Fedora 43 usa DNF5 como gerenciador de pacotes padrão (o comando `dnf` já aponta pra ele desde a Fedora 41), então todos os comandos abaixo funcionam normalmente.

---

## 1. Instalar o Julia (via juliaup)

**Não instale o Julia pelo `dnf`.** O Fedora não tem um pacote de Julia oficialmente mantido nos repositórios padrão, e o próprio projeto Julia recomenda não depender de gerenciadores de pacote de sistema operacional — eles ficam desatualizados e não são endossados pelo projeto. O método oficial e recomendado é o **juliaup**, o instalador/gerenciador de versões do Julia.

### Opção automática

Use o script incluído nesta pasta:

```bash
bash install_julia_fedora.sh
```

### Opção manual (o que o script acima faz por trás)

```bash
sudo dnf install -y curl
curl -fsSL https://install.julialang.org | sh
```

Depois, **feche e reabra o terminal** (ou rode `source ~/.bashrc`) e confirme:

```bash
julia --version
```

### Comandos úteis do juliaup para o dia a dia

```bash
juliaup status          # mostra a(s) versão(ões) instalada(s)
juliaup update          # atualiza para a versão estável mais recente
juliaup add release     # instala/garante a versão estável mais recente
```

---

## 2. Configurar o editor (VS Code + extensão Julia)

Recomendado, mas opcional — dá autocomplete, debugger integrado e um painel de variáveis, o que ajuda bastante numa análise exploratória.

### Instalar o VS Code no Fedora

**Opção A — Flatpak (mais simples no Fedora):**

```bash
flatpak install flathub com.visualstudio.code
```

**Opção B — repositório oficial da Microsoft:**

```bash
sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\nautorefresh=1\ntype=rpm-md\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'
sudo dnf check-update
sudo dnf install -y code
```

### Instalar a extensão Julia

Dentro do VS Code: `Ctrl+Shift+X` → buscar **"Julia"** (publicador: `julialang`) → Instalar.

A extensão detecta automaticamente o Julia instalado via juliaup. Se não detectar, configure manualmente em `Settings` → busque `julia.executablePath` e aponte para o caminho retornado por `which julia`.

---

## 3. Organizar o projeto

Extraia a pasta `analise_mercado_streaming/` (com este guia, os scripts e a subpasta `data/`) para um lugar fixo no seu sistema, por exemplo:

```bash
mkdir -p ~/projetos
# mova/extraia a pasta analise_mercado_streaming/ para dentro de ~/projetos/
cd ~/projetos/analise_mercado_streaming
```

A estrutura final deve ficar assim:

```
analise_mercado_streaming/
├── GUIA_AMBIENTE_FEDORA.md     # este guia
├── install_julia_fedora.sh
├── setup.jl
├── analise_mercado.jl
├── README.md
└── data/
    ├── spotify_quarterly.csv
    ├── global_market_revenue.csv
    ├── global_paid_subscribers.csv
    ├── brazil_market.csv
    ├── platform_market_share.csv
    └── FONTES.md
```

---

## 4. Criar o ambiente Julia do projeto (isolado e reprodutível)

Diferente de só instalar pacotes "no geral", a boa prática em Julia é cada projeto ter seu **próprio ambiente** (equivalente a um `venv` do Python), registrado em `Project.toml`/`Manifest.toml`. Isso é criado automaticamente ao rodar:

```bash
cd ~/projetos/analise_mercado_streaming
julia setup.jl
```

Isso vai:
1. Ativar um ambiente isolado dentro da própria pasta do projeto.
2. Instalar `CSV.jl`, `DataFrames.jl` e `Plots.jl` (isso pode demorar alguns minutos na primeira vez, principalmente o `Plots.jl`).
3. Pré-compilar tudo.

Você só precisa rodar `julia setup.jl` **uma vez** por máquina (ou de novo se apagar a pasta e recriá-la).

---

## 5. Rodar a análise

```bash
julia analise_mercado.jl
```

O script já ativa o ambiente isolado do projeto automaticamente (`Pkg.activate(@__DIR__)` está no topo do arquivo), então não precisa repetir a ativação manualmente.

Alternativa pelo VS Code: abra `analise_mercado.jl`, clique em "Run" (▶) no canto superior direito — a extensão Julia abre um painel de REPL integrado e mostra os gráficos inline.

### O que esperar

- Prints no terminal com os principais números (crescimento de MAU/assinantes, Brasil vs. mundo, índice de concentração HHI).
- 6 arquivos `.png` salvos na mesma pasta do script.

---

## 6. Problemas comuns no Fedora

**"Package X not found" ou erro de rede ao rodar `julia setup.jl`:** o Julia baixa pacotes do Registro Geral (hospedado no GitHub) na primeira instalação — confirme que sua rede/VPN não está bloqueando `github.com`.

**Erro relacionado a `libGL`, `Xrender` ou fontes ao gerar os gráficos com `Plots.jl`:** raro em instalações Workstation completas do Fedora, mas se aparecer, instale:
```bash
sudo dnf install -y mesa-libGL fontconfig freetype
```

**`julia: command not found` mesmo depois de instalar:** o instalador adiciona o Julia ao PATH via `~/.bashrc` (ou `~/.zshrc` se você usa zsh) — abra um terminal novo, ou rode `source ~/.bashrc` manualmente.

---

## 7. Referência rápida (cheatsheet)

```bash
# instalar o Julia (uma vez)
bash install_julia_fedora.sh

# preparar o ambiente do projeto (uma vez por máquina)
cd ~/projetos/analise_mercado_streaming
julia setup.jl

# rodar a análise (sempre que quiser)
julia analise_mercado.jl

# atualizar o Julia no futuro
juliaup update
```
