import torch, os, sys, cv2, numpy as np
from PIL import Image
from diffusers import StableDiffusionXLControlNetPipeline, ControlNetModel, DPMSolverMultistepScheduler
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
ctrl_path=sys.argv[2]
cn = ControlNetModel.from_pretrained("xinsir/controlnet-scribble-sdxl-1.0", torch_dtype=torch.float16)
pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0", controlnet=cn,
    torch_dtype=torch.float16, variant="fp16", use_safetensors=True).to("cuda")
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
pipe.set_progress_bar_config(disable=True)
# control -> clean edge "scribble" of the composition
img = cv2.imread(ctrl_path); img = cv2.resize(img,(1344,768))
edges = cv2.Canny(cv2.cvtColor(img,cv2.COLOR_BGR2GRAY), 60, 150)
edges = cv2.dilate(edges, np.ones((2,2),np.uint8), iterations=1)
ctrl = Image.fromarray(edges).convert("RGB"); ctrl.save(f"{out}/_edges.png")
prompt = ("carved gold relief on lapis lazuli, ancient Sumerian mythology, the horned god Enlil "
  "raising a hoe between a starry heaven dome above and the earth below, gold and deep blue, "
  "stars, intricate, epic, masterpiece")
neg = "text, watermark, blurry, lowres, deformed, extra limbs, modern, photo, ugly"
for s in [7,17,27,37]:
    g=torch.Generator("cuda").manual_seed(s)
    im=pipe(prompt=prompt, negative_prompt=neg, image=ctrl, controlnet_conditioning_scale=0.6,
            width=1344, height=768, num_inference_steps=32, guidance_scale=6.5, generator=g).images[0]
    im.save(f"{out}/cn_{s}.png"); print("saved",s,flush=True)
print("DONE",flush=True)
