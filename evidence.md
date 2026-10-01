# Exact synthetic evidence

No live agent, OS sandbox, external service or attack-rate estimate. Independent deterministic workload and authority model.

| Scenario / deleted grant | Task accepted | Removed operations | Delete-and-pass | Verify-reduction |
|---|---|---|---|---|
| overlapping_file_directory / directory_read | True | read:notes | True | True |
| overlapping_file_directory / file_read | True | none | True | False |
| optional_read / notes_read | True | read:notes | True | True |
| optional_read / sales_read | False | read:sales | False | False |
| required_input / sales_read | False | read:sales | False | False |
| baseline_overlap / notes_read | True | none | True | False |
| baseline_overlap / sales_read | False | read:sales | False | False |
| shared_dependency / tool_a | True | tool:a | True | True |
| shared_dependency / tool_b | True | tool:b | True | True |
| alternative_inputs / backup | True | read:copy | True | True |
| alternative_inputs / primary | True | read:sales | True | True |
| missing_baseline_oracle / notes_read | True | read:notes | True | False |
| missing_baseline_oracle / sales_read | False | read:sales | False | False |
| invalid_branch_oracle / notes_read | False | read:notes | False | False |
| invalid_branch_oracle / sales_read | False | read:sales | False | False |
| failed_baseline_task / notes_read | True | read:notes | True | False |
| failed_baseline_task / sales_read | False | read:sales | False | False |

Counts: {"baseline_runs": 9, "false_witness_labels": 4, "independent_deletions": 17, "joint_counterfactual_runs": 1, "naive_witnesses": 10, "scenario_families": 9, "strict_witnesses": 6}

Exact overlap trace: full file_read + directory_read allows read:sales and read:notes. Deleting file_read retains both reads through directory_read. Report remains total=5. Delete-and-pass labels a witness; Verify-reduction does not.

Genuine reduction twin: optional_read / notes_read loses read:notes, preserves read:sales and report output, and both methods label a witness.

Joint counterexample: alternative_inputs / primary and / backup each yield a strict witness. Deleting both yields no readable task input and no report. Individual witnesses are not permission to combine deletions.

Missing baseline oracle and deliberately wrong baseline output invalidate claims despite a passing restricted branch. Probe vectors measure only this finite broker; external OS access is not represented.
