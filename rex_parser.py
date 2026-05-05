#!/usr/bin/env python3
"""
Regrello .rex File Parser - Complete Flowchart-Ready Extraction

Features:
- Task-level dependencies and conditional logic
- Data flow graph construction with edge tracing
- Email body parsing with field mentions
- Form field validation rules and constraints
- Dynamic assignment rules and integration configs
- Interactive HTML data flow visualization
- Rich agent prompt rendering with field highlighting
- JSON export (machine-readable)
- Mermaid diagram generation (flowchart-ready)

Usage:
    # Default: human-readable text
    python rex_parser.py <blueprint.rex>

    # JSON export
    python rex_parser.py <blueprint.rex> --format=json

    # Mermaid diagram
    python rex_parser.py <blueprint.rex> --format=mermaid

    # Interactive HTML visualization
    python rex_parser.py <blueprint.rex> --format=html

    # All formats
    python rex_parser.py <blueprint.rex> --format=all -o output_dir/
"""

import json
import zipfile
import sys
import re
import html
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import argparse
import base64


@dataclass
class FieldConstraint:
    """Field validation constraint."""
    rule: str
    args: List[str]


@dataclass
class FieldValidation:
    """Field validation rules."""
    validation_type: Optional[str]
    constraints: List[FieldConstraint]


@dataclass
class FormFieldInfo:
    """Complete form field information."""
    field_id: int
    field_name: str
    field_type: str
    property_type: str
    required: bool
    helper_text: str
    description: str
    display_order: int
    validation: Optional[FieldValidation]
    allowed_values: List[str]
    default_value: Optional[str]
    field_unit: Optional[str]
    spectrum_field_id: Optional[int] = None


@dataclass
class FormSectionInfo:
    """Form section with complete field details."""
    section_name: str
    display_order: int
    fields: List[FormFieldInfo]


@dataclass
class FormStructure:
    """Complete form structure."""
    form_id: str
    form_name: str
    description: str
    sections: List[FormSectionInfo]


@dataclass
class EmailTemplate:
    """Complete email template information."""
    subject: str
    body_html: str
    body_plain_text: str
    field_mentions: List[Dict[str, Any]]
    to_recipients: List[str]
    cc_recipients: List[str]


@dataclass
class FieldFlow:
    """Data flow for a single field."""
    field_id: int
    field_name: str
    field_type: str
    source_task_id: Optional[int]
    source_task_name: Optional[str]
    consumed_by: List[Dict[str, Any]]


@dataclass
class TaskDependency:
    """Task dependency information."""
    task_id: int
    task_name: str


@dataclass
class StageCondition:
    """Complete stage conditional logic."""
    condition_id: int
    field_id: int
    field_name: str
    operator: str
    compare_value: Any
    value_type: str


@dataclass
class StageDependency:
    """Stage dependency."""
    stage_id: int
    stage_name: str


@dataclass
class DynamicAssignmentRule:
    """Dynamic assignment rule."""
    controlling_field: str
    controlling_field_id: int
    source_field: Optional[str]
    assignment_type: str


@dataclass
class AgentInfo:
    """AI agent information."""
    id: int
    name: str
    type: str


@dataclass
class FrozenPlanStep:
    """Frozen plan step."""
    name: str
    description: str
    tool: Optional[str]


@dataclass
class FrozenPlan:
    """Frozen execution plan."""
    plan_name: str
    version: int
    steps: List[FrozenPlanStep]


@dataclass
class TaskInfo:
    """Complete task information."""
    id: int
    name: str
    description: str
    task_type: str
    integration_type: Optional[str]
    display_order: int
    depends_on_tasks: List[TaskDependency]
    agent: Optional[AgentInfo]
    assignees: List[str]
    dynamic_assignment: Optional[DynamicAssignmentRule]
    shared_fields: List[Dict[str, Any]]
    requested_fields: List[Dict[str, Any]]
    documents: List[Dict[str, Any]]
    has_form: bool
    form_structure: Optional[FormStructure]
    due_interval_seconds: Optional[int]
    expiration_setting: Optional[str]
    escalation_paths: List[Dict[str, Any]]
    email_template: Optional[EmailTemplate]
    reject_action: Optional[Dict[str, Any]]
    requires_rejection_comment: bool
    frozen_plan: Optional[FrozenPlan]
    description_field_mentions: List[Dict[str, Any]]
    field_instructions: Optional[List[Dict[str, Any]]] = None
    linked_workflow_id: Optional[int] = None
    linked_workflow_name: Optional[str] = None


@dataclass
class StageInfo:
    """Complete stage information."""
    id: int
    name: str
    description: str
    execution_order: int
    start_on_workflow_start: bool
    start_after_stages: List[StageDependency]
    starting_conditions: List[StageCondition]
    tasks: List[TaskInfo]


@dataclass
class DataFlowEdge:
    """Data flow graph edge."""
    from_task_id: int
    from_task_name: str
    from_field_id: int
    from_field_name: str
    to_task_id: int
    to_task_name: str
    to_field_id: int
    to_field_name: str
    data_type: str


@dataclass
class BlueprintInfo:
    """Complete blueprint information."""
    id: int
    name: str
    description: str
    blueprint_type: str
    version_notes: str
    stages: List[StageInfo]
    workflow_fields: List[Dict[str, Any]]
    data_flow_edges: List[DataFlowEdge]


class RexParserV4:
    """Enhanced parser with complete extraction and multiple export formats."""

    AGENT_TYPE_NAMES = {
        'FLASH': 'Flash Agent',
        'TABLES': 'Tabular Agent',
        'TABULAR': 'Tabular Agent',
        'DOCUMENT': 'Document Agent',
        'EXCEL': 'Excel Agent',
        'GENERIC': 'Regrello Agent',
        'REGRELLO': 'Regrello Agent',
        'DOCUMENT_EXTRACTION': 'Document Extraction Agent',
        'UNKNOWN': 'Unknown Agent'
    }

    TASK_TYPE_NAMES = {
        'DEFAULT': 'Standard Task',
        'APPROVAL': 'Approval Task',
        'AUTOMATION': 'Automation Task'
    }

    EXPIRATION_NAMES = {
        'TEMPLATE_NON_EXPIRING': 'Does not expire',
        'NON_EXPIRING': 'Does not expire',
        'TEMPLATE_EXPIRING': 'Expires based on template',
        'EXPIRING': 'Expires',
    }

    def __init__(self, rex_file_path: str):
        self.rex_file_path = Path(rex_file_path)
        self.data: Optional[Dict[str, Any]] = None
        self.field_registry: Dict[int, Dict[str, Any]] = {}  # field_id -> field info
        self.task_registry: Dict[int, str] = {}  # task_id -> task_name

    def load(self) -> Dict[str, Any]:
        """Load and parse the .rex file."""
        if not self.rex_file_path.exists():
            raise FileNotFoundError(f"File not found: {self.rex_file_path}")

        with zipfile.ZipFile(self.rex_file_path, 'r') as zip_ref:
            if 'blueprint_export.json' not in zip_ref.namelist():
                raise ValueError("blueprint_export.json not found in .rex file")

            with zip_ref.open('blueprint_export.json') as json_file:
                self.data = json.load(json_file)

        return self.data

    def get_blueprint(self) -> Optional[Dict[str, Any]]:
        """Get the first workflow template."""
        if not self.data:
            self.load()
        workflow_templates = self.data.get('workflowTemplates', [])
        return workflow_templates[0] if workflow_templates else None

    def get_all_blueprints(self) -> List[Dict[str, Any]]:
        """Get all workflow templates (including linked child blueprints)."""
        if not self.data:
            self.load()
        return self.data.get('workflowTemplates', [])
    
    def parse_all_blueprints(self) -> List[BlueprintInfo]:
        """Parse all blueprints in the rex file."""
        blueprints_data = self.get_all_blueprints()
        blueprints = []
        
        for bp_data in blueprints_data:
            # Temporarily set as "current" blueprint for parsing
            original_get = self.get_blueprint
            self.get_blueprint = lambda: bp_data
            
            try:
                blueprint = self.parse_blueprint()
                blueprints.append(blueprint)
            finally:
                self.get_blueprint = original_get
        
        return blueprints

    def parse_field_constraint(self, constraint: Dict[str, Any]) -> FieldConstraint:
        """Parse field constraint."""
        spec_constraint = constraint.get('spectrumValueConstraint', {})
        return FieldConstraint(
            rule=spec_constraint.get('valueConstraintRule', 'unknown'),
            args=constraint.get('constraintArgs', [])
        )

    def parse_field_validation(self, spectrum_field_version: Dict[str, Any]) -> Optional[FieldValidation]:
        """Parse field validation rules."""
        if not spectrum_field_version:
            return None

        validation_type = None
        if spectrum_field_version.get('validationType'):
            validation_type = spectrum_field_version['validationType'].get('validationType')

        constraints = []
        if spectrum_field_version.get('fieldConstraints'):
            for fc in spectrum_field_version['fieldConstraints']:
                constraints.append(self.parse_field_constraint(fc))

        if validation_type or constraints:
            return FieldValidation(
                validation_type=validation_type,
                constraints=constraints
            )
        return None

    def parse_form_field(self, form_field: Dict[str, Any]) -> FormFieldInfo:
        """Parse complete form field with validation."""
        spectrum_field = form_field.get('spectrumFieldVersion', {})
        field_info = spectrum_field.get('field', {}) if spectrum_field else {}

        validation = self.parse_field_validation(spectrum_field) if spectrum_field else None

        return FormFieldInfo(
            field_id=form_field.get('id', 0),
            field_name=form_field.get('name', 'Unknown'),
            field_type=form_field.get('fieldType', 'UNKNOWN'),
            property_type=spectrum_field.get('propertyType', {}).get('name', 'Unknown') if spectrum_field else 'Unknown',
            required=form_field.get('isRequired', False),
            helper_text=spectrum_field.get('helperText', '') if spectrum_field else '',
            description=spectrum_field.get('description', '') if spectrum_field else '',
            display_order=form_field.get('displayOrder', 0),
            validation=validation,
            allowed_values=spectrum_field.get('allowedValues', []) if spectrum_field else [],
            default_value=None,
            field_unit=spectrum_field.get('fieldUnit') if spectrum_field else None,
            spectrum_field_id=form_field.get('spectrumFieldId')
        )

    def parse_form_structure(self, form_data: Dict[str, Any]) -> Optional[FormStructure]:
        """Parse complete form structure with all field details."""
        if not form_data:
            return None

        sections = []
        for idx, section in enumerate(form_data.get('sections', [])):
            fields = []
            # Fields can be in columns[].fields[] or directly in section.fields[]
            for column in section.get('columns', []):
                for form_field in column.get('fields', []):
                    fields.append(self.parse_form_field(form_field))
            for form_field in section.get('fields', []):
                fields.append(self.parse_form_field(form_field))
            # Sort by display order
            fields.sort(key=lambda f: f.display_order)

            sections.append(FormSectionInfo(
                section_name=section.get('name', 'Unknown'),
                display_order=idx + 1,
                fields=fields
            ))

        return FormStructure(
            form_id=form_data.get('formVersionUuid', 'unknown'),
            form_name=form_data.get('name', 'Unknown'),
            description=form_data.get('description', ''),
            sections=sections
        )

    def parse_email_body(self, description: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Parse email body HTML and extract field mentions."""
        if not description:
            return '', []

        field_mentions = []

        # Find all field mentions: <span data-field-instance-id="XXX" data-mention-label="YYY">
        pattern = r'<span[^>]*data-field-instance-id="(\d+)"[^>]*data-mention-label="([^"]+)"[^>]*>'

        for match in re.finditer(pattern, description):
            field_mentions.append({
                'field_instance_id': int(match.group(1)),
                'field_label': match.group(2),
                'position': match.start()
            })

        # Convert HTML to plain text (basic)
        plain_text = re.sub(r'<[^>]+>', '', description)
        plain_text = html.unescape(plain_text)

        return plain_text, field_mentions

    def parse_email_template(self, task: Dict[str, Any]) -> Optional[EmailTemplate]:
        """Parse complete email template."""
        if task.get('integrationType') != 'NOTIFICATION_EMAIL':
            return None

        body_html = task.get('description', '')
        body_plain, field_mentions = self.parse_email_body(body_html)

        return EmailTemplate(
            subject=task.get('emailSubject', ''),
            body_html=body_html,
            body_plain_text=body_plain,
            field_mentions=field_mentions,
            to_recipients=[],  # Determined dynamically
            cc_recipients=task.get('cc', [])
        )

    def parse_dynamic_assignment(self, field_instances: List[Dict[str, Any]]) -> Optional[DynamicAssignmentRule]:
        """Parse dynamic assignment rules."""
        if not field_instances:
            return None

        # Get first controlling assignment
        first = field_instances[0]
        field = first.get('field', {})

        # Try to find source field - check V2 paths first (most reliable)
        source_field = None
        if first.get('values'):
            for val in first['values']:
                # Multi-value party V2 path
                src_v2 = val.get('sourceFieldInstanceMultiValuePartyV2')
                if src_v2 and src_v2.get('field'):
                    source_field = src_v2['field'].get('name')
                    break
                # Single-value party V2 path
                src_v2_single = val.get('sourceFieldInstanceValuePartyV2')
                if src_v2_single and src_v2_single.get('field'):
                    source_field = src_v2_single['field'].get('name')
                    break
                # Legacy path
                src_legacy = val.get('sourceFieldInstanceMultiValueParty')
                if src_legacy and src_legacy.get('field'):
                    source_field = src_legacy['field'].get('name')
                    break

        return DynamicAssignmentRule(
            controlling_field=field.get('name', 'Unknown'),
            controlling_field_id=field.get('id', 0),
            source_field=source_field,
            assignment_type=first.get('controlsActionItemOrActionItemTemplateField', 'UNKNOWN')
        )

    def parse_agent(self, ai_agent_instance: Dict[str, Any]) -> Optional[AgentInfo]:
        """Parse AI agent instance."""
        if not ai_agent_instance:
            return None

        agent_config = ai_agent_instance.get('aiAgentConfig', {})
        if not agent_config or not agent_config.get('id'):
            return None

        return AgentInfo(
            id=agent_config.get('id'),
            name=agent_config.get('name', 'Unknown'),
            type=agent_config.get('type', 'UNKNOWN')
        )

    def parse_frozen_plan(self, ai_agent_instance: Dict[str, Any]) -> Optional[FrozenPlan]:
        """Parse frozen AI agent execution plan."""
        if not ai_agent_instance or not ai_agent_instance.get('currentPlan'):
            return None

        plan = ai_agent_instance['currentPlan']
        steps = []

        if plan.get('planSteps'):
            for step in plan['planSteps']:
                if not isinstance(step, dict):
                    continue
                steps.append(FrozenPlanStep(
                    name=step.get('name', 'Unknown'),
                    description=step.get('description', ''),
                    tool=step.get('tool', {}).get('name') if step.get('tool') else None
                ))

        if not steps:
            return None

        return FrozenPlan(
            plan_name=plan.get('planName', 'Unknown'),
            version=plan.get('version', 0),
            steps=steps
        )

    def parse_stage_conditions(self, starting_conditions: Dict[str, Any]) -> List[StageCondition]:
        """Parse complete stage starting conditions."""
        conditions = []

        if not starting_conditions or not starting_conditions.get('conditions'):
            return conditions

        for cond in starting_conditions['conditions']:
            left = cond.get('left', {})
            right = cond.get('right', {})

            # Handle both operator formats
            operator = cond.get('operator') or cond.get('operatorV2', 'EQUALS')

            field = left.get('field', {})
            field_id = field.get('id', 0)
            field_name = field.get('name', 'Unknown')

            # Extract comparison value
            compare_value = None
            value_type = 'unknown'

            # Extract value from a single value dict (shared by both formats)
            def _extract_value(val_dict):
                if not isinstance(val_dict, dict):
                    return None, 'unknown'
                typename = val_dict.get('__typename', '')
                if 'Boolean' in typename:
                    bv = val_dict.get('booleanValue')
                    if bv is not None:
                        return bv, 'boolean'
                if val_dict.get('stringValue') is not None:
                    return val_dict['stringValue'], 'string'
                if val_dict.get('textValue') is not None:
                    return val_dict['textValue'], 'text'
                if val_dict.get('booleanValue') is not None:
                    return val_dict['booleanValue'], 'boolean'
                if val_dict.get('intValue') is not None:
                    return val_dict['intValue'], 'integer'
                if val_dict.get('integerValue') is not None:
                    return val_dict['integerValue'], 'integer'
                if val_dict.get('floatValue') is not None:
                    return val_dict['floatValue'], 'float'
                if val_dict.get('dateValue') is not None:
                    return val_dict['dateValue'], 'date'
                return None, 'unknown'

            # Handle right as array (new format)
            if isinstance(right, list) and right:
                right_item = right[0]
                if isinstance(right_item, dict):
                    values = right_item.get('values', [])
                    if values and isinstance(values, list):
                        compare_value, value_type = _extract_value(values[0])
            # Handle right as dict (old format)
            elif isinstance(right, dict):
                if right.get('textValue'):
                    compare_value = right['textValue']
                    value_type = 'text'
                elif right.get('values') and isinstance(right['values'], list) and right['values']:
                    compare_value, value_type = _extract_value(right['values'][0])

            conditions.append(StageCondition(
                condition_id=cond.get('id'),
                field_id=field_id,
                field_name=field_name,
                operator=operator,
                compare_value=compare_value,
                value_type=value_type
            ))

        return conditions

    def parse_reject_action(self, reject_action: Dict[str, Any]) -> str:
        """Parse reject action into human-readable format."""
        if not reject_action:
            return None

        entity = reject_action.get('entity', {})
        typename = entity.get('__typename', 'Unknown')

        if typename == 'RejectActionEntityReopenActionItem':
            # Rejection reopens/restarts another task
            ref_task = entity.get('actionItemTemplate', {})
            if ref_task:
                task_id = ref_task.get('id')
                # Try to get name from ref_task first, then from registry
                task_name = ref_task.get('name') or self.task_registry.get(task_id, f'Task ID {task_id}')
                return f"Reopen/restart task: {task_name} (ID: {task_id})"
            return "Reopen/restart a task"

        elif typename == 'RejectActionEntityReportException':
            # Rejection reports an exception/problem
            ref_task = entity.get('actionItemTemplate', {})
            if ref_task:
                task_id = ref_task.get('id')
                # Try to get name from ref_task first, then from registry
                task_name = ref_task.get('name') or self.task_registry.get(task_id, f'Task ID {task_id}')
                return f"Report problem in task: {task_name} (ID: {task_id})"
            return "Report exception/problem"

        else:
            # Unknown type, show raw for debugging
            return f"Unknown reject action type: {typename}"

    def parse_task_dependencies(self, task: Dict[str, Any]) -> List[TaskDependency]:
        """Parse task dependencies."""
        dependencies = []

        if task.get('startAfterActionItemTemplate'):
            dep = task['startAfterActionItemTemplate']
            dependencies.append(TaskDependency(
                task_id=dep.get('id'),
                task_name=dep.get('name', 'Unknown')
            ))

        return dependencies

    def parse_field_instance(self, field_instance: Dict[str, Any]) -> Dict[str, Any]:
        """Parse field instance and register in field registry."""
        field = field_instance.get('field', {})
        property_type = field.get('propertyType', {})

        # Extract helper text from spectrumFieldVersion (used as agent instructions)
        sfv = field_instance.get('spectrumFieldVersion', {}) or {}
        helper_text = sfv.get('helperText', '') or ''

        field_id = field.get('id')
        field_info = {
            'id': field_id,
            'name': field.get('name', 'Unknown'),
            'property_type': property_type.get('name', 'Unknown'),
            'is_multi_valued': field.get('isMultiValued', False),
            'input_type': field_instance.get('inputType', 'UNKNOWN'),
            'field_type': field.get('fieldType', 'DEFAULT'),
            'description': field.get('description', ''),
            'helper_text': helper_text,
            'allowed_values': field.get('allowedValues', []),
            'field_unit': field.get('fieldUnit'),
            'field_restriction': field.get('fieldRestriction')
        }

        # Register field
        if field_id:
            self.field_registry[field_id] = field_info

        return field_info

    def parse_task(self, task: Dict[str, Any]) -> TaskInfo:
        """Parse complete task with all details."""
        # Parse agent
        agent = self.parse_agent(task.get('aiAgentInstance'))
        if not agent:
            for assignee in task.get('assignees', []):
                user = assignee.get('user')
                if user and user.get('userType') == 'AI_AGENT_ACCOUNT':
                    ai_agent_type = user.get('aiAgentType', {})
                    agent = AgentInfo(
                        id=user.get('id'),
                        name=user.get('name', 'Unknown'),
                        type=ai_agent_type.get('v4Type', 'UNKNOWN')
                    )
                    break

        # Parse field instances
        field_instances = task.get('fieldInstances', [])
        shared_fields = [
            self.parse_field_instance(fi)
            for fi in field_instances
            if fi.get('inputType') == 'INHERITED'
        ]
        requested_fields = [
            self.parse_field_instance(fi)
            for fi in field_instances
            if fi.get('inputType') in ('REQUESTED', 'OPTIONAL')
        ]

        # Store raw description field mentions for resolution in generate_summary
        description_field_mentions = task.get('descriptionFieldInstanceMentions', [])

        # Parse assignees
        assignees = []
        for assignee in task.get('assignees', []):
            user = assignee.get('user')
            team = assignee.get('team')

            if user:
                user_type = user.get('userType', '')
                name = user.get('name', 'Unknown')
                if user_type == 'AI_AGENT_ACCOUNT':
                    ai_agent_type = user.get('aiAgentType', {})
                    agent_v4_type = ai_agent_type.get('v4Type', 'UNKNOWN')
                    assignees.append(f"AI Agent: {name} ({agent_v4_type})")
                else:
                    assignees.append(f"User: {name}")
            elif team:
                assignees.append(f"Team: {team.get('name', 'Unknown')}")

        # Parse dynamic assignment
        dynamic_assignment = None
        if task.get('fieldInstancesControllingAssignees'):
            dynamic_assignment = self.parse_dynamic_assignment(
                task['fieldInstancesControllingAssignees']
            )

        # Parse task dependencies
        depends_on_tasks = self.parse_task_dependencies(task)

        # Parse form structure
        form_structure = self.parse_form_structure(task.get('exportFormStructure'))

        # Parse email template
        email_template = self.parse_email_template(task)

        # Parse frozen plan
        frozen_plan = self.parse_frozen_plan(task.get('aiAgentInstance'))

        # Parse reject action
        reject_action = self.parse_reject_action(task.get('rejectAction'))

        # Detect linked workflow (spawns child blueprint)
        linked_wf_id = task.get('createsWorkflowFromWorkflowTemplateId')
        linked_wf_name = None
        if linked_wf_id:
            ref = task.get('createsWorkflowFromWorkflowTemplateReference')
            if ref and isinstance(ref, dict):
                linked_wf_name = ref.get('name')

        # Build field instructions for Document Reader Agent tasks
        field_instructions = None
        if agent and agent.type in ('DOCUMENT_READER', 'DOCUMENT_EXTRACTION'):
            field_instructions = []
            for field in requested_fields:
                field_instructions.append({
                    'requested_field': field['name'],
                    'field_type': field['property_type'],
                    'additional_instructions': field.get('helper_text', ''),
                    'multiple_values': field.get('is_multi_valued', False),
                    'allowed_values': field.get('allowed_values', []),
                })

        return TaskInfo(
            id=task.get('id'),
            name=task.get('name', 'Unknown'),
            description=task.get('description', ''),
            task_type=task.get('type', 'DEFAULT'),
            integration_type=task.get('integrationType'),
            display_order=task.get('displayOrder', 0),
            depends_on_tasks=depends_on_tasks,
            agent=agent,
            assignees=assignees,
            dynamic_assignment=dynamic_assignment,
            shared_fields=shared_fields,
            requested_fields=requested_fields,
            documents=task.get('documents', []),
            has_form=task.get('exportFormStructure') is not None,
            form_structure=form_structure,
            due_interval_seconds=task.get('dueOnIntervalSeconds'),
            expiration_setting=task.get('expirationSetting'),
            escalation_paths=task.get('escalationPaths', []),
            email_template=email_template,
            reject_action=reject_action,
            requires_rejection_comment=task.get('requiresRejectionComment', False),
            frozen_plan=frozen_plan,
            description_field_mentions=description_field_mentions,
            field_instructions=field_instructions,
            linked_workflow_id=linked_wf_id,
            linked_workflow_name=linked_wf_name
        )

    def parse_stage(self, stage: Dict[str, Any]) -> StageInfo:
        """Parse complete stage information."""
        tasks = [
            self.parse_task(task)
            for task in stage.get('actionItemTemplates', [])
        ]

        start_after_stages = []
        for dep_stage in (stage.get('startAfterWorkflowStageTemplates') or []):
            start_after_stages.append(StageDependency(
                stage_id=dep_stage.get('id'),
                stage_name=dep_stage.get('name')
            ))

        starting_conditions = self.parse_stage_conditions(stage.get('startingConditions'))

        return StageInfo(
            id=stage.get('id'),
            name=stage.get('name', 'Unknown'),
            description=stage.get('description', ''),
            execution_order=stage.get('executionOrder', 0),
            start_on_workflow_start=stage.get('startOnWorkflowStart', False),
            start_after_stages=start_after_stages,
            starting_conditions=starting_conditions,
            tasks=tasks
        )

    def build_data_flow_graph(self, blueprint_info: BlueprintInfo) -> List[DataFlowEdge]:
        """Build complete data flow graph matching outputs to inputs."""
        edges = []

        # Build stage order map: task_id -> (stage_execution_order, task_index)
        task_order: Dict[int, Tuple[int, int]] = {}
        for stage in blueprint_info.stages:
            for tidx, task in enumerate(stage.tasks):
                task_order[task.id] = (stage.execution_order, tidx)

        # Build field output registry: field_id -> list of (task_id, task_name)
        field_outputs: Dict[int, List[Tuple[int, str]]] = defaultdict(list)

        for stage in blueprint_info.stages:
            for task in stage.tasks:
                for field in task.requested_fields:
                    field_id = field['id']
                    field_outputs[field_id].append((task.id, task.name))

        def _resolve_source(field_id: int, consumer_task_id: int) -> Optional[Tuple[int, str]]:
            """Pick the closest upstream producer for a field relative to the consumer task."""
            producers = field_outputs.get(field_id, [])
            if not producers:
                return None
            if len(producers) == 1:
                return producers[0]
            consumer_order = task_order.get(consumer_task_id, (999, 999))
            # Filter to upstream producers (stage order < consumer, or same stage but earlier task)
            upstream = [(tid, tname) for tid, tname in producers
                        if task_order.get(tid, (999, 999)) < consumer_order]
            if upstream:
                # Pick the latest upstream producer (closest predecessor)
                return max(upstream, key=lambda x: task_order.get(x[0], (0, 0)))
            # No upstream — fall back to first producer
            return producers[0]

        # Match inputs to outputs
        for stage in blueprint_info.stages:
            for task in stage.tasks:
                for input_field in task.shared_fields:
                    field_id = input_field['id']

                    source = _resolve_source(field_id, task.id)
                    if source:
                        from_task_id, from_task_name = source
                        edges.append(DataFlowEdge(
                            from_task_id=from_task_id,
                            from_task_name=from_task_name,
                            from_field_id=field_id,
                            from_field_name=input_field['name'],
                            to_task_id=task.id,
                            to_task_name=task.name,
                            to_field_id=field_id,
                            to_field_name=input_field['name'],
                            data_type=input_field['property_type']
                        ))

        return edges

    def parse_blueprint(self) -> BlueprintInfo:
        """Parse complete blueprint with data flow graph."""
        blueprint = self.get_blueprint()
        if not blueprint:
            raise ValueError("No blueprint found in .rex file")

        # Build task registry first (for reject action lookups)
        for stage in blueprint.get('stageTemplates', []):
            for task in stage.get('actionItemTemplates', []):
                task_id = task.get('id')
                task_name = task.get('name', 'Unknown')
                if task_id:
                    self.task_registry[task_id] = task_name

        stages = [
            self.parse_stage(stage)
            for stage in blueprint.get('stageTemplates', [])
        ]

        workflow_fields = [
            self.parse_field_instance(fi)
            for fi in blueprint.get('fieldInstances', [])
        ]

        blueprint_info = BlueprintInfo(
            id=blueprint.get('id'),
            name=blueprint.get('name', 'Unknown'),
            description=blueprint.get('description', ''),
            blueprint_type=blueprint.get('type', 'UNKNOWN'),
            version_notes=blueprint.get('versionNotes', ''),
            stages=stages,
            workflow_fields=workflow_fields,
            data_flow_edges=[]
        )

        # Build data flow graph
        blueprint_info.data_flow_edges = self.build_data_flow_graph(blueprint_info)

        return blueprint_info

    def export_json(self, blueprint: BlueprintInfo) -> str:
        """Export blueprint as JSON."""
        # Convert to dict and handle dataclasses
        def dataclass_to_dict(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: dataclass_to_dict(v) for k, v in asdict(obj).items()}
            elif isinstance(obj, list):
                return [dataclass_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: dataclass_to_dict(v) for k, v in obj.items()}
            return obj

        blueprint_dict = dataclass_to_dict(blueprint)
        return json.dumps(blueprint_dict, indent=2, ensure_ascii=False)

    def export_mermaid(self, blueprint: BlueprintInfo) -> str:
        """Export blueprint as Mermaid flowchart."""
        lines = []
        lines.append("```mermaid")
        lines.append("graph TB")
        lines.append("    Start([Workflow Start])")

        # Add stages
        stage_nodes = {}
        for stage in blueprint.stages:
            stage_id = f"S{stage.id}"
            stage_nodes[stage.id] = stage_id

            # Stage box
            lines.append(f"    {stage_id}[\"{stage.name}\"]")

            # Add tasks within stage
            for task in stage.tasks:
                task_id = f"T{task.id}"
                agent_info = ""
                if task.agent:
                    agent_type = self.AGENT_TYPE_NAMES.get(task.agent.type, task.agent.type)
                    agent_info = f"<br/>🤖 {agent_type}"

                form_info = ""
                if task.form_structure:
                    field_count = sum(len(s.fields) for s in task.form_structure.sections)
                    form_info = f"<br/>📝 {field_count} fields"

                lines.append(f"    {task_id}[\"{task.name}{agent_info}{form_info}\"]")

                # Connect stage to task
                lines.append(f"    {stage_id} --> {task_id}")

                # Add conditional logic if present
                if task.depends_on_tasks:
                    for dep in task.depends_on_tasks:
                        dep_task_id = f"T{dep.task_id}"
                        lines.append(f"    {dep_task_id} --> {task_id}")

        # Add stage flow
        lines.append("")
        lines.append("    %% Stage Flow")

        for stage in blueprint.stages:
            stage_id = stage_nodes[stage.id]

            if stage.start_on_workflow_start:
                lines.append(f"    Start --> {stage_id}")

            for dep in stage.start_after_stages:
                if dep.stage_id in stage_nodes:
                    dep_id = stage_nodes[dep.stage_id]
                    lines.append(f"    {dep_id} --> {stage_id}")

            # Add conditional diamonds
            if stage.starting_conditions:
                decision_id = f"D{stage.id}"
                lines.append(f"    {decision_id}{{{stage.starting_conditions[0].field_name}?}}")

                for dep in stage.start_after_stages:
                    if dep.stage_id in stage_nodes:
                        dep_id = stage_nodes[dep.stage_id]
                        lines.append(f"    {dep_id} --> {decision_id}")

                cond = stage.starting_conditions[0]
                condition_label = f"{cond.operator} {cond.compare_value}" if cond.compare_value else cond.operator
                lines.append(f"    {decision_id} -->|{condition_label}| {stage_id}")

        # Add data flow edges
        if blueprint.data_flow_edges:
            lines.append("")
            lines.append("    %% Data Flow")
            for edge in blueprint.data_flow_edges[:20]:  # Limit to first 20 to avoid clutter
                from_id = f"T{edge.from_task_id}"
                to_id = f"T{edge.to_task_id}"
                lines.append(f"    {from_id} -.->|{edge.from_field_name}| {to_id}")

        lines.append("```")
        return "\n".join(lines)

    def _clean_text(self, text: str) -> str:
        """Clean HTML entities and tags from text, preserving structure."""
        if not text:
            return ""
        text = html.unescape(text)
        # Extract data-mention-label from span tags -> [FIELD_NAME]
        text = re.sub(
            r'<span[^>]*data-mention-label="([^"]+)"[^>]*>.*?</span>',
            r'[\1]',
            text
        )
        # Convert structural HTML to text equivalents
        text = re.sub(r'<br\s*/?>', '\n', text)
        # Empty paragraphs become single blank line
        text = re.sub(r'<p>\s*</p>', '\n', text)
        text = re.sub(r'</p>', '\n', text)
        text = re.sub(r'<li[^>]*>', '- ', text)
        text = re.sub(r'</li>', '\n', text)
        # Strip remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Collapse 2+ blank lines into one blank line
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Collapse spaces within lines (but not newlines)
        text = re.sub(r'[^\S\n]+', ' ', text)
        text = text.strip()
        return text

    def _wrap_text(self, text: str, indent: int = 4, width: int = 76) -> List[str]:
        """Wrap text to width with given indent."""
        prefix = " " * indent
        lines = []
        words = text.split()
        current_line = []
        for word in words:
            if len(' '.join(current_line + [word])) <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(f"{prefix}{' '.join(current_line)}")
                current_line = [word]
        if current_line:
            lines.append(f"{prefix}{' '.join(current_line)}")
        return lines

    def _format_task_type(self, task: 'TaskInfo') -> str:
        """Get human-readable task type label."""
        if task.linked_workflow_id:
            return 'Linked Workflow'
        elif task.task_type == 'APPROVAL':
            return 'Approval'
        elif task.task_type == 'AUTOMATION' or task.integration_type == 'NOTIFICATION_EMAIL':
            return 'Automation'
        else:
            return 'Standard'

    def _format_output_field(self, field: Dict[str, Any], form_field_map: Dict[int, 'FormFieldInfo'], desc_referenced_ids: set = None) -> str:
        """Format a single output field line with constraints and required marker."""
        fname = field['name']
        ftype = field['property_type']
        fid = field.get('id')
        fid_str = f" [id: {fid}]" if fid else ""
        field_str = f"      - {fname} ({ftype}){fid_str}"
        # Show allowed values as constraints
        if field.get('allowed_values'):
            vals = field['allowed_values']
            choice_strs = []
            for v in vals:
                if isinstance(v, dict):
                    choice_strs.append(v.get('displayStringValue') or v.get('stringValue') or str(v))
                else:
                    choice_strs.append(str(v))
            field_str += f" [choices: {', '.join(choice_strs)}]"
        if field.get('field_unit'):
            unit = field['field_unit']
            if isinstance(unit, dict):
                unit_name = unit.get('name', '')
                unit_symbol = unit.get('symbol', '')
                if unit_symbol:
                    field_str += f" [unit: {unit_name} ({unit_symbol})]"
                else:
                    field_str += f" [unit: {unit_name}]"
            else:
                field_str += f" [unit: {unit}]"
        # Required marker from form
        ff = form_field_map.get(fid)
        if ff and ff.required:
            field_str += " *"
        # Description reference marker
        if desc_referenced_ids and fid in desc_referenced_ids:
            field_str += "  << referenced in description"
        return field_str

    def _format_condition(self, cond: 'StageCondition') -> str:
        """Format a stage condition as human-readable string."""
        op = cond.operator
        # Operators that don't need a value
        if op in ('EMPTY', 'NOT_EMPTY', 'IS_EMPTY', 'IS_NOT_EMPTY'):
            op_display = op.replace('_', ' ')
            return f"{cond.field_name} {op_display}"
        # Format the value
        if cond.compare_value is None:
            return f"{cond.field_name} {op} (value not set)"
        val = cond.compare_value
        if cond.value_type == 'boolean':
            val_str = "Yes" if val else "No"
        elif isinstance(val, str):
            val_str = f'"{val}"'
        else:
            val_str = str(val)
        # Human-readable operator
        op_map = {
            'EQUALS': '=',
            'NOT_EQUALS': '!=',
            'GREATER_THAN': '>',
            'GREATER_THAN_OR_EQUALS': '>=',
            'LESS_THAN': '<',
            'LESS_THAN_OR_EQUALS': '<=',
        }
        op_display = op_map.get(op, op)
        return f"{cond.field_name} {op_display} {val_str}"

    def _format_assignee(self, task: 'TaskInfo') -> str:
        """Format assignee line."""
        if task.linked_workflow_id:
            return 'N/A (linked workflow)'
        elif task.agent:
            agent_type = self.AGENT_TYPE_NAMES.get(task.agent.type, task.agent.type)
            line = f"Agent: {task.agent.name} ({agent_type})"
            human_assignees = [a for a in task.assignees if 'User' in a or 'Team' in a]
            if human_assignees:
                line += f" + {', '.join(human_assignees)}"
            return line
        elif task.dynamic_assignment:
            source = task.dynamic_assignment.source_field or task.dynamic_assignment.controlling_field
            return f"Dynamic (from {source})"
        elif task.assignees:
            return ', '.join(task.assignees)
        elif task.task_type == 'AUTOMATION' or task.integration_type == 'NOTIFICATION_EMAIL':
            return 'N/A (automation)'
        else:
            return 'MISSING'

    def generate_summary(self, blueprint: BlueprintInfo, task_prefix: str = '') -> str:
        """Generate blueprint summary with two-section format: Task Registry + Edge Table.

        task_prefix: optional prefix for task numbers (e.g. 'C1.' for child blueprints)
        """
        lines = []

        # Build lookup maps
        task_id_to_info = {}  # task_id -> (stage, task, task_idx)
        field_output_map_all = defaultdict(list)  # field_id -> list of (task_id, task_name)
        for stage in blueprint.stages:
            for task_idx, task in enumerate(stage.tasks, 1):
                task_id_to_info[task.id] = (stage, task, task_idx)
                for field in task.requested_fields:
                    field_output_map_all[field['id']].append((task.id, task.name))

        # For description mentions and simple lookups, resolve to closest upstream
        # Build a task_order helper
        task_order_map = {}
        for stage in blueprint.stages:
            for tidx, task in enumerate(stage.tasks):
                task_order_map[task.id] = (stage.execution_order, tidx)

        def _resolve_field_source(field_id, consumer_task_id):
            producers = field_output_map_all.get(field_id, [])
            if not producers:
                return None
            if len(producers) == 1:
                return producers[0]
            consumer_order = task_order_map.get(consumer_task_id, (999, 999))
            upstream = [(tid, tname) for tid, tname in producers
                        if task_order_map.get(tid, (0, 0)) < consumer_order]
            if upstream:
                return max(upstream, key=lambda x: task_order_map.get(x[0], (0, 0)))
            return producers[0]

        # Build field registry: field_id -> {name, property_type}
        field_registry = {}
        for wf in blueprint.workflow_fields:
            if wf.get('id'):
                field_registry[wf['id']] = {'name': wf['name'], 'property_type': wf['property_type']}
        for stage in blueprint.stages:
            for task in stage.tasks:
                for f in task.shared_fields + task.requested_fields:
                    if f.get('id') and f['id'] not in field_registry:
                        field_registry[f['id']] = {'name': f['name'], 'property_type': f['property_type']}

        # Resolve description field mentions → add as implicit inputs and edges
        # Also track self-referencing mentions (field is task's own output)
        desc_referenced_outputs = {}  # task_id -> set of field_ids mentioned in own description
        for stage in blueprint.stages:
            for task in stage.tasks:
                if not task.description_field_mentions:
                    continue
                own_output_ids = {f['id'] for f in task.requested_fields if f.get('id')}
                existing_field_ids = {f['id'] for f in task.shared_fields if f.get('id')}
                for mention in task.description_field_mentions:
                    field_id = mention.get('fieldId')
                    if not field_id:
                        continue
                    info = field_registry.get(field_id)
                    if not info:
                        continue
                    # Self-referencing: field is this task's own output
                    if field_id in own_output_ids:
                        desc_referenced_outputs.setdefault(task.id, set()).add(field_id)
                        continue
                    if field_id in existing_field_ids:
                        continue
                    # Add as implicit input
                    task.shared_fields.append({
                        'id': field_id,
                        'name': info['name'],
                        'property_type': info['property_type'],
                        'allowed_values': [],
                        'field_unit': None,
                        '_from_description': True,
                    })
                    existing_field_ids.add(field_id)
                    # Determine source and create edge (never self-loop)
                    source = _resolve_field_source(field_id, task.id)
                    if source:
                        src_task_id, src_task_name = source
                        if src_task_id != task.id:
                            blueprint.data_flow_edges.append(DataFlowEdge(
                                from_task_id=src_task_id,
                                from_task_name=src_task_name,
                                from_field_id=field_id,
                                from_field_name=info['name'],
                                to_task_id=task.id,
                                to_task_name=task.name,
                                to_field_id=field_id,
                                to_field_name=info['name'],
                                data_type=info['property_type']
                            ))

        # Filter out any self-loop edges
        blueprint.data_flow_edges = [e for e in blueprint.data_flow_edges if e.from_task_id != e.to_task_id]

        # Build field source map for input tracking: (to_task_id, field_name) -> source description
        field_sources = {}
        for edge in blueprint.data_flow_edges:
            source_info = task_id_to_info.get(edge.from_task_id)
            if source_info:
                src_stage, src_task, src_idx = source_info
                source_label = f"Task {task_prefix}{src_stage.execution_order}.{src_idx}: {src_task.name}"
            else:
                source_label = f"Task ID {edge.from_task_id}"
            field_sources[(edge.to_task_id, edge.from_field_name)] = source_label

        # ====================================================================
        # BLUEPRINT HEADER
        # ====================================================================
        lines.append("=" * 80)
        lines.append(f"BLUEPRINT: {blueprint.name}")
        lines.append("=" * 80)
        lines.append(f"ID: {blueprint.id}")
        lines.append(f"Type: {blueprint.blueprint_type}")

        if blueprint.description:
            desc = self._clean_text(blueprint.description)
            lines.append(f"Description: {desc}")
        else:
            lines.append("Description: (No description provided)")

        if blueprint.version_notes:
            lines.append(f"Version Notes: {blueprint.version_notes}")

        lines.append("")

        # Statistics
        total_tasks = sum(len(stage.tasks) for stage in blueprint.stages)
        ai_tasks = sum(1 for stage in blueprint.stages for task in stage.tasks if task.agent)
        human_tasks = total_tasks - ai_tasks

        task_type_counts = defaultdict(int)
        for stage in blueprint.stages:
            for task in stage.tasks:
                task_type_counts[self._format_task_type(task)] += 1

        lines.append(f"Stages: {len(blueprint.stages)}  |  Tasks: {total_tasks} (AI: {ai_tasks}, Human: {human_tasks})")
        task_types_str = " | ".join(f"{k}: {v}" for k, v in sorted(task_type_counts.items()))
        lines.append(f"Task Types: {task_types_str}")
        lines.append(f"Data Flow Edges: {len(blueprint.data_flow_edges)}")
        lines.append("")

        # Workflow-level fields - COMPLETE LIST
        if blueprint.workflow_fields:
            lines.append("Workflow-Level Fields:")
            for field in blueprint.workflow_fields:
                field_str = f"  - {field['name']} ({field['property_type']})"
                if field.get('allowed_values'):
                    vals = field['allowed_values']
                    choice_strs = []
                    for v in vals:
                        if isinstance(v, dict):
                            choice_strs.append(v.get('displayStringValue') or v.get('stringValue') or str(v))
                        else:
                            choice_strs.append(str(v))
                    field_str += f" [choices: {', '.join(choice_strs)}]"
                lines.append(field_str)
        else:
            lines.append("Workflow-Level Fields: None")

        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        # ====================================================================
        # SECTION 1: TASK REGISTRY
        # ====================================================================
        lines.append("SECTION 1: TASK REGISTRY")
        lines.append("=" * 80)
        lines.append("")

        seen_conditions = set()  # Track stage conditions to deduplicate

        for stage in blueprint.stages:
            # Stage header
            lines.append("-" * 80)
            lines.append(f"STAGE {stage.execution_order}: {stage.name} (ID: {stage.id})")

            # Stage trigger
            if stage.start_on_workflow_start:
                lines.append("  Trigger: Workflow start")
            elif stage.start_after_stages:
                after_names = [s.stage_name for s in stage.start_after_stages]
                lines.append(f"  Trigger: After {', '.join(after_names)} completes")
            elif stage.execution_order > 1:
                lines.append("  Trigger: After previous stage completes")

            # Stage condition (deduplicated)
            if stage.starting_conditions:
                cond_parts = []
                for cond in stage.starting_conditions:
                    cond_parts.append(self._format_condition(cond))
                cond_str = " AND ".join(cond_parts)
                cond_key = (stage.id, cond_str)
                if cond_key not in seen_conditions:
                    lines.append(f"  Condition: {cond_str}")
                    seen_conditions.add(cond_key)
            else:
                lines.append("  Condition: None (always runs)")

            # Task execution order within stage
            stage_start_tasks = [t for t in stage.tasks if not t.depends_on_tasks]
            dependent_tasks = [t for t in stage.tasks if t.depends_on_tasks]

            if len(stage.tasks) > 1:
                lines.append("  Task Execution Order:")
                if len(stage_start_tasks) == 1:
                    t = stage_start_tasks[0]
                    idx = stage.tasks.index(t) + 1
                    lines.append(f"    [start] Task {task_prefix}{stage.execution_order}.{idx}: {t.name}")
                elif len(stage_start_tasks) > 1:
                    task_refs = [f"{task_prefix}{stage.execution_order}.{stage.tasks.index(t) + 1}" for t in stage_start_tasks]
                    lines.append(f"    [parallel] Tasks {', '.join(task_refs)} (all start on stage start)")

                for t in dependent_tasks:
                    idx = stage.tasks.index(t) + 1
                    dep_refs = []
                    for dep in t.depends_on_tasks:
                        dep_info = task_id_to_info.get(dep.task_id)
                        if dep_info:
                            ds, dt, di = dep_info
                            dep_refs.append(f"Task {task_prefix}{ds.execution_order}.{di}")
                        else:
                            dep_refs.append(f"Task {dep.task_name}")
                    lines.append(f"    [then] Task {task_prefix}{stage.execution_order}.{idx}: {t.name} (after {', '.join(dep_refs)})")

            lines.append("")

            # Tasks
            for task_idx, task in enumerate(stage.tasks, 1):
                task_num = f"{task_prefix}{stage.execution_order}.{task_idx}"

                lines.append(f"  Task {task_num}: {task.name}")
                lines.append(f"    ID: {task.id}")
                lines.append(f"    Type: {self._format_task_type(task)}")
                if task.linked_workflow_id:
                    lw_name = task.linked_workflow_name or f"Blueprint ID {task.linked_workflow_id}"
                    lines.append(f"    Links to: {lw_name} (ID: {task.linked_workflow_id})")
                if task.integration_type:
                    lines.append(f"    Integration: {task.integration_type}")
                lines.append(f"    Assignee: {self._format_assignee(task)}")

                # Due and expiration
                if task.due_interval_seconds:
                    days = task.due_interval_seconds / 86400
                    if days >= 1:
                        lines.append(f"    Due: {days:.1f} days")
                    else:
                        hours = task.due_interval_seconds / 3600
                        lines.append(f"    Due: {hours:.1f} hours")

                if task.expiration_setting:
                    exp_name = self.EXPIRATION_NAMES.get(task.expiration_setting, task.expiration_setting)
                    lines.append(f"    Expiration: {exp_name}")

                # Dependencies
                if task.depends_on_tasks:
                    dep_strs = []
                    for dep in task.depends_on_tasks:
                        dep_info = task_id_to_info.get(dep.task_id)
                        if dep_info:
                            ds, dt, di = dep_info
                            dep_strs.append(f"Task {task_prefix}{ds.execution_order}.{di}: {dt.name}")
                        else:
                            dep_strs.append(f"{dep.task_name} (ID: {dep.task_id})")
                    lines.append(f"    Depends On: {', '.join(dep_strs)}")
                else:
                    lines.append(f"    Depends On: Stage start")

                lines.append("")

                # Description
                if task.description:
                    desc = self._clean_text(task.description)
                    if desc:
                        lines.append("    Description:")
                        for paragraph in desc.split('\n'):
                            paragraph = paragraph.strip()
                            if paragraph:
                                lines.extend(self._wrap_text(paragraph, indent=6, width=74))
                            else:
                                lines.append("")
                        lines.append("")

                # Frozen plan
                if task.frozen_plan:
                    lines.append(f"    Frozen Plan: {task.frozen_plan.plan_name} (v{task.frozen_plan.version})")
                    lines.append(f"      Steps: {len(task.frozen_plan.steps)}")
                    for i, step in enumerate(task.frozen_plan.steps, 1):
                        tool_info = f" using {step.tool}" if step.tool else ""
                        lines.append(f"        {i}. {step.name}{tool_info}")
                    lines.append("")

                # Documents
                if task.documents:
                    lines.append(f"    Documents: {len(task.documents)}")
                    for doc in task.documents:
                        lines.append(f"      - {doc.get('name', 'Unknown')}")
                    lines.append("")

                # Email template
                if task.email_template:
                    lines.append(f"    Email Subject: {task.email_template.subject}")
                    if task.email_template.field_mentions:
                        mention_names = [m.get('field_label', '?') for m in task.email_template.field_mentions]
                        lines.append(f"    Email Field Mentions: {', '.join(mention_names)}")
                    lines.append("")

                # Inputs with source tracking - ALL fields, no truncation
                all_inputs = task.shared_fields
                if all_inputs:
                    desc_count = sum(1 for f in all_inputs if f.get('_from_description'))
                    label = f"    Inputs: {len(all_inputs)}"
                    if desc_count and desc_count == len(all_inputs):
                        label += " (from description)"
                    elif desc_count:
                        label += f" ({desc_count} from description)"
                    lines.append(label)
                    for field in all_inputs:
                        fname = field['name']
                        ftype = field['property_type']
                        fid = field.get('id')
                        fid_str = f" [id: {fid}]" if fid else ""
                        source_key = (task.id, fname)
                        if source_key in field_sources:
                            source = f" <- {field_sources[source_key]}"
                        elif any(wf['name'] == fname for wf in blueprint.workflow_fields):
                            source = " <- Workflow-level field"
                        else:
                            source = ""
                        lines.append(f"      - {fname} ({ftype}){fid_str}{source}")
                    lines.append("")

                # Outputs with constraints - ALL fields, no truncation
                if task.requested_fields:
                    if task.form_structure:
                        lines.append(f"    Outputs: {len(task.requested_fields)} (via Form: \"{task.form_structure.form_name}\")")
                        # Build map: spectrumFieldId -> FormFieldInfo for required marking
                        form_field_map = {}
                        for sec in task.form_structure.sections:
                            for ff in sec.fields:
                                if ff.spectrum_field_id:
                                    form_field_map[ff.spectrum_field_id] = ff
                        # Build map: spectrumFieldId -> section name
                        field_to_section = {}
                        for sec in task.form_structure.sections:
                            for ff in sec.fields:
                                if ff.spectrum_field_id:
                                    field_to_section[ff.spectrum_field_id] = sec.section_name
                        # Group outputs by form section
                        section_fields = {}
                        unsectioned = []
                        for field in task.requested_fields:
                            fid = field.get('id')
                            sec_name = field_to_section.get(fid)
                            if sec_name:
                                section_fields.setdefault(sec_name, []).append(field)
                            else:
                                unsectioned.append(field)
                        # Output grouped by section in form order
                        task_desc_refs = desc_referenced_outputs.get(task.id, set())
                        for sec in task.form_structure.sections:
                            sec_group = section_fields.get(sec.section_name, [])
                            if sec_group:
                                lines.append(f"      -- {sec.section_name} ({len(sec_group)} fields) --")
                                for field in sec_group:
                                    lines.append(self._format_output_field(field, form_field_map, task_desc_refs))
                        if unsectioned:
                            lines.append(f"      -- Additional Outputs ({len(unsectioned)} fields) --")
                            for field in unsectioned:
                                lines.append(self._format_output_field(field, form_field_map, task_desc_refs))
                    else:
                        task_desc_refs = desc_referenced_outputs.get(task.id, set())
                        lines.append(f"    Outputs: {len(task.requested_fields)}")
                        for field in task.requested_fields:
                            lines.append(self._format_output_field(field, {}, task_desc_refs))
                    lines.append("")

                # Field Instructions for Agent (Document Reader tasks)
                if task.field_instructions:
                    lines.append("    Field Instructions for Agent:")
                    # Column headers
                    lines.append(f"      {'Requested Field':<30} {'Additional Instructions':<40} {'Multiple Values'}")
                    lines.append(f"      {'-'*30} {'-'*40} {'-'*15}")
                    for instr in task.field_instructions:
                        fname = instr['requested_field']
                        add_instr = instr['additional_instructions'] or '-'
                        multi = 'Yes' if instr['multiple_values'] else 'No'
                        lines.append(f"      {fname:<30} {add_instr:<40} {multi}")
                    lines.append("")

                # Approval reject action
                if task.task_type == 'APPROVAL':
                    if task.reject_action:
                        lines.append(f"    If Rejected: {task.reject_action}")
                    if task.requires_rejection_comment:
                        lines.append(f"    Requires rejection comment: Yes")
                    lines.append("")

        lines.append("-" * 80)
        lines.append("")
        lines.append("")

        # ====================================================================
        # SECTION 2: EDGE TABLE + STAGE FLOW
        # ====================================================================
        lines.append("SECTION 2: EDGE TABLE + STAGE FLOW")
        lines.append("=" * 80)
        lines.append("")

        # Part A: Edge Table - ALL edges, no truncation
        lines.append("EDGE TABLE")
        lines.append("-" * 80)

        if blueprint.data_flow_edges:
            def edge_sort_key(e):
                src = task_id_to_info.get(e.from_task_id)
                dst = task_id_to_info.get(e.to_task_id)
                src_order = (src[0].execution_order, src[2]) if src else (999, 999)
                dst_order = (dst[0].execution_order, dst[2]) if dst else (999, 999)
                return (src_order, dst_order)
            sorted_edges = sorted(blueprint.data_flow_edges, key=edge_sort_key)

            seen_edges = {}
            for edge in sorted_edges:
                src_info = task_id_to_info.get(edge.from_task_id)
                dst_info = task_id_to_info.get(edge.to_task_id)
                if src_info:
                    ss, st, si = src_info
                    src_label = f"Task {task_prefix}{ss.execution_order}.{si}: {st.name}"
                else:
                    src_label = f"Task ID {edge.from_task_id}"

                if dst_info:
                    ds, dt, di = dst_info
                    dst_label = f"Task {task_prefix}{ds.execution_order}.{di}: {dt.name}"
                else:
                    dst_label = f"Task ID {edge.to_task_id}"

                key = (src_label, dst_label, edge.from_field_name, edge.data_type)
                if key in seen_edges:
                    seen_edges[key] += 1
                else:
                    seen_edges[key] = 1

            for (src_label, dst_label, field_name, data_type), count in seen_edges.items():
                suffix = f" (x{count})" if count > 1 else ""
                lines.append(f"  {src_label} --[ {field_name} ({data_type}) ]--> {dst_label}{suffix}")

            unique_count = len(seen_edges)
            total_count = len(blueprint.data_flow_edges)
            lines.append("-" * 80)
            if unique_count < total_count:
                lines.append(f"Total Edges: {total_count} ({unique_count} unique)")
            else:
                lines.append(f"Total Edges: {total_count}")
        else:
            lines.append("No data flow edges found.")

        lines.append("")
        lines.append("")

        # Part B: Stage Flow - compact, deduplicated
        lines.append("STAGE FLOW")
        lines.append("-" * 80)

        # Build stage flow map
        stage_flows = defaultdict(list)
        stages_with_explicit_deps = set()
        for stage in blueprint.stages:
            for next_stage in blueprint.stages:
                if any(dep.stage_id == stage.id for dep in next_stage.start_after_stages):
                    stages_with_explicit_deps.add(next_stage.id)
                    if next_stage.starting_conditions:
                        cond_parts = [self._format_condition(c) for c in next_stage.starting_conditions]
                        cond_label = f"IF {' AND '.join(cond_parts)}"
                        stage_flows[stage.id].append((next_stage, cond_label))
                    else:
                        stage_flows[stage.id].append((next_stage, "always"))

        # Add implicit sequential transitions for stages without explicit deps
        sorted_stages = sorted(blueprint.stages, key=lambda s: s.execution_order)
        for i in range(len(sorted_stages) - 1):
            current = sorted_stages[i]
            next_s = sorted_stages[i + 1]
            if next_s.id not in stages_with_explicit_deps and not next_s.start_on_workflow_start:
                stage_flows[current.id].append((next_s, "always"))

        for stage in blueprint.stages:
            label = f"Stage {stage.execution_order}: {stage.name}"
            if stage.starting_conditions:
                label += " [CONDITIONAL]"
            lines.append(label)

            if stage.id in stage_flows:
                for target_stage, condition in stage_flows[stage.id]:
                    if condition == "always":
                        lines.append(f"  -> Stage {target_stage.execution_order}: {target_stage.name}")
                    else:
                        lines.append(f"  -> Stage {target_stage.execution_order}: {target_stage.name} ({condition})")
            lines.append("")

        lines.append("-" * 80)
        lines.append("")

        # ====================================================================
        # SUMMARY
        # ====================================================================
        lines.append("SUMMARY")
        lines.append("=" * 80)

        conditional_count = sum(1 for s in blueprint.stages if s.starting_conditions)
        sequential_count = len(blueprint.stages) - conditional_count

        lines.append(f"Stages: {len(blueprint.stages)} ({sequential_count} sequential, {conditional_count} conditional)")
        lines.append(f"Tasks: {total_tasks} ({task_types_str})")
        lines.append(f"Assignees: AI: {ai_tasks} | Human: {human_tasks}")
        lines.append(f"Data Flow Edges: {len(blueprint.data_flow_edges)}")

        # Agents used
        agent_counts = defaultdict(int)
        for stage in blueprint.stages:
            for task in stage.tasks:
                if task.agent:
                    agent_name = task.agent.name or self.AGENT_TYPE_NAMES.get(task.agent.type, task.agent.type)
                    agent_counts[agent_name] += 1

        if agent_counts:
            lines.append("Agents:")
            for agent, count in sorted(agent_counts.items(), key=lambda x: -x[1]):
                lines.append(f"  - {agent}: {count} tasks")

        # Unique fields
        all_field_names = set()
        for stage in blueprint.stages:
            for task in stage.tasks:
                for f in task.requested_fields:
                    all_field_names.add(f['name'])
                for f in task.shared_fields:
                    all_field_names.add(f['name'])
        lines.append(f"Unique Fields: {len(all_field_names)}")

        # Stage-controlling fields
        controlling_fields = set()
        for stage in blueprint.stages:
            for cond in stage.starting_conditions:
                controlling_fields.add(cond.field_name)
        if controlling_fields:
            lines.append(f"Stage-Controlling Fields: {', '.join(sorted(controlling_fields))}")

        # Fields with constraints
        constrained_count = 0
        for stage in blueprint.stages:
            for task in stage.tasks:
                for f in task.requested_fields:
                    if f.get('allowed_values') or f.get('field_unit'):
                        constrained_count += 1
        lines.append(f"Fields With Constraints: {constrained_count}")

        lines.append("=" * 80)
        return "\n".join(lines)

    # ==================================================================
    # HTML EXPORT
    # ==================================================================

    AGENT_CLASS_MAP = {
        'DOCUMENT_READER': 'doc',
        'DOCUMENT_EXTRACTION': 'doc',
        'DOCUMENT': 'doc',
        'AI_AGENT': 'ai',
        'CODER': 'ai',
        'FLASH': 'flash',
        'EXCEL': 'excel',
        'EXCEL_AUTOMATION': 'excel',
        'TABLES': 'tabular',
        'TABULAR': 'tabular',
        'GENERIC': 'regrello',
        'REGRELLO': 'regrello',
    }

    def _html_agent_class(self, task: TaskInfo) -> str:
        """Map agent type to CSS class for HTML visualization."""
        if not task.agent:
            return 'human'
        return self.AGENT_CLASS_MAP.get(task.agent.type, 'regrello')

    SYSTEM_FIELDS = {'Workflow owner', 'Workflow creator'}

    def _html_agent_label(self, task: TaskInfo) -> str:
        """Get agent display label for HTML visualization."""
        if task.linked_workflow_id:
            return 'Linked Workflow'
        if task.agent:
            return task.agent.name or self.AGENT_TYPE_NAMES.get(task.agent.type, task.agent.type)
        if task.assignees:
            for a in task.assignees:
                if 'User:' in a:
                    name = a.replace('User: ', '')
                    return f"Human (Email: {name})"
                if 'Team:' in a:
                    name = a.replace('Team: ', '')
                    return f"Human (Team: {name})"
            return task.assignees[0]
        if task.dynamic_assignment:
            src = task.dynamic_assignment.source_field or task.dynamic_assignment.controlling_field
            if src in self.SYSTEM_FIELDS:
                return f"Human (System: {src})"
            return f"Human (Role: {src})"
        return 'Human (System: Workflow owner)'

    def _html_human_subtype(self, task: TaskInfo) -> str:
        """Get human assignee subtype for icon differentiation."""
        if task.agent or task.linked_workflow_id:
            return ''
        if task.assignees:
            for a in task.assignees:
                if 'Team:' in a:
                    return 'team'
                if 'User:' in a:
                    return 'email'
        if task.dynamic_assignment:
            src = task.dynamic_assignment.source_field or task.dynamic_assignment.controlling_field
            if src in self.SYSTEM_FIELDS:
                return 'system'
            return 'role'
        return 'system'

    def _js_str(self, s: str) -> str:
        """Escape a string for embedding in JavaScript."""
        if s is None:
            return 'null'
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace("'", "\\'")
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '')
        s = s.replace('\t', '\\t')
        return s

    def _js_backtick_str(self, s: str) -> str:
        """Escape a string for embedding in JS backtick template literal."""
        if s is None:
            return 'null'
        s = s.replace('\\', '\\\\')
        s = s.replace('`', '\\`')
        s = s.replace('${', '\\${')
        return s

    def _clean_prompt_html(self, html_str: str) -> str:
        """Convert raw Regrello HTML description into display-ready HTML for the dashboard.

        Transforms:
        - <span data-mention-label="X"> → <span class="field-mention">[X]</span>
        - {{Line Break}} / {{LineBreak}} → <br>
        - {% if ... %} / {% endif %} → labeled conditional blocks
        - Literal \\n in plain text → <br>
        - Empty <p></p> → removed
        - Structural tags (<p>, <br>, <strong>, <code>, <ul>, <li>) preserved
        """
        import re
        s = html_str

        # Convert Regrello field mentions to styled spans
        s = re.sub(
            r'<span[^>]*data-mention-label="([^"]*)"[^>]*>\s*</span>',
            r'<span class="field-mention">[\1]</span>', s)
        # Also handle spans with inner text content
        s = re.sub(
            r'<span[^>]*data-mention-label="([^"]*)"[^>]*>[^<]*</span>',
            r'<span class="field-mention">[\1]</span>', s)

        # Convert {{Line Break}} and {{LineBreak}} to <br> (case-insensitive)
        s = re.sub(r'\{\{Line\s*Break\}\}', '<br>', s, flags=re.IGNORECASE)

        # Convert {% if X %} to conditional labels
        s = re.sub(r'\{%\s*if\s+(\w+)\s*%\}', r'<div class="prompt-conditional">If \1:</div>', s)
        s = re.sub(r'\{%\s*endif\s*%\}', '', s)

        # Convert literal \n in plain-text descriptions to <br>
        s = s.replace('\\n', '<br>')

        # Decode HTML entities so exports/copies are clean
        import html as html_mod
        s = html_mod.unescape(s)

        # Remove empty <p></p> tags
        s = re.sub(r'<p>\s*</p>', '', s)

        # Clean up excessive <br> sequences (3+ becomes 2)
        s = re.sub(r'(<br\s*/?>){3,}', '<br><br>', s)

        return s.strip()

    def _build_task_id(self, stage: StageInfo, task_idx: int, prefix: str = '') -> str:
        """Build task ID string like '1.1' or 'C1.1.1'."""
        return f"{prefix}{stage.execution_order}.{task_idx}"

    def _build_stage_id(self, stage: StageInfo, prefix: str = '') -> str:
        """Build stage ID for JS. Parent: int (e.g. 1), Child: string (e.g. 'C1.1')."""
        if prefix:
            return f'"{prefix}{stage.execution_order}"'
        return str(stage.execution_order)

    def _build_trigger_text(self, stage: StageInfo) -> str:
        """Build trigger description for a stage."""
        if stage.start_on_workflow_start:
            return "Workflow start"
        if stage.start_after_stages:
            names = [s.stage_name for s in stage.start_after_stages]
            return f"After {', '.join(names)} completes"
        if stage.execution_order > 1:
            return "After previous stage completes"
        return "Workflow start"

    def _build_condition_text(self, stage: StageInfo) -> Optional[str]:
        """Build condition text for a stage."""
        if not stage.starting_conditions:
            return None
        parts = [self._format_condition(c) for c in stage.starting_conditions]
        return " AND ".join(parts)

    def _build_stages_js(self, blueprint: BlueprintInfo, prefix: str = '',
                         source_map: Optional[Dict] = None,
                         child_map: Optional[Dict] = None) -> str:
        """Generate JS stages array for a blueprint."""
        lines = []
        for stage in blueprint.stages:
            trigger = self._build_trigger_text(stage)
            condition = self._build_condition_text(stage)
            sid = self._build_stage_id(stage, prefix)
            cond_js = f'"{self._js_str(condition)}"' if condition else 'null'

            task_strs = []
            for tidx, task in enumerate(stage.tasks, 1):
                task_id = self._build_task_id(stage, tidx, prefix)
                agent_label = self._html_agent_label(task)
                agent_class = self._html_agent_class(task)
                human_subtype = self._html_human_subtype(task)

                # Build inputs from shared_fields
                inputs = []
                for f in task.shared_fields:
                    fid = f.get('id', 0)
                    fname = self._js_str(f['name'])
                    ftype = self._js_str(f['property_type'])
                    # Determine source
                    src = 'Workflow-level'
                    if source_map and (task.id, f['name']) in source_map:
                        src = source_map[(task.id, f['name'])]
                    elif any(wf['name'] == f['name'] for wf in blueprint.workflow_fields):
                        src = 'Workflow-level'
                    inputs.append(f'{{n:"{fname}",t:"{ftype}",src:"{self._js_str(src)}",id:{fid}}}')

                # Build outputs from requested_fields
                outputs = []
                for f in task.requested_fields:
                    fid = f.get('id', 0)
                    fname = self._js_str(f['name'])
                    ftype = self._js_str(f['property_type'])
                    req = 1 if f.get('input_type') == 'REQUESTED' else 0
                    outputs.append(f'{{n:"{fname}",t:"{ftype}",id:{fid},req:{req}}}')

                is_child_link = 'true' if task.linked_workflow_id and child_map and task.linked_workflow_id in child_map else 'false'
                child_idx = -1
                if task.linked_workflow_id and child_map and task.linked_workflow_id in child_map:
                    child_ids = list(child_map.keys())
                    child_idx = child_ids.index(task.linked_workflow_id)

                ht_str = f',ht:"{human_subtype}"' if human_subtype else ''
                cidx_str = f',_childIdx:{child_idx}' if child_idx >= 0 else ''

                # Description (strip HTML tags for plain text, truncate for JS)
                desc_text = task.description or ''
                if desc_text:
                    import re as _re
                    desc_text = _re.sub(r'<[^>]+>', ' ', desc_text).strip()
                    desc_text = ' '.join(desc_text.split())
                desc_js = f',desc:"{self._js_str(desc_text)}"' if desc_text else ''

                # Task type
                ttype = task.task_type or 'DEFAULT'
                ttype_js = f',ttype:"{ttype}"' if ttype != 'DEFAULT' else ''
                itype_js = f',itype:"{task.integration_type}"' if task.integration_type else ''

                # Documents
                doc_names = [self._js_str(d.get('name', '?')) for d in (task.documents or [])]
                docs_js = f',docs:[{",".join(chr(34)+n+chr(34) for n in doc_names)}]' if doc_names else ''

                # Due interval
                due_js = ''
                if task.due_interval_seconds:
                    due_js = f',dueSec:{task.due_interval_seconds}'

                # Dependencies (other tasks this task depends on)
                dep_strs = []
                for dep in (task.depends_on_tasks or []):
                    dep_name = self._js_str(dep.task_name) if dep.task_name else str(dep.task_id)
                    dep_strs.append(f'"{dep_name}"')
                deps_js = f',deps:[{",".join(dep_strs)}]' if dep_strs else ''

                task_str = (
                    f'    {{id:"{task_id}",name:"{self._js_str(task.name)}",'
                    f'agent:"{self._js_str(agent_label)}",agentClass:"{agent_class}"{ht_str},'
                    f'_isChildLink:{is_child_link}{cidx_str}{desc_js}{ttype_js}{itype_js}{docs_js}{due_js}{deps_js},'
                    f'\n     inputs:[{",".join(inputs)}],'
                    f'\n     outputs:[{",".join(outputs)}]}}'
                )
                task_strs.append(task_str)

            tasks_body = ",\n".join(task_strs)
            stage_str = (
                f'  {{id:{sid},name:"{self._js_str(stage.name)}",'
                f'trigger:"{self._js_str(trigger)}",condition:{cond_js},tasks:[\n'
                f'{tasks_body}\n  ]}}'
            )
            lines.append(stage_str)

        return "[\n" + ",\n".join(lines) + "\n]"

    def _build_edges_js(self, blueprint: BlueprintInfo, prefix: str = '') -> str:
        """Generate JS edges array from data flow edges."""
        # Build task lookup: task_id -> (stage, task_idx)
        task_lookup = {}
        for stage in blueprint.stages:
            for tidx, task in enumerate(stage.tasks, 1):
                task_lookup[task.id] = (stage, tidx)

        edge_strs = []
        for edge in blueprint.data_flow_edges:
            src = task_lookup.get(edge.from_task_id)
            dst = task_lookup.get(edge.to_task_id)
            if not src or not dst:
                continue
            from_id = self._build_task_id(src[0], src[1], prefix)
            to_id = self._build_task_id(dst[0], dst[1], prefix)
            data = self._js_str(edge.from_field_name)
            dtype = self._js_str(edge.data_type)
            edge_strs.append(f'  {{from:"{from_id}",to:"{to_id}",data:"{data}",type:"{dtype}"}}')

        return "[\n" + ",\n".join(edge_strs) + "\n]"

    def _build_cross_bp_edges_js(self, blueprints: List['BlueprintInfo'], child_map: dict) -> str:
        """Build cross-blueprint data flow edges (child produces → parent consumes).

        For each field consumed in the parent that's produced in a child,
        pick the LAST producer task in that child (the final output point).
        """
        if not child_map or len(blueprints) < 2:
            return "[]"

        parent = blueprints[0]

        # Build per-blueprint field producers:
        # field_id -> {bp_index: (js_task_id, field_name, type, stage_order, task_idx)}
        # We keep the latest task per blueprint (highest stage order + task idx)
        field_last_producer: Dict[int, Dict[int, Tuple[str, str, str]]] = defaultdict(dict)

        # Parent producers (bp_index=0)
        for stage in parent.stages:
            for tidx, task in enumerate(stage.tasks, 1):
                js_id = self._build_task_id(stage, tidx, '')
                order = (stage.execution_order, tidx)
                for field in task.requested_fields:
                    fid = field.get('id')
                    if not fid:
                        continue
                    existing = field_last_producer[fid].get(0)
                    if not existing or order > existing[3:]:
                        field_last_producer[fid][0] = (js_id, field['name'], field.get('property_type', ''), stage.execution_order, tidx)

        # Child producers
        for ci, (bp_id, child_bp) in enumerate(child_map.items()):
            prefix = f"C{ci+1}."
            bp_idx = ci + 1
            for stage in child_bp.stages:
                for tidx, task in enumerate(stage.tasks, 1):
                    js_id = self._build_task_id(stage, tidx, prefix)
                    order = (stage.execution_order, tidx)
                    for field in task.requested_fields:
                        fid = field.get('id')
                        if not fid:
                            continue
                        existing = field_last_producer[fid].get(bp_idx)
                        if not existing or order > existing[3:]:
                            field_last_producer[fid][bp_idx] = (js_id, field['name'], field.get('property_type', ''), stage.execution_order, tidx)

        # Now find parent consumers whose field was produced in a child
        # For each (field, consumer) pick one edge per child blueprint that produces it
        edge_strs = []
        seen = set()

        for stage in parent.stages:
            for tidx, task in enumerate(stage.tasks, 1):
                consumer_js_id = self._build_task_id(stage, tidx, '')
                for field in task.shared_fields:
                    fid = field.get('id')
                    if not fid:
                        continue
                    producers_by_bp = field_last_producer.get(fid, {})
                    for bp_idx, prod_info in producers_by_bp.items():
                        if bp_idx == 0:
                            continue  # same blueprint — handled by intra-bp edges
                        prod_js_id = prod_info[0]
                        key = (prod_js_id, consumer_js_id, fid)
                        if key in seen:
                            continue
                        seen.add(key)
                        data = self._js_str(field['name'])
                        dtype = self._js_str(field.get('property_type', ''))
                        edge_strs.append(f'  {{from:"{prod_js_id}",to:"{consumer_js_id}",data:"{data}",type:"{dtype}"}}')

        return "[\n" + ",\n".join(edge_strs) + "\n]" if edge_strs else "[]"

    def _build_prompts_js(self, blueprints: List['BlueprintInfo']) -> str:
        """Generate JS taskPrompts object."""
        entries = []
        parent = blueprints[0]

        for stage in parent.stages:
            for tidx, task in enumerate(stage.tasks, 1):
                task_id = self._build_task_id(stage, tidx)
                desc = task.description.strip() if task.description else ''
                if desc:
                    desc = self._clean_prompt_html(desc)
                    entries.append(f'"{task_id}":`{self._js_backtick_str(desc)}`')
                else:
                    entries.append(f'"{task_id}":null')

        for ci, bp in enumerate(blueprints[1:], 1):
            prefix = f"C{ci}."
            for stage in bp.stages:
                for tidx, task in enumerate(stage.tasks, 1):
                    task_id = self._build_task_id(stage, tidx, prefix)
                    desc = task.description.strip() if task.description else ''
                    if desc:
                        desc = self._clean_prompt_html(desc)
                        entries.append(f'"{task_id}":`{self._js_backtick_str(desc)}`')
                    else:
                        entries.append(f'"{task_id}":null')

        return "{\n" + ",\n".join(entries) + "\n}"

    def _build_doc_reader_js(self, blueprints: List['BlueprintInfo']) -> str:
        """Generate JS docReaderConfig object."""
        entries = []
        parent = blueprints[0]

        def process_blueprint(bp, prefix=''):
            for stage in bp.stages:
                for tidx, task in enumerate(stage.tasks, 1):
                    if not task.field_instructions:
                        continue
                    task_id = self._build_task_id(stage, tidx, prefix)
                    form_name = 'null'
                    if task.form_structure:
                        form_name = f'"{self._js_str(task.form_structure.form_name)}"'

                    field_strs = []
                    for instr in task.field_instructions:
                        fname = self._js_str(instr['requested_field'])
                        ftype = self._js_str(instr['field_type'])
                        helper = self._js_str(instr.get('additional_instructions', '') or '')
                        multi = 'true' if instr.get('multiple_values') else 'false'
                        choices = instr.get('allowed_values', [])
                        if choices:
                            choice_strs = []
                            for v in choices:
                                if isinstance(v, dict):
                                    val = v.get('displayStringValue') or v.get('stringValue') or str(v)
                                else:
                                    val = str(v)
                                choice_strs.append(f'"{self._js_str(val)}"')
                            choices_js = f'[{",".join(choice_strs)}]'
                        else:
                            choices_js = 'null'
                        field_strs.append(
                            f'  {{n:"{fname}",t:"{ftype}",helper:"{helper}",multi:{multi},choices:{choices_js}}}'
                        )

                    fields_body = ",\n".join(field_strs)
                    entries.append(
                        f'"{task_id}":{{form:{form_name},fields:[\n{fields_body}\n]}}'
                    )

        process_blueprint(parent)
        for ci, bp in enumerate(blueprints[1:], 1):
            process_blueprint(bp, f"C{ci}.")

        return "{\n" + ",\n".join(entries) + "\n}"

    def _build_flow_js(self, blueprint: BlueprintInfo) -> str:
        """Generate JS stageFlow array from stage dependencies."""
        edges = set()

        # Build explicit stage dependencies
        stages_with_explicit_deps = set()
        for stage in blueprint.stages:
            for next_stage in blueprint.stages:
                if any(dep.stage_id == stage.id for dep in next_stage.start_after_stages):
                    stages_with_explicit_deps.add(next_stage.id)
                    edges.add((stage.execution_order, next_stage.execution_order))

        # Add implicit sequential transitions
        sorted_stages = sorted(blueprint.stages, key=lambda s: s.execution_order)
        for i in range(len(sorted_stages) - 1):
            current = sorted_stages[i]
            next_s = sorted_stages[i + 1]
            if next_s.id not in stages_with_explicit_deps and not next_s.start_on_workflow_start:
                edges.add((current.execution_order, next_s.execution_order))

        sorted_edges = sorted(edges)
        edge_strs = [f'[{e[0]},{e[1]}]' for e in sorted_edges]
        return "[" + ",".join(edge_strs) + "]"

    def _build_child_flow_js(self, blueprint: BlueprintInfo, prefix: str = 'C1.') -> str:
        """Generate JS childFlow array."""
        edges = set()
        stages_with_explicit_deps = set()
        for stage in blueprint.stages:
            for next_stage in blueprint.stages:
                if any(dep.stage_id == stage.id for dep in next_stage.start_after_stages):
                    stages_with_explicit_deps.add(next_stage.id)
                    edges.add((stage.execution_order, next_stage.execution_order))

        sorted_stages = sorted(blueprint.stages, key=lambda s: s.execution_order)
        for i in range(len(sorted_stages) - 1):
            current = sorted_stages[i]
            next_s = sorted_stages[i + 1]
            if next_s.id not in stages_with_explicit_deps and not next_s.start_on_workflow_start:
                edges.add((current.execution_order, next_s.execution_order))

        sorted_edges = sorted(edges)
        edge_strs = [f'["{prefix}{e[0]}","{prefix}{e[1]}"]' for e in sorted_edges]
        return "[" + ",".join(edge_strs) + "]"

    def _build_source_map(self, blueprint: BlueprintInfo, prefix: str = '') -> Dict:
        """Build field source map: (task_id, field_name) -> source description string."""
        # Build task lookup
        task_lookup = {}
        for stage in blueprint.stages:
            for tidx, task in enumerate(stage.tasks, 1):
                task_lookup[task.id] = (stage, tidx)

        source_map = {}
        for edge in blueprint.data_flow_edges:
            src = task_lookup.get(edge.from_task_id)
            if src:
                src_label = f"Task {prefix}{src[0].execution_order}.{src[1]}"
            else:
                src_label = f"Task ID {edge.from_task_id}"
            source_map[(edge.to_task_id, edge.from_field_name)] = src_label

        return source_map

    def export_html(self, blueprints: List[BlueprintInfo]) -> str:
        """Export blueprint visualization as self-contained HTML."""
        # Load template
        template_path = Path(__file__).parent / 'html_template.html'
        if not template_path.exists():
            raise FileNotFoundError(
                f"HTML template not found: {template_path}\n"
                f"The file html_template.html must be in the same directory as the parser."
            )
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        parent = blueprints[0]
        child_map = {bp.id: bp for bp in blueprints[1:]} if len(blueprints) > 1 else {}

        # --- TITLE ---
        title = f"{parent.name} - Data Flow Visualization"

        # --- HEADER HTML ---
        total_stages = sum(len(bp.stages) for bp in blueprints)
        total_tasks = sum(sum(len(s.tasks) for s in bp.stages) for bp in blueprints)
        agent_names = set()
        for bp in blueprints:
            for stage in bp.stages:
                for task in stage.tasks:
                    if task.agent:
                        agent_names.add(task.agent.name or task.agent.type)
        num_agents = len(agent_names)

        logo_path = Path(__file__).parent / 'cloud logo.png'
        if logo_path.exists():
            logo_b64 = base64.b64encode(logo_path.read_bytes()).decode('ascii')
            logo_tag = f'<img class="header-logo" src="data:image/png;base64,{logo_b64}" alt="Logo" height="32">'
        else:
            logo_tag = ''

        theme_switch_svg = '<div class="theme-switch" id="theme-btn" onclick="toggleTheme()" title="Toggle light/dark theme"><span class="ts-icon ts-sun"><svg viewBox="0 0 24 24"><path d="M12 7a5 5 0 100 10 5 5 0 000-10zm0-5a1 1 0 011 1v1a1 1 0 01-2 0V3a1 1 0 011-1zm0 18a1 1 0 011 1v1a1 1 0 01-2 0v-1a1 1 0 011-1zm9-9a1 1 0 010 2h-1a1 1 0 010-2h1zM4 11a1 1 0 010 2H3a1 1 0 010-2h1zm14.36-5.64a1 1 0 010 1.41l-.7.71a1 1 0 01-1.42-1.42l.71-.7a1 1 0 011.41 0zM7.76 16.24a1 1 0 010 1.41l-.7.71a1 1 0 11-1.42-1.42l.71-.7a1 1 0 011.41 0zm10.48 0a1 1 0 011.42 1.42l-.71.7a1 1 0 01-1.41-1.41l.7-.71zM7.76 7.76a1 1 0 01-1.41 0l-.71-.7a1 1 0 011.42-1.42l.7.71a1 1 0 010 1.41z"/></svg></span><span class="ts-icon ts-moon"><svg viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z"/></svg></span></div>'
        header_html = (
            f'  {logo_tag}\n'
            f'  <h1>{html.escape(parent.name)}</h1>\n'
            f'  <div class="theme-switch-cell">{theme_switch_svg}</div>\n'
            f'  <div class="view-toggle">\n'
            f'    <button class="view-btn" data-view="simple" onclick="switchView(\'simple\')">Simple View</button>\n'
            f'    <button class="view-btn active" data-view="detailed" onclick="switchView(\'detailed\')">Detailed View</button>\n'
            f'  </div>'
        )

        # --- GRAPH NOTE ---
        graph_note = f"{len(parent.stages)} stages | Click stage for details"

        # --- DATA SECTION ---
        # Build source maps for input tracking
        parent_source_map = self._build_source_map(parent)

        # Stages
        stages_js = self._build_stages_js(parent, prefix='',
                                           source_map=parent_source_map,
                                           child_map=child_map)

        # Child blueprints — flat array of ALL non-parent blueprints with tree metadata
        # _childIdx on stages indexes into this flat array, so order must match child_map
        child_blueprints_entries = []
        child_ids_list = list(child_map.keys()) if child_map else []
        if child_map:
            for ci, (bp_id, child_bp) in enumerate(child_map.items()):
                prefix = f"C{ci+1}."
                child_source_map = self._build_source_map(child_bp, prefix=prefix)
                c_stages_js = self._build_stages_js(child_bp, prefix=prefix,
                                                     source_map=child_source_map,
                                                     child_map=child_map)
                c_flow_js = self._build_child_flow_js(child_bp, prefix=prefix)
                c_name = self._js_str(child_bp.name)
                # Find which indices this child links to (grandchildren)
                grandchild_idxs = []
                for stage in child_bp.stages:
                    for task in stage.tasks:
                        if task.linked_workflow_id and task.linked_workflow_id in child_map:
                            gc_idx = child_ids_list.index(task.linked_workflow_id)
                            if gc_idx not in grandchild_idxs:
                                grandchild_idxs.append(gc_idx)
                gc_js = "[" + ",".join(str(i) for i in grandchild_idxs) + "]"
                c_edges_js = self._build_edges_js(child_bp, prefix=prefix)
                child_blueprints_entries.append(
                    f'{{id:{bp_id},name:"{c_name}",stages:{c_stages_js},flow:{c_flow_js},childIdxs:{gc_js},edges:{c_edges_js}}}'
                )
        child_blueprints_js = "[" + ",\n".join(child_blueprints_entries) + "]" if child_blueprints_entries else "[]"

        # Edges
        edges_js = self._build_edges_js(parent)
        cross_edges_js = self._build_cross_bp_edges_js(blueprints, child_map)

        # Prompts
        prompts_js = self._build_prompts_js(blueprints)

        # Doc reader config
        doc_reader_js = self._build_doc_reader_js(blueprints)

        # Stage flow
        stage_flow_js = self._build_flow_js(parent)

        data_section = (
            f"const stages = {stages_js};\n\n"
            f"const childBlueprints = {child_blueprints_js};\n\n"
            f"// Derived flat arrays (recursive — includes grandchildren at all depths)\n"
            f"var childStages=[],childFlow=[];\n"
            f"(function flattenCb(list){{list.forEach(function(cb){{cb.stages.forEach(function(s){{childStages.push(s)}});cb.flow.forEach(function(f){{childFlow.push(f)}});var gc=(cb.childIdxs||[]).map(function(i){{return childBlueprints[i]}}).filter(Boolean);if(gc.length)flattenCb(gc)}})}})(childBlueprints);\n\n"
            f"const parentEdges = {edges_js};\n"
            f"const crossBpEdges = {cross_edges_js};\n\n"
            f"// ==============================================================\n"
            f"// TASK PROMPTS & DOCUMENT READER CONFIG\n"
            f"// ==============================================================\n"
            f"const taskPrompts={prompts_js};\n"
            f"const docReaderConfig={doc_reader_js};\n\n"
            f"// ==============================================================\n"
            f"// DERIVED DATA\n"
            f"// ==============================================================\n"
            f"const taskToStage={{}}, taskMap={{}}, adj={{}};\n"
            f"const stageEdgeMap={{}}, aggTaskEdges={{}}, intraStageEdges={{}};\n"
            f"// Theme helpers\n"
            f"function cssVar(name){{return getComputedStyle(document.documentElement).getPropertyValue(name).trim()}}\n"
            f"function getColorMap(){{var c=cssVar('--border');return{{ai:c,doc:c,excel:c,human:c,regrello:c,tabular:c,flash:c}}}}\n"
            f"var colorMap=null;\n"
            f"function cm(agent){{if(!colorMap)colorMap=getColorMap();return colorMap[agent]||cssVar('--accent')}}\n"
            f"function toggleTheme(){{var r=document.documentElement;var cur=r.getAttribute('data-theme');var next=cur==='light'?'dark':'light';r.setAttribute('data-theme',next);colorMap=null;var btn=document.getElementById('theme-btn');if(btn)btn.classList.toggle('dark',next==='dark');if(window._simpleRendered){{window._simpleRendered=false;renderedTabs={{}};renderSimpleView()}}if(renderedTabs.vgraph){{renderedTabs.vgraph=false;if(curTab==='vgraph')renderVisualGraph()}}updateSvgMarkers()}}\n"
            f"function updateSvgMarkers(){{var b=cssVar('--border');var s=document.querySelector('#arr-seq path');if(s)s.setAttribute('fill',b)}}\n"
            f"var agentShort={{ai:'AI',doc:'Doc',excel:'Excel',human:'Human',regrello:'Regrello',tabular:'Tabular',flash:'Flash'}};\n"
            f"const clsMap={{ai:'a-ai',doc:'a-doc',excel:'a-excel',human:'a-human',regrello:'a-regrello',tabular:'a-tabular',flash:'a-flash'}};\n"
            f"function badgeCls(t){{var c=clsMap[t.agentClass]||'';if(t.ht)c+=' ht-'+t.ht;return c}}\n"
            f"const ftClsMap={{Document:'ft-doc',Text:'ft-text',Decimal:'ft-dec',Date:'ft-date',Checkbox:'ft-chk','Sync Object':'ft-sync',Various:'ft-sync'}};\n"
            f"function ftIcon(type){{var c=ftClsMap[type];if(!c)return'';return'<span class=\"ft-icon '+c+'\" title=\"'+type+'\"></span>'}}\n\n"
            f"function computeDerived(){{\n"
            f"  stages.forEach(s=>s.tasks.forEach(t=>{{taskToStage[t.id]=s.id;taskMap[t.id]=t}}));\n"
            f"  childStages.forEach(s=>s.tasks.forEach(t=>{{taskToStage[t.id]=s.id;taskMap[t.id]=t}}));\n"
            f"  parentEdges.forEach(e=>{{\n"
            f"    if(!adj[e.from])adj[e.from]={{up:new Set,dn:new Set,upF:{{}},dnF:{{}}}};\n"
            f"    if(!adj[e.to])adj[e.to]={{up:new Set,dn:new Set,upF:{{}},dnF:{{}}}};\n"
            f"    adj[e.from].dn.add(e.to); adj[e.to].up.add(e.from);\n"
            f"    if(!adj[e.from].dnF[e.to])adj[e.from].dnF[e.to]=[];\n"
            f"    adj[e.from].dnF[e.to].push(e.data);\n"
            f"    if(!adj[e.to].upF[e.from])adj[e.to].upF[e.from]=[];\n"
            f"    adj[e.to].upF[e.from].push(e.data);\n"
            f"    var k=e.from+'->'+e.to;\n"
            f"    if(!aggTaskEdges[k])aggTaskEdges[k]={{from:e.from,to:e.to,fields:[],types:[]}};\n"
            f"    aggTaskEdges[k].fields.push(e.data);aggTaskEdges[k].types.push(e.type);\n"
            f"  }});\n"
            f"  parentEdges.forEach(e=>{{\n"
            f"    var fs=taskToStage[e.from],ts=taskToStage[e.to];\n"
            f"    if(fs!==undefined&&ts!==undefined){{\n"
            f"      if(fs!==ts){{\n"
            f"        var k=fs+'->'+ts;\n"
            f"        if(!stageEdgeMap[k])stageEdgeMap[k]={{from:fs,to:ts,fields:new Set}};\n"
            f"        stageEdgeMap[k].fields.add(e.data);\n"
            f"      }}else{{\n"
            f"        if(!intraStageEdges[fs])intraStageEdges[fs]=new Set;\n"
            f"        intraStageEdges[fs].add(e.data);\n"
            f"      }}\n"
            f"    }}\n"
            f"  }});\n"
            f"}}\n"
            f"computeDerived();\n\n"
            f"// Field index for trace mode\n"
            f"const fieldIndex={{}};\n"
            f"function buildFieldIndex(){{\n"
            f"  function proc(sList,bp){{\n"
            f"    sList.forEach(function(s){{s.tasks.forEach(function(t){{\n"
            f"      t.outputs.forEach(function(o){{\n"
            f"        if(!fieldIndex[o.n])fieldIndex[o.n]={{name:o.n,type:o.t,id:o.id,producers:[],consumers:[]}};\n"
            f"        fieldIndex[o.n].producers.push({{taskId:t.id,stageId:s.id,bp:bp}});\n"
            f"      }});\n"
            f"      t.inputs.forEach(function(i){{\n"
            f"        if(!fieldIndex[i.n])fieldIndex[i.n]={{name:i.n,type:i.t,id:i.id,producers:[],consumers:[]}};\n"
            f"        fieldIndex[i.n].consumers.push({{taskId:t.id,stageId:s.id,bp:bp}});\n"
            f"      }});\n"
            f"    }})}});\n"
            f"  }}\n"
            f"  proc(stages,'parent');\n"
            f"  childBlueprints.forEach(function(cb,ci){{proc(cb.stages,'child-'+(ci+1))}});\n"
            f"}}\n"
            f"buildFieldIndex();\n\n"
            f"// Stage flow structure\n"
            f"const stageFlow={stage_flow_js};\n\n"
        )

        # --- Replace placeholders ---
        result = template.replace('{{TITLE}}', title)
        result = result.replace('{{HEADER_HTML}}', header_html)
        result = result.replace('{{GRAPH_NOTE}}', graph_note)
        result = result.replace('{{DATA_SECTION}}', data_section)

        return result

    def generate_combined_summary(self, blueprints: List[BlueprintInfo]) -> str:
        """Generate combined summary for multiple blueprints (parent + child workflows)."""
        lines = []
        lines.append("=" * 80)
        lines.append("COMBINED BLUEPRINT ANALYSIS")
        lines.append("=" * 80)
        lines.append("")

        bp_by_id = {bp.id: bp for bp in blueprints}

        # Build spawn tree: which blueprint spawns which
        spawns = defaultdict(list)
        for bp in blueprints:
            for stage in bp.stages:
                for task in stage.tasks:
                    if task.linked_workflow_id and task.linked_workflow_id in bp_by_id:
                        if task.linked_workflow_id not in spawns[bp.id]:
                            spawns[bp.id].append(task.linked_workflow_id)

        # Assign prefixes (C1., C2., ...) — flat index for all non-parent blueprints
        bp_prefix = {blueprints[0].id: ''}
        for i, bp in enumerate(blueprints[1:], 1):
            bp_prefix[bp.id] = f'C{i}.'

        # Hierarchy listing
        def _tree_listing(bp_id, depth=0):
            bp = bp_by_id[bp_id]
            indent = "  " * (depth + 1)
            prefix = bp_prefix.get(bp_id, '')
            label = "Parent" if depth == 0 else f"Child ({prefix.rstrip('.')})"
            lines.append(f"{indent}{label}: {bp.name} (ID: {bp.id})")
            for child_id in spawns.get(bp_id, []):
                _tree_listing(child_id, depth + 1)

        lines.append(f"Total Blueprints: {len(blueprints)}")
        _tree_listing(blueprints[0].id)
        lines.append("")

        # Combined metrics
        total_stages = sum(len(bp.stages) for bp in blueprints)
        total_tasks = sum(sum(len(s.tasks) for s in bp.stages) for bp in blueprints)
        total_ai = sum(sum(1 for t in s.tasks if t.agent) for bp in blueprints for s in bp.stages)
        total_edges = sum(len(bp.data_flow_edges) for bp in blueprints)

        lines.append("COMBINED METRICS:")
        lines.append(f"  Stages: {total_stages}")
        lines.append(f"  Tasks: {total_tasks} (AI: {total_ai}, Human: {total_tasks - total_ai})")
        lines.append(f"  Data Flow Edges: {total_edges}")
        lines.append("")

        # Agent distribution
        agent_counter = defaultdict(int)
        for bp in blueprints:
            for stage in bp.stages:
                for task in stage.tasks:
                    if task.agent:
                        name = task.agent.name or task.agent.type
                        agent_counter[name] += 1

        if agent_counter:
            lines.append("AGENT DISTRIBUTION:")
            for agent, count in sorted(agent_counter.items(), key=lambda x: -x[1]):
                lines.append(f"  - {agent}: {count} tasks")
            lines.append("")

        lines.append("=" * 80)
        lines.append("")

        # TOC placeholder — will be replaced with actual line numbers in final pass
        toc_marker = "<<TOC>>"
        lines.append(toc_marker)
        lines.append("")

        # Section markers for TOC (<<SEC:label>> on the same line as section header)
        sec_prefix = "<<SEC:"
        sec_suffix = ">>"

        # Parent blueprint analysis
        parent = blueprints[0]
        lines.append(f"{sec_prefix}Parent: {parent.name}{sec_suffix}--- PARENT: {parent.name} ---")
        lines.append("")
        lines.append(self.generate_summary(parent))
        lines.append("")
        lines.append("")

        # Cross-blueprint data flow section — scan ALL blueprints for linked tasks
        if len(blueprints) > 1:
            all_linked = []
            for bp in blueprints:
                src_prefix = bp_prefix.get(bp.id, '')
                for stage in bp.stages:
                    for tidx, task in enumerate(stage.tasks, 1):
                        if task.linked_workflow_id and task.linked_workflow_id in bp_by_id:
                            child_bp = bp_by_id[task.linked_workflow_id]
                            all_linked.append((bp, src_prefix, stage, task, tidx, child_bp))

            if all_linked:
                lines.append(f"{sec_prefix}Cross-Blueprint Data Flow{sec_suffix}{'=' * 80}")
                lines.append("CROSS-BLUEPRINT DATA FLOW")
                lines.append("=" * 80)
                lines.append("")

                for src_bp, src_prefix, stage, task, tidx, child_bp in all_linked:
                    task_num = f"{src_prefix}{stage.execution_order}.{tidx}"
                    src_label = "Parent" if not src_prefix else f"({src_prefix.rstrip('.')}) {src_bp.name}"
                    child_prefix = bp_prefix.get(child_bp.id, '')
                    child_label = f"({child_prefix.rstrip('.')}) {child_bp.name}" if child_prefix else child_bp.name
                    lines.append(f"{src_label} Task {task_num}: {task.name} (ID: {task.id})")
                    lines.append(f"  -> spawns {child_label} (ID: {child_bp.id})")
                    lines.append("")

                    if task.shared_fields:
                        lines.append(f"  Fields passed to child:")
                        for f in task.shared_fields:
                            fid_str = f" [id: {f.get('id')}]" if f.get('id') else ""
                            lines.append(f"    - {f['name']} ({f['property_type']}){fid_str}")
                        lines.append("")

                    if task.requested_fields:
                        lines.append(f"  Fields returned from child:")
                        for f in task.requested_fields:
                            fid_str = f" [id: {f.get('id')}]" if f.get('id') else ""
                            lines.append(f"    - {f['name']} ({f['property_type']}){fid_str}")
                        lines.append("")

                lines.append("=" * 80)
                lines.append("")
                lines.append("")

        # Child blueprint analyses — walk the spawn tree so hierarchy order is clear
        visited = set()
        def _emit_children(parent_id):
            for child_id in spawns.get(parent_id, []):
                if child_id in visited:
                    continue
                visited.add(child_id)
                bp = bp_by_id[child_id]
                prefix = bp_prefix.get(child_id, '')
                spawner = bp_by_id[parent_id]
                spawner_prefix = bp_prefix.get(parent_id, '')
                spawner_label = f"Parent: {spawner.name}" if not spawner_prefix else f"({spawner_prefix.rstrip('.')}) {spawner.name}"
                toc_label = f"({prefix.rstrip('.')}) {bp.name}"
                lines.append(f"{sec_prefix}{toc_label}{sec_suffix}--- {toc_label} [spawned by {spawner_label}] ---")
                lines.append("")
                lines.append(self.generate_summary(bp, task_prefix=prefix))
                lines.append("")
                lines.append("")
                _emit_children(child_id)

        _emit_children(blueprints[0].id)

        # Emit any remaining children not reachable from the parent spawn tree
        for i, bp in enumerate(blueprints[1:], 1):
            if bp.id not in visited:
                prefix = f"C{i}."
                toc_label = f"({prefix.rstrip('.')}) {bp.name}"
                lines.append(f"{sec_prefix}{toc_label}{sec_suffix}--- {toc_label} ---")
                lines.append("")
                lines.append(self.generate_summary(bp, task_prefix=prefix))
                lines.append("")
                lines.append("")

        # Final pass: build TOC with line numbers and strip markers
        raw_text = "\n".join(lines)
        raw_lines = raw_text.split("\n")
        toc_entries = []
        toc_line_idx = None
        cleaned = []
        for i, line in enumerate(raw_lines):
            if line == toc_marker:
                toc_line_idx = len(cleaned)
                cleaned.append(line)
                continue
            if line.startswith(sec_prefix):
                end = line.index(sec_suffix)
                label = line[len(sec_prefix):end]
                rest = line[end + len(sec_suffix):]
                toc_entries.append((len(cleaned) + 1, label))
                cleaned.append(rest)
            else:
                cleaned.append(line)

        # Build TOC block
        if toc_entries and toc_line_idx is not None:
            # TOC block: header(1) + separator(1) + entries(N) + separator(1) + blank(1)
            toc_block_size = 2 + len(toc_entries) + 2
            # The placeholder occupies 1 line, so net shift is toc_block_size - 1
            shift = toc_block_size - 1
            max_label = max(len(e[1]) for e in toc_entries)
            toc_lines = ["TABLE OF CONTENTS", "-" * 80]
            for line_num, label in toc_entries:
                adjusted = line_num + shift
                dots = "." * max(2, max_label + 8 - len(label))
                toc_lines.append(f"  {label} {dots} line {adjusted}")
            toc_lines.append("-" * 80)
            toc_lines.append("")
            cleaned[toc_line_idx:toc_line_idx + 1] = toc_lines

        return "\n".join(cleaned)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='Regrello .rex File Parser - Complete Flowchart-Ready Extraction'
    )
    parser.add_argument('rex_file', help='Path to .rex file')
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'mermaid', 'html', 'all'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument('-o', '--output', help='Output file or directory')

    args = parser.parse_args()

    try:
        rex_parser = RexParserV4(args.rex_file)
        rex_parser.load()

        # Parse blueprints
        all_blueprints_data = rex_parser.get_all_blueprints()
        if len(all_blueprints_data) > 1:
            blueprints = rex_parser.parse_all_blueprints()
        else:
            blueprint = rex_parser.parse_blueprint()
            blueprints = [blueprint]
        blueprint = blueprints[0]  # Primary blueprint for json/mermaid

        # Determine output base path for auto-naming
        rex_path = Path(args.rex_file)
        output_base = rex_path.stem.replace(' ', '_').lower()

        # --- TEXT ---
        if args.format in ('text', 'all'):
            if len(blueprints) > 1:
                text_output = rex_parser.generate_combined_summary(blueprints)
            else:
                text_output = rex_parser.generate_summary(blueprint)

            if args.output and args.format == 'text':
                with open(args.output, 'w') as f:
                    f.write(text_output)
                print(f"Text output written to: {args.output}")
            elif args.format == 'all':
                output_dir = Path(args.output) if args.output else rex_path.parent
                output_dir.mkdir(exist_ok=True)
                txt_path = output_dir / f'{output_base}_parsed.txt'
                with open(txt_path, 'w') as f:
                    f.write(text_output)
                print(f"Text output written to: {txt_path}")
            else:
                print(text_output)

        # --- HTML ---
        if args.format in ('html', 'all'):
            html_output = rex_parser.export_html(blueprints)

            if args.output and args.format == 'html':
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(html_output)
                print(f"HTML output written to: {args.output}")
            elif args.format == 'all':
                output_dir = Path(args.output) if args.output else rex_path.parent
                output_dir.mkdir(exist_ok=True)
                html_path = output_dir / f'{output_base}_data_flow.html'
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_output)
                print(f"HTML output written to: {html_path}")
            else:
                print(html_output)

        # --- JSON ---
        if args.format in ('json', 'all'):
            json_output = rex_parser.export_json(blueprint)
            if args.output and args.format == 'json':
                with open(args.output, 'w') as f:
                    f.write(json_output)
            elif args.format == 'all':
                output_dir = Path(args.output) if args.output else rex_path.parent
                with open(output_dir / f'{output_base}.json', 'w') as f:
                    f.write(json_output)
            else:
                print(json_output)

        # --- MERMAID ---
        if args.format in ('mermaid', 'all'):
            mermaid_output = rex_parser.export_mermaid(blueprint)
            if args.output and args.format == 'mermaid':
                with open(args.output, 'w') as f:
                    f.write(mermaid_output)
            elif args.format == 'all':
                output_dir = Path(args.output) if args.output else rex_path.parent
                with open(output_dir / f'{output_base}.mmd', 'w') as f:
                    f.write(mermaid_output)
            else:
                print(mermaid_output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
