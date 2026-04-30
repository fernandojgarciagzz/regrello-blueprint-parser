# Parser Architecture & Documentation

## Current Status: PRODUCTION READY

**Date**: April 29, 2026
**File**: `rex_parser.py` (2,641 lines) + `html_template.html` (2,498 lines) + `web-app/index.html` (1,178 lines)
**Architecture**: .rex (ZIP+JSON) → internal data model → .txt + .html output
**Latest Enhancements**:
- **Required field indicators** — red asterisks on required output fields (`REQUESTED` vs `OPTIONAL`) in Process Flow, Field Registry, Field Modal, and Side Panel
- **Human assignee differentiation** — specific labels (Team, Role, System, Email) with distinct SVG icons per category, replacing generic "Human (Dynamic)"
- **Regrello agent robot SVG** — actual Figma-sourced robot icon (node `3833:1222`) replaces emoji placeholder on all AI agent badges
- **Timeline V2 styling** — dashed connectors with green checkpoints, field type SVG icons, compact DataGrid rows, blue hover accents
- **Uniform field type badges** — all badges (doc, text, decimal, date, checkbox, sync) use consistent gray `var(--neutral-soft)` styling
- **Full agent label display** — removed `.substring()` truncation, labels display in full
- **Regrello Design System CSS** — Figma tokens (`docs/figma-tokens.json`) applied across all template sections
- **HTML dashboard export** — interactive D3.js/Dagre-D3 visualization from external template
- **Rich prompt rendering** — HTML descriptions rendered with proper formatting, field mention styling, conditional block labels
- **Document Reader field instructions** — helperText, isMultiValued, allowed values extracted
- **Agent class mapping** — all agent types (including CODER) mapped to CSS classes for HTML
- **Auto-named output files** — `{base}_parsed.txt`, `{base}_data_flow.html`
- Linked Workflow tasks detected with `Links to:` and child blueprint reference
- Cross-Blueprint Data Flow section connecting parent, child, and grandchild workflows at any depth
- Stage conditions show comparison values (boolean, string, numeric)
- Field source resolution picks closest upstream producer (no forward references)
- Child blueprint tasks prefixed with `C1.`/`C2.` to prevent numbering collisions
- Two-section output format (Task Registry + Edge Table/Stage Flow)
- Form sections integrated into outputs with required field markers
- Dynamic assignees resolved to actual source fields
- Description field mentions extracted as implicit inputs (self-references filtered)
- Self-referencing output fields marked with `<< referenced in description`
- Edge table sorted by execution order, one line per edge
- HTML-to-text preserves structure (line breaks, bullets, field mentions)
**All Blueprints**: 11 total, all with `data_flow.html` + `parsed.txt` outputs

---

## Complete Feature List

### 1. Task Descriptions with Visual Box
- ✅ Full HTML-to-text conversion
- ✅ **Boxed presentation** for clear visual separation
- ✅ Complete text displayed (no truncation)
- ✅ Line wrapping at 95 characters to fit in box
- ✅ Professional ASCII box drawing

**Example**:
```
Task 1.2: Automatically select clauses from library (ID: 15338)
    Type: Standard Task
    Starts: After previous task completes (Create Supplier Contact)

    ┌─ DESCRIPTION ─────────────────────────────────────────────────────────────────────────────┐
    │ Set Contract Type to PurchasingUse the attached clause library.Given the country field and    │
    │ contract type values shared, pick the right clause for warranty, governing law, and           │
    │ intellectual propertyPopulate those fields.                                                   │
    └───────────────────────────────────────────────────────────────────────────────────────────┘

    Assignees: AI Agent: Document Agent 004 (DOCUMENT)
```

### 2. Clean Numbering Format
- ✅ **Stages**: "Stage 1:", "Stage 2:", etc. (not "1. Stage Name:")
- ✅ **Tasks**: "Task 1.1", "Task 1.2" (stage.task numbering)
- ✅ Clear hierarchical structure

**Example**:
```
Stage 1: Contract Preparation (ID: 1974)
   Description: Drafting the contract terms and conditions.
   Starts: On workflow start
   Tasks: 5

   Task 1.1: Create Supplier Contact (ID: 15337)
       Type: Standard Task
       ...

   Task 1.2: Automatically select clauses (ID: 15338)
       Type: Standard Task
       ...
```

### 3. No Emojis - Clean Professional Format
All emoji symbols removed for clean, professional text format.

### 4. Task Dependencies Before Description
- ✅ "Starts after:" appears immediately after task type
- ✅ Shows which task must complete first
- ✅ Appears BEFORE description for better readability

**Example**:
```
Task 1.3: Autogenerate Contract (ID: 15339)
    Type: Standard Task
    Starts after: Automatically select clauses from library

    DESCRIPTION:
       Use the Mail Merge tool to fill out the sample contract...

    Assignees: AI Agent: Document Agent 004
```

### 5. Complete Task Start Conditions (EVERY Task)
- ✅ **ALL tasks show when they start** - No exceptions
- ✅ Three types of task start conditions:
  - **First task**: "Starts: When stage begins" + stage trigger details
  - **Explicit dependency**: "Starts after: [Task Name]"
  - **Sequential**: "Starts: After previous task completes ([Task Name])"
- ✅ Conditional stages show "Stage conditions:" with actual operator and value
- ✅ Complete execution clarity - never wonder when a task runs

**Example (First Task - Workflow Start)**:
```
Task 1.1: Create Supplier Contact (ID: 15337)
    Type: Standard Task
    Starts: When stage begins
    Stage trigger: Workflow start

    DESCRIPTION:
       Add the Supplier Email Address...
```

**Example (Sequential Task)**:
```
Task 1.2: Select clauses (ID: 15338)
    Type: Standard Task
    Starts: After previous task completes (Create Supplier Contact)

    DESCRIPTION:
       Use the attached clause library...
```

**Example (Explicit Dependency)**:
```
Task 1.3: Autogenerate Contract (ID: 15339)
    Type: Standard Task
    Starts after: Automatically select clauses from library

    DESCRIPTION:
       Use the Mail Merge tool...
```

**Example (Conditional Stage)**:
```
Task 5.1: High-Risk Review (ID: 15604)
    Type: Approval Task
    Starts: When stage begins
    Stage trigger: After Supplier Cybersecurity Assessment completes
    Stage conditions:
       • Cybersecurity Risk Level EQUALS High

    DESCRIPTION:
       Review and approve high-risk supplier...
```

### 6. Complete Field Display (ALL Fields Shown)
- ✅ **Shows ALL inputs** - no truncation, no "... and X more"
- ✅ **Shows ALL outputs** - complete field lists
- ✅ **Shows ALL form fields** - every field in every section
- ✅ Distinguishes prepopulated vs collected fields
- ✅ "Prepopulated/Context:" for shared fields in forms
- ✅ "Form Collects:" for new fields being gathered

**Example**:
```
Inputs: 9
   • Supplier Name (Text)
   • Supplier Contact Name (Text)
   • Contract Start Date (Date)
   • Contract End Date (Date)
   • Total Contract Value (Decimal)
   • Warranty (Text)
   • Governing Law (Text)
   • Intellectual Property (Text)
   • Payment Terms (Text)        ← All 9 shown, not "... and 4 more"
```

### 7. Human-Readable Field Values
- ✅ **Expiration** - "Does not expire" instead of "TEMPLATE_NON_EXPIRING"
- ✅ **Task types** - "Standard Task" instead of "DEFAULT"
- ✅ **Reject actions** - "Report problem in task: [Name]" with actual task names
- ✅ Natural language throughout

### 8. Complete Workflow Flow & Data Lineage (Enhanced)
- ✅ **3-section comprehensive structure** replacing simple data flow
- ✅ **Section 1: Execution Flow** - stage-by-stage with task dependencies
- ✅ **Section 2: Data Flow by Stage** - field lineage organized by stage context
- ✅ **Section 3: Summary Statistics** - counts, conditional branches, impact analysis
- ✅ **Conditional stages clearly marked** (⚠️ CONDITIONAL)
- ✅ **Stage-controlling fields highlighted** - see what triggers conditional branches
- ✅ **Task dependencies shown** - understand execution order within stages
- ✅ **Flows grouped by context** - internal vs. cross-stage flows

**Example Structure**:
```
SECTION 1: EXECUTION FLOW
────────────────────────────────────────
Stage 5: High-Risk Review ⚠️ CONDITIONAL
   Trigger: After Stage 4 completes
   Condition:
      • Cybersecurity Risk Level EQUALS High
   Tasks: 1
   └─> Task 5.1: High-Risk Review (starts when stage begins)
   Note: This stage only runs if condition is met

SECTION 2: DATA FLOW BY STAGE
────────────────────────────────────────
Stage 4 → Stage 5 Conditional Flows:
   Determine Risk Level:
      • Cybersecurity Risk Level (Text) → High-Risk Review

Conditional Stage Triggers:
   ⚠️ Determine Risk Level produces 'Cybersecurity Risk Level'
      → Controls Stage 5: High-Risk Review
      → Condition: Cybersecurity Risk Level EQUALS High

SECTION 3: SUMMARY STATISTICS
────────────────────────────────────────
Total Stages: 6
   Sequential Stages: 5
   Conditional Stages: 1
Stage-Controlling Fields: 1
   • Cybersecurity Risk Level

Conditional Branches:
   • Stage 5: High-Risk Review
     Runs only if: Cybersecurity Risk Level EQUALS High
     Affects: 1 task(s), 0 field(s)
```

### 9. Reject Actions (Human-Readable)
- ✅ Approval tasks show what happens on rejection
- ✅ Two types: Reopen/restart task, Report exception
- ✅ Shows referenced task name and ID
- ✅ Clear "If Rejected:" label

**Example**:
```
If Rejected: Reopen/restart task: Provide Company Details (ID: 16053)
```

### 10. Complete Task Information
For each task, shows:
- ✅ Task number (e.g., Task 2.3)
- ✅ Type (Standard, Approval, Automation)
- ✅ Dependencies (Starts after) - **NOW BEFORE DESCRIPTION**
- ✅ Full description with instructions
- ✅ Assignees (AI agents and/or humans)
- ✅ Timing (due date, expiration)
- ✅ Form details (if applicable)
- ✅ Inputs/Outputs (prepopulated vs collected)
- ✅ Documents attached
- ✅ Reject actions (human-readable format)

---

## Output Format Structure

```
================================================================================
BLUEPRINT: [Blueprint Name]
================================================================================
ID: [ID]
Type: [Type]
Description: [Full description]
Version Notes: [Notes]

Stages: [N]  |  Tasks: [N] (AI: [N], Human: [N])
Task Types: Standard: [N] | Approval: [N] | Automation: [N]
Data Flow Edges: [N]

Workflow-Level Fields:
  - Field Name (Type) [choices: val1, val2, ...]

================================================================================

SECTION 1: TASK REGISTRY
================================================================================

--------------------------------------------------------------------------------
STAGE [N]: [Stage Name] (ID: [ID])
  Trigger: Workflow start | After [Stage Name] completes
  Condition: [Field OPERATOR Value] | None (always runs)
  Task Execution Order:
    [start] Task N.1: Name
    [then] Task N.2: Name (after Task N.1)

  Task [S.T]: [Task Name]
    ID: [ID]
    Type: Standard | Approval | Automation | Linked Workflow
    Links to: [Child Blueprint Name] (ID: N)  (linked workflow tasks only)
    Integration: NOTIFICATION_EMAIL          (automation tasks only)
    Assignee: Agent: [Name] ([Type]) | Dynamic (from [Field]) | N/A (linked workflow) | [Human] | MISSING
    Due: [Duration]
    Expiration: [Setting]
    Depends On: [Task ref] | Stage start

    Description:
      [Full description, HTML converted to text]
      [Field mentions shown as [FIELD_NAME]]

    Documents: [N]
      - [Document Name]

    Inputs: [N] (M from description)
      - Field Name (Type) [id: N] <- Task S.T: Source Task Name
      - Field Name (Type) [id: N] <- Workflow-level field

    Outputs: [N] (via Form: "Form Name")
      -- Section Name (N fields) --
      - Field Name (Type) [id: N] [choices: val1, val2] *
      -- Additional Outputs (N fields) --
      - Field Name (Type) [id: N]
      - Field Name (Type) [id: N]  << referenced in description

    If Rejected: [Action description] (for approvals)

--------------------------------------------------------------------------------

SECTION 2: EDGE TABLE + STAGE FLOW
================================================================================

EDGE TABLE
--------------------------------------------------------------------------------
  Task S.T: Source Name --[ Field Name (Type) ]--> Task S.T: Target Name

Total Edges: [N]

STAGE FLOW
--------------------------------------------------------------------------------
Stage 1: [Name]
  -> Stage 2: [Name]

Stage 5: [Name]
  -> Stage 6: [Name] (IF Field = "Value")
  -> Stage 7: [Name] (IF Field = "Value")

Stage 6: [Name] [CONDITIONAL]

SUMMARY
================================================================================
Stages: [N] ([N] sequential, [N] conditional)
Tasks: [N] (Standard: [N] | Approval: [N])
Assignees: AI: [N] | Human: [N]
Data Flow Edges: [N]
Agents:
  - [Agent Name]: [N] tasks
Unique Fields: [N]
Stage-Controlling Fields: [Field1], [Field2]
Fields With Constraints: [N]
================================================================================
```

---

## All 10 Blueprints Processed

| # | Blueprint | Outputs | Tasks | Stages |
|---|-----------|---------|-------|--------|
| 1 | Contract Management | `parsed.txt`, `data_flow.html` | 16 | 5 |
| 2 | Invoice Auditing | `parsed.txt`, `data_flow.html` | 16 | 7 |
| 3 | Regulated Materials | `parsed.txt`, `data_flow.html` | 19 | 4 |
| 4 | Return to Vendor | `parsed.txt`, `data_flow.html` | 10 | 6 |
| 5 | Shelf Life Extension | `parsed.txt`, `data_flow.html` | 13 | 6 |
| 6 | Supplier Diversity | `parsed.txt`, `data_flow.html` | 16 | 4 |
| 7 | Supplier Qualification | `parsed.txt`, `data_flow.html` | 11 | 7 |
| 8 | Supplier Scorecard | `parsed.txt`, `data_flow.html` | 20 | 6 |
| 9 | Warranty Claims | `parsed.txt`, `data_flow.html` | 19 | 8 |
| 10 | Cybersecurity Survey | `parsed.txt`, `data_flow.html` | 21 | 6 |
| 11 | Chevron Invoice Audit | `parsed.txt`, `data_flow.html`, `parsed.json` | 67 | 25 |

**Total**: 161 tasks across 59 stages

---

## Parser Usage

### Basic Usage
```bash
cd "/Users/fgarciagonzalez/Regrello Tools"

# Text analysis to stdout
python3 rex_parser.py "path/to/blueprint.rex"

# Text analysis to file
python3 rex_parser.py "path/to/blueprint.rex" --format=text -o "output.txt"

# HTML dashboard
python3 rex_parser.py "path/to/blueprint.rex" --format=html -o "dashboard.html"

# All outputs at once (txt + html + json + mermaid)
python3 rex_parser.py "path/to/blueprint.rex" --format=all
```

---

## Task Field Display Order

**Every task displays fields in this logical order:**

1. **Task number and name** - `Task 1.3: Autogenerate Contract (ID: 15339)`
2. **Type** - `Type: Standard Task`
3. **Task start condition** ⭐ **ALWAYS SHOWN** - One of three types:
   - `Starts: When stage begins` (first task in stage)
   - `Starts after: [Task Name]` (explicit dependency on another task)
   - `Starts: After previous task completes ([Task Name])` (sequential default)
4. **Stage trigger** (first task only) - When the stage becomes active:
   - `Stage trigger: Workflow start`
   - `Stage trigger: After [Stage Name] completes`
   - `Stage trigger: After previous stage completes`
5. **Stage conditions** (if applicable, first task only) - Conditional trigger
6. **Description** - Complete instructions with visual separation
7. **Assignees** - Who performs the task
8. **Timing** - Due date and expiration
9. **Documents** - Attached files/resources (CSVs, templates, etc.)
10. **Email** - Email subject and field mentions (for automation tasks)
11. **Reject actions** - For approval tasks
12. **Inputs/Prepopulated** - Shared fields from previous tasks
13. **Form** - Form details (if applicable)
14. **Outputs/Collected** - New fields being generated

**Rationale**:
- **EVERY task shows when it starts** - No ambiguity
- Task start condition shows when the task itself becomes available
- Stage trigger shows when the entire stage becomes active (first task only)
- **Documents appear early** - See what files/templates are attached before data fields
- Both start conditions appear before description for complete execution context
- You never need to scroll back or guess when a task can run

---

## Version History

- Initial release — basic complete extraction
- Flowchart-ready with data flow graph construction
- Clean format, no emojis, enhanced readability, logical field order
- Validation fixes: form integration, dynamic assignees, description mentions, edge sorting, self-referencing edge fix
- Multi-blueprint fixes: linked workflow detection, cross-blueprint data flow, condition values, source resolution, child task numbering
- HTML dashboard export, Document Reader field instructions, rich prompt rendering, agent class mapping
- Agent prompts tab: full table with shared/requested field listings, agent filter, CSV export with field details, copy
- Field tracing: click any field to trace it across the workflow, glow/dim highlighting
- Project restructuring: clean naming, all blueprints with HTML output

## Roadmap

All major features implemented. Potential future work:
- Batch processing of multiple .rex files
- Diff/comparison mode between blueprint versions

---

## Summary

### Current Capabilities:
- **100% Information Extraction** - All field types (INHERITED, REQUESTED, OPTIONAL), description mentions, dynamic assignees
- **Required Field Detection** - `inputType == 'REQUESTED'` fields marked with red asterisks across all views
- **Human Assignee Categorization** - 4 categories (Team, Role, System, Email) with specific labels and distinct SVG icons
- **Clean Professional Format** - No emojis, no decorative characters, clear numbering
- **Two-Section Text Output** - Task Registry + Edge Table/Stage Flow
- **Interactive HTML Dashboard** - D3.js/Dagre-D3 visualization with simple view, process flow, field registry, agent prompts, visual graph
- **Regrello Design System Styling** - Figma tokens, cloud logo, Timeline V2 connectors, DataGrid tables, agent robot SVG, uniform field badges
- **Responsive Header** - Non-wrapping header with ellipsis truncation, tab count pills
- **Assignee & Agent Breakdown** - Separate context panel sections for human assignees (with role icons) and AI agents (with robot badges)
- **Child Blueprint Cards** - Dashed purple border, two-column input/output grid, field type icons
- **Field Type Icons** - Inline mask-image icons replacing parenthesized type text
- **Form Integration** - Form sections as grouping headers within outputs, required field markers
- **Document Reader Field Instructions** - helperText, isMultiValued, allowed values extracted and displayed
- **Dynamic Assignees** - Resolved to actual source fields (not internal controller names)
- **Description Field Mentions** - Extracted as implicit inputs with source tracking and edge creation; self-references marked on outputs instead
- **HTML Structure Preserved** - Line breaks, bullets, `[FIELD_NAME]` from span mentions
- **Complete Source Tracking** - All inputs show `<- Task X.Y: Name` or `<- Workflow-level field`
- **Sorted Edge Table** - One line per edge, sorted by execution order
- **Stage Flow** - Sequential + conditional transitions shown
- **Both Text + HTML** - Production ready, generated from single `.rex` input
- **Production Ready** - Tested on 11 blueprints

### Statistics:
- **Parser**: 2,479 lines (`rex_parser.py`)
- **Template**: 1,659 lines (`html_template.html`)
- **11 blueprints** processed with text + HTML output
- **228+ tasks** analyzed
- **84+ stages** documented

### Status: PRODUCTION READY
All features implemented, validated, and all blueprints processed with both text and HTML output.

---

## Update: April 1, 2026 - Output Format Refactor

Major restructuring of the text output format for machine-readability and downstream HTML flowchart generation.

### Changes Made

**New Two-Section Output Structure:**
- **Section 1: Task Registry** - One consolidated block per task, organized by stage
- **Section 2: Edge Table + Stage Flow** - Machine-readable data flow and stage transitions

**Blueprint Header:**
- Full workflow-level fields list with choice values
- Compact statistics line (stages, tasks, AI/Human counts)
- Task type breakdown

**Task Registry Format:**
- Proper task type labels: Standard, Approval, Automation, Linked WF
- Assignee handling: Agent (with type), Human, or MISSING
- Input source tracking with `<-` arrows showing where each input comes from
- Output constraints displayed (choices, units)
- Clean HTML entities (all `&gt;`, `&nbsp;` etc. properly unescaped)
- No decorative characters (removed box drawing, emojis)
- Frozen plan steps shown in full (no truncation)
- Documents shown in full (no truncation)
- Task execution order within stages (parallel vs sequential)

**Edge Table:**
- All edges listed with full field names (no truncation)
- Format: Source Task -> [Field (Type)] -> Target Task
- Total edge count

**Stage Flow:**
- Compact, deduplicated stage transitions
- Conditional triggers shown with field values
- CONDITIONAL label on conditional stages

**Removed:**
- All truncation (`[:10]`, `[:3]`, `"... and X more"`)
- Box drawing characters (┌─┐│└─┘)
- Emoji markers (⚠️)
- Duplicate conditional trigger displays
- Old three-section flow/lineage format

**Verified on Shelf Life Extension blueprint:**
- 53 edges (all present, zero truncation)
- 15 tasks across 6 stages
- Zero HTML entities in output
- All task types properly labeled
- All fields have source tracking
- Output constraints shown for all choice fields

---

## Update: April 1, 2026 - Validation Fixes

Two rounds of validation fixes addressing 15 issues found via external review of parser output.

### Round 1: 10 Fixes (Data Extraction & Formatting)

1. **OPTIONAL fields as outputs** - Fields with `inputType: OPTIONAL` now included in outputs alongside REQUESTED
2. **Output label simplified** - "Outputs (Form Collects)" changed to just "Outputs"
3. **Form field count fixed** - Parser now reads both `section.columns[].fields[]` and `section.fields[]` paths
4. **HTML-to-text preserves structure** - `<br>` to newlines, `<p>` to paragraph breaks, `<li>` to bullet points, `<span data-mention-label>` to `[FIELD_NAME]`
5. **Dynamic assignees displayed** - `_format_assignee()` now shows "Dynamic (from Field Name)" when `dynamic_assignment` exists
6. **Automation tasks show dynamic assignees** - Dynamic check precedes automation fallback in control flow
7. **Description field mentions as inputs** - `descriptionFieldInstanceMentions` extracted as implicit inputs for automation tasks
8. **Compact edge table** - One line per edge: `Task X.Y: Name --[ Field (Type) ]--> Task X.Y: Name`
9. **Sequential stage transitions** - Stage Flow shows `->` for all sequential stages, not just those with explicit dependencies
10. **Integration line** - Automation tasks show `Integration: NOTIFICATION_EMAIL` (or other type)

### Round 2: 5 Fixes (Deep Validation)

1. **Dynamic assignee source resolution** - Extracts actual source field from `sourceFieldInstanceMultiValuePartyV2.field.name` instead of showing internal "RegrelloTaskAssignees" controller name
2. **Form sections integrated into outputs** - Form sections become grouping headers within the Outputs list. Shows section name, field count, and `*` for required fields. Old separate "Form:" block removed.
3. **Description field mentions with source tracking** - Builds field registry from all tasks + workflow fields, resolves `fieldId` to name/type, traces source via `field_output_map`, creates data flow edges, annotates inputs with "(from description)"
4. **Edge table sorting** - Sorted by source task execution order then target task execution order (not raw task IDs)
5. **Description blank line cleanup** - `</p>` converts to single `\n` (not `\n\n`), empty `<p></p>` collapses to single blank line

### Form Display Format (New)

```
    Outputs: 45 (via Form: "Provide Company Information")
      -- Company Information (12 fields) --
      - Supplier Contact Name (Text) [id: 70] *
      - Company Legal Name (Text) [id: 27]
      ...
      -- Financial Information (2 fields) --
      - Employer Identification Number (Text) [id: 22] *
      ...
      -- Quality Information (12 fields) --
      ...
```

### Description Field Mentions (New)

For automation tasks (emails), fields referenced in descriptions via `[FIELD_NAME]` notation are now:
- Listed as inputs with "(from description)" annotation
- Source-tracked to originating task or workflow-level field
- Added to the edge table as data flow edges

```
    Inputs: 2 (from description)
      - Supplier Name (Text) [id: 58] <- Workflow-level field
      - Rationale for Decision (Text) [id: 76] <- Task 5.1: Provide Final Approval
```

### Verified on all 12 blueprints with zero errors

---

## Update: April 1, 2026 - Self-Referencing Edge Fix

### Problem
When a task's description mentions one of its own output fields (e.g., Task 2.2 description says "Extract [ISO 9001 Expiration Date]" and that field is Task 2.2's output), the parser was:
- Incorrectly adding the field as an input to the same task
- Creating self-loop edges (Task X.Y → Task X.Y)
- Inflating edge counts

### Fix
1. **Self-reference detection** - Before adding a description mention as an input, checks if the field is in the task's own output set (`own_output_ids`)
2. **Output marking** - Self-referenced output fields are marked with `<< referenced in description` in the output list
3. **Self-loop filtering** - All edges where `from_task_id == to_task_id` are filtered out
4. **Input count accuracy** - `(N from description)` annotation only counts non-self-referencing description mentions

### Output Format

Self-referenced outputs:
```
    Outputs: 3
      - ISO 9001 Expiration Date (Date) [id: 69]  << referenced in description
      - ISO 9001 Certificate Number (Text) [id: 36]  << referenced in description
      - Quality Certificate Overview (Text) [id: 52]  << referenced in description
```

Non-self-referencing description mentions still work as before:
```
    Inputs: 2 (from description)
      - Supplier Name (Text) [id: 58] <- Workflow-level field
      - Rationale for Decision (Text) [id: 76] <- Task 5.1: Provide Final Approval
```

### Verification (Supplier Qualification)
- Edge count: 142 (down from 155 before fix)
- Zero self-loop edges
- 13 output fields marked with `<< referenced in description`
- Tasks 6.1 and 7.1 description inputs unchanged (correctly non-self-referencing)

### Verified on all 12 blueprints with zero errors

---

## Update: April 1, 2026 - Multi-Blueprint Fixes

Five fixes targeting multi-blueprint (parent + child) workflows, primarily validated on the Chevron Invoice Audit blueprint.

### Fix 1: Linked Workflow Task Type Detection
- Tasks that spawn child blueprints now show `Type: Linked Workflow` instead of `Type: Standard`
- New `Links to: [Child Blueprint Name] (ID: N)` line
- Assignee shows `N/A (linked workflow)` instead of `MISSING`
- Detection via `createsWorkflowFromWorkflowTemplateId` field in .rex JSON
- Task Types count in header reflects the new type

### Fix 2: Cross-Blueprint Data Flow Section
- New `CROSS-BLUEPRINT DATA FLOW` section appears between parent summary and child blueprint analysis
- Shows which parent task spawns which child blueprint
- Lists "Fields passed to child" (parent task inputs) and "Fields returned from child" (parent task outputs)
- Bridges the gap between disconnected parent/child blueprint graphs

### Fix 3: Stage Condition Values
- Conditions now show comparison values for all data types:
  - Boolean: `Invoice Available = Yes`
  - String: `Document Family = "Mixed"`
  - Numeric: `Document Count >= 2`
  - EMPTY/NOT_EMPTY: `SC Number EMPTY` (no value needed)
- Human-readable operators: `=`, `!=`, `>=`, `<=`, `>`, `<`
- `(value not set)` shown when value is truly missing from configuration
- Consistent formatting in both Task Registry conditions and Stage Flow transitions

### Fix 4: Cross-Stage Source Resolution
- Field source resolution now tracks ALL producers per field (not just the last one)
- For each input, picks the closest upstream producer based on stage execution order
- Prevents impossible forward references (e.g., Stage 5 task sourcing from Stage 6)
- Applied to both `build_data_flow_graph()` and `generate_summary()` field source maps

### Fix 5: Child Blueprint Task Numbering
- Child blueprint tasks now prefixed with `C1.`/`C2.` etc. (e.g., `Task C1.1.1`, `Task C1.2.3`)
- Prefix applied everywhere: task registry, edge table, stage flow, dependency references, source tracking
- Parent tasks remain unprefixed (default context)
- Child section header shows prefix: `--- CHILD #1 (C1): Blueprint Name ---`
- Eliminates ambiguity when both blueprints have Stage 1, Stage 2, etc.

### Verified on all 12 blueprints with zero errors

---

## Update: April 14, 2026 - HTML Dashboard Export + Document Reader Field Instructions

Two new features bringing the parser from text-only to full visual output.

### Feature 1: HTML Dashboard Export

Interactive single-file HTML visualization generated directly from parsed .rex data. Uses an external template (`html_template.html`) with 4 placeholders replaced by generated data — no intermediate JSON files.

**Template Architecture:**
- Template contains all static CSS (~300 lines) and JS rendering logic (~1100 lines)
- Parser generates 7 JS data structures (`stages`, `childStages`, `parentEdges`, `taskPrompts`, `docReaderConfig`, `stageFlow`, `childFlow`) plus derived data code
- 4 placeholders: `{{TITLE}}`, `{{HEADER_HTML}}`, `{{GRAPH_NOTE}}`, `{{DATA_SECTION}}`

**Visualization Features:**
- **Graph View**: Full DAG with Dagre-D3 layout, stages as cluster boxes, tasks as color-coded nodes by agent type
- **Simple View**: Generic dagre-based stage flow layout with conditional branch arrows
- **Detail Panel**: Click any task to see inputs (with source tracking), outputs, AI prompts, and Document Reader field instruction tables
- **Parent + Child**: Linked workflow tasks navigate to child blueprint graph
- **Theme Toggle**: Light/dark modes
- **Stats Bar**: Stage count, task count, agent-type breakdown with color coding

**Agent Class Mapping:**
| Agent Type | CSS Class | Color |
|---|---|---|
| DOCUMENT_READER, DOCUMENT_EXTRACTION, DOCUMENT | `doc` | Teal |
| AI_AGENT, CODER | `ai` | Purple |
| FLASH | `flash` | Orange |
| EXCEL, EXCEL_AUTOMATION | `excel` | Green |
| TABLES, TABULAR | `tabular` | Blue |
| GENERIC, REGRELLO | `regrello` | Gray |
| None (no agent) | `human` | Yellow |

**CLI Integration:**
- `--format=html` generates HTML dashboard
- `--format=all` generates txt + html + json + mermaid
- Auto-named output: `{base}_data_flow.html`

### Feature 2: Document Reader Field Instructions

Extraction of "Provide Field Instructions for Agent" data from Document Reader tasks.

**Fields Extracted:**
- `helperText` — instruction text for the agent
- `isMultiValued` — whether the field accepts multiple values
- `allowed_values` — constrained choice lists

**Source Path in .rex JSON:**
```
actionTemplate.actions[].actionFields[].fieldInstanceFields[].fieldInstance
  → .helperText
  → .isMultiValued
  → .allowedValues[].displayValue
```

**Display in Text Output:**
```
    Field Instructions for Agent:
      - Field Name: helper text here [Multi-valued] [Choices: val1, val2]
```

**Display in HTML Output:**
- `docReaderConfig` JS object with form name and fields array
- Detail panel renders as a table with columns: Field, Type, Helper Text, Multi?, Choices

### Feature 3: Rich Prompt Rendering

Task descriptions in the .rex file contain raw Regrello HTML with field mention spans, template directives, and structural markup. The parser now cleans these into display-ready HTML.

**Transformations (`_clean_prompt_html`):**
- `<span data-mention-label="X">` → `<span class="field-mention">[X]</span>` (styled with accent color)
- `{{Line Break}}` / `{{LineBreak}}` → `<br>`
- `{% if X %}` → `<div class="prompt-conditional">If X:</div>` (styled conditional label)
- `{% endif %}` → removed
- Empty `<p></p>` → removed
- Excessive `<br>` sequences (3+) → collapsed to 2
- Structural tags (`<p>`, `<br>`, `<strong>`, `<code>`, `<ul>/<li>`) preserved and rendered

**Template Changes:**
- Prompt display changed from `<pre>` + `escHtml()` to `<div class="prompt-text">` with direct HTML rendering
- Preview text strips HTML tags for clean table display
- Copy-to-clipboard converts HTML to plain text (`<br>` → newline, tags stripped)
- CSS: `.field-mention` (accent-colored badge), `.prompt-conditional` (left-bordered italic block)

### Fix: Simple View dagre Reference

The `dagre-d3` library only exports `window.dagreD3`, not `window.dagre`. The Simple View was using `dagre.graphlib.Graph()` and `dagre.layout()`, causing a silent `ReferenceError`. Fixed to `dagreD3.graphlib.Graph()` and `dagreD3.dagre.layout()`.

### Verified on Chevron Invoice Audit (93 tasks, 29 stages) and Warranty Claims (30 tasks, 12 stages)
- All stages, tasks, edges, prompts, doc reader configs match hand-crafted reference HTML
- Agent class distribution verified: 100% match across all task types
- Simple View renders correctly with dagre auto-layout
- Rich prompts display with field mentions, formatting, and conditional blocks

---

---

## Update: April 25, 2026 - Regrello Design System CSS Integration

Full visual overhaul of the HTML dashboard template using design tokens extracted from the Regrello Figma Design System (file `0kOWTk0cXyGQxpQRqhqxQL`, library `lk-1468d9b093c4...`).

### Design Tokens Extracted (`docs/figma-tokens.json`)

476-line token file containing:
- **Colors**: Full accent system with 5 callout intents (Neutral, Primary, Danger, Success, Warning) — each with `soft` bg, `border`, and `text-muted` variants for both light and dark themes
- **Typography**: Inter font family, weight scale 400–700
- **Spacing**: 4px base unit system
- **Border Radius**: 4px (sm), 8px (md), 12px (lg)
- **Elevation**: 5-level shadow system (card, shadow-1 through shadow-4)
- **Component Specs**: Card, Callout, Button, Input, Checkbox, RadioButton, Select, Tooltip, Popover, Avatar, DataGrid stubs

### CSS Changes (template only — no HTML/JS modifications)

All changes are CSS-only in `html_template.html` (synced to `web-app/template.html`).

**CSS Custom Properties Added:**
- `--neutral-soft`, `--neutral-border`, `--neutral-solid` variants
- `--primary-soft`, `--primary-border`, `--primary-text-muted`
- `--danger-soft`, `--danger-border`, `--danger-text-muted`
- `--success-soft`, `--success-border`, `--success-text-muted`
- `--warning-soft`, `--warning-border`, `--warning-text-muted`
- `--shadow-card`, `--shadow-1` through `--shadow-4`
- `--radius-sm`, `--radius-md`, `--radius-lg`
- `--tooltip-bg`, `--tooltip-text`

**Sections Restyled:**

| Section | Key Changes |
|---------|------------|
| Header | Clean divider-separated stats (large number + label), no top stripe, no shadows |
| Filter bar | Subtle rect buttons with color dots, transparent bg, minimal borders |
| Tabs | Thin 2px accent underline, no active background fill |
| Task cards | Thin left accent border, muted task ID badge, neutral hover |
| Stage flow | Borderless headers, no shadows, clean hover |
| Stage boxes | Clean borders, no shadows |
| Trace bar | Primary callout style, no shadow |
| Context panel | Clean headings, pill tags with callout colors |
| Side panel | Clean white header, flat sections |
| Field modal | Simple border, backdrop blur, no accent stripe |
| Field registry | Light gray header row (`surface2`), 1px border, neutral hover |
| IO tags | Small rect tags with subtle tinted backgrounds |
| Cross-blueprint | Clean white background, subtle field badges |
| Edge table | Simple border headers, no shadows |
| Multi-select | Rect buttons, no shadows, primary-soft count badge |
| Prompt table | Gray header row, neutral hover, simple export button |
| Prompt elements | Subtle field mentions, warning-tinted conditionals |
| Toolbars | Simple rect buttons, accent on hover only |
| Data tables | Gray headers, neutral hover |
| Agent badges | Purple pill with robot emoji for all AI agents (uniform), gray pill with person icon for humans |

**Dark Theme:**
All new variables have matching dark variants (muted blues, deeper backgrounds, higher-contrast text). Agent pill uses `--agent-pill-bg` / `--agent-pill-text` variables.

### Pending Enhancements

- **Left navigation sidebar**: Regrello has a dark sidebar nav — parser could optionally render one for multi-blueprint sets
- **Published blueprint badge**: Green outlined "Published blueprint" tag shown in Regrello UI
- **Schedule/timeline view**: Regrello's blueprint view includes a DAY 0–6 timeline grid on the right side
- **Create workflow button**: Purple CTA button style not yet replicated
- **More screenshots needed**: Task detail panel, field modal, form editor, data tab to further refine styling

---

## Update: April 27, 2026 - Regrello Figma V2 Styling & Data Enhancements

Multiple parser + template refinements to better match the real Regrello product UI based on Figma component inspection and product screenshots.

### Feature 1: Required Field Indicators

Output fields now show whether they are required (`REQUESTED`) or optional (`OPTIONAL`), with red asterisks matching the Regrello Figma design (node `5104:11178`).

**Parser Changes (`rex_parser.py`):**
- `_build_stages_js()` now emits `req:1` or `req:0` per output field, derived from `f.get('input_type') == 'REQUESTED'`
- The `req` flag propagates to the JS data objects consumed by the template

**Template Display (CSS + JS, 5 locations):**
- **Process Flow**: Output tags show `*` prefix for required fields
- **Field Registry**: Required fields show `* FieldName` in bold
- **Field Modal**: Required fields show `*` in heading + red "Required" label next to field type badge
- **Side Panel**: Output list shows `*` prefix for required fields
- **CSS class**: `.req-ast{color:var(--danger-text-muted);font-weight:600;font-size:14px;line-height:1}`

### Feature 2: Human Assignee Type Differentiation

Human assignees now show specific categories instead of generic "Human (Dynamic)".

**Assignee Categories:**
| Category | Label Example | Icon | CSS Class |
|----------|--------------|------|-----------|
| Team | `Human (Team: Quality Team)` | Group/people | `.ht-team` |
| Role | `Human (Role: Supplier Contact)` | Shield/check | `.ht-role` |
| System | `Human (System: Workflow owner)` | Gear/settings | `.ht-system` |
| Email | `Human (Email: john@example.com)` | Envelope | `.ht-email` |

**Parser Changes (`rex_parser.py`):**
- `_html_agent_label()` — resolves assignee to specific label with category and name
- `_html_human_subtype()` — returns subtype string (`team`, `role`, `system`, `email`) for icon selection
- System fields detected: `{'Workflow owner', 'Workflow creator'}`
- Human subtype emitted as `ht:"subtype"` in JS task objects

**Template Changes:**
- `badgeCls(t)` helper function combines `clsMap[t.agentClass]` with `ht-` modifier class
- 4 CSS rules with `mask-image` SVG icons for each subtype (team, role, system, email)
- All 5 badge rendering locations updated to use `badgeCls(t)` instead of `clsMap[t.agentClass]`

### Feature 3: Agent Robot SVG Icon

AI agent badges now use the actual Regrello robot icon SVG extracted from Figma node `3833:1222` (Avatar Icon component), replacing the placeholder robot emoji.

**Implementation:**
- SVG rendered via CSS `mask-image` on `.a-ai::before`, `.a-flash::before`, etc.
- Purple circle background with white robot face silhouette
- Consistent across all AI agent types (Document, Flash, Excel, Tabular, Regrello, Coder)

### Feature 4: Timeline V2 Process Flow Styling

Stage flow section restyled to match Regrello's Timeline + DataGrid V2 Figma designs:
- Dashed vertical connectors between stages with green dot checkpoints
- Field type SVG icons in badges (document, text, currency, date, checkbox, sync)
- Compact DataGrid-style tables with 32px rows
- Blue left-border accent on hover
- Task IDs as blue text without background, matching the Regrello "fMPkxb" pattern

### Feature 5: Uniform Field Type Badges

All field type badges in the Field Registry use uniform gray styling:
```css
.ft-doc, .ft-text, .ft-dec, .ft-date, .ft-chk, .ft-sync {
  background: var(--neutral-soft);
  color: var(--text-dim);
  border: none;
}
```
Each badge retains its distinct `mask-image` SVG icon (document, text, decimal, date, checkbox, sync arrows).

### Feature 6: Full Agent Label Display

Removed `.substring()` truncation from agent labels in both side panel and stage flow task cards, allowing full display of labels like "Human (System: Workflow owner)".

### Architecture Notes

- **CSS-only template rule**: All visual changes in the template are CSS-only. HTML structure and JavaScript logic in the template are never modified — only the parser's generated `{{DATA_SECTION}}` can change JS behavior.
- **Template sync**: `html_template.html` and `web-app/template.html` must always be kept in sync via `cp`.
- **Template integrity**: 4 placeholders (`{{TITLE}}`, `{{HEADER_HTML}}`, `{{GRAPH_NOTE}}`, `{{DATA_SECTION}}`), 1 `</style>`, 3 `</script>`, 1 `</html>`.

### Statistics Update

- **Parser**: 2,474 lines (`rex_parser.py`)
- **Template**: 1,593 lines (`html_template.html`)
- **Blueprints**: 11 total, all with `data_flow.html` + `parsed.txt` outputs

---

## Update: April 27, 2026 - Dashboard UX Refinements

Multiple template and parser enhancements improving layout, iconography, and data presentation.

### Feature 1: Responsive Header Layout

Header now uses `flex-wrap: nowrap` so the view toggle, theme button, and title stay on one row at any viewport width. The blueprint title truncates with ellipsis instead of pushing controls to a second line. Stats row (stages/tasks/agents) removed from the header.

### Feature 2: Tab Count Pills

Field and agent counts displayed as inline pill badges within tab labels:
- **Field Registry**: shows field count
- **Agent Prompts**: shows count of non-human agent tasks

Counts are computed dynamically from the data section at init time. Active tabs use accent-colored pills. Process Flow tab has no pill to avoid duplicating the context panel overview stats.

### Feature 3: Cloud Logo Branding

The Regrello cloud logo (`cloud logo.png`) is embedded as base64 in generated dashboards. The web-app loads it at runtime from `cloud-logo.png`. No external image requests needed.

### Feature 4: Child Blueprint Card Redesign

Child workflow invocation tasks now render as distinct cards with:
- Dashed purple border (`--agent-pill-text`) to distinguish from regular tasks
- Two-column grid layout (Inputs | Outputs) with a 1px divider
- Field type icons using the existing CSS mask-image system
- Purple left-border accent

### Feature 5: Input/Output Color Coding

- **Input (shared) fields**: Yellow styling (`--warning-text-muted`) for `.io-tag.inp` and `.io-lbl.inp`
- **Output fields**: Green styling (`--green`) — unchanged

### Feature 6: Field Type Icons

Parenthesized field type text (e.g., `(Document)`) replaced with inline icons using the existing `.ft-doc`, `.ft-text`, etc. CSS classes. A new `.ft-icon` class strips the background/border from the type badge classes and renders just the mask-image icon at 16x14px.

### Feature 7: Per-Task Required/Optional in Field Modal

The field modal (opened from Field Registry) now shows which tasks require vs. optionally use each field, with clickable task chips that navigate to the Process Flow task. Asterisks removed from the main field registry table.

### Feature 8: Agent Prompts — Human Task Filter

Human tasks filtered out of the Agent Prompts tab:
- `ptBuildRows()` skips tasks with `agentClass === 'human'`
- `'human'` removed from the agent filter dropdown array

### Feature 9: Assignee & Agent Breakdown

The context panel summary now splits into two sections:
- **Assignee Breakdown**: Human assignees grouped by exact name, with icons (person for email/system, circle for role, two-people for team) using the `ht-*` CSS classes
- **Agent Breakdown**: Non-human AI agents grouped by exact agent name, each with the robot icon badge

Each row is clickable to filter by that specific agent/assignee name. Selected rows highlight with a blue left-border accent; unselected rows dim. Filters work by agent name (not class), so selecting "AI Agent 005" only affects that specific agent.

### Feature 10: Linked Workflow Icon

Linked workflow tasks (child blueprint invocations) now use a chain/link icon instead of the person icon. New `.a-linked` CSS class with a horizontal link SVG, styled in purple agent pill colors.

### Feature 11: Outline-Style Action Icons

Copy and CSV export icons in the Agent Prompts tab replaced with clean outline-style stroke-based SVGs (Feather icon style) instead of filled shapes.

### Feature 12: Global Search Bar

Search bar below the header filters across all views and tabs:
- **Simple View**: dims non-matching stage nodes
- **Process Flow**: dims non-matching task cards and stage boxes
- **Field Registry**: syncs into the local field search and filters rows
- **Agent Prompts**: filters rows via global search (no local search bar)
- **Visual Graph**: dims non-matching D3 nodes

### Feature 13: Interactive Data Flow Overlay

Simple View's Data Flow toggle completely overhauled:
- Curves render at moderate opacity (35%) by default — visible without overwhelming
- Hover any curve to highlight it and see a field list tooltip
- Click a stage to isolate its incoming/outgoing data connections; all others dim
- Click again to deselect
- Better curve routing with source-grouped spread offsets instead of alternating left/right
- Field count labels appear on active connections
- `intraStageEdges` map tracks within-stage data flow (not drawn as arrows, but available in data)

### Feature 14: Transitive Reduction for Stage Arrows

Simple View applies transitive reduction to `stageFlow` edges before layout. Removes redundant arrows where a longer path already exists (e.g., A→C removed if A→B→C exists). For Chevron Invoice Audit: 36 edges reduced to 20, significantly cleaner layout.

### Feature 15: Human Assignee Icon Refinement

- **Person icon** (single person): default for email and system assignees (gear icon removed)
- **Circle icon**: role-based assignments (replaced shield)
- **Two-people icon**: team assignments (unchanged)

### Statistics Update

- **Parser**: 2,484 lines (`rex_parser.py`)
- **Template**: 1,803 lines (`html_template.html`)
- **Blueprints**: 11 total, all with `data_flow.html` + `parsed.txt` outputs

---

## Update: April 29, 2026 - Deep Hierarchy Text Output + Stage Badge Styling

### Fix 1: Recursive Child Blueprint Text Output

The text output (`--format=text`) previously only detected direct parent→child linked workflow relationships. Child→grandchild and deeper links were missing from both the Cross-Blueprint Data Flow section and the blueprint listing.

**Root Cause:**
- `generate_combined_summary()` only scanned `parent.stages` for linked workflow tasks
- Child blueprints were listed flat ("Child #1", "Child #2") with no hierarchy indication

**Fix (both Python parser and web-app JS parser):**
- Build a spawn tree mapping which blueprint spawns which via `createsWorkflowFromWorkflowTemplateId`
- **Tree listing**: Recursive `_tree_listing` / `treeListing` renders indented hierarchy at any depth
- **Cross-Blueprint Data Flow**: Scans ALL blueprints (not just parent) for linked workflow tasks
- **Child section headers**: Each child shows `[spawned by ...]` indicating its actual parent
- **Child emission order**: Recursive spawn-tree walk with `visited` set to prevent cycles, plus fallback for orphans

**Example (Supplier Diversity — 3 levels):**
```
Total Blueprints: 3
  Parent: Supplier Diversity Survey - Email (ID: 329)
    Child (C1): Supplier Diversity Survey - Matrix (ID: 373)
      Child (C2): Supplier Diversity Survey (ID: 327)

CROSS-BLUEPRINT DATA FLOW:
  Parent Task 2.2 -> spawns (C1) Supplier Diversity Survey - Matrix
  (C1) Task C1.1.1 -> spawns (C2) Supplier Diversity Survey
```

**Verified on:**
- Supplier Diversity (parent → child → grandchild, 3 blueprints)
- Chevron Invoice Audit (parent → child, 2 blueprints)
- All 9 single-blueprint .rex files (no regression)

### Fix 2: Gray Stage Number Badges in Process Flow

Stage number circles in the Detailed View Process Flow tab were colored based on the dominant agent type (blue/purple). Changed to neutral gray for visual consistency.

**Root Cause:**
- `renderStageBox()` set inline `style="background:..."` using `cm(dominantAgent(s))` which resolved to `--accent` (blue) or agent colors
- The `.stage-num` CSS class change had no effect because inline styles override CSS classes

**Fix:**
- `renderStageBox()` now uses `cssVar('--neutral-solid')` (`#88929a` light / `#505a65` dark) for all non-child stage badges
- Child stage badges still use `--agent-pill-text` (purple) for visual distinction
- Removed unused `dominantAgent()` call and `col` variable from the function
- Added cache-bust query param (`?v=Date.now()`) to `template.html` fetch in web-app to prevent stale template caching

### Cleanup

- Removed orphan `blueprints/Golden Test - Master V2/` directory (had `parsed.txt` + `data_flow.html` but no source `.rex` file)

### Statistics Update

- **Parser**: 2,641 lines (`rex_parser.py`)
- **Template**: 2,498 lines (`html_template.html`)
- **Web-app**: 1,178 lines (`web-app/index.html`)
- **Blueprints**: 11 total, all with `data_flow.html` + `parsed.txt` outputs

---

**Last Updated**: April 29, 2026
**Maintained By**: rex_parser.py
**Location**: `/Users/fgarciagonzalez/Regrello Parser Tools/`
