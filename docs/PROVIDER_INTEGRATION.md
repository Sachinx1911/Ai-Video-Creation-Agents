# Provider Integration

Status: **no provider is integrated or verified yet.** Provider selection happens at the start of Phase 3, after the owner confirms which accounts and budget exist (REQUIREMENTS Q-01). Every provider fact below must be re-checked against current official documentation at integration time; nothing here is a verified API claim.

## Capability interfaces (planned)

`ScriptGeneration`, `ImageGeneration`, `VideoGeneration`, `SpeechSynthesis`, `SpeechRecognition`, `Embeddings`. An adapter declares the subset it supports plus limits (max duration, aspect ratios, reference-image support, async/sync, rate limits). Requests outside declared limits are rejected before any paid call.

## Candidate categories (UNVERIFIED — to evaluate in Phase 3)

| Capability | Cloud candidates to evaluate | Local candidates to evaluate | Notes for this machine (RTX 3050, 4 GB VRAM) |
|---|---|---|---|
| Reasoning / script | Anthropic Claude API, others | Ollama with small quantised models | Local 3–8B models possible on CPU/GPU, quality lower for Marathi |
| Image | Major hosted image APIs | Stable-Diffusion-class models | 4 GB VRAM: slow, low-res; cloud recommended |
| Video | Hosted text/image-to-video APIs | — | Not feasible locally at useful quality |
| TTS (Marathi) | Cloud TTS with Marathi voices | Open TTS models with Indic support | Must test real Marathi samples before choosing |
| ASR (subtitle alignment) | Cloud ASR | Whisper-family models | Local Whisper small/medium feasible |

## Rules
- Keys only in `.env` / secret store, loaded as `SecretStr`; never sent to the web app; redacted in logs.
- Store the provider's remote job id **before** polling so a restart resumes polling instead of re-submitting (no double charge).
- Use provider idempotency keys where the provider supports them.
- Real-provider tests are opt-in (`RUN_PROVIDER_TESTS=1`) and reported separately from mocked tests.
