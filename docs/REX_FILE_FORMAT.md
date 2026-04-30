# Regrello .rex File Format Guide

## Overview

A `.rex` file is a **Regrello blueprint export** - essentially a ZIP archive containing the complete blueprint configuration in JSON format along with associated metadata files.

### File Structure

```
warranty_claims.rex (ZIP archive)
├── blueprint_export.json       # Main blueprint configuration
├── <uuid-1>                    # Metadata files (various UUIDs)
├── <uuid-2>
├── <uuid-3>
└── ...
```

The primary file of interest is `blueprint_export.json`, which contains the complete blueprint definition.

---

## JSON Structure: Top Level

```json
{
  "Version": {
    "Major": 2,
    "Minor": 1
  },
  "workflowTemplates": [...]
}
```

### Key Elements:
- **Version**: Format version of the export
- **workflowTemplates**: Array of blueprint definitions (typically contains 1 blueprint per export)

---

## Workflow Template Structure

Each workflow template represents a complete blueprint:

```json
{
  "id": 315,
  "name": "Warranty Claims",
  "nameTemplate": {
    "stringTemplate": "{{.fieldId10}}",
    "fieldIds": [10]
  },
  "description": "Process description...",
  "versionNotes": "Version notes...",
  "type": "COMPANY",
  "tags": [],
  "isEditingWorkflowApprovalsRestricted": false,
  "isEditingWorkflowsRestricted": false,
  "stageTemplates": [...],
  "fieldInstances": [...],
  "exportFormStructure": {...},
  "workflowOwnerParty": {...},
  "referenceNumberPrefix": "...",
  "referenceNumberStartingValue": 1000,
  "autoAdjustDueOn": false,
  "isCreateViaEmailEnabled": true,
  "createViaEmailContactEmail": "...",
  "createViaEmailConfiguration": {...},
  "collaborations": [...],
  "relations": [...],
  "isVariantCreationEnabled": false,
  "variantData": null
}
```

### Key Fields:
- **id**: Unique blueprint ID
- **name**: Blueprint display name
- **nameTemplate**: Dynamic naming template for workflow instances (uses field references)
- **description**: Blueprint description
- **type**: Blueprint type (COMPANY, PERSONAL, etc.)
- **stageTemplates**: Array of stages (workflow steps)
- **fieldInstances**: Workflow-level shared fields
- **exportFormStructure**: Optional form structure if blueprint has forms

---

## Stage Template Structure

Stages are the workflow phases. Each stage contains action items (tasks).

```json
{
  "id": 1894,
  "name": "Claim Submission",
  "description": "Starts: When the workflow starts",
  "executionOrder": 1,
  "startAt": null,
  "startAfterWorkflowStageTemplates": [],
  "actionItemTemplates": [...]
}
```

### Key Fields:
- **id**: Unique stage ID
- **name**: Stage display name
- **description**: Stage description (often includes trigger conditions)
- **executionOrder**: Numeric order in the blueprint
- **startAt**: Absolute start time (if scheduled)
- **startAfterWorkflowStageTemplates**: Array of stage IDs that must complete before this stage starts
- **actionItemTemplates**: Array of tasks/action items in this stage

### Stage Conditions

Stage start conditions are typically described in the `description` field:
- "Starts: When the workflow starts"
- "Starts: After the previous stage"
- "Starts after stages: X, Y; AND if Field EQUALS 'Value'"
- "Starts after stages: X; AND if Field CONTAINS_ANY_OF 'A, B, C'"

**Note**: Conditional logic is often embedded in the description text rather than structured fields.

---

## Action Item Template (Task) Structure

Action items are the individual tasks within stages.

```json
{
  "uuid": "abc-123-...",
  "id": 5678,
  "name": "Complete the initial claim form",
  "description": "<p>Task instructions...</p>",
  "descriptionFieldInstanceMentions": [...],
  "type": "...",
  "tags": [],
  "displayOrder": 1,
  "dueOn": null,
  "dueOnIntervalSeconds": 86400,
  "dueOnIntervalSecondsAfterTrigger": null,
  "startAt": null,
  "startAfterActionItemTemplate": null,
  "fieldInstances": [...],
  "assignees": [...],
  "cc": [...],
  "documents": [...],
  "aiAgentInstance": {...},
  "exportFormStructure": {...},
  "approvalActionItemTemplates": [],
  "rejectAction": null,
  "requiresRejectionComment": false,
  "isLocked": false,
  "integrationType": null,
  "automationRequests": [],
  "integrationAutomationInstance": null,
  "escalationPaths": [],
  "expirationSetting": null,
  "emailSubject": null,
  "fieldInstancesControllingAssignees": [],
  "fieldInstancesControllingCc": [],
  "fieldInstanceControllingDueOn": null,
  "createsWorkflowFromWorkflowTemplateId": null,
  "createsWorkflowFromWorkflowTemplateReference": null
}
```

### Key Fields:

#### Basic Information
- **id** / **uuid**: Unique task identifiers
- **name**: Task display name
- **description**: HTML-formatted task instructions (the prompt for AI agents)
- **descriptionFieldInstanceMentions**: Fields mentioned in description using @ syntax
- **type**: Task type (standard, approval, etc.)
- **displayOrder**: Order within the stage

#### Timing
- **dueOn**: Absolute due date
- **dueOnIntervalSeconds**: Time to complete in seconds (e.g., 86400 = 1 day)
- **startAt**: Absolute start time
- **startAfterActionItemTemplate**: Task dependency (wait for another task)

#### Assignees & Collaboration
- **assignees**: Array of assigned parties (users, teams, AI agents)
- **cc**: Array of CC'd parties
- **fieldInstancesControllingAssignees**: Dynamic assignee assignment based on field values
- **fieldInstancesControllingCc**: Dynamic CC based on field values

#### Fields & Data
- **fieldInstances**: Array of field instances (inputs and outputs for this task)
- **documents**: Array of attached documents/files

#### AI Agent
- **aiAgentInstance**: AI agent configuration if task is assigned to an agent

#### Forms
- **exportFormStructure**: Form structure if task uses a form

#### Approvals
- **approvalActionItemTemplates**: Child approval tasks
- **rejectAction**: What happens when task is rejected
- **requiresRejectionComment**: Whether rejection requires a comment

#### Automation & Integration
- **integrationType**: External integration type
- **automationRequests**: Automation configurations
- **integrationAutomationInstance**: Integration automation details

#### Task Management
- **expirationSetting**: Task expiration behavior
  - `null`: No expiration setting
  - `"TEMPLATE_NON_EXPIRING"`: Task does not expire (most common)
  - Other values possible for time-limited tasks
- **escalationPaths**: Array of escalation rules (when task is overdue)
- **isLocked**: Whether task configuration is locked from changes

---

## Task Types

Tasks can be of different types, each with distinct characteristics:

### Default Task (Standard)
```json
{
  "type": "DEFAULT",
  "assignees": [...],
  "aiAgentInstance": {...}
}
```
- Regular tasks assigned to humans, AI agents, or both
- Most common task type (DEFAULT, not "STANDARD")
- Can have any combination of assignees

### Approval Task
```json
{
  "type": "APPROVAL",
  "rejectAction": {
    "id": 1710,
    "entity": {
      "__typename": "RejectActionEntityReopenActionItem",
      "actionItemTemplate": {
        "id": 15313,
        "name": "Complete the Diverse Supplier Survey"
      }
    }
  },
  "requiresRejectionComment": false
}
```
- Has approve/reject actions
- Can be assigned to AI agents (with validation logic) or humans
- **rejectAction** defines what happens on rejection:
  - `RejectActionEntityReopenActionItem`: Reopens a previous task
  - Other action types possible
- **requiresRejectionComment**: Whether a comment is required when rejecting

### Automation Task
```json
{
  "type": "AUTOMATION",
  "integrationType": "CUSTOM",
  "integrationAutomationInstance": null,
  "assignees": []
}
```
- System integrations and automations
- **No assignees** (empty array)
- **No AI agents**
- `integrationType` values:
  - **"CUSTOM"**: General automation/integration
  - **"NOTIFICATION_EMAIL"**: Automated email sending
  - Other integration types (ERP, document signing, etc.)
- Examples:
  - Getting current timestamp
  - External API calls
  - Database updates
  - ERP system integrations
  - Sending notification emails

#### Notification Email Tasks
A special type of automation task for sending emails:
```json
{
  "type": "AUTOMATION",
  "integrationType": "NOTIFICATION_EMAIL",
  "assignees": [],
  "description": "Email content with {{placeholders}}"
}
```
- Used for automated notifications
- Email content typically in description field
- Recipients controlled by fields or workflow configuration
- Common use cases: approval notifications, status updates, reminders

### Task Type Summary

| Type | Has Assignees | Can Have AI Agents | Purpose |
|------|---------------|-------------------|---------|
| DEFAULT | Yes | Yes | Regular work tasks (standard type) |
| APPROVAL | Yes | Yes | Approval with logic |
| AUTOMATION | No (empty) | No | System integrations |

**Note**: The API uses "DEFAULT" for what the UI calls "Standard" tasks.

---

## Dynamic Assignment

Tasks can have dynamic assignees determined by field values at runtime.

### Field-Controlled Assignment
```json
{
  "assignees": [
    {
      "user": {
        "name": "Flash Agent 004",
        "userType": "AI_AGENT_ACCOUNT"
      }
    }
  ],
  "fieldInstancesControllingAssignees": [
    {
      "values": [{
        "sourceFieldInstanceMultiValuePartyV2": {
          "field": {
            "id": 97,
            "name": "Supplier Contact"
          }
        }
      }]
    }
  ]
}
```

**How it works**:
- **Static assignees**: Listed in `assignees` array
- **Dynamic assignees**: Determined by field values in `fieldInstancesControllingAssignees`
- At runtime, the person/team stored in the specified field gets assigned

**Example**: Survey completion task
- Static: Flash Agent 004 (prefills the form)
- Dynamic: Supplier Contact field value (reviews and submits)

**Assignee Categories (HTML parser)**:
The parser categorizes non-agent assignees into 4 types with distinct labels and icons:

| Category | Detection Logic | Label Example |
|----------|----------------|---------------|
| **Team** | `assignees` array has `team` key | `Human (Team: Quality Team)` |
| **Email** | `assignees` array has `user` key (non-agent) | `Human (Email: john@example.com)` |
| **System** | Dynamic assignment with source field = "Workflow owner" or "Workflow creator" | `Human (System: Workflow owner)` |
| **Role** | Dynamic assignment with any other source field | `Human (Role: Supplier Contact)` |

**System fields**: Only `"Workflow owner"` and `"Workflow creator"` are system fields. All other dynamic assignment source fields are treated as roles/people fields.

**Parser Note**: The parser extracts the actual source field name from `sourceFieldInstanceMultiValuePartyV2.field.name` within `fieldInstancesControllingAssignees`.

---

## Field Instance Structure

Field instances represent the inputs and outputs for tasks and workflows.

```json
{
  "values": [...],
  "field": {
    "id": 389,
    "name": "Email attachments (field)",
    "description": "",
    "isMultiValued": true,
    "fieldType": "DEFAULT",
    "allowedValues": [],
    "propertyType": {
      "id": 4,
      "name": "Document",
      "dataType": "DOCUMENT_ID"
    },
    "fieldUnit": null,
    "fieldRestriction": null,
    "regrelloObject": null
  },
  "formFieldID": null,
  "regrelloObjectPropertyId": null,
  "displayOrder": 0,
  "inputType": "INHERITED",
  "isCopy": true,
  "isMultiValued": false,
  "projection": null,
  "spectrumMetadata": null,
  "spectrumFieldVersion": {...},
  "isSplitter": false,
  "shouldSplitAssignees": null,
  "controllerBehaviorModifier": null,
  "formInstanceID": null,
  "controlsActionItemOrActionItemTemplateField": null
}
```

### Field Types (propertyType.name):
- **Text**: String values
- **Number**: Numeric values
- **Date**: Date values
- **Boolean**: True/false values (Checkbox)
- **Document**: File attachments
- **People**: User references
- **Currency**: Monetary values
- **Select**: Single-choice enum
- **Multi-select**: Multi-choice enum

### Input Types:
- **INHERITED**: Shared field (passed from previous task or workflow-level) — treated as task input
- **REQUESTED**: Required output field (this task must fill it) — shown with red asterisk in HTML dashboard
- **OPTIONAL**: Optional output field — no asterisk, but still displayed as an output
- **HIDDEN**: Hidden from UI but accessible to agents/automations

**Required field detection**: The HTML parser uses `inputType == 'REQUESTED'` to mark fields as required. This is the most reliable indicator across all tasks regardless of form structure. The `isRequired` flag in `exportFormStructure` only works for tasks that have form sections.

### Key Patterns:
- **Shared Fields**: Fields with `inputType: "INHERITED"` - these are inputs to the task
- **Requested Fields**: Fields with `inputType: "REQUESTED"` - these are outputs the task must populate
- **Field Mapping**: Fields have source/sink relationships tracked via:
  - `sourceFieldInstanceValueString`
  - `sourceFieldInstanceMultiValueDocument`
  - `sinksFieldInstanceValueString`
  - etc.

---

## AI Agent Instance Structure

**IMPORTANT**: The `aiAgentInstance` field does NOT contain agent configuration. It contains the frozen execution plan.

### Without a Frozen Plan
```json
{
  "currentPlan": null
}
```

### With a Frozen Plan
```json
{
  "currentPlan": {
    "version": "5",
    "planName": "2025-09-25T16:06:38.629579+00:00_67b04349a3714d8984b2806bb88dce13",
    "numSuccesses": 1368,
    "planSteps": "{...large JSON string with plan details...}",
    "planGenerationTaskParameters": "{...}",
    "planGenerationTaskParametersHash": "...",
    "isValidPlan": true
  }
}
```

### Key Points:
- **currentPlan**: The frozen execution plan (null if not yet frozen)
- **planSteps**: JSON string containing the detailed execution plan
- **numSuccesses**: Number of successful executions using this plan
- **isValidPlan**: Whether the plan is valid

### Agent Configuration Location:
**Agent information is NOT in `aiAgentInstance`**. It's in the `assignees` array:
```python
# WRONG - This doesn't work
agent_config = task['aiAgentInstance']['aiAgentConfig']  # ❌ Does not exist

# CORRECT - Get agent from assignees
for assignee in task['assignees']:
    user = assignee.get('user')
    if user and user.get('userType') == 'AI_AGENT_ACCOUNT':
        agent_name = user['name']
        agent_type = user['aiAgentType']['v4Type']
        # agent_type will be: FLASH, GENERIC, DOCUMENT, TABLES, EXCEL
```

### Plan Structure:
When a plan exists, `planSteps` contains a JSON string with:
- Tool calls sequence
- Variable mappings
- Instructions for each step
- Input/output definitions

Plans are generated on first run and frozen for deterministic execution

---

## Form Structure

Forms can be attached to tasks or workflows:

```json
{
  "name": "Warranty Claim Form",
  "sections": [
    {
      "name": "Customer Details",
      "displayOrder": 1,
      "fieldGroups": [
        {
          "fieldInstance": {...},
          "displayOrder": 1
        }
      ]
    },
    {
      "name": "Purchase Information",
      "displayOrder": 2,
      "fieldGroups": [...]
    }
  ]
}
```

### Structure:
- **name**: Form name
- **sections**: Array of form sections
  - **name**: Section name
  - **displayOrder**: Order of sections
  - **fieldGroups**: Array of fields in this section
    - **fieldInstance**: Reference to field instance
    - **displayOrder**: Order of fields within section

---

## Document Structure

Documents attached to tasks:

```json
{
  "id": 789,
  "name": "Warranty_Resolution_Path_Table.csv",
  "type": "csv",
  "url": "https://...",
  "size": 12345,
  "createdAt": "2025-01-10T..."
}
```

---

## Conditional Logic Patterns

### Stage Conditions
Parsed from stage `description` field:
- **Sequential**: "Starts: After the previous stage"
- **Parallel**: "Starts after stages: Stage A, Stage B"
- **Conditional**: "Starts after stages: X; AND if Field EQUALS 'Value'"
- **Multiple conditions**: "Starts after stages: X, Y; AND if Field1 EQUALS 'A' AND Field2 CONTAINS_ANY_OF 'B, C'"

### Common Operators:
- `EQUALS`: Exact match
- `CONTAINS_ANY_OF`: Field contains any of the specified values
- `CONTAINS_ALL_OF`: Field contains all specified values
- `NOT_EQUALS`: Does not equal
- `IS_EMPTY`: Field is empty
- `IS_NOT_EMPTY`: Field is not empty

### Task Dependencies
- **startAfterActionItemTemplate**: Task waits for specific previous task to complete
- Tasks can also start based on stage triggers

---

## Assignee Structure

**IMPORTANT**: The assignee structure uses `user` and `team` keys, NOT `party`.

### User Assignee (Human)
```json
{
  "id": 123,
  "user": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "userType": "INTERNAL",
    "isMuted": false,
    "accessLevel": "INTERNAL"
  },
  "team": null
}
```

### User Assignee (AI Agent)
```json
{
  "id": 5,
  "user": {
    "id": 5,
    "name": "Flash Agent 004",
    "email": "agent-v4-flash-agent-004@regrello.com",
    "userType": "AI_AGENT_ACCOUNT",
    "isMuted": false,
    "accessLevel": "INTERNAL",
    "aiAgentType": {
      "v4Type": "FLASH"
    }
  },
  "team": null
}
```

### Team Assignee
```json
{
  "id": 456,
  "user": null,
  "team": {
    "id": 789,
    "name": "Quality Team",
    "description": "Quality assurance team"
  }
}
```

### Key Fields:
- **user.userType**: "AI_AGENT_ACCOUNT" indicates an AI agent, "INTERNAL" for human users
- **user.aiAgentType.v4Type**: Agent type code (FLASH, GENERIC, DOCUMENT, TABULAR, EXCEL)
- **team**: Present when assigned to a team instead of an individual

### Agent Type Codes:
- **FLASH** → Flash Agent (single LLM call)
- **GENERIC** → Regrello Agent (general multi-step agent)
- **DOCUMENT** → Document Agent (document generation)
- **TABLES** → Tabular Agent (SQL and arithmetic)
- **EXCEL** → Excel Agent (Excel operations)

**Important API Code Mappings**:
- The v4 API uses **"GENERIC"** for what's displayed as "Regrello Agent" in the UI
- The v4 API uses **"TABLES"** for what's displayed as "Tabular Agent" in the UI

---

## Parsing Strategy

### Step 1: Extract the ZIP
```bash
unzip warranty_claims.rex -d extracted/
```

### Step 2: Load the JSON
```python
import json
with open('extracted/blueprint_export.json', 'r') as f:
    data = json.load(f)
```

### Step 3: Navigate the Structure
```python
# Get the blueprint
blueprint = data['workflowTemplates'][0]

# Iterate through stages
for stage in blueprint['stageTemplates']:
    stage_name = stage['name']
    stage_description = stage['description']

    # Iterate through tasks in stage
    for task in stage['actionItemTemplates']:
        task_name = task['name']
        task_description = task['description']

        # Check if AI agent assigned (check assignees list)
        for assignee in task.get('assignees', []):
            user = assignee.get('user')
            if user and user.get('userType') == 'AI_AGENT_ACCOUNT':
                agent_name = user.get('name')
                agent_type = user.get('aiAgentType', {}).get('v4Type')
                # FLASH, GENERIC, DOCUMENT, TABULAR, EXCEL
                break

        # Note: aiAgentInstance contains frozen plans, not agent info
        # Use aiAgentInstance to check if a plan exists:
        has_frozen_plan = (
            task.get('aiAgentInstance', {}).get('currentPlan') is not None
        )

        # Get shared fields (inputs)
        shared_fields = [
            fi for fi in task['fieldInstances']
            if fi['inputType'] == 'INHERITED'
        ]

        # Get requested fields (outputs)
        requested_fields = [
            fi for fi in task['fieldInstances']
            if fi['inputType'] == 'REQUESTED'
        ]

        # Get attached documents
        documents = task.get('documents', [])

        # Get form structure
        form = task.get('exportFormStructure')
```

---

## Key Insights

### 1. Field Flow
Fields flow through the workflow via source/sink relationships:
- A field output by Task A can be input (INHERITED) to Task B
- This creates a data pipeline through the workflow
- Track via `sourceFieldInstance*` and `sinksFieldInstance*` fields

### 2. Agent Assignment
- Tasks can be assigned to AI agents, humans, or both
- Co-assignment (agent + human) means agent fills fields but human reviews
- Agent type determines available tools and capabilities

### 3. Conditional Branching
- Stages use conditional logic to create branching workflows
- Conditions are text-based in the description field
- Common pattern: "if Field X equals/contains Y, then start this stage"

### 4. Forms vs. Fields
- Forms group fields into sections for UI presentation
- The same field instances appear in both `fieldInstances` array and within forms
- Forms are optional - tasks can have fields without forms

### 5. Determinism via Plans
- AI agents create execution plans on first run
- Plans freeze the sequence of tool calls
- Plans can break if fields/description/agent changes
- Always re-test after modifications

---

## Common Analysis Tasks

### List all stages and tasks
```python
for stage in blueprint['stageTemplates']:
    print(f"Stage: {stage['name']}")
    for task in stage['actionItemTemplates']:
        print(f"  - Task: {task['name']}")
```

### Find all AI-agent-assigned tasks
```python
agent_tasks = []
for stage in blueprint['stageTemplates']:
    for task in stage['actionItemTemplates']:
        if task.get('aiAgentInstance'):
            agent = task['aiAgentInstance']['aiAgentConfig']
            agent_tasks.append({
                'stage': stage['name'],
                'task': task['name'],
                'agent': agent['name'],
                'agent_type': agent['type']
            })
```

### Map field flow through workflow
```python
field_usage = {}
for stage in blueprint['stageTemplates']:
    for task in stage['actionItemTemplates']:
        for fi in task['fieldInstances']:
            field_name = fi['field']['name']
            input_type = fi['inputType']

            if field_name not in field_usage:
                field_usage[field_name] = []

            field_usage[field_name].append({
                'stage': stage['name'],
                'task': task['name'],
                'type': input_type
            })
```

### Extract conditional stage logic
```python
for stage in blueprint['stageTemplates']:
    description = stage['description']
    if 'if' in description.lower():
        print(f"Conditional stage: {stage['name']}")
        print(f"  Condition: {description}")
```

---

## Comparison: .rex vs .docx

### .rex (JSON)
- **Complete**: Contains all configuration details
- **Structured**: Easy to parse programmatically
- **Machine-readable**: Can be processed by code
- **Verbose**: Large files with nested structures
- **Precise**: All IDs, types, relationships preserved

### .docx (Human-readable)
- **Summary**: High-level overview
- **Formatted**: Easy to read for humans
- **Simplified**: Omits internal IDs and low-level details
- **Concise**: More compact representation
- **Descriptive**: Focuses on what matters to users

### Use Cases
- **Use .rex when**: Building tools, analyzing structure, extracting data, reverse engineering
- **Use .docx when**: Documentation, review, sharing with stakeholders, quick reference

---

## Common Pitfalls & Solutions

### Pitfall 1: Looking for Agent Info in `aiAgentInstance`
**Problem**: `aiAgentInstance` does NOT contain `aiAgentConfig`. It only contains frozen plans.

**Solution**: Extract agent information from the `assignees` array:
```python
for assignee in task['assignees']:
    user = assignee.get('user')
    if user and user.get('userType') == 'AI_AGENT_ACCOUNT':
        agent_type = user['aiAgentType']['v4Type']  # FLASH, GENERIC, etc.
```

### Pitfall 2: Using `party` Instead of `user`/`team`
**Problem**: Documentation may show `assignee['party']`, but the actual structure uses `assignee['user']` or `assignee['team']`.

**Solution**: Always check for `user` and `team` keys:
```python
user = assignee.get('user')
team = assignee.get('team')
```

### Pitfall 3: Agent Type Mismatch
**Problem**: The v4 API uses "GENERIC" but the UI shows "Regrello Agent".

**Solution**: Map API codes to friendly names:
```python
AGENT_NAMES = {
    'FLASH': 'Flash Agent',
    'GENERIC': 'Regrello Agent',  # Note: GENERIC, not REGRELLO
    'DOCUMENT': 'Document Agent',
    'TABULAR': 'Tabular Agent',
    'EXCEL': 'Excel Agent'
}
```

### Pitfall 4: Assuming `aiAgentInstance` Exists
**Problem**: Tasks without agents may not have an `aiAgentInstance` field, or it may be empty `{}`.

**Solution**: Always check before accessing:
```python
ai_instance = task.get('aiAgentInstance', {})
if ai_instance and ai_instance.get('currentPlan'):
    # Has frozen plan
```

### Pitfall 5: Ignoring Human Assignees
**Problem**: Focusing only on AI agents and missing human co-assignments.

**Solution**: Check all assignees:
```python
for assignee in task['assignees']:
    user = assignee.get('user')
    if user:
        if user['userType'] == 'AI_AGENT_ACCOUNT':
            # AI agent
        else:
            # Human user
```

---

## Next Steps

To build a comprehensive parser or skill:
1. Create data classes/types for each major structure (Blueprint, Stage, Task, Field, etc.)
2. Build traversal functions to walk the nested structure
3. Implement field flow analysis (track inputs/outputs across tasks)
4. Extract conditional logic from text descriptions
5. Generate human-readable summaries from parsed data
6. Build validation logic to check for common issues (missing fields, broken references, etc.)

---

**End of Guide**
