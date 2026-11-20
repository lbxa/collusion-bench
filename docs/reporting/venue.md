# Venue and submission record

No submission venue has been selected for the current revision of the
[paper](../../report/agentic/main.tex).

## Current report layouts

### Active prospective report, updated 2026-11-20

The active report uses US Letter with 0.8-inch margins and a 0.27-inch
column gutter. The two columns use 11pt native Computer Modern text and
mathematics with approximately 14pt body leading. The ruled 20pt title and
abstract sit above both columns on the first page. Wide figures and tables
span both columns, and black-outline panels identify attributed excerpts.
The title lists all five coauthors in their supplied order with their
confirmed affiliations. References precede the limitations and ethics
appendix and the detailed evidence appendices.

### Historical layouts

The historical October agentic manuscript uses `article` at 11pt on US Letter,
one-inch margins and New TX text/math fonts. Build `make -C report agentic-historical`
with TeX Live pdfLaTeX through latexmk; the PDF is
`report/agentic/build/historical/historical-october-main.pdf`.
Its main text is followed by references, the limitations/ethics appendix,
and a complete run/episode appendix. The
[review record](../../report/agentic/review.md) preserves checks and gaps.

The editable sample is [report/main.tex](../../report/main.tex), using the
user-supplied `arxiv.sty` unchanged as a general starting guide. This is an
**internal baseline integration report**. Its two-episode live smoke evidence
replaces the earlier fictional teaching comparison.
The supplied style is not evidence of arXiv acceptance or compliance with a
conference's current requirements. Its attribution and attachment hashes are
recorded in [template provenance](../../report/template/README.md).

Build with `make -C report`, or open `report/main.tex` in TeXShop and typeset
with its selected `pdflatexmk` engine: pdfLaTeX through `latexmk -pdf`, on US
Letter with 6.5-inch text width and 9-inch text height from the style. The sample uses a
small keyed `thebibliography` in its own section file, with no external
bibliography pass. The document date is fixed in `report/preamble.tex`.
The vector figures are included in `report/figures/`; regenerate them explicitly
with `make -C report figures` when their sources change.
The [review record](../../report/review.md) records the tested toolchain and PDF
inspection. The submission fields below remain open for the actual venue.

## Required record

Update this record when a submission venue is selected. Keep the source URL
and the date checked beside each external rule.

| Field | Project value |
| --- | --- |
| Venue, year, track, and paper type | Research paper, venue pending |
| Document stage | Working draft |
| Official author guide, policies, and template | Pending venue selection |
| Local report root and main `.tex` file | `report/agentic/main.tex` |
| Compiler, TeX distribution, bibliography backend, exact build command | pdfLaTeX, TeX Live 2025, latexmk 4.86a; inline bibliography; `make -C report agentic` |
| Page limits, anonymity, accessibility, disclosures, and submission logistics | Pending venue selection |

Official rules for the chosen venue and stage take precedence over house
formatting. Preserve scientific accuracy and disclose limitations when fitting
the format. If official pages disagree, record the conflict and seek an
authoritative resolution; do not silently choose the convenient rule.

## ICLR 2027 example snapshot

This is a worked reference only. The
[official ICLR 2027 author guide](https://iclr.cc/Conferences/2027/AuthorGuidelines)
was inspected on **2026-10-25**. Its relevant headings state:

| Heading | Verified example requirement |
| --- | --- |
| Paper formatting | At submission, main text is at most 9 pages; discussion/rebuttal and camera-ready allow 10. References are excluded and unlimited. Appendices follow the bibliography and have no page limit; reviewers need not read them. |
| Style files and Templates | Use the [official 2027 LaTeX archive](https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip) linked by the guide. |
| Double-blind submission and anonymity | Submission and supplementary material must be anonymous; related self-authored work is cited in third person. |
| Required: AI use statement | A mandatory AI-use section is excluded from the page limit. |

The separate [official AI policy for authors](https://iclr.cc/Conferences/2027/AIPolicyForAuthors),
under “Policy on LLM use for research and writing papers,” also requires
disclosure in the submission form and assigns responsibility for AI-assisted
content to the authors. Check its task-specific disclosure categories when
preparing a submission.

The archive URL was verified from the guide; its contents were not unpacked
or compiled for this snapshot. These entries do not establish template package
compatibility. Recheck all live rules and complete the project record before
using this example for an actual submission. Other tracks and years require
their own records. See [source notes](sources/latex-sources.md) and
[the review checklist](review.md).
