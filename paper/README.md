# Paper workflow

`main.tex` is Overleaf-ready and compiles with pdfLaTeX. The paper is designed
to remain valid before and after the real experiment: result cells are `TBD`
until `generated_results.tex` is produced from a non-mock run.

## Files to import into Overleaf now

- `main.tex`
- `references.bib`
- `figures/system_pipeline.pdf`
- `figures/experimental_matrix.pdf`

Set `main.tex` as the main document and select pdfLaTeX.

## Local build

From `paper/`:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Generate figures

From the repository root:

```bash
pip install -r requirements-paper.txt
python scripts/generate_paper_figures.py
```

The script always regenerates the two study-design figures. If
`results/runs.jsonl` and `results/summary.json` come from a real run, it also
creates:

- `paper/generated_results.tex`
- `paper/figures/channel_detection.pdf`
- `paper/figures/policy_tradeoff.pdf`

The script refuses to generate submission result artifacts from mock results.
`--allow-mock` exists only for layout debugging and its outputs must never be
submitted.

## Final-result sequence

```bash
python scripts/build_results.py
python scripts/generate_paper_figures.py
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Before submission, replace the status paragraph in the Results section with a
short evidence-based interpretation, add the numerator/denominator and Wilson
interval for each reported rate, and complete the named error analysis.

