import torch
import random

class RandomAspectRatioMask:
    def __init__(self):
        self._prev_seed = None
        self._current_aspect_ratio = "16:9"

    @classmethod
    def INPUT_TYPES(cls):
        presets = ["16:9", "9:16", "3:2", "2:3", "4:5", "5:4"]
        return {
            "required": {
                "image": ("IMAGE",),

                "aspect_ratio": (
                    presets,
                    {"default": "16:9"}
                ),

                "placement": (
                    ["center", "random", "left", "right", "up", "down"],
                    {"default": "center"}
                ),

                "seed": (
                    "INT",
                    {"default": 0, "min": 0, "max": 2**31 - 1},
                ),

                "feathering": (
                    "INT",
                    {"default": 40, "min": 0, "max": 1024},
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("Image", "Mask", "Used Aspect Ratio")
    FUNCTION = "process"
    CATEGORY = "va1"

    def process(self, image, aspect_ratio, placement, seed, feathering):
        changed = (self._prev_seed is not None and seed != self._prev_seed)
        self._prev_seed = seed

        presets = ["16:9", "9:16", "3:2", "2:3", "4:5", "5:4"]
        if changed:
            aspect_ratio = random.Random(seed).choice(presets)

        self._current_aspect_ratio = aspect_ratio

        # Parse AR
        try:
            w_f, h_f = map(float, aspect_ratio.split(":"))
            target_ar = w_f / h_f
        except:
            target_ar = 1.0

        # Image dims
        b, h, w, c = image.size()
        orig_ar = w / h

        # Compute canvas size
        if abs(orig_ar - target_ar) < 1e-6:
            new_h, new_w = h, w
        elif target_ar > orig_ar:
            new_w, new_h = int(target_ar * h), h
        else:
            new_h, new_w = int(w / target_ar), w

        new_w = ((new_w + 7) // 8) * 8
        new_h = ((new_h + 7) // 8) * 8

        pad_l = pad_t = 0

        # Smart placement
        rng = random.Random(seed + 999)
        horizontal = target_ar >= 1.0
        vertical = target_ar < 1.0

        # Fallback invalid placements to center
        effective_placement = placement
        if placement in ("left", "right") and not horizontal:
            effective_placement = "center"
        if placement in ("up", "down") and not vertical:
            effective_placement = "center"

        if effective_placement == "center":
            pad_l = (new_w - w) // 2
            pad_t = (new_h - h) // 2
        elif effective_placement == "random":
            pad_l = rng.randint(0, new_w - w)
            pad_t = rng.randint(0, new_h - h)
        elif effective_placement == "left":
            pad_l = 0
            pad_t = (new_h - h) // 2
        elif effective_placement == "right":
            pad_l = new_w - w
            pad_t = (new_h - h) // 2
        elif effective_placement == "up":
            pad_t = 0
            pad_l = (new_w - w) // 2
        elif effective_placement == "down":
            pad_t = new_h - h
            pad_l = (new_w - w) // 2

        pad_r = new_w - w - pad_l
        pad_b = new_h - h - pad_t

        # Build padded image
        new_image = torch.full(
            (b, new_h, new_w, c),
            0.5, dtype=image.dtype, device=image.device
        )
        new_image[:, pad_t:pad_t+h, pad_l:pad_l+w, :] = image

        # Feathered mask
        mask = torch.ones((new_h, new_w), dtype=image.dtype, device=image.device)
        inner = torch.zeros((h, w), dtype=image.dtype, device=image.device)

        if feathering > 0 and feathering*2 < h and feathering*2 < w:
            for i in range(h):
                for j in range(w):
                    dt = i if pad_t > 0 else h
                    db = (h - 1 - i) if pad_b > 0 else h
                    dl = j if pad_l > 0 else w
                    dr = (w - 1 - j) if pad_r > 0 else w
                    d = min(dt, db, dl, dr)
                    if d < feathering:
                        v = (feathering - d) / feathering
                        inner[i, j] = v * v

        mask[pad_t:pad_t+h, pad_l:pad_l+w] = inner

        return (new_image, mask.unsqueeze(0), aspect_ratio)
