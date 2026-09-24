# Test results

Run with:

```
uv run --python 3.12 --with pytest pytest plugins/forge/tests/ -q
```

```
........................................................................ [ 65%]
......................................                                   [100%]
110 passed in 6.01s
```

Also re-run clean under Python 3.14 (`uv run --python 3.14 --with pytest ...`)
and via the bare system `python3` (3.14.3) driving `bin/forge` directly, to
confirm the "Python 3.12+ stdlib only, runs anywhere with python3" runtime
constraint actually holds, not just under the pinned test interpreter.

**Counts by file** (110 total, 0 failed):

| File | Tests |
|---|---|
| `test_jcs.py` | 42 |
| `test_doctor.py` | 11 |
| `test_lock.py` | 11 |
| `test_version_check.py` | 11 |
| `test_toolcheck.py` | 10 |
| `test_guard.py` | 8 |
| `test_files_lock.py` | 8 |
| `test_mcp_probe.py` | 9 |

## Each protection, and the test that proves it fails on bad input

| Protection | Proving test(s) |
|---|---|
| JCS key ordering (UTF-16 code-unit, not code-point) | `test_jcs.py::test_utf16_key_ordering_disagrees_with_codepoint_ordering` -- asserts the *opposite* of what a naive code-point sort gives |
| JCS Unicode pass-through (no normalisation; hidden chars matter) | `test_jcs.py::test_strings_are_not_unicode_normalised`, `test_hidden_unicode_changes_the_hash` -- a zero-width space appended to a tool description must change the hash |
| JCS ECMAScript number formatting (int and float, fixed/exponential boundaries) | `test_jcs.py::test_number_formatting_vectors` (21 vectors incl. the 1e21 and 1e-6/1e-7 boundary cases), `test_large_int_uses_exact_digits_not_float_rounding` |
| Claude Code version floor (terminal + Desktop) | `test_version_check.py::test_check_claude_binary_FAILS_below_the_floor` (2.1.279 vs. hard floor 2.1.280; 2.1.280 warns below recommended 2.1.281), `test_doctor.py::test_doctor_FAILS_on_claude_code_below_the_version_floor` |
| Tool pin check: missing binary | `test_toolcheck.py::test_FAILS_on_missing_binary`, `test_doctor.py::test_doctor_FAILS_on_missing_binary` |
| Tool pin check: version mismatch (with and without a capture group) | `test_toolcheck.py::test_FAILS_on_version_mismatch_with_capturing_group`, `test_FAILS_on_version_mismatch_without_capturing_group`, `test_doctor.py::test_doctor_FAILS_on_version_mismatch` |
| Tool pin check: unpinned entry | `test_toolcheck.py::test_FAILS_on_unpinned_entry`, `test_doctor.py::test_doctor_FAILS_on_unpinned_entry` |
| `forge doctor` fail-closed on an internal error (exit 2, never 0) | `test_doctor.py::test_cli_doctor_returns_2_on_an_INJECTED_INTERNAL_ERROR`, `test_cli_doctor_never_returns_0_when_run_doctor_raises` -- a monkeypatched `run_doctor` that raises |
| `CheckResult` can't report `fail` without a remediation string | `test_toolcheck.py::test_check_result_with_fail_status_requires_a_fix_string` |
| MCP lock: probe -> lock -> re-probe is stable | `test_lock.py::test_probe_lock_reprobe_are_equal` |
| MCP lock: rug pull (tool description changes) is caught, naming the tool and field | `test_lock.py::test_diff_entry_FAILS_to_stay_clean_when_tool_description_mutates`, `test_run_mcp_checks_MUTATE_reports_drift_naming_tool_and_field` |
| MCP lock: duplicate item names rejected | `test_lock.py::test_duplicate_tool_names_are_rejected` |
| MCP lock: env values never stored, only names | `test_lock.py::test_env_values_are_never_stored_only_names` |
| MCP lock: missing lock entry fails closed | `test_lock.py::test_missing_lock_entry_for_a_real_server_FAILS_closed` |
| MCP lock: `pending_install` is a warning, never a pass | `test_lock.py::test_pending_install_server_is_a_warning_not_a_pass` |
| MCP probe: both protocol eras (`server/discover` and legacy `initialize`) | `test_mcp_probe.py::test_probe_uses_server_discover_by_default`, `test_probe_falls_back_to_legacy_initialize`, `test_both_protocol_eras_return_equivalent_tool_definitions`; guard-level: `test_guard.py::test_guard_works_over_the_legacy_protocol_era` |
| MCP probe: request timeout, dead command | `test_mcp_probe.py::test_request_times_out_when_server_never_answers`, `test_probe_FAILS_fast_on_a_dead_command` |
| Guard: clean pass-through (`tools/list`, `tools/call`) | `test_guard.py::test_guard_passes_through_tools_list_and_tools_call` |
| Guard: rug pull mid-session -> second `tools/list` replaced with `-32001` | `test_guard.py::test_guard_MUTATE_second_tools_list_replaced_with_drift_error` |
| Guard: unknown `tools/call` rejected without forwarding | `test_guard.py::test_guard_rejects_call_to_a_tool_name_not_in_the_lock` |
| Guard: an extra, unlisted tool is rejected | `test_guard.py::test_guard_rejects_an_extra_tool_not_present_in_the_lock` |
| Guard: no lock entry -> refuses to start, exit 2 | `test_guard.py::test_guard_FAILS_closed_with_no_lock_entry` |
| Guard: non-JSON-RPC noise from the server is dropped, not forwarded | `test_guard.py::test_guard_drops_noise_lines_from_the_server` (asserts every raw line the guard emits parses as JSON) |
| Guard: malformed input from the client is dropped, connection still works | `test_guard.py::test_guard_drops_malformed_input_from_the_client` |
| File lock: tracked-file drift detected | `test_files_lock.py::test_run_file_checks_FAILS_when_a_tracked_file_changes` (content changed), `test_run_file_checks_FAILS_when_a_tracked_file_is_deleted` (file removed) |
| File lock: empty tracked set is a warning, not silently passing | `test_files_lock.py::test_run_file_checks_with_empty_lock_is_a_warning` |
