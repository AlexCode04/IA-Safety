# Paper workflow

The submission is available in two synchronized LaTeX entry points:

- `main_en.tex`: English.
- `main_es.tex`: Spanish, retaining technical names and acronyms in English
  where translation would reduce precision.
- `main.tex`: convenience wrapper that selects the English version.
- `references.bib`: shared bibliography.
- `generated_results.tex`: shared provenance and channel-level numerical macros.
- `generated_policy_results.tex`: shared policy-table numerical macros.

Both papers use the same figures and the same numerical result contract. Do not
edit experimental numbers directly in either manuscript. Channel metrics are
generated from `results/summary.json`; policy-table macros are generated from
`results/summary.json` plus `results/runs.jsonl`.

The dashboard figure in both papers uses two screenshots of the current
operator interface (`dashboard_overview.jpg` and `dashboard_cases.jpg`). They
show the deterministic mock run and remain explicitly labelled as synthetic in
the manuscripts. `dashboard_summary.pdf` is the reproducible publication-style
summary generated from the same canonical metrics.

## Current sprint deliverable

The committed values are from the deterministic mock pipeline and are visibly
labelled as a **synthetic demonstration**. They validate software integration,
not Qwen, NLA, probe, or Gemini safety performance.

```bash
python scripts/run_experiment.py --reset-output
python scripts/build_results.py
python scripts/generate_paper_figures.py --allow-mock
python scripts/generate_policy_macros.py
```

The current dashboard and both papers consume the same canonical result
contract. This is deliberate: the paper is the publication view of the
experiment, while the dashboard is the operator-facing inspection view of the
same run data and aggregated metrics.

## Browser-only PDF preview on GitHub

No local Git, VS Code, or LaTeX installation is required to compile the paper.
The repository includes the GitHub Actions workflow
`.github/workflows/build-paper.yml`, which compiles both languages with
pdfLaTeX/latexmk and uploads the two PDFs as one artifact.

From the GitHub website:

1. Open **Actions**.
2. Select **Build bilingual paper**.
3. Click **Run workflow** and choose the branch you want to inspect.
4. Open the finished workflow run.
5. Under **Artifacts**, download **BUDGET-NLA-papers**.

The artifact contains:

- `BUDGET-NLA_EN.pdf`
- `BUDGET-NLA_ES.pdf`

The same workflow also runs automatically when the paper changes, so a pull
request shows whether both language versions still compile before merging.

GitHub does not provide an Overleaf-style live split editor for `.tex` files.
The workflow is the GitHub-native verification path: it compiles on GitHub and
offers the resulting PDFs as a browser download. For an actual side-by-side
source/PDF view in a browser, open the branch in Codespaces and use the VS Code
setup below.

## Side-by-side PDF preview in VS Code or Codespaces

The repository recommends the **LaTeX Workshop** extension and includes shared
workspace settings. After installing a TeX distribution (MiKTeX on Windows or
TeX Live on Linux), open either `paper/main_en.tex` or `paper/main_es.tex` and
save the file. LaTeX Workshop builds it automatically.

Use **LaTeX Workshop: View LaTeX PDF** from the Command Palette to open the PDF
in a VS Code tab, then move that tab to the right editor group for the same
source/PDF arrangement shown by Overleaf. The preview supports SyncTeX: Ctrl+
click in the PDF jumps to the source, and the extension's SyncTeX command jumps
from source to PDF.

The same workflow works in a GitHub Codespace, entirely in the browser, as long
as the Codespace contains a TeX distribution.

## Browser-only dashboard preview

The dashboard is a Streamlit application backed by the same canonical run and
summary contract used by the paper. If you work entirely from the browser, the
simplest GitHub-native option is Codespaces:

1. Open the repository on GitHub.
2. Select **Code > Codespaces > Create codespace** on the desired branch.
3. In the browser terminal run:

```bash
pip install -r requirements.txt
python scripts/run_experiment.py --reset-output
python scripts/build_results.py
streamlit run app/dashboard.py
```

4. GitHub Codespaces will expose port `8501`; open the forwarded URL in the
   browser to view the dashboard.

For the sprint mock deliverable, the dashboard must remain visibly labelled as
synthetic/mock evidence. For a real run, rebuild `summary.json` from the frozen
real artifacts before presenting it as model-performance evidence.

## Real replacement on the cluster

```bash
bash scripts/run_pipeline_gpu.sh real auto
```

A real run cannot be summarized silently without all Observable, CoT, and NLA
Gemini verdicts. The aggregator exits with an error unless the external set is
complete or the operator explicitly requests an exploratory incomplete build.

## Overleaf

Upload the complete `paper/` folder. Choose either `main_en.tex` or
`main_es.tex` as the main document and use pdfLaTeX. Required files are:

- the selected `.tex`;
- `generated_results.tex`;
- `generated_policy_results.tex`;
- `references.bib`;
- `figures/system_pipeline.pdf`;
- `figures/experimental_matrix.pdf`;
- `figures/dashboard_overview.jpg`;
- `figures/dashboard_cases.jpg`.

Both entry points use Latin Modern vector fonts and place the abstract/resumen
across the full text width before the two-column body. Keep the complete author
block unchanged between languages so every contributor is rendered with the
same typographic hierarchy.

## Local compilation

Local compilation remains available if desired:

```bash
cd paper
pdflatex main_en.tex
bibtex main_en
pdflatex main_en.tex
pdflatex main_en.tex

pdflatex main_es.tex
bibtex main_es
pdflatex main_es.tex
pdflatex main_es.tex
```

The inline PGFPlots result chart is regenerated by LaTeX from shared macros, and
both policy tables use the same generated policy macros, so numerical values
cannot drift between languages without changing the canonical generated files.
