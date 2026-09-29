// Portrait Mask prototype (M0): "2.5D" mapping.
//
// Idea: the same 468-landmark face mesh is detected twice:
//   1. once on the painted portrait  -> used as texture coordinates (UVs)
//   2. every frame on the webcam     -> used as vertex positions
// Drawing the mesh with positions from (2) and UVs from (1) warps the painting
// onto the user's face and follows head pose, blinks and mouth movement.
// Everything runs on-device; no image or face data leaves the browser.

import { FaceLandmarker, FilesetResolver } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";

const WASM_URL = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm";
const MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

const N = 468; // mesh vertices (the model returns 478; the last 10 are irises)

// Ordered silhouette loop of the face mesh.
const FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377,
  152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109];

// The mesh has holes at the eyes and mouth. These ordered loops let us fill them
// so the painted eyes/mouth are drawn (toggleable: unfilled shows the real ones).
const HOLES = [
  [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],          // right eye
  [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466],       // left eye
  [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191], // inner lips
];

// Extra rings of vertices pushed outward from the face oval. They carry the
// portrait's hair/forehead/jaw area beyond the tracked face (relative scale per ring).
const RINGS = [0.22, 0.45];
const V = N + RINGS.length * FACE_OVAL.length;

// ---------- DOM ----------
const $ = (id) => document.getElementById(id);
const canvas = $("out"), video = $("cam"), statusEl = $("status");
const ui = {
  opacity: $("opacity"), feather: $("feather"), ext: $("ext"), fillHoles: $("fillHoles"),
  bg: $("bg"), debug: $("debug"), fitScale: $("fitScale"), fitX: $("fitX"), fitY: $("fitY"),
};
const setStatus = (msg) => { statusEl.textContent = msg; };

// ---------- State ----------
let videoLandmarker = null, imageLandmarker = null;
let liveLms = null;            // latest webcam landmarks
let refBase = null;            // portrait landmarks (normalized to portrait image), before fit sliders
let portraitSource = null;     // Image or Canvas
let uvDirty = true;

// ---------- Mesh topology (built once) ----------
function buildTopology() {
  const adj = Array.from({ length: N }, () => new Set());
  for (const { start, end } of FaceLandmarker.FACE_LANDMARKS_TESSELATION) {
    if (start < N && end < N) { adj[start].add(end); adj[end].add(start); }
  }
  const base = [];
  // Triangles = 3-cliques of the tessellation edge graph.
  for (let a = 0; a < N; a++) for (const b of adj[a]) if (b > a)
    for (const c of adj[b]) if (c > b && adj[a].has(c)) base.push(a, b, c);
  // Rings: stitch each loop to the next one outward.
  let inner = FACE_OVAL;
  RINGS.forEach((_, r) => {
    const outer = FACE_OVAL.map((_, i) => N + r * FACE_OVAL.length + i);
    for (let i = 0; i < inner.length; i++) {
      const j = (i + 1) % inner.length;
      base.push(inner[i], outer[i], inner[j], inner[j], outer[i], outer[j]);
    }
    inner = outer;
  });
  const holes = [];
  for (const loop of HOLES) for (let i = 1; i < loop.length - 1; i++) holes.push(loop[0], loop[i], loop[i + 1]);
  return { base, holes };
}

// Positions of ring vertices, derived from the oval (works for both live and reference points).
// pts: array of {x,y,z} normalized; returns array of {x,y,z} for ring vertices.
function ringPoints(pts, ext) {
  let cx = 0, cy = 0;
  for (const i of FACE_OVAL) { cx += pts[i].x; cy += pts[i].y; }
  cx /= FACE_OVAL.length; cy /= FACE_OVAL.length;
  let halfH = 0;
  for (const i of FACE_OVAL) halfH = Math.max(halfH, Math.abs(pts[i].y - cy));
  const out = [];
  RINGS.forEach((k, r) => {
    for (const i of FACE_OVAL) {
      const p = pts[i];
      // Extend more above the face (hair/crown) than below it (neck).
      const up = Math.max(0, (cy - p.y) / (halfH || 1));
      const s = 1 + ext * k * (0.6 + 0.9 * up);
      out.push({ x: cx + (p.x - cx) * s, y: cy + (p.y - cy) * s, z: (p.z || 0) + 0.02 * (r + 1) });
    }
  });
  return out;
}

// ---------- WebGL ----------
const gl = canvas.getContext("webgl", { premultipliedAlpha: false, depth: true, antialias: true });
if (!gl) throw new Error("WebGL not available");

function program(vsSrc, fsSrc) {
  const mk = (type, src) => {
    const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  };
  const p = gl.createProgram();
  gl.attachShader(p, mk(gl.VERTEX_SHADER, vsSrc)); gl.attachShader(p, mk(gl.FRAGMENT_SHADER, fsSrc));
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
  return p;
}

const bgProg = program(`
  attribute vec2 a_pos; varying vec2 v_uv;
  void main() { v_uv = vec2(a_pos.x * 0.5 + 0.5, 0.5 - a_pos.y * 0.5); gl_Position = vec4(a_pos, 0.999, 1.0); }`, `
  precision mediump float; uniform sampler2D u_tex; uniform float u_dim; varying vec2 v_uv;
  void main() { gl_FragColor = vec4(texture2D(u_tex, v_uv).rgb * u_dim, 1.0); }`);

const meshProg = program(`
  attribute vec3 a_pos; attribute vec2 a_uv; attribute float a_alpha;
  varying vec2 v_uv; varying float v_alpha;
  void main() {
    v_uv = a_uv; v_alpha = a_alpha;
    gl_Position = vec4(a_pos.xy, clamp(a_pos.z * 2.0, -0.99, 0.99), 1.0);
    gl_PointSize = 3.0;
  }`, `
  precision mediump float;
  uniform sampler2D u_tex; uniform float u_opacity; uniform bool u_debug;
  varying vec2 v_uv; varying float v_alpha;
  void main() {
    if (u_debug) { gl_FragColor = vec4(0.3, 1.0, 0.5, 1.0); return; }
    vec4 c = texture2D(u_tex, v_uv);
    gl_FragColor = vec4(c.rgb, c.a * v_alpha * u_opacity);
  }`);

function makeTexture() {
  const t = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, t);
  for (const [k, v] of [[gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE],
    [gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR]]) gl.texParameteri(gl.TEXTURE_2D, k, v);
  return t;
}
const videoTex = makeTexture(), portraitTex = makeTexture();

const quadBuf = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, quadBuf);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);

const posArr = new Float32Array(V * 3), uvArr = new Float32Array(V * 2), alphaArr = new Float32Array(V);
const posBuf = gl.createBuffer(), uvBuf = gl.createBuffer(), alphaBuf = gl.createBuffer(), idxBuf = gl.createBuffer();
let topo = null;

function uploadIndices() {
  topo = buildTopology();
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, idxBuf);
  gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array([...topo.base, ...topo.holes]), gl.STATIC_DRAW);
}

function attrib(prog, name, buf, size) {
  const loc = gl.getAttribLocation(prog, name);
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, size, gl.FLOAT, false, 0, 0);
  return loc;
}

// ---------- Reference (portrait) handling ----------
function fittedRef() {
  const s = +ui.fitScale.value, ox = +ui.fitX.value, oy = +ui.fitY.value;
  let cx = 0, cy = 0;
  for (let i = 0; i < N; i++) { cx += refBase[i].x; cy += refBase[i].y; }
  cx /= N; cy /= N;
  return refBase.map((p) => ({ x: cx + (p.x - cx) * s + ox, y: cy + (p.y - cy) * s + oy, z: p.z || 0 }));
}

function updateUVsAndAlpha() {
  const ext = +ui.ext.value, feather = +ui.feather.value;
  const ref = fittedRef();
  const rings = ringPoints(ref, ext);
  for (let i = 0; i < N; i++) { uvArr[2 * i] = ref[i].x; uvArr[2 * i + 1] = ref[i].y; alphaArr[i] = 1; }
  rings.forEach((p, k) => { uvArr[2 * (N + k)] = p.x; uvArr[2 * (N + k) + 1] = p.y; });
  // Fade toward the outermost loop so the painting blends into the background.
  const outer = ext > 0.001 ? RINGS.length : 0;
  for (const i of FACE_OVAL) alphaArr[i] = outer ? 1 : 1 - feather;
  RINGS.forEach((_, r) => {
    const a = 1 - feather * (r + 1) / RINGS.length;
    for (let j = 0; j < FACE_OVAL.length; j++) alphaArr[N + r * FACE_OVAL.length + j] = a;
  });
  gl.bindBuffer(gl.ARRAY_BUFFER, uvBuf); gl.bufferData(gl.ARRAY_BUFFER, uvArr, gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, alphaBuf); gl.bufferData(gl.ARRAY_BUFFER, alphaArr, gl.DYNAMIC_DRAW);
  uvDirty = false;
}

// When the portrait's face can't be detected (heavily stylized art), fall back to
// the user's current live face, centred in the portrait, and let them fine-tune with the fit sliders.
function manualRefFromLive(src) {
  const vw = video.videoWidth, vh = video.videoHeight, iw = src.width, ih = src.height;
  const pts = liveLms.slice(0, N).map((p) => [p.x * vw, p.y * vh, p.z]);
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const [x, y] of pts) { minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y); }
  const s = (0.5 * iw) / (maxX - minX), cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
  return pts.map(([x, y, z]) => ({ x: (iw / 2 + (x - cx) * s) / iw, y: (ih * 0.55 + (y - cy) * s) / ih, z }));
}

async function setPortrait(src, thumbUrl) {
  portraitSource = src;
  $("portraitThumb").src = thumbUrl; $("portraitThumb").style.display = "block";
  gl.bindTexture(gl.TEXTURE_2D, portraitTex);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src);
  for (const el of [ui.fitScale, ui.fitX, ui.fitY]) el.value = el.defaultValue;

  const res = imageLandmarker.detect(src);
  if (res.faceLandmarks.length) {
    refBase = res.faceLandmarks[0].slice(0, N);
    setStatus("Portrait face detected ✓");
  } else if (liveLms) {
    refBase = manualRefFromLive(src);
    setStatus("No face found in portrait: using manual fit. Adjust the Fit sliders.");
  } else {
    refBase = null;
    setStatus("No face found in portrait. Start the camera, face it, then load the portrait again.");
  }
  uvDirty = true;
}

// ---------- Inputs ----------
$("upload").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const url = URL.createObjectURL(file);
  const img = new Image();
  img.onload = () => setPortrait(img, url);
  img.src = url;
});

// Test texture: snapshot the webcam and posterize it, so the pipeline can be tried without art.
$("snapshot").addEventListener("click", () => {
  if (!video.videoWidth) return setStatus("Start the camera first.");
  const c = document.createElement("canvas");
  c.width = video.videoWidth; c.height = video.videoHeight;
  const ctx = c.getContext("2d");
  ctx.filter = "saturate(1.4) contrast(1.15) blur(1px)";
  ctx.drawImage(video, 0, 0);
  const d = ctx.getImageData(0, 0, c.width, c.height), px = d.data, levels = 6, step = 255 / (levels - 1);
  for (let i = 0; i < px.length; i += 4) for (let k = 0; k < 3; k++) px[i + k] = Math.round(px[i + k] / step) * step;
  ctx.putImageData(d, 0, 0);
  setPortrait(c, c.toDataURL("image/jpeg", 0.8));
});

for (const k of ["ext", "feather", "fitScale", "fitX", "fitY"]) ui[k].addEventListener("input", () => { uvDirty = true; });

$("startCam").addEventListener("click", async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720, facingMode: "user" }, audio: false });
    video.srcObject = stream;
    await video.play();
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.parentElement.style.aspectRatio = `${video.videoWidth} / ${video.videoHeight}`;
    setStatus(portraitSource ? "Tracking…" : "Tracking. Now load a portrait.");
  } catch (err) {
    setStatus(`Camera error: ${err.message}`);
  }
});

$("stream").addEventListener("click", () => {
  const preview = $("preview");
  preview.srcObject = canvas.captureStream(30);
  preview.style.display = "block";
});

// ---------- Frame loop ----------
let lastVideoTime = -1;
function frame() {
  requestAnimationFrame(frame);
  if (!video.videoWidth || !videoLandmarker) return;

  if (video.currentTime !== lastVideoTime) {
    lastVideoTime = video.currentTime;
    const res = videoLandmarker.detectForVideo(video, performance.now());
    liveLms = res.faceLandmarks[0] || null;
  }

  gl.viewport(0, 0, canvas.width, canvas.height);
  gl.clearColor(0, 0, 0, 1); gl.clearDepth(1);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  // Background: the camera frame (optionally dimmed).
  gl.disable(gl.DEPTH_TEST); gl.disable(gl.BLEND);
  gl.useProgram(bgProg);
  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, videoTex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, video);
  gl.uniform1i(gl.getUniformLocation(bgProg, "u_tex"), 0);
  gl.uniform1f(gl.getUniformLocation(bgProg, "u_dim"), +ui.bg.value);
  const bgLoc = attrib(bgProg, "a_pos", quadBuf, 2);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  gl.disableVertexAttribArray(bgLoc);

  if (!liveLms || !refBase) return;
  if (uvDirty) updateUVsAndAlpha();

  // Vertex positions from the live face (normalized image coords -> clip space).
  const rings = ringPoints(liveLms, +ui.ext.value);
  const put = (i, p) => { posArr[3 * i] = p.x * 2 - 1; posArr[3 * i + 1] = 1 - p.y * 2; posArr[3 * i + 2] = p.z; };
  for (let i = 0; i < N; i++) put(i, liveLms[i]);
  rings.forEach((p, k) => put(N + k, p));
  gl.bindBuffer(gl.ARRAY_BUFFER, posBuf); gl.bufferData(gl.ARRAY_BUFFER, posArr, gl.DYNAMIC_DRAW);

  gl.enable(gl.DEPTH_TEST); gl.depthFunc(gl.LESS);
  gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  gl.useProgram(meshProg);
  const locs = [attrib(meshProg, "a_pos", posBuf, 3), attrib(meshProg, "a_uv", uvBuf, 2), attrib(meshProg, "a_alpha", alphaBuf, 1)];
  gl.bindTexture(gl.TEXTURE_2D, portraitTex);
  gl.uniform1i(gl.getUniformLocation(meshProg, "u_tex"), 0);
  gl.uniform1f(gl.getUniformLocation(meshProg, "u_opacity"), +ui.opacity.value);
  gl.uniform1i(gl.getUniformLocation(meshProg, "u_debug"), 0);
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, idxBuf);
  const count = topo.base.length + (ui.fillHoles.checked ? topo.holes.length : 0);
  gl.drawElements(gl.TRIANGLES, count, gl.UNSIGNED_SHORT, 0);

  if (ui.debug.checked) {
    gl.disable(gl.DEPTH_TEST);
    gl.uniform1i(gl.getUniformLocation(meshProg, "u_debug"), 1);
    gl.drawArrays(gl.POINTS, 0, V);
  }
  locs.forEach((l) => gl.disableVertexAttribArray(l));
}

// ---------- Boot ----------
(async () => {
  try {
    const fileset = await FilesetResolver.forVisionTasks(WASM_URL);
    const opts = (runningMode) => ({ baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" }, runningMode, numFaces: 1 });
    [videoLandmarker, imageLandmarker] = await Promise.all([
      FaceLandmarker.createFromOptions(fileset, opts("VIDEO")),
      FaceLandmarker.createFromOptions(fileset, opts("IMAGE")),
    ]);
    uploadIndices();
    setStatus("Face tracker ready. Start the camera.");
    requestAnimationFrame(frame);
  } catch (err) {
    setStatus(`Failed to load face tracker: ${err.message}`);
    console.error(err);
  }
})();
