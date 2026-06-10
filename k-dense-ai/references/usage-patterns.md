# K-Dense AI Usage Patterns

Version: Scientific Agent Skills `v2.45.0`

Primary skill path:

```text
~/.claude/plugins/marketplaces/claude-scientific-skills/skills/{skill-name}/SKILL.md
```

Legacy fallback path:

```text
~/.claude/plugins/marketplaces/claude-scientific-skills/scientific-skills/{skill-name}/SKILL.md
```

## Core Pattern

1. Pick the smallest useful skill set.
2. Read each selected skill's `SKILL.md`.
3. Load only task-specific references under that skill.
4. Execute the workflow and cite what was checked.

## Common Workflows

### Literature and Evidence Review

Use:

- `research-lookup` for current web-backed research and recent findings
- `paper-lookup` for paper database search
- `literature-review` for systematic review structure
- `citation-management` for metadata, BibTeX, and bibliography cleanup
- `scientific-writing` for manuscript-style output
- `peer-review` or `scholar-evaluation` for quality review

### Public Database Lookup

Use `database-lookup` first. It consolidates 78 public scientific, biomedical, materials, clinical, regulatory, economic, and demographic APIs. Use dedicated skills such as `depmap`, `imaging-data-commons`, `primekg`, `usfiscaldata`, or `hugging-science` when they match the query better.

Avoid starting with legacy per-database names such as `pubmed-database` or `chembl-database` unless the current `skills/` tree lacks the route and the legacy tree has it.

### Bioinformatics Pipeline

Use:

- `get-available-resources` before heavy local computation
- `nextflow` for reproducible pipelines, nf-core workflows, `.nf` files, samplesheets, and workflow scaling
- `biopython`, `pysam`, `scanpy`, `anndata`, `scvi-tools`, `scvelo`, `pydeseq2`, `cellxgene-census`, or `gtars` for domain execution

### Cheminformatics and Drug Discovery

Use:

- `rdkit`, `datamol`, `medchem`, `molfeat` for molecule handling and descriptors
- `deepchem`, `torchdrug`, `pytdc` for ML/drug-discovery datasets
- `diffdock`, `molecular-dynamics`, `cobrapy`, `matchms`, `pyopenms` for docking, simulation, metabolism, and mass spectrometry workflows

### Scientific Data Analysis

Use:

- `statistical-analysis`, `statsmodels`, `pymc`, `scikit-learn`, `shap`
- `polars`, `dask`, `vaex`, `zarr-python` for large data
- `matplotlib`, `seaborn`, `scientific-visualization`, `networkx`, `geopandas` for visualization and spatial/network work

### Research Output and QC

Use:

- `scientific-writing`, `scientific-slides`, `scientific-schematics`, `infographics`, `latex-posters`, `pptx-posters`
- `docx`, `pdf`, `pptx`, `xlsx`, `markitdown`, `liteparse`
- `scientific-critical-thinking`, `peer-review`, `scholar-evaluation`, `hypothesis-generation` for review and refinement

## Selection Rule

If more than three skills seem relevant, start with the router plus one planning/QC skill, then load additional skills only when the next step requires their details.
