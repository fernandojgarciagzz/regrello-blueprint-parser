#!/usr/bin/env node
/**
 * Test script: validates that the JS parser produces the same metrics
 * as the Python parser for both Warranty Claims and Chevron .rex files.
 */
const fs = require('fs');
const path = require('path');

// We need JSZip - but let's just use Node's built-in zlib + manual ZIP parsing
// Actually, let's use the approach of extracting the JSON from the ZIP ourselves
const { execSync } = require('child_process');

// Extract JSON from .rex using Python (since we're just testing)
function extractJson(rexPath) {
  const cmd = `python3 -c "import zipfile,sys;z=zipfile.ZipFile('${rexPath}');print(z.read('blueprint_export.json').decode())"`;
  return JSON.parse(execSync(cmd, { maxBuffer: 50 * 1024 * 1024 }).toString());
}

// ---- PORT OF THE JS PARSER (same code as index.html) ----

const AGENT_CLASS_MAP = {
  'DOCUMENT_READER':'doc','DOCUMENT_EXTRACTION':'doc','DOCUMENT':'doc',
  'AI_AGENT':'ai','CODER':'ai','FLASH':'flash',
  'EXCEL':'excel','EXCEL_AUTOMATION':'excel',
  'TABLES':'tabular','TABULAR':'tabular',
  'GENERIC':'regrello','REGRELLO':'regrello'
};
const AGENT_TYPE_NAMES = {
  'FLASH':'Flash Agent','TABLES':'Tabular Agent','TABULAR':'Tabular Agent',
  'DOCUMENT':'Document Agent','EXCEL':'Excel Agent',
  'GENERIC':'Regrello Agent','REGRELLO':'Regrello Agent',
  'DOCUMENT_EXTRACTION':'Document Extraction Agent','UNKNOWN':'Unknown Agent'
};

function parseFieldInstance(fi) {
  const field = fi.field || {};
  const pt = field.propertyType || {};
  const sfv = fi.spectrumFieldVersion || {};
  return {
    id: field.id || 0,
    name: field.name || 'Unknown',
    property_type: pt.name || 'Unknown',
    is_multi_valued: field.isMultiValued || false,
    input_type: fi.inputType || 'UNKNOWN',
    helper_text: sfv.helperText || '',
    allowed_values: field.allowedValues || []
  };
}

function parseAgent(task) {
  const agi = task.aiAgentInstance;
  if (agi) {
    const cfg = agi.aiAgentConfig || {};
    if (cfg.id) return { id: cfg.id, name: cfg.name || 'Unknown', type: cfg.type || 'UNKNOWN' };
  }
  for (const a of (task.assignees || [])) {
    const u = a.user;
    if (u && u.userType === 'AI_AGENT_ACCOUNT') {
      const aat = u.aiAgentType || {};
      return { id: u.id, name: u.name || 'Unknown', type: aat.v4Type || 'UNKNOWN' };
    }
  }
  return null;
}

function agentClass(task, agent) {
  if (!agent) return 'human';
  return AGENT_CLASS_MAP[agent.type] || 'regrello';
}

function agentLabel(task, agent) {
  if (task.createsWorkflowFromWorkflowTemplateId) return 'Linked Workflow';
  if (agent) return agent.name || AGENT_TYPE_NAMES[agent.type] || agent.type;
  for (const a of (task.assignees || [])) {
    if (a.user && a.user.userType !== 'AI_AGENT_ACCOUNT') return 'Human (' + (a.user.name || 'User') + ')';
    if (a.team) return 'Human (' + a.team.name + ')';
  }
  if (task.fieldInstancesControllingAssignees && task.fieldInstancesControllingAssignees.length) return 'Human (Dynamic)';
  return 'Human (Workflow owner)';
}

function parseStageConditions(sc) {
  if (!sc || !sc.conditions) return [];
  return sc.conditions.map(c => {
    const left = c.left || {};
    const right = c.right;
    const field = left.field || {};
    const op = c.operator || c.operatorV2 || 'EQUALS';
    let val = null;
    function extractVal(v) {
      if (!v || typeof v !== 'object') return null;
      if (v.stringValue != null) return v.stringValue;
      if (v.textValue != null) return v.textValue;
      if (v.booleanValue != null) return v.booleanValue;
      if (v.intValue != null) return v.intValue;
      if (v.integerValue != null) return v.integerValue;
      if (v.floatValue != null) return v.floatValue;
      return null;
    }
    if (Array.isArray(right) && right.length) {
      const ri = right[0];
      if (ri && ri.values && ri.values.length) val = extractVal(ri.values[0]);
    } else if (right && typeof right === 'object') {
      if (right.textValue) val = right.textValue;
      else if (right.values && right.values.length) val = extractVal(right.values[0]);
    }
    return { field_name: field.name || 'Unknown', operator: op, compare_value: val };
  });
}

function parseBlueprintData(bpData) {
  const stages = [];
  for (const stageData of (bpData.stageTemplates || [])) {
    const tasks = [];
    for (const taskData of (stageData.actionItemTemplates || [])) {
      const agent = parseAgent(taskData);
      const fieldInstances = taskData.fieldInstances || [];
      const shared = fieldInstances.filter(fi => fi.inputType === 'INHERITED').map(parseFieldInstance);
      const requested = fieldInstances.filter(fi => fi.inputType === 'REQUESTED' || fi.inputType === 'OPTIONAL').map(parseFieldInstance);
      let fieldInstructions = null;
      if (agent && (agent.type === 'DOCUMENT_READER' || agent.type === 'DOCUMENT_EXTRACTION')) {
        fieldInstructions = requested.map(f => ({
          requested_field: f.name, field_type: f.property_type,
          additional_instructions: f.helper_text || '',
          multiple_values: f.is_multi_valued || false,
          allowed_values: f.allowed_values || []
        }));
      }
      tasks.push({
        id: taskData.id, name: taskData.name || 'Unknown',
        description: taskData.description || '',
        task_type: taskData.type || 'DEFAULT',
        display_order: taskData.displayOrder || 0,
        agent, agentClass: agentClass(taskData, agent), agentLabel: agentLabel(taskData, agent),
        shared_fields: shared, requested_fields: requested,
        linked_workflow_id: taskData.createsWorkflowFromWorkflowTemplateId || null,
        field_instructions: fieldInstructions,
        form_structure: taskData.exportFormStructure ? { form_name: taskData.exportFormStructure.name || 'Unknown' } : null
      });
    }
    const startAfter = (stageData.startAfterWorkflowStageTemplates || []).map(s => ({ stage_id: s.id, stage_name: s.name }));
    const conditions = parseStageConditions(stageData.startingConditions);
    stages.push({
      id: stageData.id, name: stageData.name || 'Unknown',
      execution_order: stageData.executionOrder || 0,
      start_on_workflow_start: stageData.startOnWorkflowStart || false,
      start_after_stages: startAfter, starting_conditions: conditions, tasks
    });
  }
  const wfFields = (bpData.fieldInstances || []).map(parseFieldInstance);
  return { id: bpData.id, name: bpData.name || 'Unknown', stages, workflow_fields: wfFields };
}

function buildDataFlowEdges(bp) {
  const edges = [];
  const taskOrder = {};
  for (const stage of bp.stages) {
    for (let tidx = 0; tidx < stage.tasks.length; tidx++) {
      taskOrder[stage.tasks[tidx].id] = [stage.execution_order, tidx];
    }
  }
  const fieldOutputs = {};
  for (const stage of bp.stages) {
    for (const task of stage.tasks) {
      for (const f of task.requested_fields) {
        if (!fieldOutputs[f.id]) fieldOutputs[f.id] = [];
        fieldOutputs[f.id].push({ task_id: task.id, task_name: task.name });
      }
    }
  }
  function resolveSource(fieldId, consumerTaskId) {
    const producers = fieldOutputs[fieldId] || [];
    if (!producers.length) return null;
    if (producers.length === 1) return producers[0];
    const co = taskOrder[consumerTaskId] || [999, 999];
    const upstream = producers.filter(p => {
      const po = taskOrder[p.task_id] || [999, 999];
      return po[0] < co[0] || (po[0] === co[0] && po[1] < co[1]);
    });
    if (upstream.length) return upstream.reduce((best, p) => {
      const bo = taskOrder[best.task_id] || [0,0];
      const po = taskOrder[p.task_id] || [0,0];
      return (po[0] > bo[0] || (po[0] === bo[0] && po[1] > bo[1])) ? p : best;
    });
    return producers[0];
  }
  for (const stage of bp.stages) {
    for (const task of stage.tasks) {
      for (const inp of task.shared_fields) {
        const src = resolveSource(inp.id, task.id);
        if (src) {
          edges.push({
            from_task_id: src.task_id, from_task_name: src.task_name,
            from_field_name: inp.name, to_task_id: task.id, to_task_name: task.name,
            to_field_name: inp.name, data_type: inp.property_type
          });
        }
      }
    }
  }
  return edges;
}

function buildSourceMap(bp, prefix) {
  const taskLookup = {};
  for (const stage of bp.stages) {
    for (let tidx = 0; tidx < stage.tasks.length; tidx++) {
      taskLookup[stage.tasks[tidx].id] = { stage, tidx: tidx + 1 };
    }
  }
  const edges = buildDataFlowEdges(bp);
  const map = {};
  for (const edge of edges) {
    const src = taskLookup[edge.from_task_id];
    const key = edge.to_task_id + '|' + edge.from_field_name;
    if (src) map[key] = 'Task ' + prefix + src.stage.execution_order + '.' + src.tidx;
    else map[key] = 'Task ID ' + edge.from_task_id;
  }
  return { map, edges };
}

function generateDataStructures(blueprints) {
  const parent = blueprints[0];
  const childBps = blueprints.slice(1);
  const childMap = {};
  childBps.forEach(bp => { childMap[bp.id] = bp; });
  const { map: parentSourceMap, edges: parentEdges } = buildSourceMap(parent, '');

  const stagesArr = [];
  for (const stage of parent.stages) {
    const tasksArr = [];
    for (let tidx = 0; tidx < stage.tasks.length; tidx++) {
      const task = stage.tasks[tidx];
      const taskId = stage.execution_order + '.' + (tidx + 1);
      const inputs = task.shared_fields.map(f => {
        let src = 'Workflow-level';
        const key = task.id + '|' + f.name;
        if (parentSourceMap[key]) src = parentSourceMap[key];
        return { n: f.name, t: f.property_type, src, id: f.id };
      });
      const outputs = task.requested_fields.map(f => ({ n: f.name, t: f.property_type, id: f.id }));
      const isChildLink = !!(task.linked_workflow_id && childMap[task.linked_workflow_id]);
      tasksArr.push({ id: taskId, name: task.name, agent: task.agentLabel, agentClass: task.agentClass, _isChildLink: isChildLink, inputs, outputs });
    }
    stagesArr.push({ id: stage.execution_order, name: stage.name, tasks: tasksArr });
  }

  let childStagesArr = [];
  if (childBps.length) {
    const childBp = childBps[0];
    for (const stage of childBp.stages) {
      const tasksArr = [];
      for (let tidx = 0; tidx < stage.tasks.length; tidx++) {
        const task = stage.tasks[tidx];
        const taskId = 'C1.' + stage.execution_order + '.' + (tidx + 1);
        const inputs = task.shared_fields.map(f => ({ n: f.name, t: f.property_type, src: 'Workflow-level', id: f.id }));
        const outputs = task.requested_fields.map(f => ({ n: f.name, t: f.property_type, id: f.id }));
        tasksArr.push({ id: taskId, name: task.name, agent: task.agentLabel, agentClass: task.agentClass, _isChildLink: false, inputs, outputs });
      }
      childStagesArr.push({ id: 'C1.' + stage.execution_order, name: stage.name, tasks: tasksArr });
    }
  }

  const taskLookup = {};
  for (const stage of parent.stages) {
    for (let tidx = 0; tidx < stage.tasks.length; tidx++) {
      taskLookup[stage.tasks[tidx].id] = stage.execution_order + '.' + (tidx + 1);
    }
  }
  const edgesArr = parentEdges.filter(e => taskLookup[e.from_task_id] && taskLookup[e.to_task_id]).map(e => ({
    from: taskLookup[e.from_task_id], to: taskLookup[e.to_task_id], data: e.from_field_name, type: e.data_type
  }));

  const prompts = {};
  function addPrompts(bp, prefix) {
    for (const stage of bp.stages) {
      for (let tidx = 0; tidx < stage.tasks.length; tidx++) {
        const task = stage.tasks[tidx];
        const tid = prefix + stage.execution_order + '.' + (tidx + 1);
        prompts[tid] = (task.description || '').trim() || null;
      }
    }
  }
  addPrompts(parent, '');
  childBps.forEach((bp, ci) => addPrompts(bp, 'C' + (ci + 1) + '.'));

  return { stages: stagesArr, childStages: childStagesArr, parentEdges: edgesArr, taskPrompts: prompts };
}

// ---- RUN TESTS ----

function test(name, rexPath, expected) {
  console.log(`\n=== ${name} ===`);
  const rawData = extractJson(rexPath);
  const bps = (rawData.workflowTemplates || []).map(parseBlueprintData);
  const data = generateDataStructures(bps);

  const totalTasks = data.stages.reduce((s, st) => s + st.tasks.length, 0);
  const childTasks = data.childStages.reduce((s, st) => s + st.tasks.length, 0);
  const promptCount = Object.values(data.taskPrompts).filter(v => v !== null).length;

  console.log(`  Stages: ${data.stages.length} (expected ${expected.stages})`);
  console.log(`  Tasks: ${totalTasks} (expected ${expected.tasks})`);
  console.log(`  Edges: ${data.parentEdges.length} (expected ${expected.edges})`);
  console.log(`  Prompts: ${promptCount} (expected ${expected.prompts})`);
  if (expected.childStages !== undefined) {
    console.log(`  Child Stages: ${data.childStages.length} (expected ${expected.childStages})`);
    console.log(`  Child Tasks: ${childTasks} (expected ${expected.childTasks})`);
  }

  let pass = true;
  if (data.stages.length !== expected.stages) { console.log('  FAIL: stage count mismatch'); pass = false; }
  if (totalTasks !== expected.tasks) { console.log('  FAIL: task count mismatch'); pass = false; }
  if (data.parentEdges.length !== expected.edges) { console.log('  FAIL: edge count mismatch'); pass = false; }
  if (promptCount !== expected.prompts) { console.log('  FAIL: prompt count mismatch'); pass = false; }
  if (expected.childStages !== undefined && data.childStages.length !== expected.childStages) { console.log('  FAIL: child stage count mismatch'); pass = false; }
  if (expected.childTasks !== undefined && childTasks !== expected.childTasks) { console.log('  FAIL: child task count mismatch'); pass = false; }

  if (pass) console.log('  PASS');
  return pass;
}

const basePath = path.resolve(__dirname, '..');
const r1 = test('Warranty Claims',
  path.join(basePath, 'blueprints/Warranty Claims/Regrello Export - Warranty Claims.rex'),
  { stages: 12, tasks: 30, edges: 238, prompts: 29 }
);

const r2 = test('Chevron Invoice Audit',
  path.join(basePath, 'blueprints/Chevron Invoice Audit/Chevron - Invoice Audit 04_13_26.rex'),
  { stages: 20, tasks: 48, edges: 75, prompts: 57, childStages: 7, childTasks: 17 }
);

console.log(`\n${'='.repeat(40)}`);
console.log(`Results: ${r1 && r2 ? 'ALL PASS' : 'SOME FAILED'}`);
process.exit(r1 && r2 ? 0 : 1);
