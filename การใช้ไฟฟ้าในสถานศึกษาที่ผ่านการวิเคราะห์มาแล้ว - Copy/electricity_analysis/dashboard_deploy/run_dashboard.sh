#!/bin/sh
# Local run on Linux/macOS. Extra arguments are passed to Streamlit, e.g.  ./run_dashboard.sh --server.address 0.0.0.0
cd "$(dirname "$0")" || exit 1
if [ ! -d .venv ]; then python3 -m venv .venv || exit 1; fi
if [ ! -f .venv/.installed ]; then
  .venv/bin/python -m pip install -r requirements-tested.txt || .venv/bin/python -m pip install -r requirements.txt || exit 1
  echo done > .venv/.installed
fi
.venv/bin/python preflight.py || exit 1
.venv/bin/python -m streamlit run app.py --server.port 8501 "$@"
