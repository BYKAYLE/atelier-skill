---
name: k-dense-ai
version: "2.45.0"
description: |
  Use when performing scientific analysis, literature research, database lookup, bioinformatics,
  cheminformatics, clinical/medical analysis, data science, scientific writing, or research QC.
  Routes requests to K-Dense-AI Scientific Agent Skills v2.45.0.
metadata:
  upstream_repo: "https://github.com/K-Dense-AI/scientific-agent-skills"
  upstream_release: "v2.45.0"
  upstream_commit: "d9a978a"
  checked_at: "2026-06-03 KST"
  installed_skill_count: 141
  database_api_count: 78
  local_skill_root: "~/.claude/plugins/marketplaces/claude-scientific-skills/skills"
  legacy_skill_root: "~/.claude/plugins/marketplaces/claude-scientific-skills/scientific-skills"
---

# K-Dense AI - Scientific Agent Skills Router

K-Dense AI routes scientific and research requests to the correct installed Agent Skill. The current primary source is `K-Dense-AI/scientific-agent-skills` release `v2.45.0`, installed with 141 current skills. The old `scientific-skills/` tree is preserved only as a legacy fallback.

## Skill Locations

Primary current skills:

```text
~/.claude/plugins/marketplaces/claude-scientific-skills/skills/{skill-name}/SKILL.md
```

Legacy fallback, only when a current skill is absent:

```text
~/.claude/plugins/marketplaces/claude-scientific-skills/scientific-skills/{skill-name}/SKILL.md
```

Router references:

- Catalog: `~/.claude/skills/k-dense-ai/references/skill-catalog.md`
- Usage patterns: `~/.claude/skills/k-dense-ai/references/usage-patterns.md`
- Database guide: `~/.claude/skills/k-dense-ai/references/database-guide.md`

## Routing Rules

1. Identify the user's domain, goal, data type, and expected output.
2. If the task maps to a current skill, read that skill's `SKILL.md` before acting.
3. Prefer the current `skills/` tree over the legacy `scientific-skills/` tree.
4. For public scientific, biomedical, materials, regulatory, economics, or demographic API queries, use `database-lookup` first. Do not route to old per-database skill names unless the current tree lacks the needed route and the legacy fallback contains it.
5. For paper and literature work, choose among `research-lookup`, `paper-lookup`, `literature-review`, `citation-management`, `scientific-writing`, `peer-review`, and `scholar-evaluation`.
6. For computationally heavy analysis, read `get-available-resources` first, then pick the analysis skill.
7. For reproducible bioinformatics/data pipelines, use `nextflow` when Nextflow, nf-core, `.nf`, samplesheets, workflow scaling, or pipeline reproducibility is relevant.
8. If uncertain, read the catalog and choose the smallest set of skills that covers the task.

## High-Level Map

- Literature and current research: `research-lookup`, `paper-lookup`, `literature-review`, `citation-management`
- Public data APIs: `database-lookup`, plus dedicated data skills such as `depmap`, `imaging-data-commons`, `primekg`, `usfiscaldata`, `hugging-science`
- Bioinformatics and genomics: `biopython`, `anndata`, `scanpy`, `scvi-tools`, `scvelo`, `nextflow`, `pysam`, `pydeseq2`, `cellxgene-census`
- Cheminformatics and drug discovery: `rdkit`, `datamol`, `medchem`, `deepchem`, `diffdock`, `pytdc`, `molfeat`, `cobrapy`
- Machine learning and data science: `scikit-learn`, `pytorch-lightning`, `transformers`, `statsmodels`, `pymc`, `dask`, `polars`, `shap`
- Visualization and documents: `scientific-visualization`, `matplotlib`, `seaborn`, `pptx`, `docx`, `pdf`, `xlsx`, `markdown-mermaid-writing`
- Scientific communication and QC: `scientific-writing`, `scientific-slides`, `scientific-schematics`, `peer-review`, `scholar-evaluation`, `scientific-critical-thinking`

## Execution Pattern

When this router is triggered:

```text
1. Select skill(s) from the map or catalog.
2. Read ~/.claude/plugins/marketplaces/claude-scientific-skills/skills/{skill-name}/SKILL.md.
3. Load only the referenced files needed for the task.
4. Execute the user's requested research, analysis, writing, or QC workflow.
5. Report which skill(s) were used and any verification performed.
```

Do not stop at naming a skill. Use the selected skill to perform the task.
