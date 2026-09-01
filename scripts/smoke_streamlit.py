#!/usr/bin/env python3
"""Executa todas as páginas do app Streamlit headless e falha se alguma lançar exceção.

Uso, a partir da raiz do projeto:
    python scripts/smoke_streamlit.py            # estado padrão de cada página
    python scripts/smoke_streamlit.py --widgets  # + cada estado alternativo de radio/checkbox

Serve para garantir que uma mudança em `src/eda_utils.py` ou em `streamlit/common.py`
não quebrou nenhuma página — o Streamlit engole exceções de página em silêncio quando
rodando no navegador, então o erro só apareceria para quem estivesse olhando a aba certa.
"""
from __future__ import annotations

import glob
import os
import sys

from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "streamlit"))  # as páginas importam `common`

PAGES = ["streamlit/app.py"] + sorted(glob.glob("streamlit/pages/*.py"))


def _abs(path: str) -> str:
    """AppTest resolve caminhos relativos a partir DESTE arquivo, não do cwd."""
    return os.path.join(ROOT, path)


def _report(path: str, at: AppTest, rotulo: str = "") -> int:
    if at.exception:
        print(f"❌ {path} {rotulo}")
        for e in at.exception:
            print("   ", str(e.value)[:600].replace("\n", "\n    "))
        return 1
    print(f"✅ {path} {rotulo}".rstrip())
    return 0


def main() -> int:
    testar_widgets = "--widgets" in sys.argv
    falhas = 0
    for path in PAGES:
        at = AppTest.from_file(_abs(path), default_timeout=300)
        at.run()
        falhas += _report(path, at)

        if not testar_widgets:
            continue

        combos: list[tuple[str, int, object]] = [
            ("radio", i, opt) for i, r in enumerate(at.radio) for opt in r.options[1:]
        ] + [("checkbox", i, True) for i, _ in enumerate(at.checkbox)]

        for kind, idx, val in combos:
            t = AppTest.from_file(_abs(path), default_timeout=300)
            t.run()
            widget = t.radio[idx] if kind == "radio" else t.checkbox[idx]
            widget.set_value(val)
            t.run()
            falhas += _report(path, t, f"[{kind}#{idx}={val}]")

    print(f"\n{'FALHOU' if falhas else 'OK'} — {falhas} erro(s).")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
