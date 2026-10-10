# Agent Specifications

Status: **design only** — no agent is implemented in Phase 1. Every agent:

- has a versioned Pydantic input and output contract (`schema_version`),
- runs as a job (or set of jobs) through the job queue, never inside an HTTP request,
- returns structured output or raises a typed `AgentError(category, message, retryable)`,
- is complete only when its output passes schema validation **and** its domain checks below,
- treats LLM/provider output as untrusted data (validated, never executed).

| # | Agent | Input | Output | Completion criteria | Phase |
|---|---|---|---|---|---|
| 1 | Orchestrator | ProjectBrief, workflow config | WorkflowRun (DAG of tasks) | All required tasks succeeded, final QA passed | 5 |
| 2 | Research | ProjectBrief, optional user sources | ResearchBrief: objective, audience, `claims[] {text, status: verified/assumed/creative, sources[], confidence}`, contradictions, open questions | Every `verified` claim has ≥1 source; uncertainty reported | 2 |
| 3 | Script | ResearchBrief, duration, language, platform | ScriptVersion: hook, segments[] (text, est. seconds, pauses, pronunciation notes), CTA, total est. duration | Est. duration within ±15% of target (language speaking-rate table) | 2 |
| 4 | Storyboard | ScriptVersion, style | Scenes[] with all §4.4 fields, each linked to a script segment id | Coverage: every segment mapped; durations sum to target ± tolerance | 2 |
| 5 | Visual Director | Brief, Storyboard | StyleBible: palette, lighting, lens, characters/locations refs, continuity rules; per-scene prompt blocks | Style bible referenced by every scene prompt | 2 |
| 6 | Image Generation | Scene + StyleBible + refs, provider choice | Asset(image) versions | File received, decodes, dimensions/aspect correct | 3 |
| 7 | Video Generation | Scene + start/end frame refs | Asset(video) versions | Clip received, probed: duration, resolution, fps valid | 3 |
| 8 | Voice-over | Script segments, voice settings | Asset(voice) per segment + measured durations | Audio decodes, duration measured, not silent | 3 |
| 9 | Audio / Sound Design | Voice assets, music/SFX library (licensed) | Mix plan (tracks, gains, ducking, fades) | Peak ≤ −1 dBTP, integrated loudness in target range | 4 |
| 10 | Editing | Storyboard, assets, mix plan | TimelineSpec (validated) | No missing refs, no negative/unintended gaps, A/V lengths consistent | 4 |
| 11 | QA | Rendered export, timeline, subtitles | QAReport (pass/warn/fail per check, affected scene) | Report persisted; failures mapped to stage/scene | 5 |
| 12 | Publishing Metadata | Script, brief, platform | Title, description, caption, hashtags, cover brief, SRT | Platform length limits respected; labelled "not published" | 5 |

Detailed field-level contracts are written when each agent's phase is approved.
