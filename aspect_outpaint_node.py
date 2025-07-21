import torch
import random
import torch.nn.functional as F

class RandomAspectRatioMask:
    def __init__(self):
        self._current_aspect_ratio = "16:9"

    @classmethod
    def INPUT_TYPES(cls):
        ar_presets = ["random", "16:9", "9:16", "3:2", "2:3", "4:5", "5:4", "1:1"]
        placements = [
            "center", "random",
            "left", "right", "up", "down",
            "top-left", "top-mid", "top-right",
            "mid-left",             "mid-right",
            "bottom-left", "bottom-mid", "bottom-right"
        ]
        scales = ["random", "50", "60", "70", "80", "90", "100"]
        return {
            "required": {
                "image":        ("IMAGE",),
                "aspect_ratio": (ar_presets,   {"default": "16:9"}),
                "placement":    (placements,   {"default": "center"}),
                "scale_pct":    (scales,       {"default": "100"}),
                "seed":         ("INT",        {"default": 0, "min": 0, "max": 2**31-1}),
                "feathering":   ("INT",        {"default": 40, "min": 0, "max": 1024}),
            }
        }

    RETURN_TYPES  = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES  = ("Image", "Mask", "Used Aspect Ratio")
    FUNCTION      = "process"
    CATEGORY      = "va1"

    def process(self, image, aspect_ratio, placement, scale_pct, seed, feathering):
        # ── 1) Handle aspect_ratio (random if chosen) ─────────────────────────────
        presets = ["16:9", "9:16", "3:2", "2:3", "4:5", "5:4", "1:1"]
        if aspect_ratio == "random":
            aspect_ratio = random.choice(presets)
        self._current_aspect_ratio = aspect_ratio

        # ── 2) Compute canvas size from ORIGINAL image dims ────────────────────────
        b0, h0, w0, c0 = image.size()
        try:
            wf, hf = map(float, aspect_ratio.split(":"))
            target_ar = wf / hf
        except:
            target_ar = 1.0
        orig_ar = w0 / h0

        if abs(orig_ar - target_ar) < 1e-6:
            new_h, new_w = h0, w0
        elif target_ar > orig_ar:
            new_w, new_h = int(target_ar * h0), h0
        else:
            new_h, new_w = int(w0 / target_ar), w0

        # Round to multiples of 8
        new_w = ((new_w + 7) // 8) * 8
        new_h = ((new_h + 7) // 8) * 8

        # ── 3) Pick scale (after canvas dims)—100% disallowed for 1:1 ──────────────
        all_scales   = ["50", "60", "70", "80", "90", "100"]
        valid_scales = all_scales[:-2] if aspect_ratio == "1:1" else all_scales

        if scale_pct == "random":
            chosen_scale = random.choice(valid_scales)
        else:
            chosen_scale = scale_pct if scale_pct in valid_scales else valid_scales[-1]

        scale = int(chosen_scale) / 100.0

        # ── 4) Resize the **original image** now, so canvas stays fixed ───────────
        if scale != 1.0:
            nh0 = max(1, int(h0 * scale))
            nw0 = max(1, int(w0 * scale))
            # B×H×W×C → B×C×H×W for F.interpolate
            img_bc = image.permute(0, 3, 1, 2)
            resized = F.interpolate(
                img_bc,
                size=(nh0, nw0),
                mode='bilinear',
                align_corners=False
            )
            image = resized.permute(0, 2, 3, 1)
            b, h, w, c = b0, nh0, nw0, c0
        else:
            b, h, w, c = b0, h0, w0, c0

        # ── 5) Determine placement offsets ─────────────────────────────────────────
        # Orientation check for directional fallbacks
        horizontal = (target_ar >= 1.0)
        vertical   = (target_ar <  1.0)
        effective  = placement
        if placement in ("left", "right") and not horizontal:
            effective = "center"
        if placement in ("up", "down") and not vertical:
            effective = "center"

        mid_x = (new_w - w) // 2
        mid_y = (new_h - h) // 2

        pos_map = {
            "center":      (mid_x,      mid_y),
            "random":      (random.randint(0, new_w - w),
                            random.randint(0, new_h - h)),
            "left":        (0,          mid_y),
            "right":       (new_w - w,  mid_y),
            "up":          (mid_x,      0),
            "down":        (mid_x,      new_h - h),
            "top-left":    (0,          0),
            "top-mid":     (mid_x,      0),
            "top-right":   (new_w - w,  0),
            "mid-left":    (0,          mid_y),
            "mid-right":   (new_w - w,  mid_y),
            "bottom-left": (0,          new_h - h),
            "bottom-mid":  (mid_x,      new_h - h),
            "bottom-right":(new_w - w,  new_h - h),
        }

        pad_l, pad_t = pos_map.get(effective, pos_map["center"])
        pad_r = new_w - w - pad_l
        pad_b = new_h - h - pad_t

        # ── 6) Build padded image ─────────────────────────────────────────────────
        new_image = torch.full(
            (b, new_h, new_w, c),
            0.5,
            dtype=image.dtype,
            device=image.device
        )
        new_image[:, pad_t:pad_t+h, pad_l:pad_l+w, :] = image

        # ── 7) Feathered mask ─────────────────────────────────────────────────────
        mask  = torch.ones((new_h, new_w),
                           dtype=image.dtype,
                           device=image.device)
        inner = torch.zeros((h, w),
                            dtype=image.dtype,
                            device=image.device)
        if feathering > 0 and feathering * 2 < h and feathering * 2 < w:
            for i in range(h):
                for j in range(w):
                    dt = i if pad_t > 0 else h
                    db = (h - 1 - i) if pad_b > 0 else h
                    dl = j if pad_l > 0 else w
                    dr = (w - 1 - j) if pad_r > 0 else w
                    d  = min(dt, db, dl, dr)
                    if d < feathering:
                        v = (feathering - d) / feathering
                        inner[i, j] = v * v

        mask[pad_t:pad_t+h, pad_l:pad_l+w] = inner

        return (new_image, mask.unsqueeze(0), aspect_ratio)
