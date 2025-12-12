import torch
import random
import math
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
        rotations = ["random", "0", "30", "60", "90", "120", "150", "180", "210", "240", "270", "300", "330"]
        bg_colors = ["white", "black", "grey"]
        return {
            "required": {
                "image":        ("IMAGE",),
                "aspect_ratio": (ar_presets,   {"default": "16:9"}),
                "placement":    (placements,   {"default": "center"}),
                "scale_pct":    (scales,       {"default": "100"}),
                "rotation":     (rotations,    {"default": "0"}),
                "bg_color":     (bg_colors,    {"default": "white"}),
                "seed":         ("INT",        {"default": 0, "min": 0, "max": 2**31-1}),
                "feathering":   ("INT",        {"default": 40, "min": 0, "max": 1024}),
            }
        }

    RETURN_TYPES  = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES  = ("Image", "Mask", "Params")
    FUNCTION      = "process"
    CATEGORY      = "va1"

    def process(self, image, aspect_ratio, placement, scale_pct, rotation, bg_color, seed, feathering):
        # ── 1) Handle aspect_ratio (random if chosen) ─────────────────────────────
        presets = ["16:9", "9:16", "3:2", "2:3", "4:5", "5:4", "1:1"]
        if aspect_ratio == "random":
            aspect_ratio = random.choice(presets)
        self._current_aspect_ratio = aspect_ratio

        # ── 1.5) Handle rotation (random if chosen) ──────────────────────────────
        rotation_options = [150, 180, 210, 240, 270, 300, 330, 0, 30, 60, 90, 120]
        if rotation == "random":
            rotation_deg = random.choice(rotation_options)
        else:
            rotation_deg = int(rotation)
        
        # Determine background color value early for rotation
        bg_value = 1.0 if bg_color == "white" else (0.0 if bg_color == "black" else 0.5)
        
        # Apply rotation to input image if needed
        if rotation_deg != 0:
            image = self._rotate_image(image, rotation_deg, bg_value)

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
        
        # Store selected parameters for output
        selected_scale = chosen_scale
        selected_rotation = str(rotation_deg)

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
        
        # Store selected placement for output
        selected_placement = effective

        # ── 6) Build padded image ─────────────────────────────────────────────────
        new_image = torch.full(
            (b, new_h, new_w, c),
            bg_value,
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
        
        # Create parameters string
        params_str = f"AR: {aspect_ratio}, Placement: {selected_placement}, Scale: {selected_scale}%, Rotation: {selected_rotation}°"

        return (new_image, mask.unsqueeze(0), params_str)
    
    def _rotate_image(self, image, degrees, bg_value=0.5):
        """Rotate image by given degrees using bilinear interpolation with specified background color."""
        if degrees == 0:
            return image
        
        b, h, w, c = image.shape
        
        # Convert degrees to radians
        angle_rad = math.radians(degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Calculate new dimensions after rotation
        new_h = int(abs(h * cos_a) + abs(w * sin_a))
        new_w = int(abs(w * cos_a) + abs(h * sin_a))
        
        # Create coordinate grids for the output image
        device = image.device
        dtype = image.dtype
        
        # Create background canvas with specified color
        rotated_image = torch.full(
            (b, new_h, new_w, c),
            bg_value,
            dtype=dtype,
            device=device
        )
        
        # Center coordinates
        center_h = (h - 1) / 2
        center_w = (w - 1) / 2
        new_center_h = (new_h - 1) / 2
        new_center_w = (new_w - 1) / 2
        
        # Create meshgrid for new image coordinates
        y_coords = torch.arange(new_h, dtype=dtype, device=device)
        x_coords = torch.arange(new_w, dtype=dtype, device=device)
        yy, xx = torch.meshgrid(y_coords, x_coords, indexing='ij')
        
        # Translate to center, rotate, then translate back
        yy_centered = yy - new_center_h
        xx_centered = xx - new_center_w
        
        # Apply inverse rotation to find source coordinates
        yy_rot = yy_centered * cos_a + xx_centered * sin_a
        xx_rot = -yy_centered * sin_a + xx_centered * cos_a
        
        # Translate back to original coordinate system
        yy_orig = yy_rot + center_h
        xx_orig = xx_rot + center_w
        
        # Normalize coordinates to [-1, 1] for grid_sample
        yy_norm = 2.0 * yy_orig / (h - 1) - 1.0
        xx_norm = 2.0 * xx_orig / (w - 1) - 1.0
        
        # Stack coordinates for grid_sample (N, H, W, 2)
        grid = torch.stack([xx_norm, yy_norm], dim=-1).unsqueeze(0)
        
        # Reshape image for grid_sample: (B, C, H, W)
        image_permuted = image.permute(0, 3, 1, 2)
        
        # Apply rotation using grid_sample with reflection padding
        rotated_temp = F.grid_sample(
            image_permuted, 
            grid.repeat(b, 1, 1, 1),
            mode='bilinear', 
            padding_mode='reflection', 
            align_corners=True
        )
        
        # Reshape back to (B, H, W, C)
        rotated_temp = rotated_temp.permute(0, 2, 3, 1)
        
        # Create a mask for valid pixels (within original image bounds)
        mask = ((yy_orig >= 0) & (yy_orig < h) & (xx_orig >= 0) & (xx_orig < w)).float()
        mask = mask.unsqueeze(0).unsqueeze(-1)  # Add batch and channel dimensions
        
        # Blend the rotated image with the background using the mask
        rotated_image = rotated_image * (1 - mask) + rotated_temp * mask
        
        return rotated_image
