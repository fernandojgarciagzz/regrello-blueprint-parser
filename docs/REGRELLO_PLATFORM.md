# Regrello Platform Documentation
## Agentforce for Supply Chain

**Version**: 1.0
**Last Updated**: March 26, 2026
**Source**: Official Regrello Documentation

---

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Getting Started](#getting-started)
3. [Core Concepts](#core-concepts)
4. [AI Agents](#ai-agents)
5. [Tools Reference](#tools-reference)
6. [Data Types & Fields](#data-types--fields)
7. [Writing Task Descriptions](#writing-task-descriptions)
8. [Plans & Determinism](#plans--determinism)
9. [Testing & Debugging](#testing--debugging)
10. [API Reference](#api-reference)
11. [Platform Features & Releases](#platform-features--releases)

---

## Platform Overview

### What is Regrello?

Regrello (branded as **Agentforce for Supply Chain**) is a workflow orchestration platform that uses AI agents to automate tasks within supply chain processes. The platform is invite-only and users must be invited to access the application.

### Key Capabilities

- **AI-Powered Automation**: Multiple specialized AI agents handle different task types
- **Workflow Orchestration**: Build reusable process templates (blueprints) that create workflow instances
- **Document Processing**: Extract data from PDFs, images, Excel files, and other documents
- **Data Transformation**: SQL queries, arithmetic calculations, table operations
- **Deterministic Execution**: Agents create frozen plans that execute consistently
- **API Integration**: GraphQL API for programmatic workflow management

---

## Getting Started

### Access & Authentication

Regrello is invite-only. Users cannot sign up directly and must be invited to access the application.

#### First-Time Sign-In

New users receive a "Welcome to Regrello" email with an "Accept Invite" button. The authentication method depends on organizational setup:

**Method 1: Single Sign-On (SSO)**
- Click "Accept Invite" → Redirects to SSO provider
- If already authenticated through SSO, gain immediate access
- If not authenticated, follow SSO provider steps

**Method 2: Password Setup**
- Click "Accept Invite" → Password creation prompt
- Password requirements (must meet ALL):
  - At least 15 characters in length
  - Include at least 3 of 4 types: lowercase letters, uppercase letters, numbers, special characters
- Automatic sign-in after password set

**Method 3: Sign In With Google**
- Click "Accept Invite" → Sign-in page
- Select "Sign in with Google"
- Authenticate with Google credentials

#### User Types

**Internal Users**:
- Receive welcome email
- Can access full platform features (Home dashboard, launching workflows, bulk replies)
- Must sign in to platform

**External Users** (suppliers, customers):
- Do not receive welcome email unless explicitly invited via task
- Can complete assigned tasks via email or webform without logging in
- Limited platform access

---

## Core Concepts

### Blueprint

A **blueprint** is the reusable template that defines a supply chain process. It contains:
- Structure and stages
- Action Items (tasks and approvals)
- Agents assigned to specific tasks
- Logic (conditional branching, smart rules, forms)

A blueprint is published once and used to create multiple workflow instances.

### Workflow

A **workflow** is a single run (instance) of a blueprint. Each workflow:
- Follows the blueprint's structure
- May differ per run due to conditional branches, smart rules, or forms
- Contains runtime data specific to that instance

### Action Item

An **Action Item** is a task or approval within a workflow. It has:
- **Name**: Descriptive task name
- **Description**: Natural language instructions (the prompt the agent follows)
- **Inputs**: Shared fields and attached documents
- **Outputs**: Requested fields the agent must fill
- **Assigned Agent or Human**: Who executes this task

**Critical**: Everything the agent knows comes from what's configured in the Action Item. Agents cannot see other Action Items in the workflow.

### Passing Data Between Action Items

Outputs from one Action Item can be shared as inputs to the next:
- Configure field mapping in the blueprint editor
- Map a field from a previous task as a shared field on the next task
- The receiving agent sees the value but not where it came from
- This is how you chain agents together

**Example flow**:
1. Task 1 extracts data from a PDF (Document Agent)
2. Task 2 filters that data with SQL (Tabular Agent)
3. Task 3 makes a decision based on the result (Flash Agent)

Each task only sees what you explicitly pass to it.

### Plan

A **plan** is the execution strategy an agent creates the first time it runs a task:
- A linear sequence of tool calls
- Same tools, same order, same variable mappings every time
- Once saved, the agent follows this exact plan on all future runs
- Plans are **deterministic** after the first run

**Limitations**:
- Plans cannot loop
- Plans cannot branch
- Plans cannot adapt to variable-length inputs
- Plans are strictly linear

**This makes agents deterministic** but also means certain tasks (like processing a variable number of documents) are not possible within a single Action Item.

### Freeze Plan

A way to test and lock an agent's plan before going live:

**Two methods**:
1. Run the blueprint in draft mode
2. Run the task in Prompt Studio (test tab)

When the test run completes successfully, the plan is saved. From that point on, every execution of that task follows the frozen plan exactly.

**Always freeze plans before publishing to production.**

**Warning**: If a task does not have a saved plan when the blueprint is published, it will re-plan on every single run and will not save a plan for reuse. This means non-deterministic behavior in production.

### When Does a Saved Plan Break?

Modifying a task after its plan has been frozen can invalidate the saved plan:

**Changes that break a plan**:
- Renaming or removing input/output fields the plan references
- Changing the agent assigned to the task
- Significantly rewriting the task description
- Changing the type of an input or output field (e.g., Text → Number)

When a plan breaks, the agent will attempt to create a new plan from scratch on the next run, which may fail or produce different results.

**After making changes to a frozen task, always re-test** in Prompt Studio or draft mode to generate and freeze a new plan before going live.

**Note**: Duplicating a task creates a completely separate task. Plans do not transfer to duplicates. The duplicated task will need its own test run to generate and freeze a new plan.

---

## AI Agents

### How Agents Execute Tasks

When a task starts, the AI Agent immediately begins work. Tasks typically take **20-90 seconds** to complete.

**Assignment behavior**:
- **Agent is sole assignee**: Autonomously completes and submits
- **Agent co-assigned with human**: Fills all fields but waits for human review/submit
- **Fallback assignees configured**: Task reassigns to fallback users on failure
- **No fallback, no co-assignee**: Agent reports a problem on the task

### What Agents Cannot Do

Agents have hard boundaries:

- Cannot access other Action Items in the same workflow (each task is isolated)
- Cannot call external APIs, web services, or send emails/notifications
- Cannot create or modify blueprints or workflows
- Cannot access files via URL or document links (only uploaded/attached files)
- Cannot process password-protected or encrypted documents
- Cannot run longer than 20 minutes per task
- Cannot loop or branch within a single plan (plans are strictly linear)
- Cannot process a variable number of inputs (the plan locks in a fixed number of tool calls)

---

## Available Agents

### Flash Agent

**Single LLM call** — no planning, no tool steps. All inputs go directly to Gemini, all outputs come back in one response.

**Best for**:
- Extracting specific fields from documents (names, dates, amounts, addresses, tables from PDFs)
- Classification and heuristics: yes/no decisions, categorization, routing
- Summarization and text transformation
- OCR: reading text from images and PDFs
- Simple reasoning: comparing values, applying business rules
- Task approval/rejection with criteria
- Extracting data from unstructured text fields
- Image-based classification
- Filling large forms (20+ fields) to pre-populate for human review

**Approval tasks**: An approval task is a special Action Item type with Approve/Reject buttons. To use Flash Agent for approvals:
1. Configure the Action Item as an approval task in the blueprint
2. Assign Flash Agent
3. Specify approval/rejection criteria in task description
4. Agent will approve or reject and can fill in a text field with rationale

**Not for**:
- Tables with more than ~100 rows
- Generating or transforming large tables (use Tabular agent)
- Precise arithmetic (use Tabular agent)
- Creating documents (PDFs, DOCX) (use Document agent)

**Limitations**:
- Non-deterministic: same inputs may produce slightly different outputs across runs
- Context limit: ~20,000 tokens total (~30 pages text, ~15 page PDF, ~200 rows × 10 columns CSV). Large inputs will be truncated.
- Output chunking: 8+ output variables are split into multiple LLM calls, slowing execution and causing inconsistency
- Cannot create files — can only select from documents already provided as inputs
- For image-based tasks: struggles to identify image quality issues (out-of-focus, unreadable text)
- Cannot handle conditional logic in prompts ("if X then do Y, else Z"). Plans are linear and cannot branch. Move conditional logic to blueprint-level stage conditions.

### Tabular Agent

**Multi-step agent with deterministic data tools.** A planner sequences the tool calls; you guide it via the task description.

**Best for**:
- Filtering, joining, aggregating, or transforming tables (SQL Tool)
- Querying data sources (Data Source SQL / Search tools)
- Date calculations (Date Math Tool)
- Arithmetic (Arithmetic Tool)
- Converting between CSV documents and tables
- Merging multiple CSV files

**Prefer this over Flash Agent when**: The task involves data that can be expressed as SQL or arithmetic. SQL is deterministic and scalable; LLM is not.

**Limitations**:
- Handles up to 1,000,000 rows
- Search/filter is case-sensitive by default. User must specify case-insensitive matching in prompt
- Cannot perform fuzzy search. Search terms must match exactly (substring-based)
- Cannot do "smart" filtering without a specific search term
- Calculated columns limited to basic math: + - * /
- Cannot read Excel formatting or formulas. Columns may rename to snake_case, numbers become decimals (120 → 120.0)
- Tabular extraction only from electronically-generated PDFs

### Document Agent

**Multi-step agent for generating and comparing documents.**

**Best for**:
- Filling DOCX templates with data ({{ placeholder }} style)
- Generating PDFs from markdown templates with rich text and tables inline (cannot insert images or merge with other PDFs). To control length, specify word count (not page count)
- Comparing two DOCX files — returns a table of all differences in content, redlines, and comments (CSV)
- Extracting structured data from documents (PDFs, images, CSV, .xlsx, .docx, .pptx)
- Summarizing one or more documents

**Limitations**:
- Performance degrades when extracting 15+ fields. Recommend splitting into two tasks
- Tabular extraction only from electronically-generated PDFs. Cannot extract tables spanning multiple pages
- .docx template variables MUST use exact format: `{{ variable_name }}` (lowercase, underscores)
  - **Correct**: `{{ supplier_name }}`
  - **WRONG**: `SupplierName`, `{{ Supplier Name }}`, `{supplier_name}`
- Document summarization degrades with large/multiple documents

### Excel Agent

**Multi-step agent for working with Excel files.**

**Best for**:
- Extracting sheets from Excel files as tables
- Executing Excel formulas by mapping input values to cells and reading output cells
- Reading/writing Excel cells using natural language instructions

### Document Extraction Agent (Document Reader)

**Specialized agent for extracting structured fields and tables from documents using LLM+OCR.**

**Best for**: Extracting named fields (invoice number, vendor name, line items table) from PDFs, images, or scanned forms.

**Note**: May not be available in all configurations. If unavailable, assign Flash Agent instead — it handles most document extraction tasks.

### Regrello Agent (General)

**Multi-step agent with access to the General LLM Tool alongside other tools.** Used when the task requires LLM reasoning as one step within a larger tool sequence.

**Example**: Extract a table from a PDF, then use the LLM to classify rows, then output a summary.

**This is the only agent that can query from data sources.**

**Data source capabilities**:
- Requested data sources look like tables
- Can be queried with Data Source SQL Tool or Data Source Search Tool
- Column filtering, keyword search, and semantic search

**Three search types**:
- **Column filtering**: "Find all suppliers where Country = 'USA' and NAICS code is '54151'"
- **Keyword search**: "Find all parts that contain 'aluminum'"
- **Intelligent search (semantic)**: "Find all customer claims related to damage during shipment"

**Data source limitations**:
- Can search datasets with millions of rows but works best returning 100 rows or fewer
- Search is substring-based — cannot do logic like "Return all items with a price above $100"
- Data sources must be manually configured by Regrello for agent search
- Semantic search cannot be combined with column filters

**Date calculations** (absorbed from deprecated Date Calculation Agent):
- Example: "Calculate the renewal date by subtracting 60 days from the expiration date"
- Example: "Calculate the expected duration by finding the difference between 'start_date' and 'expected_end_date'"
- Limitation: Offsets must be whole numbers representing days. Timestamps not supported

**Create small tables** (up to 20 rows) from any file type:
- Example: "Extract the '5 Whys' analysis from the provided root cause analysis and format it as a table"
- Recommended for 30 lines or fewer
- LLM-created so accuracy may be lower

**Note**: Avoid over-relying on the General LLM Tool within this agent. Prefer deterministic tools where possible and use the LLM tool only for steps that genuinely require reasoning.

---

## Agent Selection Guide

**Before recommending an agent, consider**:
1. What is the primary operation? (extraction, transformation, decision, generation)
2. Does it need determinism? (If yes, prefer Tabular over Flash)
3. How large is the data? (>100 rows → Tabular; >1M → may need splitting)
4. Does it need data source queries? (Only Regrello Agent)
5. Does it need to create a document? (Only Document Agent)

### Quick Reference Table

| Task | Assign |
|------|--------|
| Extract fields from a document (name, date, amount) | Flash (or Document Extraction if available) |
| Classify, categorize, or make a yes/no decision | Flash |
| Summarize a document or text | Flash |
| Filter, aggregate, or join tabular data | Tabular |
| Query a table with SQL | Tabular |
| Query a datasource with SQL or filters | Regrello |
| Arithmetic (calculations on numbers) | Tabular |
| Fill a DOCX template or generate a PDF | Document |
| Compare two DOCX files | Document |
| Read/write Excel cells or execute Excel formulas | Excel |
| Extract sheets from an Excel file as tables | Excel |
| Extract a table from a PDF or image | Flash or Document Extraction |
| LLM reasoning as one step in a multi-tool workflow | Regrello |
| Approve or reject a task based on criteria | Flash (must be approval task) |
| Classify images (damage type, document type) | Flash |
| Extract data from unstructured text/email body | Flash |
| Date math (differences between dates, offsets) | Regrello |
| Search a datasource (column filter, keyword, semantic) | Regrello |
| Create a small table (≤20 rows) from any file | Regrello |

---

## Tools Reference

### Tabular Agent Tools

**General LLM Tool**
- Single LLM call for reasoning, extraction, classification
- Returns: Text, Number, Boolean, Date, TextList, Table (small), or Document selection
- Cannot create documents
- All agents have access to this tool
- Shouldn't be used to analyze or create large tables (< 50 rows)
- Shouldn't be used where determinism is important
- Should only be used for heuristics, limited matching/scoring, re-formatting, or document extraction

**Excel to Tables Tool**
- Extract one or more sheets from an Excel file as Tables
- Output variable names should describe the sheet content

**SQL Tool**
- Execute DuckDB SQL on in-memory tables
- Use `$variable_name` for parameter substitution
- Returns: Table, Number, or Text
- Multi-statement queries use semicolons; last result is returned
- Good for deterministic logic, especially table operations like joins, filters
- Can only do what SQL can do

**Arithmetic Tool**
- Evaluate expressions like `x * y + z`
- Supports: +, -, *, /, ^ (power)
- Returns: Number

**Date Math Tool**
- Calculate days between two dates
- Offset a date by days/weeks/months/years

**CSV to Table Tool**
- Convert a CSV document to a Table

**Table to CSV Tool**
- Convert a Table to a CSV document

**Document Merge Tool**
- Merge multiple CSV documents with identical column structure into one CSV

### Document Agent Tools

**General LLM Tool**
- Single LLM call for reasoning, extraction, classification
- Returns: Text, Number, Boolean, Date, TextList, Table (small), or Document selection
- Cannot create documents

**Docx Template Filling Tool**
- Fill `{{ placeholder }}` variables in a DOCX template
- All placeholder names must match input variable names exactly

**Create PDF Tool**
- Generate a PDF from a markdown template with `{{ placeholder }}` variables

**Docx Diff CSV Tool**
- Compare two DOCX files
- Output CSV has columns: line_number, original_text, updated_text, change_type, change, location

### Excel Agent Tools

**Excel Execution Tool**
- Map input values to Excel cells, execute, read output cells
- Cell references use format: `{"variable": "B2"}`

**Excel Interaction Tool**
- Read/write Excel cells using natural language instructions
- Returns modified Excel file and/or extracted values

### Regrello Agent Tools

**General LLM Tool**
- Single LLM call for reasoning, extraction, classification
- Returns: Text, Number, Boolean, Date, TextList, Table (small), or Document selection
- Cannot create documents

**Data Source SQL Tool**
- Query a datasource with a SELECT statement
- Use `$variable_name` for parameter substitution
- Max 1000 rows

**Data Source Search Tool**
- Search a datasource by column filters, keyword, or semantic search
- Max 100 results
- Semantic search cannot be combined with column filters

**Arithmetic Tool**
- Evaluate expressions like `x * y + z`
- Supports: +, -, *, /, ^ (power)
- Returns: Number

### Flash Agent Tools

**General LLM Tool**
- Single LLM call for reasoning, extraction, classification
- Returns: Text, Number, Boolean, Date, TextList, Table (small), or Document selection
- Cannot create documents

**Context limit**: ~20,000 tokens
- In practical terms:
  - ~30 pages of plain text
  - ~15-page PDF
  - ~200 rows × 10 columns in a CSV

If input exceeds this, it will be silently truncated — the agent won't error, it will just miss data. If input is larger, recommend Tabular Agent (handles up to 1M rows) or split document extraction across multiple tasks.

---

## Data Types & Fields

### Field Type Capabilities

| Field Type | Can Read | Can Write | Notes |
|------------|----------|-----------|-------|
| Checkbox | Yes | Yes | Boolean data |
| Currency | Yes | Yes | - |
| Date | Yes | Yes | - |
| Email | Yes | Yes | - |
| Multi-select | Yes | Yes | - |
| Number | Yes | Yes | - |
| Select | Yes | Yes | - |
| Text | Yes | Yes | - |
| Document | Partial | Partial | **Read**: images, PDF, CSV, .xlsx, .docx, .pptx. Cannot read document links. **Write**: Can generate CSV and PDF from scratch, can fill .docx templates. Can pass documents from shared fields to requested fields. |
| People | Yes | Partial | Can only fill in people by email address. Cannot create new users or look up users by name. |
| Phone | Yes | Partial | Phone numbers extracted from documents as-is — no standard formatting applied. |
| Signature | Yes | No | Cannot generate signatures. |
| Data source | Yes | Partial | Each data source must be configured for agent use — contact Regrello to set this up. Agents can select up to 100 rows at a time. |
| Role | Yes | Partial | Can only select users already assigned to that role. Fills by email address, not by name. |

### User-Facing Data Types

**Checkbox**: Represents boolean data

**Text**: Represents textual data
- Minimum length
- Maximum length
- Enable formatting: will be represented as markdown

**Email**: Subset of Text with email validation (no options)

**Phone**: Subset of Text with phone number validation (no options)

**Select**: An enum text value
- Choices: Which text strings are allowed

**Multi Select**: An enum text value, but can check multiple values
- Choices: Which text strings are allowed

**People**: Represents a person in the workspace (agent gets these as emails)
- Allow adding multiple people or teams: choose whether one or more people are allowed

**Number**:
- Decimal places: number between 0 and 8. The number of decimals. 0 means it's an integer
- Separators: enabled or disabled. Whether in UI it looks like "1,234,567" or "1234567". Not used in agents
- Minimum value
- Maximum value

**Currency**:
- Currency symbol: "USD", "EUR", "GBP", "CNY", "JPY"
- Decimal places: default to 2
- Separators
- Minimum value
- Maximum value

**Date**:
- Accepted dates: "All dates", "Only dates in the future, including today", "Only dates in the past, including today"

**Document**: Can take one or more document(s)
- File extensions: The types of files people can upload. Leave empty to accept any file type
- Disallow external link: External links are never handled by agents, so this option doesn't matter

**Signature**: A signature by a user. Cannot be used with agents.

### Internal Data Types

Internally, all fields translate to these types, using constraints to represent extra field options:

| Type | What It Holds | Key Constraints |
|------|---------------|-----------------|
| Text | String | choices (enum, fuzzy-matched), multiple_choice, min/max_characters, validation_type (email/phone/markdown) |
| Number | Decimal | decimal_places (auto-rounds down), min/max_value, currency |
| Boolean | True/False | Accepts "yes/true/1" or "no/false/0" from text |
| Date | Date ("January 15, 2024") | before_or_after_today_inclusive |
| TextList | List of strings | Same as Text constraints, applied per element |
| Table | Tabular data | columns (required columns + types), allow_additional_columns, is_data_source |
| Document | File (PDF, CSV, XLSX, PNG, JPEG, DOCX) | allowed_types (file extensions) |
| DocumentBatch | Multiple documents | - |

**Note on Tables**: Column names are auto-sanitized to snake_case. Tables over ~100 rows should not be passed to Flash Agent or General LLM Tool — use Tabular agent with SQL instead.

**Note on Documents**: Attached documents are parsed as Document variable by the agent, with the name of the variable being the name of the document.

### Datasources

A datasource is a Table variable marked with `is_data_source=true`. The agent does not receive the full data — it queries it on demand using the Data Source SQL Tool or Data Source Search Tool. Results always include a `row_id` column (integer) as the first column.

Use datasources when:
- Data is too large to pass inline
- Task involves lookup/search against an external system

**Input datasources**: Used as tables
**Output datasources**: Must be queried with the Regrello AI Agent

**Important**: Each data source must be configured for agent use by Regrello. If a user's agent can't fill a data source field, check whether it's been configured. Visit the Data Source tab on the Admin page or contact Regrello support.

---

## Writing Task Descriptions

The task description is the prompt. It drives everything the agent does.

**The agent only has access to data provided in the task** — it cannot look across other tasks in the workflow or workspace. All information needed must be provided as shared fields, documents, or written in the description.

### DO

- Name inputs and outputs explicitly: "Read invoice_document and extract vendor_name, invoice_date, and total_amount"
- Describe the expected output format: "The summary_table should have columns: department (text), headcount (integer), avg_salary (2 decimal places)"
- Include business rules: "If total_amount exceeds $10,000, set requires_approval to true"
- For datasources: "Search the customers datasource for records where region matches target_region. Return up to 50 results"
- Refer to fields by name in single quotes, e.g., 'Supplier Name'. Never refer to columns by number (e.g., "Extract the 10th column" will confuse the agent)
- Use the @ field mention feature to insert fields into the description
- For multi-step processes, number each step clearly. Example: "1. Join the 'Order lines' sheet... 2. Calculate tariff_amount... 3. Output CSV with columns..."
- For document extraction, prompts are often not needed. Only add for edge cases. Example: "'Part number' may be labelled 'PN' or 'Item #' in some invoices"
- Make field names easily understandable. 'Supplier Invoice Date' is better than 'sid'

### DON'T

- Be vague: "process the document" — say what to extract or produce
- Leave out output format details — the agent will guess and may guess wrong
- Ask the Flash Agent / LLM to generate a large table or do arithmetic — use the Tabular agent
- Ask the agent to create a document file — use the Document agent
- Refer to columns by number: "Extract column 3" — always use the column name instead
- Use placeholder/fake data in tests (e.g., "ABC Corp", "123 Main St") — the LLM may hallucinate because it can't distinguish fake data from a signal to make things up
- Use conditional logic in the task description (e.g., "Only calculate the tariff if the supplier is outside the US"). Agents cannot handle conditional steps — the plan is linear and breaks when steps are condition-dependent. Move conditional logic to blueprint-level stage conditions instead

### Example Prompts: Good vs. Bad

#### Routing & Triage (Flash Agent)

**Good**:
```
Determine the appropriate priority level based on:
P0 — Critical Failure (device inoperable, no workaround, blocking production)
P1 — High Severity (major impairment, workaround exists)
P2 — Moderate...
P3 — Low...
```

**Bad**: "Prioritize the incoming customer support cases as P0, P1, P2, or P3 based on the importance of the customer need."

**Why bad fails**: No criteria for decisions. Agent will guess inconsistently.

#### Document Data Extraction

**Good**: "Extract all requested fields." (No further prompt needed — agent uses requested field names.)

**Bad**: Listing all fields in the description when they're already configured as requested fields.

**Why bad is worse**: Duplicates config, confuses agent if names don't match exactly.

#### Tabular Data (Tabular Agent)

**Good**:
```
1. Join 'Order lines' with tariff table on 'hs_code'
2. Calculate tariff_amount = quantity × unit_cost × tariff_rate
3. Output CSV with columns: item_sku, quantity, unit_cost, total_item_cost,
   hs_code, tariff_rate, tariff_amount
```

**Bad**: "Calculate tariffs for the CSV using HS code. Output columns 1, 2, 4, 8, 9. Clean column 14."

**Why bad fails**: Columns by number, no join logic, 'clean' is vague.

---

## Testing & Debugging

### Testing Best Practices

1. Create a draft blueprint with agent tasks configured (description, inputs/outputs, agent assigned)
2. Test individual tasks in **Prompt Studio** (test tab). Run each task separately and review the agent's step-by-step execution in the activity pane
3. Run an end-to-end workflow from the draft blueprint. Review each agent task's output before proceeding to the next
4. If a task fails or produces wrong output, **restart it with feedback first** — the restart dialog lets you write instructions to help the agent generate a better plan. Only change the prompt in the blueprint if feedback alone doesn't fix it
5. Test on a variety of input data — different document formats, edge cases, missing fields. For structured tasks (simple calculations), fewer examples suffice. For unstructured tasks (documents, images), test widely
6. Use realistic data. Placeholder data like "Customer ABC" causes hallucination — the LLM can't distinguish fake data from a signal to make things up
7. **Publish the blueprint** to lock all plans. Once published, agents follow frozen plans deterministically

### Common Errors & Fixes

#### "An unexpected issue occurred. Try running the task again and reach out to Regrello Support if the issue persists with identifier {UUID}"

**What happened**: An unhandled exception — a system bug or unexpected edge case

**What to do**: Try re-running. If it fails again, share the identifier with Regrello Support

#### "The AI Agent is waiting for another agent to finish. The AI Agent will attempt to run {n} more time(s) before giving up."

**What happened**: Another instance of this task is already running (lock contention)

**What to do**: Wait. It will retry automatically. Check if the task was triggered more than once

#### "The AI model did not return a response. The AI Agent will attempt to run {n} more time(s) before giving up."

**What happened**: The LLM service timed out or was unreachable

**What to do**: Wait for automatic retry. If persistent, there may be a service outage

#### "The AI Agent took too long to complete this task and was automatically stopped. The AI Agent will attempt to run {n} more time(s) before giving up."

**What happened**: Task exceeded the 20-minute limit

**What the user can change**:
- **Task description**: Simplify — ask the agent to do less in one run
- **Inputs/Outputs**: Reduce input data size or number of outputs
- **Agent assigned**: If Flash Agent is processing large data, assign Tabular agent with SQL instead
- **Split**: Break into multiple tasks if the scope is genuinely too large

#### "The AI Agent was unable to fill out the fields for the task due to a connection issue. Please try running the task again later."

**What happened**: Backend connection error. Transient.

**What to do**: Retry later. No configuration change needed

#### "The user '{email}' is not a member of this workspace. Please invite them before the AI Agent can assign them."

**What happened**: The agent tried to assign a user who isn't in the workspace

**What to do**: Invite the user, then re-run

#### "The AI Agent was unable to fill all required fields. Some values generated by the agent do not fit the required field format."

Includes a breakdown:
```
Field: {field_name} (required/optional)
Value: {generated_value}
Error: {constraint_violation_reason}
```

**What happened**: The agent's output doesn't satisfy the output field constraints

**What the user can change**:
- **Inputs/Outputs**: Fix the constraint — add the generated value to choices if valid, widen min/max_value, adjust decimal_places
- **Task description**: Clarify what values are acceptable, referencing the constraint

#### "The AI Agent failed as it did not have enough information to complete the task. Ensure that all inputs necessary for the task are provided."

**What happened**: Required input data was missing or the documents didn't contain what was needed

**What the user can change**:
- **Inputs/Outputs**: Add missing input variables; verify documents contain the needed information
- **Task description**: Be more specific about where to find the needed information

#### "Agent failed due to incompatible data types between steps."

**What happened**: A type mismatch — one step produced a type the next step couldn't accept

**What the user can change**:
- **Inputs/Outputs**: Check that output types match what the next step expects
- **Task description**: Clarify the expected type at each stage

#### "The AI Agent was unable to complete the task after multiple attempts. The agent could not create a valid plan to complete the task."

**What happened**: The planner exhausted its attempts without generating a valid tool sequence

**What the user can change**:
- **Task description**: Simplify and clarify. Be explicit about what the agent should do step by step
- **Agent assigned**: The assigned agent may lack the tools needed. Check that the right agent is assigned
- **Inputs/Outputs**: Reduce the number of outputs or simplify their types
- **Split**: If the task is genuinely complex, split into simpler focused tasks

#### "The AI Agent did not detect any output fields for this task after multiple attempts. Completing the task without taking action."

**What happened**: No output variables were found on the Action Item

**What the user can change**:
- **Inputs/Outputs**: Add output variables to the Action Item

#### Agent returns nothing, "null", or "N/A" for all fields

**What happened**: Agent was not given the data it needed

**Fix**: Ensure all fields/documents are properly shared. Agent can only see data explicitly passed

#### Agent returns completely random or hallucinated data

**What happened**: No real data provided, or test data uses fake names

**Fix**: Verify fields/docs are shared. Use realistic test data — fake names like "ABC Corp" cause hallucination

#### "Maximum recursion depth reached"

**What happened**: Agent stuck in loop or task exceeds 15 internal steps

**Common causes**:
- Data source not configured
- Vague prompt
- Search term doesn't match data (e.g., "USA" vs "United States of America")
- Task too complex

**Fix**:
- Configure data source (Admin > Data Sources)
- Be more specific in prompt
- Ensure search terms match actual values
- Split if >15 steps needed

#### DOCX template filling fails

**Fix**:
- Assign to Document Agent
- Check template uses `{{ variable_name }}` format (lowercase, underscores)
- Any other format will fail

#### Agent fails to fill Data Source (synced object)

**Fix**:
- Ensure data source is configured for agent use (Admin > Data Sources)
- Agent can only select ~100 rows

#### Agent taking unusually long

**Normal**: 20-90 seconds

**Causes of delay**:
- High demand on underlying models
- Too many concurrent agent tasks

Usually resolves in 1-2 hours

---

## API Reference

### GraphQL API Setup

Regrello provides a GraphQL API for programmatic interaction with blueprints and workflows.

#### Prerequisites

- Active Regrello workspace with Admin or Owner permissions
- Knowledge of HTTP requests, GraphQL APIs, and REST APIs
- Secure storage prepared for Client ID and Client Secret

#### What is a Service Account?

**Service Account**: Regrello Service Accounts are modeled as a special type of user. This means:
- They will receive email if given an email address with an inbox
- Nearly everything you can do with a normal Regrello User can be done with a Service Account

#### Setup Steps

**1. Login and Access Your Workspace**
- Login to the workspace where you want to create the new service account
- Ensure your active browser window is on https://app.regrello.com

**2. Get Your Bearer Token**

Determine your current session's Bearer Token by running this JavaScript snippet in your browser's developer console:

```javascript
"Bearer " + JSON.parse(localStorage.getItem('_auth0_user'))['token']
```

After hitting enter, the console should print your current session's Bearer Token in the form of a JWT. This token will be active for a short period of time and should be treated as a secret.

**3. Access the GraphQL Playground**
- Open https://app.regrello.com/playground in your browser
- Copy your bearer token into the Headers section at the bottom of the screen
- Refresh your browser window
- Documentation should now be accessible through introspection of the GraphQL API Schema

**4. Query Access Roles**

Paste the following GraphQL query into the Query section:

```graphql
query {
  accessRoles(scope: TEAM) {
    id
    name
  }
}
```

**5. Create Service Account**

Use the mutation below, replacing placeholders with your values:

```graphql
mutation {
  createServiceAccount(
    input: {
      name: "Your Service Account Name"
      email: "service-account@yourdomain.com"
      accessRoleId: "<access_role_id_from_previous_query>"
    }
  ) {
    serviceAccount {
      id
      name
      email
    }
    clientId
    clientSecret
  }
}
```

**IMPORTANT**: Save the `clientId` and `clientSecret` securely. They will not be shown again.

#### Using the API

**Authentication**:
Use the Client ID and Client Secret to obtain access tokens for API requests.

**Common Operations**:
- Create workflows
- Upload documents
- Query workflow status
- Update task fields
- Submit tasks programmatically

Refer to the GraphQL Playground documentation for full schema details.

---

## Platform Features & Releases

The platform receives regular updates with new features and improvements. Key release documentation is available covering:

- **April 2025 Release**: Feature updates and enhancements
- **July 2025 Release**: Major feature additions
- **October 2025 Release**: Platform improvements
- **January 2026 Release**: Latest features and capabilities

Consult the release documentation for detailed information on specific features, changes, and migration guides.

---

## Summary: Key Principles

1. **Agents are isolated**: Each Action Item only sees what you explicitly pass to it
2. **Plans are linear**: No loops, no branches, no variable-length inputs
3. **Always freeze plans**: Test and freeze before publishing to production
4. **Use the right agent**: Match agent capabilities to task requirements
5. **Prefer determinism**: Use SQL/Arithmetic over LLM when possible
6. **Test with real data**: Avoid placeholders that cause hallucination
7. **Be explicit**: Clear descriptions, named fields, defined output formats
8. **Data sources must be configured**: Contact Regrello to set up datasource access
9. **Plans can break**: Re-test after any changes to frozen tasks
10. **Context limits matter**: Flash Agent has ~20K token limit, Tabular handles 1M rows

---

**For additional support**: Contact Regrello Support or your Center of Excellence

**API Documentation**: https://app.regrello.com/playground

**Platform Access**: https://app.regrello.com (invite-only)
