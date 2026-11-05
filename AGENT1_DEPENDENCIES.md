# Agent 1 Dependency Record

Recorded on 2026-11-01. Agent 1 dependencies were installed in the project-local `.venv312`; no global Python packages were installed.

| Package/tool | Version | Use | Compatibility / license | Integrity / state |
|---|---|---|---|---|
| Python | 3.12.10 | Agent 1 runtime | Windows x64 | Existing `.venv312` |
| RDKit | 2026.09.1 | SDF parsing, sanitization, molecular formula and canonical SMILES | Official PyPI wheel tagged `cp312-win_amd64`; BSD-3-Clause | SHA-256 `fa4f8bed07bd6a49f71f49a579b99dc07cd45b9c66af8d5f133adb0a0876361e`; installed from locally verified wheel |
| Pillow | 13.0.0 | Image adapter used by RDKit/PDFium | Installed in `.venv312`; existing NumPy 2.5.4 satisfied | Installed with RDKit package dependencies |
| pypdfium2 | 5.14.0 | Render PDF pages for OCR/visual QA | Windows x64 `py3-none-win_amd64`; BSD-3-Clause, Apache-2.0 and dependency licenses | SHA-256 `149fd5c6397b8df8bf7911a93506eff0be874f877afe7ac936cf5d37d21a6a06`; installed from locally verified PyPI wheel |
| Tesseract OCR | 5.5.0.20241111 | Diagnostic OCR of rendered scan pages | Existing Windows installation at `C:\Program Files\Tesseract-OCR\tesseract.exe` | Not installed or modified by this task |

No project requirements or lock file existed before this stage. The environment change is recorded here instead of introducing an incomplete dependency manifest. The installed wheels are local environment state; no package wheel is included in the research corpus or redistributed.

RDKit publishes a CPython 3.12 Windows x64 wheel and recommends the PyPI package for installation ([official install documentation](https://rdkit.org/docs/Install.html), [PyPI release](https://pypi.org/project/rdkit/2026.9.1/)). pypdfium2 publishes a Windows x64 wheel and documents its bundled PDFium runtime and license notices ([PyPI release](https://pypi.org/project/pypdfium2/5.14.0/)).
