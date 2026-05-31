#!/usr/bin/env python3
import json
import os
import re
import sys
import subprocess
from pathlib import Path

from path_defaults import resolve_repo_root

ROOT = resolve_repo_root(__file__)
DEFAULT_HELP_TIMEOUT_SECONDS = 15
DEFAULT_BUILD_TIMEOUT_SECONDS = 120
BANNED_HELP_PATTERNS = [
    r"e\.g\.\s*NQ",
    r"NQ,\s*ES,\s*GC",
    r"NQ,\s*ES,\s*AAPL,\s*BTCUSDT",
]
_ICT_ENGINE_BIN = None
EXPECTED_NO_OUTPUT_MODE_COMMANDS = {
    'train',
    'update',
    'auto-quant-promote-canonical-setup',
    'factor-autoresearch',
    'auto-quant-bootstrap',
    'auto-quant-update',
    'auto-quant-prepare',
    'auto-quant-adoption-decision',
    'clean-futures',
    'futures-sop',
    'expansion-sop',
    'register-structural-path-ranking-trainer-artifact',
    'clear-structural-path-ranking-trainer-artifact',
    'enable-structural-path-ranking-runtime',
    'disable-structural-path-ranking-runtime',
    'auto-quant-seed-evidence',
    'auto-quant-agent-material-batch',
    'auto-quant-agent-material-dispatch',
    'auto-quant-agent-material-rank',
    'auto-quant-results-import',
    'auto-quant-consume-live-signals',
    'auto-quant-ingest-real-trades',
    'auto-quant-prior-init',
}


def build_timeout_seconds():
    raw = os.environ.get('ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS', '').strip()
    if not raw:
        return DEFAULT_BUILD_TIMEOUT_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_BUILD_TIMEOUT_SECONDS
    return value if value > 0 else DEFAULT_BUILD_TIMEOUT_SECONDS


def help_timeout_seconds():
    raw = os.environ.get('ICT_ENGINE_HELP_AUDIT_HELP_TIMEOUT_SECONDS', '').strip()
    if not raw:
        return DEFAULT_HELP_TIMEOUT_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_HELP_TIMEOUT_SECONDS
    return value if value > 0 else DEFAULT_HELP_TIMEOUT_SECONDS


def ict_engine_bin():
    global _ICT_ENGINE_BIN
    if _ICT_ENGINE_BIN is not None:
        return _ICT_ENGINE_BIN

    explicit = os.environ.get('ICT_ENGINE_HELP_AUDIT_BIN')
    if explicit:
        candidate = Path(explicit)
    else:
        exe_name = 'ict-engine.exe' if sys.platform == 'win32' else 'ict-engine'
        for existing in [
            ROOT / '.local-artifacts' / 'cargo-target' / 'debug' / exe_name,
            ROOT / 'target' / 'debug' / exe_name,
        ]:
            if existing.exists():
                _ICT_ENGINE_BIN = existing
                return existing

        subprocess.run(
            ['cargo', 'build', '--quiet'],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
            timeout=build_timeout_seconds(),
        )
        metadata = subprocess.run(
            ['cargo', 'metadata', '--format-version', '1', '--no-deps'],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
        target_dir = Path(json.loads(metadata.stdout)['target_directory'])
        candidate = target_dir / 'debug' / exe_name

    if not candidate.exists():
        raise FileNotFoundError(f'ict-engine binary not found: {candidate}')

    _ICT_ENGINE_BIN = candidate
    return candidate


def run_help(args, timeout=None):
    if timeout is None:
        timeout = help_timeout_seconds()
    result = subprocess.run(
        [str(ict_engine_bin()), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        timeout=timeout,
    )
    return result.stdout


def command_list():
    text = run_help(['--help'])
    commands = []
    in_commands = False
    for line in text.splitlines():
        if line.strip() == 'Commands:':
            in_commands = True
            continue
        if not in_commands:
            continue
        if not line.strip():
            break
        m = re.match(r'^\s{2,}([a-z][a-z0-9-]+)(?:\s+|$)', line)
        if m and m.group(1) != 'help':
            commands.append(m.group(1))
    return commands


def parse_options(help_text):
    lines = help_text.splitlines()
    options = []
    in_options = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == 'Options:':
            in_options = True
            i += 1
            continue
        if not in_options:
            i += 1
            continue
        if not line.strip():
            break
        if not re.match(r'^\s{2,}[-]', line):
            i += 1
            continue
        stripped = line.strip()
        if '  ' in stripped:
            left, right = re.split(r'\s{2,}', stripped, maxsplit=1)
            desc = right.strip()
            same_line = True
        else:
            left = stripped
            desc = ''
            same_line = False
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    break
                if re.match(r'^\s{2,}[-]', nxt):
                    break
                if re.match(r'^\s{10,}\S', nxt):
                    desc = (desc + ' ' + nxt.strip()).strip()
                    j += 1
                    continue
                break
            i = j - 1
        options.append(
            {
                'flag': left,
                'description': desc,
                'has_description': bool(desc),
                'same_line': same_line,
            }
        )
        i += 1
    return options


def output_mode_support(options):
    flags = ' '.join(option['flag'] for option in options)
    return {
        'output_format': '--output-format' in flags,
        'human': '--human' in flags,
        'agent': '--agent' in flags,
        'compact': '--compact' in flags,
    }


def output_mode_status(support):
    if all(support.values()):
        return 'full'
    if any(support.values()):
        return 'partial'
    return 'none'


def none_output_mode_policy(rows):
    observed_none = sorted(
        row['command'] for row in rows if row['output_mode_status'] == 'none'
    )
    expected_none = sorted(EXPECTED_NO_OUTPUT_MODE_COMMANDS)
    observed_set = set(observed_none)
    expected_set = set(expected_none)
    return {
        'expected_count': len(expected_none),
        'observed_count': len(observed_none),
        'unclassified_none_commands': sorted(observed_set - expected_set),
        'missing_expected_commands': sorted(expected_set - observed_set),
        'matches_expected': observed_set == expected_set,
        'expected_none_commands': expected_none,
        'observed_none_commands': observed_none,
    }


def main():
    commands = command_list()
    rows = []
    missing = []
    command_errors = []
    market_bias_hits = []
    root_help = run_help(['--help'])
    for pattern in BANNED_HELP_PATTERNS:
        if re.search(pattern, root_help):
            market_bias_hits.append({'command': '<root>', 'pattern': pattern})
    for cmd in commands:
        try:
            text = run_help([cmd, '--help'])
        except subprocess.TimeoutExpired:
            command_errors.append({'command': cmd, 'error': 'help_timeout'})
            continue
        except subprocess.CalledProcessError as exc:
            command_errors.append(
                {
                    'command': cmd,
                    'error': 'help_failed',
                    'returncode': exc.returncode,
                    'stderr': exc.stderr.strip(),
                }
            )
            continue
        opts = parse_options(text)
        cmd_missing = [o['flag'] for o in opts if o['flag'] != '-h, --help' and not o['has_description']]
        for pattern in BANNED_HELP_PATTERNS:
            if re.search(pattern, text):
                market_bias_hits.append({'command': cmd, 'pattern': pattern})
        rows.append(
            {
                'command': cmd,
                'option_count': len(opts),
                'missing_description_count': len(cmd_missing),
                'missing_descriptions': cmd_missing,
                'output_modes': output_mode_support(opts),
                'output_mode_status': output_mode_status(output_mode_support(opts)),
            }
        )
        if cmd_missing:
            missing.append({'command': cmd, 'missing_descriptions': cmd_missing})

    none_policy = none_output_mode_policy(rows)
    status = (
        'pass'
        if commands
        and not missing
        and not market_bias_hits
        and not command_errors
        and none_policy['matches_expected']
        else 'needs_fix'
    )
    summary = {
        'root_help_has_version_flag': '-V, --version' in root_help,
        'command_count': len(commands),
        'commands_with_missing_help': len(missing),
        'commands_with_help_errors': len(command_errors),
        'commands_with_market_bias': len(market_bias_hits),
        'commands_with_full_output_modes': sum(
            1 for row in rows if row['output_mode_status'] == 'full'
        ),
        'commands_with_partial_output_modes': sum(
            1 for row in rows if row['output_mode_status'] == 'partial'
        ),
        'commands_with_no_output_modes': sum(
            1 for row in rows if row['output_mode_status'] == 'none'
        ),
        'none_output_mode_policy_matches_expected': none_policy['matches_expected'],
        'status': status,
    }

    report = {
        'summary': summary,
        'commands': rows,
        'missing': missing,
        'command_errors': command_errors,
        'market_bias_hits': market_bias_hits,
        'none_output_mode_policy': none_policy,
    }
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
