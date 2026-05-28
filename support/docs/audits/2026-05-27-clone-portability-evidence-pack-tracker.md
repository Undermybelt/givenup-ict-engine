# Clone Portability Evidence Pack Tracker

Date: 2026-05-27
Status: in progress, not complete
Scope: audit whether a fresh GitHub clone can use ict-engine without maintainer-local assumptions, and whether evidence packs / factor candidates can be added, removed, reused, and audited with low coupling.

## Current verdict

No, the objective is not yet proven complete.

Fresh evidence on 2026-05-27:

- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes`
  still returns `summary.status=needs_fix`.
  - unresolved: `worktree_clean_for_release`
  - unresolved: `remote_readback`
  - current nuance: both `origin` and release mirror readback fail from the
    current network path, but the audit now preserves
    `origin.fallback_public_probe` so that SSH-remote vs public-HTTPS failure is
    explicit
- `python3 support/scripts/research/factor_candidate_resolver.py --repo-root . --output-dir <tmp> --build-packs`
  succeeds with:
  - `candidate_count=14`
  - `buildable_count=8`
  - `built_pack_count=8`
- `python3 support/scripts/research/factor_candidate_resolver.py --repo-root . --backfill-pack-manifests --output-format human`
  succeeds with:
  - `written_count=25`
  - `skipped_count=0`
- `python3 support/scripts/research/factor_candidate_resolver.py --repo-root . --verify-pack-contracts --output-format human`
  succeeds with:
  - `pack_dir_count=25`
  - `registered_count=8`
  - `unregistered_count=17`
  - `invalid_count=0`

This means the repo can currently distill reusable candidate-pack outputs, but
release portability is still blocked and the clone-to-release path is not yet
cleanly proven.

## What was fixed in this slice

### 1. Exported candidate packs are now self-describing

Problem before this slice:

- built candidate packs emitted only:
  - `factor_expression.json`
  - `factor_eval_grid_summary.json`
  - `transfer_score.json`
- a downstream user could copy a pack directory, but the directory itself did
  not declare:
  - what artifact family it belonged to
  - which files were required members
  - which reusable source artifact produced it

Change made:

- `support/scripts/research/factor_candidate_resolver.py` now writes
  `pack_manifest.json` into every built pack directory.
- `candidate_pack_index.json` now records `pack_manifest_path` for every built
  candidate.

Result:

- a single pack directory is now inspectable in isolation
- pack consumers can validate membership without external prose
- add/remove/copy flows are less dependent on implicit directory knowledge

### 1b. Repo-native example packs were backfilled to the same contract

Problem before this slice:

- `support/examples/factor_candidate_packs/**` still contained legacy
  three-file directories
- fresh clones could inspect them, but the repo itself did not carry the same
  self-describing manifest contract as exported packs

Change made:

- `support/scripts/research/factor_candidate_resolver.py` now exposes
  `--backfill-pack-manifests`
- current repo-native example packs were backfilled with committed
  `pack_manifest.json`
- `candidate_pack_dir` validation now fails closed when the manifest is missing

Result:

- clone users now receive repo-native packs that are already self-describing
- pack portability is no longer limited to generated `/tmp` exports
- a “legacy three JSON files is enough” assumption now fails closed

### 1c. Repo-native pack drift now has a direct read-only verifier

Problem before this slice:

- clone users had two imperfect surfaces:
  - `--list-buildable` only showed the explicit product-visible candidate set
  - `--backfill-pack-manifests` was a write path, not a safe verifier
- this left an ambiguity gap between:
  - repo-native pack directories that physically exist
  - the smaller subset explicitly registered in
    `config/factor_candidate_harness_presets.json`
  - packs that are malformed versus merely unregistered

Change made:

- `support/scripts/research/factor_candidate_resolver.py` now exposes
  `--verify-pack-contracts`
- the verifier scans all repo-native pack directories under
  `support/examples/factor_candidate_packs/**`
- it reports:
  - contract validity (`valid` / `invalid`)
  - registration status (`registered` / `unregistered`)
  - pack-local fail-closed reason when the contract is broken

Result:

- clone users now have a safe one-command audit surface for repo-native packs
- “directory exists” is no longer conflated with “product-visible candidate”
- malformed packs fail closed without requiring a write action first

### 1d. Regime sidecar consumer docs no longer overstate `trade_usable`

Problem before this slice:

- `support/docs/regime-classifier-sidecar-chain.md` described the clean
  narrowed-scope smoke as producing `trade_usable=true`
- the actual consumer bundle contract and tests already fail closed:
  - `trade_usable=false`
  - `promotion_allowed=false`
  - `closed_loop_consumption_status=inspection_only_regime_sidecar_requires_downstream_live_admission`
- this was a consumer-facing wording bug: strong regime sidecar confidence could
  be misread as downstream trade readiness

Change made:

- updated the sidecar-chain doc so the smoke example matches the current
  consumer bundle/test contract

Result:

- regime sidecar confidence stays clearly separated from downstream live-trade
  admission
- clone users are less likely to mistake an `accept_regime` hint for
  `trade_usable=true`

### 2. Release audit now preserves GitHub public fallback diagnostics

Problem before this slice:

- `release_readiness_audit.py` read `origin` via `git ls-remote origin`
  directly.
- when a workstation used SSH remotes or URL rewrites, failures could look like
  a general remote/readiness problem without showing whether the underlying
  public GitHub URL was still reachable.

Change made:

- `support/scripts/release_readiness_audit.py` now:
  - records the declared `origin` URL
  - recognizes GitHub SSH remotes such as
    `git@github.com:Undermybelt/givenup-ict-engine.git`
  - probes the public HTTPS fallback
    `https://github.com/Undermybelt/givenup-ict-engine.git`
  - preserves the fallback probe result under
    `origin.fallback_public_probe`

Result:

- clone users and release auditors can distinguish:
  - SSH/transport policy issues
  - public GitHub reachability issues
  - actual release-mirror readback failures

### 3. Strategy-library provenance no longer leaks caller-local absolute paths

Problem before this slice:

- `support/scripts/research/factor_candidate_pack.py` preserved
  `metadata.source_artifact` as `str(zip_path)` when building a strategy
  library manifest from a `freqtrade` backtest zip
- when the caller passed an absolute path, the exported manifest embedded a
  maintainer-local filesystem path inside a supposedly reusable evidence asset
- the strategy-library projection also dropped `source_artifact`, so consumers
  lost a stable provenance hint while still risking local-path leakage one
  layer earlier

Change made:

- freqtrade zip provenance is now normalized to a portable reference
  (`backtest.zip` for absolute caller-local inputs)
- exported strategy-library manifests now retain that portable
  `metadata.source_artifact` field instead of silently dropping it

Result:

- reusable evidence exports no longer depend on maintainer-local absolute paths
- clone users still receive a provenance hint for the originating input
  artifact
- portability and provenance both improve without widening the pack contract

### 4. Coordinated closure snapshot shells no longer hard-code one workstation's paths

Problem before this slice:

- `support/scripts/objective_closure_snapshot.py --output-dir ...` wrote a
  reusable coordination packet, but the packet embedded:
  - absolute `repo_root`
  - absolute `options.output_dir`
  - absolute child `evidence_files`
  - absolute repo-local script paths inside `audit_commands`
- that made the packet harder to move across clones or attach to another audit
  handoff without carrying one machine's filesystem layout as an implicit
  contract

Change made:

- the persisted snapshot now uses packet-relative references when
  `--output-dir` is supplied:
  - `repo_root` becomes `ict-engine`
  - `options.output_dir` becomes `.`
  - child evidence files are stored as local filenames
  - repo-local script entries in `audit_commands` are rewritten to
    `support/scripts/...`

Result:

- the parent coordinated closure snapshot remains self-contained inside its output root
- clone users can move or compare the packet without inheriting
  maintainer-local absolute path assumptions
- current blocker truth still survives, but the parent packet contract is now more
  reusable

## What is still not good enough

### 1. Release readiness is still blocked by real current-state evidence

As of 2026-05-27:

- the working tree is not release-clean
  - `status_entries=1489`
  - `tracked_entries=27`
  - `untracked_entries=1462`
- release mirror readback still fails from the current machine/network
- therefore a fresh public release claim is still unproven

### 2. Factor discovery still depends on explicit registry entries

Current behavior is hybrid, not pure auto-discovery:

- reusable pack directories exist under
  `support/examples/factor_candidate_packs/**`
- buildability and selection still flow through
  `config/factor_candidate_harness_presets.json`

This explicit registry is good for safety and zero-config determinism, but it
means “drop a directory and it automatically becomes a product candidate” is
still false. That should be documented as the intended contract unless the repo
later chooses directory auto-discovery.

### 3. Coordinated closure factor child payload now supports packet-safe runtime labels

Problem before this slice:

- the parent `objective_closure_snapshot.json` had already become portable, but
  the factor child compact payload still carried local runtime paths such as:
  - `claims_dir=/tmp/ict-engine-agent-claims/board-b-factor-refinement`
  - live-process `run_root=/private/tmp/...`
  - live-process `exit_file=/private/tmp/...`

Change made:

- `support/scripts/factor_claim_terminalization_audit.py` now supports
  `--portable-paths` for compact output
- `support/scripts/objective_closure_snapshot.py` now passes that flag when it
  writes coordinated packet children under `--output-dir`
- compact factor child payloads now collapse runtime-local `/tmp` and
  `/private/tmp` paths into packet-safe labels while preserving:
  - blocker counts
  - `run_root_state`
  - `exit_file_state`
  - live-process presence

Result:

- the coordinated factor child payload is now substantially more clone-portable
- operational blocker truth is retained without embedding workstation-local tmp
  roots in the compact packet
- this closes the specific factor-child portability debt, even though the full
  objective is still blocked by live factor/release truth

### 4. Practical-source debt quarantine and proof reuse now preserve current evidence

Problem before this slice:

- the parent objective packet could apply a prior heavy done-definition proof
  and accidentally drop the current light child details for practical-source
  debt
- reviewed untracked wrapper residue stayed indistinguishable from unreviewed
  objective blockers, even when tracked source was clean

Change made:

- `objective_closure_snapshot.py` now merges proof fields into the current
  done-definition surface instead of replacing the surface wholesale
- `done_definition_audit.py` writes a practical-source debt manifest with a
  stable untracked-violation fingerprint
- `support/docs/audits/practical-admission-source-debt-quarantine.json` records
  the reviewed fingerprint for the current untracked multi-agent residue

Result:

- full done-definition proof can be reused without losing current source-debt
  evidence
- tracked-source regressions still fail closed
- untracked residue stays visible as quarantined debt and cannot silently become
  release/completion proof

### 5. Release and factor action queues are more precise

Problem before this slice:

- `release_readiness_audit.py` could tell operators to restore release-mirror
  readback even when the release mirror was readable and only source `origin`
  failed
- `factor_claim_terminalization_audit.py` compared `/tmp` and `/private/tmp`
  literally, so a macOS tmp alias could make one live-owned active claim also
  appear in the fresh-without-live queue

Change made:

- release remote readback now records `failed_sides` and emits source-origin
  action text when only origin fails
- factor live-runtime ownership now normalizes tmp aliases and lane subdirs
  before comparing claim roots with live process roots

Result:

- parent evidence packets point release operators at the actual failing remote
  side
- factor action queues avoid double-counting one live-owned lane as both live
  and fresh-without-live
- current blocker truth remains red, but it is more actionable and less noisy

## Recommended compatibility contract

For public clone users, keep the extension model explicit:

1. A factor/evidence pack is a repo-local directory with a pack manifest plus
   machine-readable member files.
2. Product-visible candidate selection happens through an explicit registry,
   not implicit directory scanning.
3. Temporary run state stays under `/tmp`, never as the semantic owner of a
   reusable pack.

This keeps add/remove behavior predictable while avoiding maintainer-local path
coupling.

## Evidence for this slice

Tests:

- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver support.scripts.tests.test_release_readiness_audit -v`
  - passed `27` tests
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack support.scripts.research.tests.test_factor_candidate_resolver -v`
  - passed `31` tests
- `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  - passed `9` tests
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  - passed `52` tests
- `python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v`
  - passed `45` tests
- `python3 -m unittest support.scripts.tests.test_release_readiness_audit -v`
  - passed `22` tests
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  - passed `67` tests
- `python3 support/scripts/done_definition_audit.py --run-all-heavy --compact --output /tmp/ict-engine-goal-20260528-current-heavy-done.json`
  - passed all `9/9` gates with `completion_ready=true`

Current-state probes:

- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes`
  - current result: `needs_fix`
- `python3 support/scripts/research/factor_candidate_resolver.py --repo-root . --output-dir /tmp/ict-engine-candidate-pack-audit.PtVwYo --build-packs`
  - current result: `built_pack_count=8`
- portable provenance probe:
  - a fresh synthetic strategy-library export now emits
    `metadata.source_artifact="backtest.zip"` instead of an absolute temp path
- portable closure-snapshot probe:
  - `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260527-closure-snapshot-portable4`
    now emits a packet with:
    - `repo_root="ict-engine"`
    - `options.output_dir="."`
    - `audit_commands[*][0]="python3"`
    - `factor_closure` child audit invoked with `--portable-paths`
    - child evidence files stored as relative filenames
    - current blocker truth still explicit:
      `factor_closure.status=needs_attention`,
      `active_claims=14`,
      `live_factor_processes=1`,
      `release_readiness.unresolved=["worktree_clean_for_release","remote_readback"]`
  - `rg -n '/Users|/private/tmp|/opt/homebrew|python3\.13|/tmp/ict-engine-goal-20260527-closure-snapshot-portable4' /tmp/ict-engine-goal-20260527-closure-snapshot-portable4/objective_closure_snapshot.json`
    returned no matches
  - factor child packet-safe proof:
    - `factor_claim_terminalization_audit.compact.json` now emits:
      - `claims_dir="ict-engine-agent-claims/board-b-factor-refinement"`
      - `run_root="ict-engine-..."`
      - `exit_file="ict-engine-.../checks/..."` for live processes
    - `rg -n '/Users|/private/tmp|/tmp/ict-engine-goal-20260527-closure-snapshot-portable4|claims_dir|run_root|exit_file' /tmp/ict-engine-goal-20260527-closure-snapshot-portable4/factor_claim_terminalization_audit.compact.json`
      no longer shows workstation-local absolute tmp roots; remaining matches are
      the field names themselves
- proof/quarantine/actionability probes:
  - `/tmp/ict-engine-goal-20260528-origin-action-proofed-snapshot/objective_closure_snapshot.json`
    remains `status=not_complete`, with full done-definition proof applied and
    current practical-source quarantine evidence preserved
  - `/tmp/ict-engine-goal-20260528-release-origin-action.json` shows
    `failed_sides=["origin"]`, release mirror readback passing, and next action
    focused on source origin readback
  - `/tmp/ict-engine-goal-20260528-factor-after-tmpmatch.json` shows the
    macOS `/tmp`/`/private/tmp` live TOD root matched to its claim, reducing the
    fresh-without-live queue to genuinely non-live claims

Example emitted manifest:

- `/private/tmp/ict-engine-candidate-pack-audit.PtVwYo/packs/family_f_vrp_compression_15m_v1/pack_manifest.json`
- `python3 support/scripts/research/factor_candidate_resolver.py --repo-root . --backfill-pack-manifests --output-format human`
  - current result: `written_count=25 skipped_count=0`

## Next concrete moves

1. Finish a clean release slice from a sanitized export or a clean worktree,
   then rerun release readiness with remote readback on a network that can
   actually reach the release mirror.
2. Consider a scaffold command for new pack directories plus preset
   registration, or keep that flow manual-but-explicit.
3. If more Board B/example packs should become product-visible, promote them
   through explicit preset entries instead of relying on directory presence.
4. Continue scanning active consumer-facing docs for stale practical-admission
   wording, especially any surface that could let `accept_regime` read like
   live-trade readiness.
