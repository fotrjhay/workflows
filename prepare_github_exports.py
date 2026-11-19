#!/usr/bin/env python3
"""Create reviewable n8n workflow exports with account-specific values scrubbed."""
import json
from pathlib import Path
import re


SOURCE = Path(__file__).parent
OUTPUT = SOURCE / "github-ready"
EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
SHEET_ID = re.compile(r"(?<=/d/)[A-Za-z0-9_-]{20,}(?=/)|(?<=spreadsheetId=)[A-Za-z0-9_-]{20,}")


def scrub(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if key == "credentials":
                cleaned[key] = {
                    credential_type: {"id": "REPLACE_WITH_N8N_CREDENTIAL_ID", "name": name}
                    for credential_type, details in item.items()
                    for name in [details.get("name", "")]
                }
            elif key.lower() in {"webhookid", "credentialid", "api_key", "apikey", "access_token", "refreshtoken"}:
                cleaned[key] = "REPLACE_BEFORE_USE"
            elif key.lower() == "chatid":
                cleaned[key] = "REPLACE_WITH_TELEGRAM_CHAT_ID"
            elif key.lower() == "instanceid" and len(str(item)) > 24:
                cleaned[key] = "REPLACE_WITH_N8N_INSTANCE_ID"
            else:
                cleaned[key] = scrub(item)
        return cleaned
    if isinstance(value, list):
        return [scrub(item) for item in value]
    if isinstance(value, str):
        return SHEET_ID.sub("REPLACE_WITH_GOOGLE_SHEET_ID", EMAIL.sub("REPLACE_WITH_EMAIL", value))
    return value


def main():
    OUTPUT.mkdir(exist_ok=True)
    for source in sorted(SOURCE.glob("*.json")):
        workflow = json.loads(source.read_text(encoding="utf-8"))
        sanitized = scrub(workflow)
        for key in ("id", "versionId", "activeVersionId", "createdAt", "updatedAt"):
            sanitized.pop(key, None)
        sanitized["active"] = False
        (OUTPUT / source.name).write_text(
            json.dumps(sanitized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(source.name)


if __name__ == "__main__":
    main()
