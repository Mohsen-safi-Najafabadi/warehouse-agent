# Warehouse Agent

An agentic text-to-SQL system over a synthetic manufacturing database,
built to measure how far careful engineering — not model choice — moves reliability.

**Status: work in progress.**

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python data/generate.py
```