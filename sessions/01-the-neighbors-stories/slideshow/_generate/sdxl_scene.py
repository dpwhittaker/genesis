import torch, os, sys
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16, variant="fp16", use_safetensors=True).to("cuda")
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
pipe.set_progress_bar_config(disable=True)
# kept under 77 CLIP tokens so nothing truncates
prompt = ("Sumerian creation myth: the horned god Enlil at center raises a great hoe, prying "
  "a starry blue heaven up off the dark earth, dawn light breaking through the gap between, "
  "ancient Mesopotamian painterly mythology, lapis and gold, epic, masterpiece")
neg = ("modern, photo, text, letters, watermark, signature, frame, border, blurry, lowres, "
  "deformed hands, extra fingers, extra limbs, ugly, cartoon, anime")
for s in [101,202,303,404,505,606]:
    g = torch.Generator("cuda").manual_seed(s)
    img = pipe(prompt=prompt, negative_prompt=neg, width=1344, height=768,
               num_inference_steps=34, guidance_scale=6.5, generator=g).images[0]
    img.save(f"{out}/s_{s}.png"); print("saved", s, flush=True)
print("DONE", flush=True)
