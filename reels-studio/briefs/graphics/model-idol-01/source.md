# idol — speridlabs/idol (model card, huggingface.co/speridlabs/idol, read 2026-11-08)

Idol turns one picture of an object into a 3D Gaussian splat. Give it a render, a generated image or a
photo: it removes the background, frames the object and generates up to 1,048,576 Gaussians, written as a
standard 3DGS `.ply`. It runs on consumer GPUs, using 7.2 GB of VRAM and can run in under 2 seconds.

Code: github.com/speridlabs/idol-sdk (`pip install -e .`, Python 3.10+, PyTorch 2.5+, an NVIDIA GPU with CUDA).
Demo: free Hugging Face Space: huggingface.co/spaces/speridlabs/idol.
Command: `python -m idol.sample --image photo.jpg --mode real` writes <name>.ply, <name>_input.png, <name>_camera.json.
Modes: `--mode synthetic` (default) for renders of a single object (object fills 1/1.2 of the frame);
       `--mode real` for photographs (object fills 1/1.7 of the frame).
Encoders: it reads input through two gated models — facebook/dinov3-vith16plus-pretrain-lvd1689m and
black-forest-labs/FLUX.2-dev (only its VAE is downloaded); you accept their terms once with a HF account.
Weights: about 3 GB, auto-download on first run.

Benchmark (their numbers, 1 × H100 per model, 50 steps, 262,144 Gaussians): Idol 12.25 PSNR, 0.726 SSIM,
0.213 LPIPS, 0.862 IoU, 0.781 DINOv2, 0.885 CLIP, 0.81 sharpness distance, 6.8 s request time — best in
every column except PSNR (LGM 12.46, with a footnote that PSNR averages squared pixel error) and request
time (LGM 1.1 s). TripoSplat and TRELLIS lose every visual column.

Across GPUs (one image to 262,144 Gaussians, 50 steps): B300 3.4 s, H100 6.7 s, RTX 5090 14.1 s,
RTX 3080 46.2 s, L4 54.6 s.

Downloads last month: 22,854. Trending #1 on Hugging Face 2026-11-08 (trend score ~765, 1,291 likes).
