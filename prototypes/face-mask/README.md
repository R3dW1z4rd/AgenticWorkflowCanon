# Portrait Mask: concept, architecture and prototype

> A user describes a character. The app paints a retro RPG-style portrait of it (think Baldur's Gate 1),
> then turns it into a live "mask" that follows the user's face on webcam and can be used in calls.

This folder has two things:

1. **This document.** It breaks the idea into parts, lists the realistic technical options, recommends one, and names the risks.
2. **A working prototype of the riskiest part** (steps 3–4): [`index.html`](./index.html) + [`mask.js`](./mask.js).
   It maps any painted portrait onto your live face in the browser, at real-time frame rates, with no server.

---

## 1. The pipeline at a glance

```
 ┌──────────────┐   ┌────────────────────┐   ┌───────────────────────┐   ┌──────────────────────┐
 │ 1. Narrative │──▶│ 2. Portrait gen    │──▶│ 3. Portrait ➜ mask    │──▶│ 4. Live use          │
 │  (free text) │   │  (style-locked     │   │  (landmarks / UVs,    │   │  (webcam tracking,   │
 │              │   │   image model)     │   │   later: 3D head fit) │   │   render, WebRTC)    │
 └──────┬───────┘   └─────────┬──────────┘   └───────────┬───────────┘   └──────────┬───────────┘
        │ LLM → character     │ server/GPU               │ once per portrait        │ on-device,
        │ sheet (JSON)        │ (~5–20 s)                │ (client or server)       │ every frame
        ▼                     ▼                          ▼                          ▼
   CharacterSheet      portrait.png +             MaskAsset {texture,          MediaStream /
                       mask_texture.png           uvs, mesh, rig}              blendshape stream
```

The key insight is that **steps 1–3 happen once, offline, and step 4 happens every frame, on the user's device.**
Build and validate them separately. The shared contract between them is the `MaskAsset`.

---

## 2. Step by step

### Step 1: Narrative → character sheet

Don't pass the user's prose straight to the image model. First use an LLM (e.g. Claude, with structured
output) to turn it into a **character sheet**. That gives you consistent prompts, a record you can edit and
re-roll, and one place to enforce content rules.

```jsonc
{
  "name": "Varra Ashgrove",
  "ancestry": "half-elf", "apparent_age": "late 30s", "gender_presentation": "feminine",
  "face": { "shape": "angular", "skin": "weathered olive", "eyes": "grey, heavy-lidded",
            "marks": ["scar through left eyebrow"], "facial_hair": null },
  "hair": { "color": "ash blonde", "style": "cropped, uneven" },
  "headwear_or_accessories": ["iron circlet"],   // anything that covers the forehead matters for mapping
  "expression": "neutral",                        // forced neutral for the mask texture
  "palette_mood": "cold, desaturated, torchlit",
  "safety": { "depicts_real_person": false }      // gate: refuse likenesses of real people
}
```

Let the user edit the sheet in the UI ("make the scar the other side") before generating. It is cheaper than re-rolling images.

### Step 2: Character sheet → speedpaint portrait

You're right that this needs lots of reference material. Two things need deciding up front:

**a) Where the style comes from (and the IP question).**
BG1 portraits are copyrighted game art. Training a model on them, or feeding them in as references, is fine for a
private experiment. It is a real legal and reputational risk for a product. The durable path is to **commission or
license ~40–150 original portraits "in the spirit of" late-90s CRPG speedpaints** (painterly, visible brushwork,
dark vignette, 3/4 bust). Then train a **style LoRA** on an open image model (SDXL/Flux-class) with those.
You own the look, and it becomes your brand.

Ways to steer style, weakest to strongest:

| Technique | Effort | Consistency | Notes |
|---|---|---|---|
| Prompting a hosted model ("oil speedpaint, 1998 CRPG portrait…") | none | low | Fine for a mood board, not for a product |
| Style reference / IP-Adapter with a few ref images | low | medium | Good for early prototypes |
| **Style LoRA trained on your own reference set** | medium | **high** | Recommended. Run via ComfyUI / Replicate / fal |
| Full fine-tune | high | high | Only if the LoRA plateaus |

**b) Generate two images, not one.**
A BG1-style portrait is usually a 3/4 view with a vignette. That is great to display, but bad for mapping onto a face.
For each character, generate:

1. **Display portrait**: the pretty 3/4 bust, shown in profiles and character sheets.
2. **Mask texture**: the *same* character, **frontal, neutral expression, eyes open, mouth closed, even lighting,
   hair off the face**. Use pose conditioning (ControlNet with a frontal face-landmark or OpenPose map) so the
   face lands in a known place. Keep identity consistent with the same seed, the character sheet and an
   identity adapter (IP-Adapter FaceID / InstantID-class) from the display portrait.

**Automatic QA gate.** After generation, run the same face-landmark model the client uses on the mask texture.
Reject and regenerate if no face is found, the yaw/pitch is off-frontal, or the eyes or mouth are open.
This one check stops most mapping failures before the user ever sees them.

### Step 3: 2D portrait → mask asset

This is the core technical choice. Four tiers, simplest first:

| Tier | Approach | Quality | Real-time on laptop/phone | Effort |
|---|---|---|---|---|
| **A. 2.5D mesh warp** *(the prototype)* | Detect the 468-point face mesh on the portrait → those points become texture coordinates. Every frame, draw the same mesh at the live positions. | Good for frontal ±30°. Expressions come "for free" (blinks, mouth). No real back or side of head. | ✅ Easily | Days |
| **B. Morphable-model fit** | Fit a parametric 3D head (FLAME-family; DECA/EMOCA/SMIRK-style single-image regressors) to the portrait, then bake its texture. Drive it with the 52 ARKit-style blendshapes + head pose from the live tracker. | Proper 3D: better side views, lighting, stable silhouette | ✅ (a few thousand verts) | Weeks |
| **C. Image-to-3D generator** | Use a single-image 3D generator (TRELLIS / Hunyuan3D / TripoSR-class) to get a full head, including hair, then auto-rig it with blendshapes. | Full head and hair, most "3D" | ✅ once rigged | Rigging is the hard part |
| **D. Neural / Gaussian avatars** | Gaussian-splat head avatars, neural renderers | Best realism | ⚠️ Research-grade on consumer hardware | Research |

**Recommendation.** Ship **A** first. It shows what the product feels like in days, and it is what the
prototype here does. Move to **B** once you need side angles and lighting. Look at **C** for hair and full
heads later. For a painterly, stylized look, A and B usually hold up better than photoreal approaches: a
speedpaint doesn't have to survive a 90° turn to feel right.

Proposed `MaskAsset` contract, so step 4 doesn't care which tier produced it:

```jsonc
{
  "version": 1,
  "tier": "mesh-warp",                  // "mesh-warp" | "flame" | "rigged-mesh"
  "texture": "mask_texture.png",
  "uvs": "landmark_uvs.json",           // tier A: 468 (x,y) in texture space
  "mesh": null, "blendshapes": null,    // tiers B/C
  "hair_extension": 0.35, "feather": 0.6
}
```

### Step 4: Live use in calls

Per frame, on the user's device:

1. **Track**: MediaPipe Face Landmarker (478 landmarks + 52 blendshapes + head transform), about 30–60 fps in the browser via WASM/WebGL.
2. **Render**: WebGL/Three.js draws the mask over (or instead of) the camera frame.
3. **Send**, with three options:

| Option | How | Pros | Cons |
|---|---|---|---|
| **In-app calls: send video** | `canvas.captureStream()` → WebRTC (LiveKit / Daily / mediasoup SFU) | Simple; any client can watch | Bandwidth as normal video |
| **In-app calls: send parameters** | Send head pose + 52 blendshapes (~1 KB/frame over a data channel); each viewer renders the mask locally | Tiny bandwidth, crisp at any resolution, **the real face never leaves the device** | Viewers need the app and the mask asset |
| **Other apps (Zoom/Discord/Meet)** | Virtual camera driver in a desktop app (Electron + OBS-style virtual cam, or native) | Works everywhere | Needs a native install, per-OS work |

You asked for "simply opening the camera inside the app", which means **in-app calls**. Start with option 1
because it is a single line in the prototype (`captureStream`). Option 2 is a strong differentiator for privacy
and bandwidth once the app has its own call UI.

---

## 3. Hard problems to plan for

- **Stylized faces confuse landmark detectors.** Very painterly or heavily vignetted portraits may yield no
  landmarks. Mitigate with the frontal "mask texture" (step 2b), the QA gate, and a manual fit fallback
  (already in the prototype).
- **Mouth interior and eyes.** When the user opens their mouth, the painted closed lips stretch. Options: let
  the real mouth show through (prototype toggle), or paint an inner-mouth texture (tier B handles this better).
  The eyes have the same choice. Letting the real eyes show through often looks surprisingly "alive".
- **Hair and silhouette.** The tracked mesh ends at the face oval. The prototype extends it with outer rings
  so the painted hair follows the head, which works for moderate motion. For real hair you need tier C,
  or a separate "hair card" billboard that follows head pose, plus person segmentation to hide real hair.
- **Occlusions** (hands, glasses, mics). Add a segmentation mask to clip the mask where something covers the face.
- **Lighting mismatch.** A torchlit painting on a daylit webcam frame looks pasted on. Either stylize the whole
  frame (dim/paint-filter the background, as the prototype does) or relight the mask (tier B).
- **Latency budget.** Aim for under 50 ms from capture to rendered frame. Tracking takes about 5–15 ms on laptops;
  keep rendering cheap and avoid round trips to a server per frame.
- **Trust and safety.** "Describe a character" can become "describe a real person", which is deepfake territory.
  Gate at the character-sheet stage (`depicts_real_person`), refuse uploads of real-person photos as portraits in
  the product (the prototype's upload is for testing), moderate generated images, and watermark or label streams
  as masked.
- **Privacy and biometrics.** Face geometry is biometric data under GDPR, BIPA and similar laws. Keep tracking
  on-device and never store live landmarks. The architecture above lets the product make that claim honestly.

---

## 4. Suggested milestones

| # | Milestone | Exit criterion |
|---|---|---|
| **M0** | *Mask-warp prototype* (this folder) | Any frontal portrait follows your face live at ≥ 30 fps |
| M1 | Style bible + reference set | 40–150 commissioned or licensed reference portraits; style LoRA v1 produces on-brand busts |
| M2 | Narrative → sheet → two images | 8/10 generated mask textures pass the landmark QA gate without manual fixes |
| M3 | In-app 1:1 call | Two browsers in a masked call via WebRTC (LiveKit), mask asset loaded from the server |
| M4 | Tier B (3D head fit) *or* parameter streaming | Decide from M3 user feedback: "looks better at angles" vs. "bandwidth/privacy" |

Suggested stack for M1–M3: a Next.js web app, an LLM for step 1, ComfyUI (self-hosted GPU) or a hosted
inference API for step 2, MediaPipe + Three.js on the client, and LiveKit for calls.

---

## 5. Running the prototype

The page needs to be served over `http://localhost` or HTTPS, because browsers only allow camera access there.

```bash
cd prototypes/face-mask
python3 -m http.server 8000      # or: npx serve .
# open http://localhost:8000
```

1. **Start camera.**
2. **Upload portrait image**: any frontal painted face. Or click **Test: snapshot me** to use a posterized
   photo of yourself, which is handy for checking tracking without art.
3. Adjust the controls: **Head extension** carries painted hair beyond the face, **Paint eyes & mouth** switches
   between painted and real eyes/mouth, **Background** dims the real room, and the **Fit** sliders align portraits
   where the face couldn't be auto-detected.
4. **Start output MediaStream** shows the exact stream a WebRTC call would send.

How it works: the face mesh is detected once on the portrait (texture coordinates) and every frame on the
webcam (positions). Drawing the mesh with live positions and portrait UVs warps the painting onto your face.
It is about 350 lines of JavaScript, WebGL and MediaPipe Tasks Vision from a CDN, with no build step.

**Verified:** in headless Chromium with a fake camera fed by a face image, the portrait was detected, warped
onto the live face at a different position and scale, the hair-extension rings and landmark overlay rendered,
and `captureStream()` produced a 640×480 stream with no page errors. It has not yet been tried on real webcams,
real painted portraits or mobile devices. That is the next thing to check.
