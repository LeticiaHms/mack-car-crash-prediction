#!/bin/bash

# ============================================================
# CONFIGURAÇÃO DO AMBIENTE
# ============================================================
#
# Caso o script não tenha permissão de execução, rode:
#
#     chmod +x scripts/setup.sh
#
# Depois, execute com:
#
#     ./scripts/setup.sh
#
# Ou, sem precisar alterar a permissão:
#
#     bash scripts/setup.sh
#
# ============================================================

set -e

echo "======================================"
echo " Configuração do ambiente do projeto"
echo "======================================"

# --------------------------------------
# DuckDB
# --------------------------------------

echo ""
echo "[1/3] Verificando DuckDB..."

if command -v duckdb &> /dev/null; then
    echo "DuckDB já está instalado."
    duckdb --version
else
    echo "DuckDB não encontrado."
    echo "Instalando DuckDB..."

    curl https://install.duckdb.org | bash

    # Adiciona DuckDB ao PATH da sessão atual
    export PATH="$HOME/.duckdb/cli/latest:$PATH"

    # Adiciona DuckDB ao PATH permanentemente
    if ! grep -q '.duckdb/cli/latest' "$HOME/.bashrc" 2>/dev/null; then
        echo 'export PATH="$HOME/.duckdb/cli/latest:$PATH"' >> "$HOME/.bashrc"
    fi

    echo "DuckDB instalado com sucesso."
    duckdb --version
fi

# --------------------------------------
# Python
# --------------------------------------

echo ""
echo "[2/3] Verificando Python..."

if command -v python3 &> /dev/null; then
    echo "Python encontrado:"
    python3 --version
else
    echo "ERRO: Python3 não encontrado."
    exit 1
fi

# --------------------------------------
# Dependências Python
# --------------------------------------

echo ""
echo "[3/3] Instalando dependências Python..."

if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
    echo "Dependências Python instaladas com sucesso."
else
    echo "AVISO: requirements.txt não encontrado."
fi

echo ""
echo "======================================"
echo " Ambiente configurado com sucesso!"
echo "======================================"