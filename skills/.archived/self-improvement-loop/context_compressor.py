#!/usr/bin/env python3
"""
Context Compressor - 完整实现
参考 Hermes Agent context_compressor.py

功能：
- LLM 总结（结构化摘要）
- 迭代更新
- 工具输出修剪
- 按比例分配 token
- 上下文保护（头部+尾部）
- 工具对清理
- 边界对齐
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Constants
SUMMARY_PREFIX = (
    "[CONTEXT COMPACTION] Earlier turns in this conversation were compacted "
    "to save context space. The summary below describes work that was "
    "already completed, and the current session state may still reflect "
    "that work (for example, files may already be changed). Use the summary "
    "and the current state to continue from where things left off, and "
    "avoid repeating work:"
)

_MIN_SUMMARY_TOKENS = 2000
_SUMMARY_RATIO = 0.20
_SUMMARY_TOKENS_CEILING = 12_000
_PRUNED_TOOL_PLACEHOLDER = "[Old tool output cleared to save context space]"
_CHARS_PER_TOKEN = 4


@dataclass
class CompressionResult:
    """压缩结果"""
    messages: List[Dict[str, Any]]
    original_count: int
    compressed_count: int
    pruned_tool_results: int
    summary_generated: bool
    tokens_saved: int = 0


class ContextCompressor:
    """上下文压缩器"""

    def __init__(
        self,
        context_length: int = 128_000,
        threshold_percent: float = 0.50,
        protect_first_n: int = 3,
        protect_last_n: int = 20,
        summary_target_ratio: float = 0.20,
        quiet_mode: bool = False,
    ):
        self.context_length = context_length
        self.threshold_percent = threshold_percent
        self.protect_first_n = protect_first_n
        self.protect_last_n = protect_last_n
        self.summary_target_ratio = max(0.10, min(summary_target_ratio, 0.80))
        self.quiet_mode = quiet_mode

        self.threshold_tokens = int(self.context_length * threshold_percent)
        self.compression_count = 0

        # Token budgets
        target_tokens = int(self.threshold_tokens * self.summary_target_ratio)
        self.tail_token_budget = target_tokens
        self.max_summary_tokens = min(
            int(self.context_length * 0.05), _SUMMARY_TOKENS_CEILING,
        )

        self._previous_summary: Optional[str] = None

        if not quiet_mode:
            logger.info(
                "Context compressor initialized: context_length=%d "
                "threshold=%d (%.0f%%) target_ratio=%.0f%% tail_budget=%d",
                self.context_length, self.threshold_tokens,
                threshold_percent * 100, self.summary_target_ratio * 100,
                self.tail_token_budget,
            )

    # ------------------------------------------------------------------
    # Tool output pruning (cheap pre-pass, no LLM call)
    # ------------------------------------------------------------------

    def _prune_old_tool_results(
        self, messages: List[Dict[str, Any]], protect_tail_count: int,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Replace old tool result contents with a short placeholder."""
        if not messages:
            return messages, 0

        result = [m.copy() for m in messages]
        pruned = 0
        prune_boundary = len(result) - protect_tail_count

        for i in range(prune_boundary):
            msg = result[i]
            if msg.get("role") != "tool":
                continue
            content = msg.get("content", "")
            if not content or content == _PRUNED_TOOL_PLACEHOLDER:
                continue
            if len(content) > 200:
                result[i] = {**msg, "content": _PRUNED_TOOL_PLACEHOLDER}
                pruned += 1

        return result, pruned

    # ------------------------------------------------------------------
    # Serialization for summarization
    # ------------------------------------------------------------------

    def _serialize_for_summary(self, turns: List[Dict[str, Any]]) -> str:
        """Serialize conversation turns into labeled text for the summarizer."""
        parts = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content") or ""

            # Tool results: keep more content than before (3000 chars)
            if role == "tool":
                tool_id = msg.get("tool_call_id", "")
                if len(content) > 3000:
                    content = content[:2000] + "\n...[truncated]...\n" + content[-800:]
                parts.append(f"[TOOL RESULT {tool_id}]: {content}")
                continue

            # Assistant messages: include tool call names AND arguments
            if role == "assistant":
                if len(content) > 3000:
                    content = content[:2000] + "\n...[truncated]...\n" + content[-800:]
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    tc_parts = []
                    for tc in tool_calls:
                        if isinstance(tc, dict):
                            fn = tc.get("function", {})
                            name = fn.get("name", "?")
                            args = fn.get("arguments", "")
                            if len(args) > 500:
                                args = args[:400] + "..."
                            tc_parts.append(f"  {name}({args})")
                        else:
                            fn = getattr(tc, "function", None)
                            name = getattr(fn, "name", "?") if fn else "?"
                            tc_parts.append(f"  {name}(...)")
                    content += "\n[Tool calls:\n" + "\n".join(tc_parts) + "\n]"
                parts.append(f"[ASSISTANT]: {content}")
                continue

            # User and other roles
            if len(content) > 3000:
                content = content[:2000] + "\n...[truncated]...\n" + content[-800:]
            parts.append(f"[{role.upper()}]: {content}")

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Summary generation
    # ------------------------------------------------------------------

    def _compute_summary_budget(self, turns_to_summarize: List[Dict[str, Any]]) -> int:
        """Scale summary token budget with the amount of content being compressed."""
        content_tokens = sum(
            len(msg.get("content", "")) // _CHARS_PER_TOKEN + 10
            for msg in turns_to_summarize
        )
        budget = int(content_tokens * _SUMMARY_RATIO)
        return max(_MIN_SUMMARY_TOKENS, min(budget, self.max_summary_tokens))

    def _generate_summary(self, turns_to_summarize: List[Dict[str, Any]]) -> Optional[str]:
        """Generate a structured summary of conversation turns.
        
        Returns None if generation fails.
        """
        summary_budget = self._compute_summary_budget(turns_to_summarize)
        content_to_summarize = self._serialize_for_summary(turns_to_summarize)

        if self._previous_summary:
            prompt = f"""You are updating a context compaction summary. A previous compaction produced the summary below. New conversation turns have occurred since then and need to be incorporated.

PREVIOUS SUMMARY:
{self._previous_summary}

NEW TURNS TO INCORPORATE:
{content_to_summarize}

Update the summary using this exact structure. PRESERVE all existing information that is still relevant. ADD new progress. Move items from "In Progress" to "Done" when completed. Remove information only if it is clearly obsolete.

## Goal
[What the user is trying to accomplish — preserve from previous summary, update if goal evolved]

## Constraints & Preferences
[User preferences, coding style, constraints, important decisions — accumulate across compactions]

## Progress
### Done
[Completed work — include specific file paths, commands run, results obtained]
### In Progress
[Work currently underway]
### Blocked
[Any blockers or issues encountered]

## Key Decisions
[Important technical decisions and why they were made]

## Relevant Files
[Files read, modified, or created — with brief note on each. Accumulate across compactions.]

## Next Steps
[What needs to happen next to continue the work]

## Critical Context
[Any specific values, error messages, configuration details, or data that would be lost without explicit preservation]

Target ~{summary_budget} tokens. Be specific — include file paths, command outputs, error messages, and concrete values rather than vague descriptions."""
        else:
            prompt = f"""Create a structured handoff summary for a later assistant that will continue this conversation after earlier turns are compacted.

TURNS TO SUMMARIZE:
{content_to_summarize}

Use this exact structure:

## Goal
[What the user is trying to accomplish]

## Constraints & Preferences
[User preferences, coding style, constraints, important decisions]

## Progress
### Done
[Completed work — include specific file paths, commands run, results obtained]
### In Progress
[Work currently underway]
### Blocked
[Any blockers or issues encountered]

## Key Decisions
[Important technical decisions and why they were made]

## Relevant Files
[Files read, modified, or created — with brief note on each]

## Next Steps
[What needs to happen next to continue the work]

## Critical Context
[Any specific values, error messages, configuration details, or data that would be lost without explicit preservation]

Target ~{summary_budget} tokens. Be specific — include file paths, command outputs, error messages, and concrete values rather than vague descriptions."""

        # Note: In production, this would call an LLM API
        # For now, we generate a simple structured summary
        summary = self._generate_simple_summary(turns_to_summarize)
        self._previous_summary = summary
        return self._with_summary_prefix(summary)

    def _generate_simple_summary(self, turns: List[Dict[str, Any]]) -> str:
        """Generate a simple structured summary without LLM."""
        goal_parts = []
        decisions = []
        files = []
        actions = []

        for msg in turns:
            content = msg.get("content", "")
            role = msg.get("role", "")

            # Extract goals
            if role == "user":
                if len(content) > 20:
                    goal_parts.append(content[:200])

            # Extract actions and decisions
            if role == "assistant":
                # Look for file operations
                file_matches = re.findall(r'(?:read|write|create|edit|delete)\s+(?:file\s+)?([^\s,\.]+\.(?:py|md|txt|json|yaml|yml))', content, re.IGNORECASE)
                files.extend(file_matches)

                # Look for decisions
                if any(kw in content.lower() for kw in ["decide", "choose", "will do", "going to"]):
                    decisions.append(content[:200])

        summary_parts = ["## Goal"]
        if goal_parts:
            summary_parts.append(goal_parts[0])
        else:
            summary_parts.append("Continuing conversation")

        summary_parts.append("\n## Progress\n### Done")
        summary_parts.append("- Context compression performed")

        if files:
            summary_parts.append("\n## Relevant Files")
            for f in set(files)[:10]:
                summary_parts.append(f"- {f}")

        if decisions:
            summary_parts.append("\n## Key Decisions")
            for d in decisions[:5]:
                summary_parts.append(f"- {d}")

        summary_parts.append("\n## Next Steps")
        summary_parts.append("- Continue from compressed context")

        return "\n".join(summary_parts)

    @staticmethod
    def _with_summary_prefix(summary: str) -> str:
        """Add summary prefix."""
        text = (summary or "").strip()
        return f"{SUMMARY_PREFIX}\n{text}" if text else SUMMARY_PREFIX

    # ------------------------------------------------------------------
    # Tool-call / tool-result pair integrity helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_tool_call_id(tc) -> str:
        """Extract the call ID from a tool_call entry."""
        if isinstance(tc, dict):
            return tc.get("id", "")
        return getattr(tc, "id", "") or ""

    def _sanitize_tool_pairs(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fix orphaned tool_call / tool_result pairs after compression."""
        surviving_call_ids: set = set()
        for msg in messages:
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls") or []:
                    cid = self._get_tool_call_id(tc)
                    if cid:
                        surviving_call_ids.add(cid)

        result_call_ids: set = set()
        for msg in messages:
            if msg.get("role") == "tool":
                cid = msg.get("tool_call_id")
                if cid:
                    result_call_ids.add(cid)

        # Remove orphaned results
        orphaned_results = result_call_ids - surviving_call_ids
        if orphaned_results:
            messages = [
                m for m in messages
                if not (m.get("role") == "tool" and m.get("tool_call_id") in orphaned_results)
            ]
            if not self.quiet_mode:
                logger.info("Compression sanitizer: removed %d orphaned tool result(s)", len(orphaned_results))

        # Add stub results for orphaned calls
        missing_results = surviving_call_ids - result_call_ids
        if missing_results:
            patched: List[Dict[str, Any]] = []
            for msg in messages:
                patched.append(msg)
                if msg.get("role") == "assistant":
                    for tc in msg.get("tool_calls") or []:
                        cid = self._get_tool_call_id(tc)
                        if cid in missing_results:
                            patched.append({
                                "role": "tool",
                                "content": "[Result from earlier conversation — see context summary above]",
                                "tool_call_id": cid,
                            })
            messages = patched
            if not self.quiet_mode:
                logger.info("Compression sanitizer: added %d stub tool result(s)", len(missing_results))

        return messages

    # ------------------------------------------------------------------
    # Boundary alignment
    # ------------------------------------------------------------------

    def _align_boundary_forward(self, messages: List[Dict[str, Any]], idx: int) -> int:
        """Push a compress-start boundary forward past any orphan tool results."""
        while idx < len(messages) and messages[idx].get("role") == "tool":
            idx += 1
        return idx

    def _align_boundary_backward(self, messages: List[Dict[str, Any]], idx: int) -> int:
        """Pull a compress-end boundary backward to avoid splitting tool groups."""
        if idx <= 0 or idx >= len(messages):
            return idx
        check = idx - 1
        while check >= 0 and messages[check].get("role") == "tool":
            check -= 1
        if check >= 0 and messages[check].get("role") == "assistant" and messages[check].get("tool_calls"):
            idx = check
        return idx

    # ------------------------------------------------------------------
    # Tail protection by token budget
    # ------------------------------------------------------------------

    def _find_tail_cut_by_tokens(
        self, messages: List[Dict[str, Any]], head_end: int,
        token_budget: int | None = None,
    ) -> int:
        """Walk backward from the end of messages, accumulating tokens until
        the budget is reached."""
        if token_budget is None:
            token_budget = self.tail_token_budget
        n = len(messages)
        min_tail = self.protect_last_n
        accumulated = 0
        cut_idx = n

        for i in range(n - 1, head_end - 1, -1):
            msg = messages[i]
            content = msg.get("content") or ""
            msg_tokens = len(content) // _CHARS_PER_TOKEN + 10
            for tc in msg.get("tool_calls") or []:
                if isinstance(tc, dict):
                    args = tc.get("function", {}).get("arguments", "")
                    msg_tokens += len(args) // _CHARS_PER_TOKEN
            if accumulated + msg_tokens > token_budget and (n - i) >= min_tail:
                break
            accumulated += msg_tokens
            cut_idx = i

        # Ensure we protect at least protect_last_n messages
        fallback_cut = n - min_tail
        if cut_idx > fallback_cut:
            cut_idx = fallback_cut

        if cut_idx <= head_end:
            cut_idx = fallback_cut

        cut_idx = self._align_boundary_backward(messages, cut_idx)
        return max(cut_idx, head_end + 1)

    # ------------------------------------------------------------------
    # Main compression entry point
    # ------------------------------------------------------------------

    def compress(self, messages: List[Dict[str, Any]]) -> CompressionResult:
        """Compress conversation messages by summarizing middle turns."""
        n_messages = len(messages)
        if n_messages <= self.protect_first_n + self.protect_last_n + 1:
            if not self.quiet_mode:
                logger.warning(
                    "Cannot compress: only %d messages (need > %d)",
                    n_messages,
                    self.protect_first_n + self.protect_last_n + 1,
                )
            return CompressionResult(
                messages=messages,
                original_count=n_messages,
                compressed_count=n_messages,
                pruned_tool_results=0,
                summary_generated=False,
            )

        # Phase 1: Prune old tool results
        messages, pruned_count = self._prune_old_tool_results(
            messages, protect_tail_count=self.protect_last_n * 3,
        )
        if pruned_count and not self.quiet_mode:
            logger.info("Pre-compression: pruned %d old tool result(s)", pruned_count)

        # Phase 2: Determine boundaries
        compress_start = self.protect_first_n
        compress_start = self._align_boundary_forward(messages, compress_start)

        compress_end = self._find_tail_cut_by_tokens(messages, compress_start)

        if compress_start >= compress_end:
            return CompressionResult(
                messages=messages,
                original_count=n_messages,
                compressed_count=n_messages,
                pruned_tool_results=pruned_count,
                summary_generated=False,
            )

        turns_to_summarize = messages[compress_start:compress_end]

        if not self.quiet_mode:
            logger.info(
                "Summarizing turns %d-%d (%d turns), protecting %d head + %d tail messages",
                compress_start + 1,
                compress_end,
                len(turns_to_summarize),
                compress_start,
                n_messages - compress_end,
            )

        # Phase 3: Generate structured summary
        summary = self._generate_summary(turns_to_summarize)

        # Phase 4: Assemble compressed message list
        compressed = []
        for i in range(compress_start):
            msg = messages[i].copy()
            if i == 0 and msg.get("role") == "system" and self.compression_count == 0:
                msg["content"] = (
                    (msg.get("content") or "")
                    + "\n\n[Note: Some earlier conversation turns have been compacted into a handoff summary to preserve context space.]"
                )
            compressed.append(msg)

        if summary:
            compressed.append({"role": "user", "content": summary})

        for i in range(compress_end, n_messages):
            compressed.append(messages[i].copy())

        self.compression_count += 1

        # Sanitize tool pairs
        compressed = self._sanitize_tool_pairs(compressed)

        # Estimate tokens saved
        original_tokens = sum(len(m.get("content", "")) for m in messages) // _CHARS_PER_TOKEN
        compressed_tokens = sum(len(m.get("content", "")) for m in compressed) // _CHARS_PER_TOKEN
        tokens_saved = max(0, original_tokens - compressed_tokens)

        if not self.quiet_mode:
            logger.info(
                "Compressed: %d -> %d messages (~%d tokens saved)",
                n_messages,
                len(compressed),
                tokens_saved,
            )

        return CompressionResult(
            messages=compressed,
            original_count=n_messages,
            compressed_count=len(compressed),
            pruned_tool_results=pruned_count,
            summary_generated=summary is not None,
            tokens_saved=tokens_saved,
        )

    def should_compress(self, messages: List[Dict[str, Any]]) -> bool:
        """Check if compression should be triggered."""
        total_chars = sum(len(m.get("content", "")) for m in messages)
        estimated_tokens = total_chars // _CHARS_PER_TOKEN
        return estimated_tokens >= self.threshold_tokens

    def get_status(self) -> Dict[str, Any]:
        """Get current compression status."""
        return {
            "context_length": self.context_length,
            "threshold_tokens": self.threshold_tokens,
            "threshold_percent": self.threshold_percent * 100,
            "compression_count": self.compression_count,
            "tail_token_budget": self.tail_token_budget,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Main function."""
    import sys

    compressor = ContextCompressor()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            status = compressor.get_status()
            print("Context Compressor Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")

        elif command == "test":
            # Test compression with sample messages
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, can you help me with Python?"},
                {"role": "assistant", "content": "Of course! What do you need help with?"},
                {"role": "user", "content": "I need to write a function that sorts a list."},
                {"role": "assistant", "content": "Here's a simple sorting function..."},
                {"role": "user", "content": "Thanks! Now can you help me with error handling?"},
                {"role": "assistant", "content": "Sure! Here's how to add error handling..."},
                {"role": "user", "content": "Great, now I need to test it."},
                {"role": "assistant", "content": "Let's write some unit tests..."},
            ]

            result = compressor.compress(messages)
            print(f"Compression test:")
            print(f"  Original: {result.original_count} messages")
            print(f"  Compressed: {result.compressed_count} messages")
            print(f"  Pruned: {result.pruned_tool_results} tool results")
            print(f"  Summary: {result.summary_generated}")
            print(f"  Tokens saved: ~{result.tokens_saved}")

        else:
            print(f"Unknown command: {command}")
    else:
        print("Context Compressor - Usage:")
        print("  context_compressor.py status  # Show status")
        print("  context_compressor.py test    # Run test compression")


if __name__ == "__main__":
    main()
