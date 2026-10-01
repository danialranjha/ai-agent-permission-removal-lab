# AI-agent permission-removal witness lab

Deleting a permission declaration is not necessarily a reduction in access. This independent, synthetic experiment audits the evidence needed to claim that a fixed task succeeded with less authority.

It uses a finite Python permission model and an in-memory report task. It does **not** run an AI model, Aletheia, a real agent, or an operating-system sandbox. No network, credentials, external endpoints, downloads or shell commands occur in the workload. Python itself remains fully trusted; this is not a sandbox for arbitrary Python programs.

## Hypothesis

A passing task after deleting one grant can be mislabeled as a successful authority reduction when another grant or baseline still permits the same operations. Require an accepted full run, an accepted restricted run, and a strictly smaller effective operation set to reject these false witnesses.

## Setup and reproduction

Python3.10+ standard library only; independently run here with Python3.11.6. No installation or keys.

```sh
python3 experiment.py
python3 -m unittest -v
python3 run_checks.py
```

The first command regenerates `artifacts/run.json` and `evidence.md`. The third writes `artifacts/tests.json` and `artifacts/mutations.json`. No timestamps, random IDs or machine paths enter the evidence, so reruns are byte-identical.

## Actual results

Nine scenario families produced nine baseline runs and17 independent one-grant deletions. One extra joint-removal run makes27 workload runs. The denominator describes chosen fixtures, not sampled attacks.

| Classification | Witness labels across17 deletions |
|---|---:|
| Delete-and-pass (valid restricted output only) |10|
| Verify-reduction (both runs accepted and effective set strictly smaller) |6|

Four labels were unsupported: two deletions removed no effective access, one had no valid baseline oracle, and one had a deliberately failing baseline output. Those last two are harness-validity controls, not claims about agent behavior. Invalid restricted-oracle output never counts as accepted, even if its text matches.

Twelve test methods pass. Two functional regressions are detected: removing the strict-reduction condition fails two checks, and ignoring baseline acceptance fails two checks. See [exact branch evidence](evidence.md), [run records](artifacts/run.json), [tests](artifacts/tests.json), and [mutations](artifacts/mutations.json).

## Technical walkthrough

### Exact paired trace

The fixed task reads invented sales values `[2,3]` and writes `total=5` to an in-memory report. A trusted independent oracle expects exactly `total=5\n`.

The full configuration grants:

- `file_read`: `read:sales`.
- `directory_read`: `read:sales` and `read:notes`.
- Baseline: `write:report`.

`directory_read` is an explicit finite expansion in this toy model, not a real path matcher.

Delete only `file_read`. The remaining directory grant still permits both reads. The exact effective set stays `{read:sales,read:notes,write:report}`. The report passes. Delete-and-pass calls this a witness; Verify-reduction rejects that classification because no operation was removed. Neither method changes the workload's action; they classify the same recorded branch differently.

The genuine-reduction twin starts with separate sales and notes grants. Removing `notes_read` makes its access probe false, retains the required sales read, and preserves the report. Both methods classify that branch as a witness.

### Additional boundaries

- Removing the only required sales read prevents the report. Lost access without successful completion is not a witness.
- A baseline grant can also cover a deleted permission, leaving coverage unchanged.
- Two tools share an interpreter and sales-read dependency. Rebuilding closure from the retained tool preserves those dependencies. The removed tool itself is no longer available.
- Primary and backup inputs each contain the same invented numbers. Either grant can be removed alone while preserving the report. Removing both fails. Individual witnesses cannot justify their untested combination.
- Missing baseline oracle, invalid restricted oracle and deliberately wrong baseline output exercise measurement validity.

Every branch gets the same fresh resource state. Grant deletions do not accumulate. A separate joint branch is explicitly labeled as a counterfactual. Probes enumerate the seven known operation atoms without changing state; actual task events separately record attempted reads and report writes.

### Model and threat assumptions

An untrusted rule may ask for excessive authority, but this experiment does not parse a rule or persuade a model. It assumes proposed grants and checks a measurement procedure. Trusted components are the finite resource/permission mapping, dependency compiler, broker, fixed workload and independent expected-output oracle. The monitor mediates all operations of this fixed workload only.

Authority compilation starts with baseline plus retained grants, then repeatedly adds dependency successors until stable. The classifier checks strict set inclusion on the resulting finite coverage, not grant identifiers. Tests compare compilation to an independent graph traversal for every subset of each scenario, including a cyclic-dependency case; this validates these finite cases, not every possible compiler.

## Source and interpretation

[Aletheia: Permission-Minimality Testing for Coding-Agent Rules](https://arxiv.org/html/2609.39678v1), sections2.3–2.4, motivates effective-authority comparison, fixed branch setup, and independent deletion witnesses. Our code is an independent simplified model, not extracted upstream code, a reproduction of the paper's agent runs, or a new vulnerability report. The paper's benchmark results do not describe this repository.

## Limitations and supported engineering decision

A passing restricted task establishes only a task-relative witness under trusted coverage and oracle assumptions. It does not establish malicious intent, population detection performance, minimum authority, or that a permission is unnecessary for other tasks. Natural-language translation, filesystem aliasing, real policy installation, concurrent state, subprocesses and live-model variability are absent. The seven-atom universe intentionally excludes real systems. No runtime or kernel containment is established.

For a real permission-ablation harness, restore the same fixtures, rebuild the remaining policy including shared dependencies, verify an actual coverage reduction, and require valid passing full/restricted task checks. Probe the installed restrictions separately and test combinations before removing multiple grants together. This lab supports those measurement checks, not automatic production-policy removal.
