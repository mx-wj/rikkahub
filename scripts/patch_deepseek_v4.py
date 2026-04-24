#!/usr/bin/env python3
from pathlib import Path

api = Path("ai/src/main/java/me/rerere/ai/provider/providers/openai/ChatCompletionsAPI.kt")
s = api.read_text()

old = "addAssistantMessages(message, index > lastUserMessageIndex)"
new = "addAssistantMessages(message, true)"

if new in s:
    print("[OK] DeepSeek reasoning history patch already applied")
elif old in s:
    api.write_text(s.replace(old, new, 1))
    print("[OK] Applied DeepSeek reasoning history patch")
else:
    print("[WARN] target line not found; maybe upstream changed it")

reg = Path("ai/src/main/java/me/rerere/ai/registry/ModelRegistry.kt")
rs = reg.read_text()
if "DEEPSEEK_V4_PRO" in rs and "DEEPSEEK_V4_FLASH" in rs:
    print("[OK] DeepSeek V4 model registry exists")
else:
    print("[WARN] DeepSeek V4 model registry not found; check upstream manually")
