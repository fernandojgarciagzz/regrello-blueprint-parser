# Regrello Blueprint Parser

Toolkit for analyzing Regrello workflow exports (`.rex` files). Produces interactive HTML dashboards and detailed text analyses from any blueprint export.

**Requirements**: Python 3 (standard library only — no pip install needed)

---

## Quick Start

### Option A: With Claude Code (recommended)

If you have [Claude Code](https://claude.ai/code) installed, use the built-in `/parse` command:

```
/parse blueprints/Warranty Claims/Regrello Export - Warranty Claims.rex
```

This automatically generates both outputs, places them in the right folder, and opens the dashboard in your browser.

### Option B: Command Line

```bash
# Generate interactive HTML dashboard
python3 rex_parser.py "path/to/blueprint.rex" --format=html -o "output/data_flow.html"

# Generate text analysis
python3 rex_parser.py "path/to/blueprint.rex" --format=text -o "output/parsed.txt"

# Generate all formats at once
python3 rex_parser.py "path/to/blueprint.rex" --format=all -o output_dir/
```

### Try it now

Every blueprint in `blueprints/` already has generated outputs. Open any `data_flow.html` in your browser to see the interactive dashboard:

```bash
open blueprints/Chevron\ Invoice\ Audit/data_flow.html
```

---

## What It Produces

### Interactive HTML Dashboard (`data_flow.html`)

A single self-contained HTML file — no server needed, just open in any browser. Styled to match the real Regrello product using Figma Design System tokens.

- **Simple View** — Auto-layout stage flow with conditional branches and transitive-reduced arrows
- **Data Flow Overlay** — Toggle in Simple View to see inter-stage data connections; click a stage to isolate its data paths, hover for field details
- **Detailed View** — Tabbed interface with Process Flow, Field Registry, Agent Prompts, and Visual Graph
- **Process Flow** — Click any task to see its inputs, outputs, and data connections. Dashed connectors with green checkpoints between stages
- **Global Search** — Search bar below the header filters across all views: Process Flow, Field Registry, Agent Prompts, and Visual Graph
- **Required Fields** — Red asterisks on required output fields across Process Flow, Field Registry, and Field Modal
- **Field Type Icons** — Inline icons for document, text, decimal, date, checkbox, and sync field types
- **Field Tracing** — Click any field to highlight it across the entire workflow; click again to toggle off
- **Field Registry** — Searchable index of every field with producer/consumer mapping, per-task required/optional status in field modal
- **Agent Prompts** — Full table of all AI agent prompts (human tasks filtered out) with shared/requested field listings, agent filter, CSV export, and copy
- **Agent & Assignee Breakdown** — Context panel shows human assignees (with person/circle/team icons) separately from AI agents; click any entry to filter by that specific agent or assignee
- **Linked Workflow Icon** — Chain/link icon distinguishes linked workflow tasks from human assignees
- **Child Blueprint Cards** — Dashed purple border cards with two-column input/output layout for child workflow invocations
- **Parent + Child + Grandchild Workflows** — Full hierarchy support at any depth; linked workflow tasks expand into child blueprint graphs; navigating resets filters
- **Responsive Header** — Title truncates on narrow screens; view toggle and theme button never wrap
- **Tab Count Pills** — Field and agent counts displayed as inline pills in tab labels
- **Light/Dark Theme** — Toggle switch in the header

### Text Analysis (`parsed.txt`)

Complete human-readable breakdown:
- Every stage, task, field, agent assignment, and condition
- Data flow edge table showing field connections between tasks
- Stage flow with conditional transitions

---

## How to Parse a New Blueprint

1. Export the blueprint from Regrello as a `.rex` file
2. Drop the `.rex` file anywhere (or into `blueprints/{Name}/`)
3. Run the parser:

```bash
# Create a folder for it
mkdir -p "blueprints/My New Blueprint"

# Generate outputs
python3 rex_parser.py "My New Blueprint.rex" --format=html -o "blueprints/My New Blueprint/data_flow.html"
python3 rex_parser.py "My New Blueprint.rex" --format=text -o "blueprints/My New Blueprint/parsed.txt"

# Open the dashboard
open "blueprints/My New Blueprint/data_flow.html"
```

Or with Claude Code: `/parse "My New Blueprint.rex"`

---

## Project Structure

```
Regrello Parser Tools/
├── rex_parser.py              # Parser script (2,641 lines, Python 3, no dependencies)
├── html_template.html         # Dashboard template (2,498 lines, must stay next to parser)
├── cloud logo.png             # Regrello cloud logo (embedded as base64 in dashboards)
├── README.md                  # This file
│
├── blueprints/                # All processed blueprints
│   ├── Chevron Invoice Audit/
│   │   ├── *.rex              # Source blueprint export
│   │   ├── data_flow.html     # Interactive dashboard  <-- open this
│   │   ├── parsed.txt         # Text analysis
│   │   └── parsed.json        # JSON export
│   ├── Warranty Claims/
│   ├── Contract Management/
│   ├── Cybersecurity Survey/
│   ├── Invoice Auditing/
│   ├── Regulated Materials Survey/
│   ├── Return to Vendor/
│   ├── Shelf Life Extension/
│   ├── Supplier Diversity/
│   ├── Supplier Qualification/
│   └── Supplier Scorecard/
│
├── web-app/                   # Web app version (synced template)
│   ├── index.html             # Web app entry point
│   ├── template.html          # Copy of html_template.html (always synced)
│   └── test_parser.js         # JS parser tests
│
├── .claude/skills/parse/      # Claude Code /parse skill (optional)
│
├── docs/                      # Technical documentation
│   ├── PARSER_ARCHITECTURE.md # Parser internals & version history
│   ├── REX_FILE_FORMAT.md     # .rex file structure & JSON schema
│   ├── REGRELLO_PLATFORM.md   # Regrello platform reference
│   └── figma-tokens.json      # Design system tokens from Figma
│
└── reference/                 # Regrello product documentation (PDFs)
```

---

## Blueprints Included

| Blueprint | Stages | Outputs |
|-----------|--------|---------|
| Chevron Invoice Audit (2 levels) | 20+7 | data_flow.html, parsed.txt, parsed.json |
| Warranty Claims | 8 | data_flow.html, parsed.txt, parsed.json |
| Contract Management | 5 | data_flow.html, parsed.txt |
| Cybersecurity Survey | 6 | data_flow.html, parsed.txt |
| Invoice Auditing | 7 | data_flow.html, parsed.txt |
| Regulated Materials Survey | 4 | data_flow.html, parsed.txt |
| Return to Vendor | 6 | data_flow.html, parsed.txt |
| Shelf Life Extension | 6 | data_flow.html, parsed.txt |
| Supplier Diversity (3 levels) | 4+4+4 | data_flow.html, parsed.txt |
| Supplier Qualification | 7 | data_flow.html, parsed.txt |
| Supplier Scorecard | 6 | data_flow.html, parsed.txt |

---

## Output Formats

| Format | Flag | Description |
|--------|------|-------------|
| Text | `--format=text` | Human-readable analysis |
| HTML | `--format=html` | Interactive visual dashboard |
| JSON | `--format=json` | Machine-readable structured data |
| Mermaid | `--format=mermaid` | Flowchart diagram markup |
| All | `--format=all` | Generates all formats at once |

---

## Notes

- `rex_parser.py` and `html_template.html` must be in the **same directory** — the parser loads the template at runtime
- `web-app/template.html` is always kept in sync with `html_template.html` via `cp`
- `.rex` files are ZIP archives containing `blueprint_export.json` — exported from the Regrello platform
- Generated HTML files are fully self-contained (embedded CSS/JS, CDN-loaded D3.js) — no server needed
- The parser uses only Python 3 standard library — zero external dependencies
- HTML template follows a CSS-only modification rule — visual changes go in CSS, not HTML/JS structure
- Dashboard styling matches the Regrello product using Figma Design System tokens (`docs/figma-tokens.json`)
