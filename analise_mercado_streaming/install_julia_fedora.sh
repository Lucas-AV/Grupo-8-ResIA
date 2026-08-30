#!/usr/bin/env bash
# install_julia_fedora.sh
# Instala o Julia no Fedora via juliaup (método oficial e recomendado pelo projeto Julia).
# Uso: bash install_julia_fedora.sh

set -e

echo "== Instalação do Julia no Fedora =="

if command -v julia &> /dev/null; then
    echo "Julia já está instalado: $(julia --version)"
    echo "Se quiser atualizar para a versão mais recente, rode: juliaup update"
    exit 0
fi

echo "Garantindo que o curl está disponível..."
sudo dnf install -y curl

echo "Baixando e instalando o Julia via juliaup (instalador oficial)..."
curl -fsSL https://install.julialang.org | sh

cat <<'EOF'

Instalação concluída.

PRÓXIMO PASSO: feche e reabra o terminal (ou rode `source ~/.bashrc`),
depois confirme com:

    julia --version

Se aparecer a versão do Julia, está tudo pronto.
EOF
