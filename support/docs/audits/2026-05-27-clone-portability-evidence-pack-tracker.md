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

Current-state probes:

- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes`
  - current result: `needs_fix`
- `python3 support/scripts/research/factor_candidate_resolver.py --repo-root . --output-dir /tmp/ict-engine-candidate-pack-audit.PtVwYo --build-packs`
  - current result: `built_pack_count=8`

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
