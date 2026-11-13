"""Audit Age of Crowns event and interest-group overrides against an installed game."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys


MOD = Path(__file__).resolve().parents[1]
SCRIPT_SUFFIXES = {".txt", ".gui", ".asset"}
EVENT_ID = r"[A-Za-z0-9_]+\.\d+"
TOKEN = re.compile(r'#[^\n]*|"(?:\\.|[^"\\])*"|[{}=]|[^\s{}="#]+')
EVENT_DEFINITION = re.compile(rf"(?m)^\s*({EVENT_ID})\s*=\s*\{{")
EVENT_VALUE = re.compile(EVENT_ID)
RETIRED_IG = re.compile(r"ig_trade_unions", re.IGNORECASE)
VANILLA_EVENT_EXCEPTIONS = {
    Path("events/colonial_administration_events.txt"),  # AoC's rewritten chain
    Path("events/law_imposition_events.txt"),
}
REQUIRED_LAW_EVENTS = {
    "generic_laws.1", "generic_laws.3", "generic_laws.5",
    "law_notification.1", "law_notification.2", "law_notification.3",
    "law_notification.4", "unable_to_enact.2",
    "law_imposition_events.1", "law_imposition_events.2", "law_imposition_events.3",
}


def source(path):
    return path.read_text(encoding="utf-8-sig")


def script_files(root):
    for folder in ("common", "events", "gfx", "gui"):
        for path in (root / folder).rglob("*"):
            if path.is_file() and path.suffix in SCRIPT_SUFFIXES:
                yield path.relative_to(root), path


def event_calls(tokens, on_actions):
    for index, token in enumerate(tokens):
        if token == "trigger_event" and tokens[index + 1:index + 2] == ["="]:
            cursor = index + 2
            if cursor >= len(tokens):
                continue
            target = tokens[cursor]
            if target == "{":
                cursor += 1
                while cursor < len(tokens) and tokens[cursor] not in ("{", "}"):
                    if tokens[cursor].lower() == "id" and tokens[cursor + 1:cursor + 2] == ["="]:
                        target = tokens[cursor + 2]
                        break
                    cursor += 1
            if EVENT_VALUE.fullmatch(target):
                yield target
        if on_actions and token in ("events", "random_events", "first_valid"):
            if tokens[index + 1:index + 3] != ["=", "{"]:
                continue
            depth = 1
            for entry in tokens[index + 3:]:
                if entry == "{":
                    depth += 1
                elif entry == "}":
                    depth -= 1
                    if depth == 0:
                        break
                elif depth == 1 and EVENT_VALUE.fullmatch(entry):
                    yield entry


def audit(game):
    paths = dict(script_files(MOD))
    game_files = dict(script_files(game))
    for dlc in (game / "dlc").iterdir():
        if dlc.is_dir():
            game_files.update(script_files(dlc))

    metadata = json.loads(source(MOD / ".metadata/metadata.json"))
    replaced = set(metadata["game_custom_data"]["replace_paths"])
    errors = []
    for rel, path in game_files.items():
        if rel in paths:
            continue
        if rel.parts[0] == "events":
            errors.append(f"Vanilla event file without a same-path override: {rel}")
        if not any(p.as_posix() in replaced for p in (rel, *rel.parents)):
            paths[rel] = path

    definitions = Counter()
    law_events = set()
    for rel, path in paths.items():
        if rel.parts[0] == "events":
            ids = EVENT_DEFINITION.findall(source(path))
            definitions.update(ids)
            if rel.parts[1] == "law_events" or rel == Path("events/law_imposition_events.txt"):
                law_events.update(ids)
            if (ids and rel in game_files and rel.parts[1] != "law_events"
                    and rel not in VANILLA_EVENT_EXCEPTIONS):
                errors.append(f"Non-law vanilla event file contains event definitions: {rel}")
    for event, count in definitions.items():
        if count > 1:
            errors.append(f"Duplicate event ID: {event}")
    for event in sorted(REQUIRED_LAW_EVENTS - definitions.keys()):
        errors.append(f"Missing law event: {event}")

    called_events = set()
    for rel, path in paths.items():
        script = source(path)
        on_actions = rel.parts[:2] == ("common", "on_actions")
        if not (on_actions or RETIRED_IG.search(script) or "trigger_event" in script):
            continue
        tokens = [m[0] for m in TOKEN.finditer(script) if not m[0].startswith("#")]
        if any(RETIRED_IG.search(token) for token in tokens):
            errors.append(f"Reference to removed interest group: {rel}")
        targets = set(event_calls(tokens, on_actions))
        called_events.update(targets)
        for target in sorted(targets - definitions.keys()):
            errors.append(f"{rel} calls undefined event {target}")

    for event in sorted(law_events - called_events):
        errors.append(f"Law event has no scripted caller: {event}")

    return errors, len(definitions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path, help="Victoria 3 installation's game directory")
    args = parser.parse_args()
    if not (args.game / "events/law_events").is_dir():
        parser.error("pass the Victoria 3 game directory containing events/law_events")
    errors, count = audit(args.game)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Checked {count} event IDs, vanilla file overrides, and Trade Unions references.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
