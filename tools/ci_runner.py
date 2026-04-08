import argparse
import json
import os
import sys
import uuid
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "execution-providers.json"

MAIN_SETTINGS = {
    "permissions": {
        "allow": [
            "Bash(*)",
            "Read(*)",
            "Write(*)",
            "Edit(*)",
            "Glob(*)",
            "Grep(*)",
            "Agent(*)",
            "Task(*)",
            "WebFetch(*)",
            "WebSearch(*)",
            "TodoRead",
            "TodoWrite",
            "NotebookEdit",
        ]
    }
}

PORTAL_SETTINGS = {
    "permissions": {
        "allow": [
            "Bash(*)",
            "Read(*)",
            "Write(*)",
            "Edit(*)",
            "Glob(*)",
            "Grep(*)",
            "TodoRead",
            "TodoWrite",
        ]
    }
}

SKILL_HINTS = {
    "/auto-wiki": [
        "- Do NOT ask for user confirmation at any step. Automatically continue all phases.",
        "- For /auto-wiki: proceed through all phases without pausing for confirmation.",
    ],
    "/auto-wiki-expand": [
        "- Do NOT ask for user confirmation at any step. Automatically continue all phases.",
        "- For /auto-wiki-expand: run one expansion cycle and finish without asking to continue.",
    ],
    "/auto-wiki-react": [
        "- Do NOT ask for user confirmation at any step. Automatically continue all phases.",
        "- For /auto-wiki-react: automatically process all affinity pairs with score >= 0.7 without asking for selection.",
    ],
    "/auto-wiki-sync": [
        "- Do NOT ask for user confirmation at any step. Automatically continue all phases.",
    ],
    "/auto-wiki-feedback": [
        "- Do NOT ask for user confirmation at any step. Automatically continue all phases.",
    ],
    "/auto-wiki-request": [
        "- Do NOT ask for user confirmation at any step. Automatically continue all phases.",
    ],
    "/auto-wiki-portal": [
        "- Do NOT ask for user confirmation at any step.",
    ],
}


def load_execution_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def get_provider(config: dict, provider_id: str | None) -> tuple[str, dict | None]:
    providers = {provider["id"]: provider for provider in config.get("providers", [])}
    resolved_id = provider_id or config.get("defaultProvider") or ""
    return resolved_id, providers.get(resolved_id)


def get_model(provider: dict | None, requested_model: str | None) -> tuple[str, str]:
    if not provider:
        model_id = requested_model or ""
        return model_id, model_id

    models = {model["id"]: model for model in provider.get("models", [])}
    if provider.get("lockModel") and provider.get("defaultModel"):
        model_id = provider["defaultModel"]
    else:
        model_id = requested_model or provider.get("defaultModel") or ""
    model = models.get(model_id)
    if not model and provider.get("defaultModel"):
        model_id = provider["defaultModel"]
        model = models.get(model_id)
    if model:
        return model["id"], model.get("label", model["id"])
    return model_id, model_id


def get_effort(provider: dict | None, requested_effort: str | None) -> str:
    if not provider:
        return requested_effort or ""
    return requested_effort or provider.get("effort", "")


def build_prompt(skill: str, args: str, provider: dict | None) -> str:
    command = f"{skill} {args}".strip()
    hints = SKILL_HINTS.get(skill)
    if not hints:
        raise ValueError(f"Unsupported skill: {skill}")

    commit_strategy = (provider or {}).get("commitStrategy", "")
    completion_line = "After completion, commit all changes and push directly to the current branch."
    if commit_strategy == "workflow":
        completion_line = "After completion, leave all changes in the working tree. Do NOT create commits and do NOT push."

    lines = [
        "Run the following Auto-Wiki skill:",
        command,
        "",
        "IMPORTANT: This is running in a non-interactive CI environment.",
        *hints,
        "",
        completion_line,
    ]
    return "\n".join(lines)


def build_prepare_payload(
    provider_id: str | None,
    model_id: str | None,
    effort: str | None,
    skill: str,
    args: str,
) -> dict:
    config = load_execution_config()
    resolved_provider_id, provider = get_provider(config, provider_id)
    resolved_model_id, resolved_model_label = get_model(provider, model_id)
    resolved_effort = get_effort(provider, effort)

    if provider is None:
        return {
            "provider": resolved_provider_id,
            "provider_label": resolved_provider_id or "unknown",
            "provider_supported": "false",
            "provider_error": f'Execution provider "{resolved_provider_id}" is not configured for this repository.',
            "runner": "",
            "model": resolved_model_id,
            "model_label": resolved_model_label,
            "effort": resolved_effort,
            "sandbox": "",
            "safety_strategy": "",
            "commit_strategy": "",
            "main_prompt": "",
            "react_prompt": "",
            "portal_prompt": "",
            "main_settings_json": json.dumps(MAIN_SETTINGS),
            "react_settings_json": json.dumps(MAIN_SETTINGS),
            "portal_settings_json": json.dumps(PORTAL_SETTINGS),
        }

    return {
        "provider": resolved_provider_id,
        "provider_label": provider.get("label", resolved_provider_id),
        "provider_supported": "true" if provider.get("ciSupported") else "false",
        "provider_error": ""
        if provider.get("ciSupported")
        else f'Execution provider "{resolved_provider_id}" is configured but not enabled for GitHub Actions.',
        "runner": provider.get("runner", ""),
        "model": resolved_model_id,
        "model_label": resolved_model_label,
        "effort": resolved_effort,
        "sandbox": provider.get("sandbox", ""),
        "safety_strategy": provider.get("safetyStrategy", ""),
        "commit_strategy": provider.get("commitStrategy", "agent"),
        "main_prompt": build_prompt(skill, args, provider),
        "react_prompt": build_prompt("/auto-wiki-react", "", provider),
        "portal_prompt": build_prompt("/auto-wiki-portal", "", provider),
        "main_settings_json": json.dumps(MAIN_SETTINGS),
        "react_settings_json": json.dumps(MAIN_SETTINGS),
        "portal_settings_json": json.dumps(PORTAL_SETTINGS),
    }


def append_github_output(path: Path, key: str, value: str) -> None:
    delimiter = f"EOF_{uuid.uuid4().hex}"
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"{key}<<{delimiter}\n")
        fh.write(f"{value}\n")
        fh.write(f"{delimiter}\n")


def command_prepare(args: argparse.Namespace) -> int:
    payload = build_prepare_payload(args.provider, args.model, args.effort, args.skill, args.args or "")
    github_output = args.github_output or os.environ.get("GITHUB_OUTPUT")
    if github_output:
        output_path = Path(github_output)
        for key, value in payload.items():
            append_github_output(output_path, key, str(value))
    else:
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare CI execution metadata for Auto-Wiki skills.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Resolve provider/model config and emit GitHub outputs.")
    prepare.add_argument("--provider", default=None)
    prepare.add_argument("--model", default=None)
    prepare.add_argument("--effort", default=None)
    prepare.add_argument("--skill", required=True)
    prepare.add_argument("--args", default="")
    prepare.add_argument("--github-output", default=None)
    prepare.set_defaults(func=command_prepare)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
