"""Finite, synthetic permission-removal audit. No OS sandbox or live agent."""
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json

RESOURCES = {'sales': [2, 3], 'copy': [2, 3], 'notes': ['fictional unused note']}
UNIVERSE = frozenset({'read:sales', 'read:copy', 'read:notes', 'write:report',
                      'tool:a', 'tool:b', 'exec:runtime'})
EXPECTED = 'total=5\n'  # Independently fixed task oracle, never supplied by workload.

@dataclass
class Scenario:
    name: str
    grants: dict
    baseline: frozenset = frozenset({'write:report'})
    dependencies: dict = field(default_factory=dict)
    sources: tuple = ('sales',)
    require_tool: bool = False
    baseline_oracle: str = 'valid'
    branch_oracle: str = 'valid'
    baseline_wrong_output: bool = False


def scenarios():
    return [
        Scenario('overlapping_file_directory', {
            'file_read': {'read:sales'}, 'directory_read': {'read:sales', 'read:notes'}}),
        Scenario('optional_read', {'sales_read': {'read:sales'}, 'notes_read': {'read:notes'}}),
        Scenario('required_input', {'sales_read': {'read:sales'}}),
        Scenario('baseline_overlap', {'sales_read': {'read:sales'}, 'notes_read': {'read:notes'}},
                 baseline=frozenset({'write:report', 'read:notes'})),
        Scenario('shared_dependency', {'tool_a': {'tool:a'}, 'tool_b': {'tool:b'}},
                 dependencies={'tool:a': {'exec:runtime', 'read:sales'},
                               'tool:b': {'exec:runtime', 'read:sales'}}, require_tool=True),
        Scenario('alternative_inputs', {'primary': {'read:sales'}, 'backup': {'read:copy'}},
                 sources=('sales', 'copy')),
        Scenario('missing_baseline_oracle', {'sales_read': {'read:sales'}, 'notes_read': {'read:notes'}},
                 baseline_oracle='missing'),
        Scenario('invalid_branch_oracle', {'sales_read': {'read:sales'}, 'notes_read': {'read:notes'}},
                 branch_oracle='invalid'),
        Scenario('failed_baseline_task', {'sales_read': {'read:sales'}, 'notes_read': {'read:notes'}},
                 baseline_wrong_output=True),
    ]


def compile_authority(s, retained):
    if not set(retained) <= s.grants.keys():
        raise ValueError('Unknown grant')
    atoms = set(s.baseline)
    for name in retained:
        atoms.update(s.grants[name])
    while True:
        grown = atoms | {b for a in atoms for b in s.dependencies.get(a, ())}
        if grown == atoms:
            break
        atoms = grown
    if not atoms <= UNIVERSE:
        raise ValueError('Operation outside finite modeled universe')
    return frozenset(atoms)


def state_hash(resources):
    return hashlib.sha256(json.dumps(resources, sort_keys=True).encode()).hexdigest()


class Broker:
    """All toy-workload effects traverse this broker, not arbitrary Python code."""
    def __init__(self, authority):
        self.authority = authority
        self.resources = json.loads(json.dumps(RESOURCES))
        self.sink = {}
        self.events = []

    def allowed(self, operation):
        if operation not in UNIVERSE:
            raise ValueError('Unknown operation')
        return operation in self.authority

    def require(self, operation):
        ok = self.allowed(operation)
        self.events.append({'operation': operation, 'allowed': ok})
        if not ok:
            raise PermissionError(operation)

    def read(self, name):
        self.require('read:' + name)
        return list(self.resources[name])

    def write_report(self, text):
        self.require('write:report')
        self.sink['report'] = text


def execute(s, authority, full=False):
    b = Broker(authority)
    initial_hash = state_hash(b.resources)
    error = None
    try:
        if s.require_tool:
            chosen = next((x for x in ('tool:a', 'tool:b') if b.allowed(x)), None)
            if chosen is None:
                raise PermissionError('no alternative tool')
            b.require(chosen)
            b.require('exec:runtime')
        values = None
        for source in s.sources:
            try:
                values = b.read(source)
                break
            except PermissionError:
                continue
        if values is None:
            raise PermissionError('no readable task input')
        total = sum(values)
        if full and s.baseline_wrong_output:
            total += 1  # Deliberate harness fault fixture; never a claimed attack.
        b.write_report('total=' + str(total) + '\n')
    except PermissionError as exc:
        error = str(exc)
    oracle_state = s.baseline_oracle if full else s.branch_oracle
    output = b.sink.get('report')
    passed = output == EXPECTED
    return {'authority': sorted(authority), 'probes': {op: b.allowed(op) for op in sorted(UNIVERSE)},
            'initial_state_sha256': initial_hash, 'final_resource_sha256': state_hash(b.resources),
            'output': output, 'events': b.events, 'error': error,
            'oracle_state': oracle_state, 'task_output_matches': passed,
            'accepted': error is None and oracle_state == 'valid' and passed}


def classify(full, branch, require_reduction=True, require_baseline=True):
    reduced = set(branch['authority']) < set(full['authority'])
    return bool(branch['accepted'] and (full['accepted'] or not require_baseline)
                and (reduced or not require_reduction))


def run():
    rows = []
    for s in scenarios():
        all_names = set(s.grants)
        full = execute(s, compile_authority(s, all_names), full=True)
        deletions = []
        for removed in sorted(all_names):
            retained = all_names - {removed}
            branch = execute(s, compile_authority(s, retained))
            deletions.append({'removed_grant': removed, 'retained_grants': sorted(retained),
                'removed_operations': sorted(set(full['authority']) - set(branch['authority'])),
                'naive_witness': branch['accepted'], 'strict_witness': classify(full, branch),
                'branch': branch})
        rows.append({'scenario': s.name, 'grants': {k: sorted(v) for k,v in s.grants.items()},
                     'baseline_operations': sorted(s.baseline),
                     'dependencies': {k: sorted(v) for k,v in s.dependencies.items()},
                     'full': full, 'deletions': deletions})
    alternative = next(s for s in scenarios() if s.name == 'alternative_inputs')
    joint = execute(alternative, compile_authority(alternative, set()))
    ds = [d for r in rows for d in r['deletions']]
    return {'schema_version': 1, 'scope': 'independent synthetic finite-authority model; no OS sandbox, model or source implementation',
            'operation_universe': sorted(UNIVERSE), 'expected_report': EXPECTED,
            'summary': {'scenario_families': len(rows), 'independent_deletions': len(ds),
                        'baseline_runs': len(rows), 'joint_counterfactual_runs': 1,
                        'naive_witnesses': sum(d['naive_witness'] for d in ds),
                        'strict_witnesses': sum(d['strict_witness'] for d in ds),
                        'false_witness_labels': sum(d['naive_witness'] and not d['strict_witness'] for d in ds)},
            'scenarios': rows, 'joint_removal_counterexample': joint}


def evidence(result):
    lines = ['# Exact synthetic evidence', '',
             'No live agent, OS sandbox, external service or attack-rate estimate. Independent deterministic workload and authority model.', '',
             '| Scenario / deleted grant | Task accepted | Removed operations | Delete-and-pass | Verify-reduction |',
             '|---|---|---|---|---|']
    for row in result['scenarios']:
        for d in row['deletions']:
            lines.append('| '+row['scenario']+' / '+d['removed_grant']+' | '+str(d['branch']['accepted'])+' | '+(', '.join(d['removed_operations']) or 'none')+' | '+str(d['naive_witness'])+' | '+str(d['strict_witness'])+' |')
    lines += ['', 'Counts: '+json.dumps(result['summary'], sort_keys=True), '',
        'Exact overlap trace: full file_read + directory_read allows read:sales and read:notes. Deleting file_read retains both reads through directory_read. Report remains total=5. Delete-and-pass labels a witness; Verify-reduction does not.',
        '', 'Genuine reduction twin: optional_read / notes_read loses read:notes, preserves read:sales and report output, and both methods label a witness.',
        '', 'Joint counterexample: alternative_inputs / primary and / backup each yield a strict witness. Deleting both yields no readable task input and no report. Individual witnesses are not permission to combine deletions.',
        '', 'Missing baseline oracle and deliberately wrong baseline output invalidate claims despite a passing restricted branch. Probe vectors measure only this finite broker; external OS access is not represented.']
    return '\n'.join(lines)+'\n'


def main():
    result = run()
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/run.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    Path('evidence.md').write_text(evidence(result))
    print(json.dumps(result['summary'], sort_keys=True))

if __name__ == '__main__':
    main()
