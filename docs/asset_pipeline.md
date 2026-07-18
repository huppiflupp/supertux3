# SuperTux3 Asset Pipeline (ComfyUI + FLUX-schnell)

Background art for SuperTux3 is generated locally with **ComfyUI** driving the
**FLUX.1-schnell** diffusion model. This document explains how to start the
server, how to use the `comfy_gen.py` CLI, which models are involved, and which
assets have been produced.

## 1. Starting ComfyUI (headless)

ComfyUI lives outside this repo:

```bash
cd /home/seeas/MU/mu_generator/ComfyUI
./run.sh            # starts headless on http://127.0.0.1:8188 (RTX 5080, CUDA)
```

`run.sh` uses a dedicated Python 3.11 venv (`ComfyUI/venv`) with
`torch 2.11+cu128`. It listens on `0.0.0.0:8188` (via `--listen`). Wait until the
API answers before generating:

```bash
curl -s http://127.0.0.1:8188/system_stats
```

To run it fully in the background:

```bash
cd /home/seeas/MU/mu_generator/ComfyUI && nohup ./run.sh > /tmp/comfy.log 2>&1 &
```

## 2. Models used

All under `ComfyUI/models/`:

| Role            | File                                        | Notes                          |
|-----------------|---------------------------------------------|--------------------------------|
| Diffusion model | `diffusion_models/flux1-schnell-fp8.safetensors` | FLUX schnell, 4 steps, fast |
| Text encoder 1  | `text_encoders/t5xxl_fp8_e4m3fn.safetensors`| T5-XXL (fp8)                   |
| Text encoder 2  | `text_encoders/clip_l.safetensors`          | CLIP-L                         |
| VAE             | `vae/ae.safetensors`                        | FLUX autoencoder               |

FLUX-schnell sampling params (baked into the graph): **4 steps, cfg 1.0,
sampler `euler`, scheduler `simple`**.

## 3. The `comfy_gen.py` CLI

`tools/asset_pipeline/comfy_gen.py` builds the FLUX-schnell graph, POSTs it to
the running ComfyUI API (`/prompt`), polls `/history/<id>` until done, downloads
the image via `/view` and writes the PNG into the background folder.

It uses **only the Python standard library** (urllib/json), so it runs fine in
the game venv with no extra dependencies.

### Usage

```bash
# Minimal (defaults: 1536x768, 4 steps, random seed, -> assets/images/background/)
python tools/asset_pipeline/comfy_gen.py --prompt "sunny cartoon sky" --out sky.png

# Full control
python tools/asset_pipeline/comfy_gen.py \
  --prompt "..." --out title.png \
  --width 1280 --height 720 --steps 4 --seed 777

# Custom output directory / server
python tools/asset_pipeline/comfy_gen.py --prompt "..." --out x.png \
  --outdir /some/dir --server http://127.0.0.1:8188
```

### Options

| Flag        | Default                              | Meaning                       |
|-------------|--------------------------------------|-------------------------------|
| `--prompt`  | (required)                           | Positive text prompt          |
| `--out`     | (required)                           | Output filename, e.g. `sky.png` |
| `--width`   | `1536`                               | Image width (px)              |
| `--height`  | `768`                                | Image height (px)             |
| `--steps`   | `4`                                  | Sampling steps (schnell = 4)  |
| `--seed`    | random                               | Fixed seed for reproducibility|
| `--outdir`  | `assets/images/background/`          | Destination directory         |
| `--server`  | `http://127.0.0.1:8188`              | ComfyUI API base URL          |

The complete FLUX graph is embedded in the script (`build_graph()`), so no
external workflow JSON is required.

### Prompting tips

- Always add `no characters, no people, no text, no letters, no UI` for clean
  parallax backdrops.
- For title/mascot art, ask for `lots of empty sky space at the top for a
  title` and `no embedded text` (title text is composited by the game, not baked
  into the image).

## 4. Generated assets

All in `assets/images/background/`:

| File                  | Size      | Purpose                                                    |
|-----------------------|-----------|------------------------------------------------------------|
| `sky_parallax.png`    | 1536x768  | Far parallax layer: blue sky, soft clouds, distant hills.  |
| `hills_midground.png` | 1536x512  | Midground parallax: green rolling-hills silhouette with flat sky-blue top for compositing. |
| `title_art.png`       | 1280x720  | Title screen art: cute cartoon penguin hero jumping in green hills with coins, empty sky top for a title. |

### Regenerating them

```bash
python tools/asset_pipeline/comfy_gen.py \
  --prompt "cheerful 16-bit platformer background, bright blue sky, soft fluffy clouds, gentle rolling green hills in the distance, flat clean cartoon style like SuperTux, no characters, no text, no UI" \
  --out sky_parallax.png --width 1536 --height 768 --seed 12345

python tools/asset_pipeline/comfy_gen.py \
  --prompt "16-bit platformer, silhouette of gentle rolling green hills along the bottom, flat sky-blue color filling the top half, cartoon style like SuperTux, no characters, no text, no UI" \
  --out hills_midground.png --width 1536 --height 512 --seed 2024

python tools/asset_pipeline/comfy_gen.py \
  --prompt "joyful cartoon title art, cute chubby penguin hero jumping through sunny green rolling hills, gold coins in the air, blue sky, SuperTux style, empty sky at the top for a title, no embedded text, no UI" \
  --out title_art.png --width 1280 --height 720 --seed 777
```

### Notes / limitations

- FLUX-schnell outputs opaque RGB PNGs (no real alpha channel). `hills_midground.png`
  uses a flat sky-blue top region that can be colour-keyed or masked at load
  time if a transparent midground layer is needed.
