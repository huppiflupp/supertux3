#!/usr/bin/env python3
"""comfy_gen.py -- Generate background art via a running ComfyUI + FLUX-schnell.

Reusable CLI that builds a FLUX-schnell text2image graph, submits it to a
running ComfyUI server via its HTTP API, waits for the result and copies the
resulting PNG into the SuperTux3 background asset folder.

Only the Python standard library is used (urllib/json/...), so this script can
run inside the game venv without extra dependencies.

Usage:
    python comfy_gen.py --prompt "sunny cartoon sky" --out sky.png
    python comfy_gen.py --prompt "..." --out title.png --width 1280 --height 720
    python comfy_gen.py --prompt "..." --out x.png --steps 4 --seed 42 --outdir /some/dir

Requires a running ComfyUI (default http://127.0.0.1:8188). Start it with:
    cd /home/seeas/MU/mu_generator/ComfyUI && ./run.sh
"""

import argparse
import json
import os
import shutil
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
import uuid

# --- Model / node defaults (match the installed ComfyUI environment) ---------
DEFAULT_SERVER = "http://127.0.0.1:8188"
UNET_NAME = "flux1-schnell-fp8.safetensors"
UNET_DTYPE = "fp8_e4m3fn"
T5_NAME = "t5xxl_fp8_e4m3fn.safetensors"
CLIP_L_NAME = "clip_l.safetensors"
VAE_NAME = "ae.safetensors"

# Default output directory for SuperTux3 backgrounds.
DEFAULT_OUTDIR = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "assets", "images", "background",
    )
)


def build_graph(prompt, width, height, steps, seed, cfg=1.0,
                sampler="euler", scheduler="simple", filename_prefix="stux"):
    """Return a ComfyUI prompt graph (dict) for FLUX-schnell text2image.

    Graph:  UNETLoader -> DualCLIPLoader -> CLIPTextEncode(+/-) ->
            EmptySD3LatentImage -> KSampler -> VAEDecode(ae) -> SaveImage
    """
    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": UNET_NAME, "weight_dtype": UNET_DTYPE},
        },
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": T5_NAME,
                "clip_name2": CLIP_L_NAME,
                "type": "flux",
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["2", 0], "text": prompt},
        },
        "4": {  # negative / empty conditioning (cfg 1.0 => effectively unused)
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["2", 0], "text": ""},
        },
        "5": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": 1.0,
            },
        },
        "7": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": VAE_NAME},
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["6", 0], "vae": ["7", 0]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": filename_prefix, "images": ["8", 0]},
        },
    }


def _post_json(server, path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        server + path, data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(server, path):
    with urllib.request.urlopen(server + path, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def submit(server, graph, client_id):
    return _post_json(server, "/prompt", {"prompt": graph, "client_id": client_id})


def wait_for_result(server, prompt_id, timeout=600, poll=2.0):
    """Poll /history/<id> until the prompt finishes; return its history entry."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            hist = _get_json(server, "/history/" + prompt_id)
        except urllib.error.URLError:
            time.sleep(poll)
            continue
        if prompt_id in hist:
            entry = hist[prompt_id]
            status = entry.get("status", {})
            if status.get("completed") or entry.get("outputs"):
                return entry
            if status.get("status_str") == "error":
                raise RuntimeError("ComfyUI reported an error: %s" % json.dumps(status))
        time.sleep(poll)
    raise TimeoutError("Timed out waiting for prompt %s" % prompt_id)


def fetch_image(server, image_info):
    """Download an output image described by a SaveImage history entry."""
    q = urllib.parse.urlencode({
        "filename": image_info["filename"],
        "subfolder": image_info.get("subfolder", ""),
        "type": image_info.get("type", "output"),
    })
    with urllib.request.urlopen(server + "/view?" + q, timeout=60) as resp:
        return resp.read()


def generate(prompt, out, width=1536, height=768, steps=4, seed=None,
             outdir=DEFAULT_OUTDIR, server=DEFAULT_SERVER):
    if seed is None:
        seed = int.from_bytes(os.urandom(4), "big")
    client_id = str(uuid.uuid4())
    graph = build_graph(prompt, width, height, steps, seed,
                        filename_prefix=os.path.splitext(out)[0])

    print("[comfy_gen] submitting graph (%dx%d, %d steps, seed %d)"
          % (width, height, steps, seed))
    res = submit(server, graph, client_id)
    prompt_id = res.get("prompt_id")
    if not prompt_id:
        raise RuntimeError("No prompt_id in response: %s" % json.dumps(res))
    print("[comfy_gen] prompt_id=%s -- waiting..." % prompt_id)

    entry = wait_for_result(server, prompt_id)
    images = []
    for node_out in entry.get("outputs", {}).values():
        images.extend(node_out.get("images", []))
    if not images:
        raise RuntimeError("No images produced")

    img_bytes = fetch_image(server, images[0])
    os.makedirs(outdir, exist_ok=True)
    dest = os.path.join(outdir, out)
    with open(dest, "wb") as fh:
        fh.write(img_bytes)
    print("[comfy_gen] wrote %s (%d bytes)" % (dest, len(img_bytes)))
    return dest


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate art via ComfyUI + FLUX-schnell")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True, help="output filename, e.g. sky.png")
    ap.add_argument("--width", type=int, default=1536)
    ap.add_argument("--height", type=int, default=768)
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    ap.add_argument("--server", default=DEFAULT_SERVER)
    args = ap.parse_args(argv)
    try:
        generate(args.prompt, args.out, args.width, args.height, args.steps,
                 args.seed, args.outdir, args.server)
    except Exception as exc:  # noqa: BLE001
        print("[comfy_gen] ERROR: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
