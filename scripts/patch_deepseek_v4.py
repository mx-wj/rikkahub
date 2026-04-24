#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

MODEL_REGISTRY = ROOT / "ai/src/main/java/me/rerere/ai/registry/ModelRegistry.kt"
CHAT_COMPLETIONS = ROOT / "ai/src/main/java/me/rerere/ai/provider/providers/openai/ChatCompletionsAPI.kt"


def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def patch_model_registry() -> bool:
    text = read(MODEL_REGISTRY)
    original = text

    v4_defs = '''
    private val DEEPSEEK_V4_FLASH = defineModel {
        tokens("deepseek", "v", "4", "flash")
        toolReasoningAbility()
    }

    private val DEEPSEEK_V4_PRO = defineModel {
        tokens("deepseek", "v", "4", "pro")
        toolReasoningAbility()
    }
'''

    if "DEEPSEEK_V4_PRO" not in text:
        marker = '''    private val DEEPSEEK_REASONER = defineModel {
        tokens("deepseek", "reasoner")
        toolReasoningAbility()
    }
'''
        if marker in text:
            text = text.replace(marker, marker + v4_defs, 1)
        else:
            marker = '''    private val DEEPSEEK_V3_2 = defineModel {
        tokens("deepseek", "v", "3", "2")
        toolReasoningAbility()
    }
'''
            if marker not in text:
                raise RuntimeError("Cannot find DeepSeek model block in ModelRegistry.kt")
            text = text.replace(marker, marker + v4_defs, 1)

    if "DEEPSEEK_V4_PRO," not in text:
        marker = "        DEEPSEEK_REASONER,\n"
        if marker in text:
            text = text.replace(
                marker,
                marker + "        DEEPSEEK_V4_FLASH,\n        DEEPSEEK_V4_PRO,\n",
                1,
            )
        else:
            marker = "        DEEPSEEK_V3_2,\n"
            if marker not in text:
                raise RuntimeError("Cannot find DeepSeek list entry in ALL_MODELS")
            text = text.replace(
                marker,
                marker + "        DEEPSEEK_V4_FLASH,\n        DEEPSEEK_V4_PRO,\n",
                1,
            )

    if text != original:
        write(MODEL_REGISTRY, text)
        return True
    return False


def patch_chat_completions() -> bool:
    text = read(CHAT_COMPLETIONS)
    original = text

    # DeepSeek V4 thinking API: {"thinking":{"type":"enabled/disabled"}} + reasoning_effort.
    # Release 2.1.9 does not have this host branch; master has it.
    if '"api.deepseek.com"' not in text:
        marker = '''                "api.moonshot.cn" -> {
                    put("thinking", buildJsonObject {
                        put("type", if (!level.isEnabled) "disabled" else "enabled")
                    })
                }

                else -> {
'''
        replacement = '''                "api.moonshot.cn" -> {
                    put("thinking", buildJsonObject {
                        put("type", if (!level.isEnabled) "disabled" else "enabled")
                    })
                }

                "api.deepseek.com" -> {
                    put("thinking", buildJsonObject {
                        put("type", if (!level.isEnabled) "disabled" else "enabled")
                    })
                    if (level.isEnabled && level != ReasoningLevel.AUTO) {
                        put("reasoning_effort", level.effort)
                    }
                }

                else -> {
'''
        if marker not in text:
            raise RuntimeError("Cannot find reasoning provider switch insertion point in ChatCompletionsAPI.kt")
        text = text.replace(marker, replacement, 1)

    # DeepSeek thinking + tool calls requires preserving reasoning_content in later turns.
    # Upstream master currently preserves reasoning for every assistant message.
    old_build_messages = '''    private fun buildMessages(messages: List<UIMessage>) = buildJsonArray {
        val filteredMessages = messages.filter { it.isValidToUpload() }
        val lastUserMessageIndex = filteredMessages.indexOfLast { it.role == MessageRole.USER }
        filteredMessages.forEachIndexed { index, message ->
            if (message.role == MessageRole.ASSISTANT) {
                addAssistantMessages(message, index > lastUserMessageIndex)
            } else {
                addNonAssistantMessage(message)
            }
        }
    }
'''
    new_build_messages = '''    private fun buildMessages(messages: List<UIMessage>) = buildJsonArray {
        val filteredMessages = messages.filter { it.isValidToUpload() }
        filteredMessages.forEach { message ->
            if (message.role == MessageRole.ASSISTANT) {
                addAssistantMessages(message, includeReasoning = true)
            } else {
                addNonAssistantMessage(message)
            }
        }
    }
'''
    if "addAssistantMessages(message, includeReasoning = true)" not in text:
        if old_build_messages not in text:
            raise RuntimeError("Cannot find old buildMessages() block in ChatCompletionsAPI.kt")
        text = text.replace(old_build_messages, new_build_messages, 1)

    if text != original:
        write(CHAT_COMPLETIONS, text)
        return True
    return False


def main() -> int:
    changed = []
    if patch_model_registry():
        changed.append(str(MODEL_REGISTRY.relative_to(ROOT)))
    if patch_chat_completions():
        changed.append(str(CHAT_COMPLETIONS.relative_to(ROOT)))

    if changed:
        print("Patched:")
        for item in changed:
            print(f"  - {item}")
    else:
        print("Already patched; no changes needed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"patch_deepseek_v4.py failed: {exc}", file=sys.stderr)
        raise
