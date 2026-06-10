# K-Dense AI Database Guide

Version: Scientific Agent Skills `v2.45.0`

Primary database skill:

```text
~/.claude/plugins/marketplaces/claude-scientific-skills/skills/database-lookup/SKILL.md
```

The current K-Dense repository consolidates most public database access into `database-lookup`. It covers 78 public REST APIs across science, medicine, materials, regulation, economics, finance, and demographics. Use old per-database skill names only as legacy fallback.

## Workflow

1. Read `skills/database-lookup/SKILL.md`.
2. Match the user query to one or more databases.
3. Read the specific reference file under `skills/database-lookup/references/`.
4. Query the API and return raw JSON plus the database and endpoint used.
5. If no results are found, say that explicitly.

## Database Families

- Chemistry and drugs: PubChem, ChEMBL, DrugBank, FDA/OpenFDA, DailyMed, KEGG, ZINC, BindingDB
- Biology and genomics: Reactome, UniProt, STRING, Ensembl, NCBI Gene, GEO, GTEx, PDB, AlphaFold, InterPro, BioGRID, Gene Ontology, dbSNP, gnomAD, ENCODE, Human Protein Atlas, Human Cell Atlas
- Disease and clinical: COSMIC, Open Targets, ClinicalTrials.gov, OMIM, ClinVar, GDC/TCGA, cBioPortal, DisGeNET, GWAS Catalog, Monarch, HPO
- Physics and astronomy: NASA, NIST, SDSS, SIMBAD, Exoplanet Archive
- Earth and environment: USGS, NOAA, EPA, OpenWeatherMap
- Materials science: Materials Project, COD
- Regulatory and patents: FDA, USPTO, SEC EDGAR
- Economics and finance: FRED, BEA, BLS, Federal Reserve, World Bank, ECB, US Treasury, Alpha Vantage, Data Commons
- Demographics and public health: US Census, Eurostat, WHO

## Identifier Rule

If a query fails, check identifier format before concluding that data is absent. Convert symbols, compound names, disease names, and variant IDs through the lookup workflow described in `database-lookup`.
