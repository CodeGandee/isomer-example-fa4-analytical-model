# Chat Log Analysis

This directory contains extracted timelines from the Kimi Code sessions copied into `../raw/`. The primary reading surface is `merged-timeline.md`, which merges all direct user-level events across sessions in chronological order.

Each timeline keeps only direct user-level events from `agents/main/wire.jsonl`: typed user prompts, user-slash skill activations, cancel/interruption events, and the final visible assistant response for the matched turn when Kimi recorded one.

Hidden thinking, tool calls, tool results, injected reminders, background task notifications, model-invoked skill calls, and subagent-internal conversations are intentionally omitted from these analysis files. The full event streams remain available under `../raw/`.

## Files

| File | Purpose |
| --- | --- |
| `merged-timeline.md` | Single chronological timeline across all copied sessions. Event headings use `Event <index> - <Short Title>`, followed by a blockquoted `Time` and `Session` reference. |

## Per-Session Extracts

| Session | Created | Updated | Direct prompts | User actions | Cancels | Matched events | Analysis |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `session_62c9b0be-1923-4da6-9a58-9a2a66f94220` | 2026-07-04T10:00:55.336Z | 2026-07-04T10:49:48.374Z | 14 | 2 | 0 | 16 | `session_62c9b0be-1923-4da6-9a58-9a2a66f94220.md` |
| `session_08579621-605a-4231-aa58-89f103b78ee8` | 2026-07-04T12:15:35.022Z | 2026-07-05T16:32:15.853Z | 16 | 6 | 0 | 22 | `session_08579621-605a-4231-aa58-89f103b78ee8.md` |
| `session_8794124c-4c0c-4042-82f5-0586b287de3c` | 2026-07-05T17:31:47.204Z | 2026-07-06T16:16:31.735Z | 56 | 13 | 7 | 62 | `session_8794124c-4c0c-4042-82f5-0586b287de3c.md` |

## Extraction Notes

- `User Prompt:` comes from `context.append_message` records with `message.role == "user"` and `message.origin.kind == "user"`.
- `User Action:` includes user-slash skill activations from `message.origin.kind == "skill_activation"` with `trigger == "user-slash"`, plus cancel/interruption records from `turn.cancel`. Model-invoked skill calls are internal AI actions and are omitted from this direct-user timeline.
- `AI:` is the text from visible `content.part` events in the matched turn whose step ended with `finishReason == "end_turn"`. If the turn never reached `end_turn`, the file says so and shows any visible assistant text that was recorded before the turn stopped or continued.
- Matching first checks whether the user event occurred during an active main-agent turn, which captures user steers and interrupts. Otherwise it uses the next nearby main-agent turn. Cancellation events remain standalone actions.
