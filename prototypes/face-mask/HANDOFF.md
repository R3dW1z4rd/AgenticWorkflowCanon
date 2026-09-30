# Handoff: RPG Masks

*Session handoff so work can resume in a fresh repo. Written 2026-09-30.*

## The idea

1. The user writes a narrative description of their character.
2. The app generates a portrait in a speedpaint style, similar to Baldur's Gate 1 portraits.
3. The portrait is turned into a "mask" mapped onto the user's face on webcam.
4. The user wears that mask in online interactions by opening their camera in the app.

Full concept, architecture, options and risks: [`README.md`](./README.md).

## Current state

- **M0 prototype working** (`index.html` + `mask.js`, ~430 lines, no build step, MediaPipe Tasks Vision 0.10.14 + WebGL from a CDN).
  The owner has run it on their Mac with a real webcam and portraits: "it's amazing".
- Technique: "2.5D mesh warp". The 468 face landmarks are detected once on the portrait (texture UVs) and every frame on the
  webcam (positions). The mesh is drawn with live positions and portrait UVs. Extra outer rings carry hair beyond the face
  oval. The eye/mouth holes can be painted or left to show the real ones. `canvas.captureStream()` gives the output MediaStream.
- Run locally: `python3 -m http.server 8000 --bind 127.0.0.1` from the project folder, then open http://localhost:8000.
  The server must start *inside* the project folder (it once started in `/tmp` and listed the wrong directory).
- Owner's local copy: `~/Documents/AI_Tests/RPG_Masks` (copied from the old location; not yet a git clone).

## Where the code came from

It was first committed to `R3dW1z4rd/AgenticWorkflowCanon` on branch `claude/elegant-feynman-v6t0n2`, in `prototypes/face-mask/`.
That repo is an unrelated project (an architecture canon). Once this repo is set up, delete that branch; it was never merged.

## Decisions and findings so far

- **Start with tier A (2.5D warp).** Move to tier B (3D morphable-model fit, FLAME-family) only when side angles and lighting matter.
- **Style/IP:** don't build the product on actual BG1 art. Commission or license 40–150 original reference portraits and
  train a style LoRA on an open image model.
- **Generate two images per character:** a 3/4 display portrait, plus a frontal "mask texture" built for mapping.
- **Findings from the owner's tests with real portraits:** some map very well, others don't.
  - *Teeth / no teeth:* portraits with open, smiling mouths paint teeth over a closed real mouth; closed painted lips
    stretch when the user opens theirs.
  - *Forehead looks like a hat:* the Head extension rings stretch whatever is above the face oval (tall hair, headwear, background).
  - *General quality:* suffers with 3/4 poses, side lighting, sideways gaze, tilt, or hair/beard covering the face edges.
- **Proposed "mask-ready portrait" spec:** frontal (within ~5°), neutral expression, mouth closed, eyes open looking at the
  viewer, soft even lighting, fixed framing (face centred at about 50% of the width of a square image), face edges
  uncovered, plain background.
- **Proposed layers:** face (closed mouth) + mouth interior (drawn as far as the jaw opens) + hair/headwear with alpha, following head pose.
- **Enforcing the spec in generation:** pose control (ControlNet on MediaPipe face landmarks), fixed prompts, and an automatic
  QA gate that runs the same landmarker on each generated image (jawOpen, smile and eyeBlink blendshapes, head angle from
  the transformation matrix, face size and position) and regenerates on failure.
- **Google Meet / Zoom:** OBS Virtual Camera works today with no code. A Chrome extension that overrides getUserMedia covers
  Meet on the web (1–2 weeks). A Zoom App with camera mode needs verification. A native virtual camera
  (macOS CoreMediaIO Camera Extension + Windows) takes 1–2 months plus upkeep.

## Next steps (the owner hasn't chosen yet)

1. **Portrait checker** in the prototype: pass/fail per rule of the spec above. This explains now why a portrait works or
   not, and later becomes the generation QA gate.
2. **Mouth-interior layer**, which solves the teeth problem.
3. **Fail-closed:** when tracking is lost, never show the real face (today it shows the plain camera frame). This is a
   priority before any real use.
4. **"Output only" view** (not mirrored, no panel) to capture with OBS and try Meet/Zoom.
5. Extract the engine as a reusable module: `createPortraitMask({canvas})`, `setPortrait()`, `start(stream) → MediaStream`,
   plus self-hosting the WASM files and the model.

## Notes for the next agent

- **Testing without a webcam** (how M0 was verified): Playwright + Chromium with `--use-fake-device-for-media-stream
  --use-file-for-fake-video-capture=face.y4m` and a `.y4m` generated from a face image. The public-domain scikit-image
  "astronaut" photo, extracted from the wheel, worked well.
- In cloud sandboxes `cdn.jsdelivr.net` may be blocked. Intercept those requests with `context.route()` and serve the files
  from `npm pack @mediapipe/tasks-vision@0.10.14`. Do the same with the `.task` model downloaded with curl.
- The owner is non-technical in this area. Explain in plain language, and give full paths and exact commands.
