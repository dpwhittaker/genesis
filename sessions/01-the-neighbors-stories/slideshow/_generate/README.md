# Scene 2 art pipeline (SDXL + ControlNet, → WAN)

The painted scene (`../assets/sumerian-scene.png`) is **scene 1's exact vector
composition, repainted by SDXL** so the layout (sky-dome above, Enlil + hoe at
left, earth furrows below) is preserved and the magnify regions still map.

1. `render_control_image.js` — screenshots scene 1 with labels/chrome hidden →
   `control-composition.png` (the composition to follow).
2. `controlnet_scene.py` — Canny-edges that control image and runs SDXL +
   `xinsir/controlnet-scribble-sdxl-1.0` (gold-relief-on-lapis prompt) → candidates.
   Pick one → `../assets/sumerian-scene.png`.
3. `sdxl_scene.py` — free-composition SDXL (no control), kept for reference.

Next: WAN 2.1 I2V-14B (4-bit quantized to fit the 4080) animates the still into
the separation clip → `../assets/sumerian-separation.mp4`, wired via the scene's
`{type:'video'}` animation hook. CLIP's 77-token limit applies to the SDXL
prompts; lift it with Compel if longer prompts are needed.

`_generate/` is underscore-prefixed so Jekyll never publishes it.
