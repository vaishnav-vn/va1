# 🧩 Pad Image by Aspect for Outpaint — Custom ComfyUI Node

A versatile ComfyUI node designed to **expand**, **pad**, and **mask** images to fixed or randomized aspect ratios with precise spatial and scale control — engineered for outpainting, compositional layout, and creative canvas expansion.

---

## 🌟 Key Features

* 🔁 **Aspect Ratio with Random Option**: Choose from fixed presets (`16:9`, `9:16`, `3:2`, `2:3`, `4:5`, `5:4`, `1:1`) or select **`random`** to pick a new ratio on each run.
* 🔧 **Scale Percentage**: Shrink the input image **after** canvas sizing. Presets range from **`50%`** to **`100%`**, plus **`random`** for varying scales each execution. When using `1:1`, **100%** is disabled to ensure visible shrinkage.
* 🧭 **Placement Control**: Full spatial options:

  * **Directional**: `left`, `right`, `up`, `down`
  * **3×3 Grid**: `top-left`, `top-mid`, `top-right`, `mid-left`, `center`, `mid-right`, `bottom-left`, `bottom-mid`, `bottom-right`
  * **Random**: Uniform placement anywhere on the canvas.
  * **Smart Fallbacks**: Directional choices auto-revert to **`center`** if incompatible with the aspect ratio’s orientation (e.g., `left` on a portrait canvas).
* 🪶 **Feathered Mask**: Generates a soft-edged mask for the new padded areas to facilitate seamless inpainting/outpainting.

---

## 🧠 Primary Use Case: Outpainting & Canvas Expansion

This node is ideal for workflows where you need to prepare a larger canvas around an existing image:

* **Directional Outpainting**: Expand to the right for narrative extension, upward for sky or background, etc.
* **Randomized Compositions**: Generate varied framing and scales in batch jobs.
* **Precise Layouts**: Use grid/aligned placements to position the subject consistently.
* **Seamless Blending**: Feathered masks ensure your inpainting edits blend naturally with original content.

---

## 🔧 Inputs

| Name           | Type                                                                                                                                                                                        | Description                                                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `image`        | `IMAGE`                                                                                                                                                                                     | The input image tensor (B×H×W×C).                                                                                                             |
| `aspect_ratio` | `"random"`, `"16:9"`, `"9:16"`, `"3:2"`,<br>`"2:3"`, `"4:5"`, `"5:4"`, `"1:1"`                                                                                                              | Target aspect ratio for the canvas. Select **`random`** for a fresh ratio each run.                                                           |
| `placement`    | `"center"`, `"random"`,<br>`"left"`,`"right"`,`"up"`,`"down"`,<br>`"top-left"`,`"top-mid"`,`"top-right"`,<br>`"mid-left"`,`"mid-right"`,<br>`"bottom-left"`,`"bottom-mid"`,`"bottom-right"` | Spatial placement of the shrunk image inside the new canvas.                                                                                  |
| `scale_pct`    | `"random"`, `"50"`, `"60"`, `"70"`, `"80"`, `"90"`, `"100"`                                                                                                                                 | Percentage to shrink the original image **after** canvas sizing. `random` selects one of the valid scales each run. `100` disabled for `1:1`. |
| `seed`         | `INT` (default `0`)                                                                                                                                                                         | Slider to **force** node re-execution in ComfyUI. Does **not** affect any random modes — each `random` is truly independent.                  |
| `feathering`   | `INT` (0–1024)                                                                                                                                                                              | Softness of the mask’s edge—higher values produce smoother transitions at the padded border.                                                  |

---

## 🧾 Outputs

| Name                | Type     | Description                                                                                     |
| ------------------- | -------- | ----------------------------------------------------------------------------------------------- |
| `Image`             | `IMAGE`  | The padded (and optionally shrunk) image tensor.                                                |
| `Mask`              | `MASK`   | Feathered mask where `0` = original content, `>0` = padded regions with smooth blending values. |
| `Used Aspect Ratio` | `STRING` | The final aspect ratio used (e.g., `"3:2"`).                                                    |

---

## 🚀 Installation

**Option 1: ComfyUI Manager**

1. Open **ComfyUI Manager**
2. Click **“Install from URL”**
3. Paste:

   ```text
   https://github.com/vaishnav-vn/va1
   ```

**Option 2: Manual**

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/vaishnav-vn/va1.git
```

Restart ComfyUI.

---

## 🔄 Example Workflows

### 1. Random Outpainting Variations

* `aspect_ratio`: `random`
* `placement`: `random`
* `scale_pct`: `random`
* `seed`: slide to re-run

### 2. Grid-Aligned Portrait Expansion

* `aspect_ratio`: `9:16`
* `placement`: `top-mid`
* `scale_pct`: `80`
* `seed`: any value (just to refresh)

### 3. Left-Aligned Landscape Resize

* `aspect_ratio`: `16:9`
* `placement`: `left`
* `scale_pct`: `50`

---

## 📋 Node Metadata

* **Node Name**: `Pad Image by Aspect for Outpaint`
* **Category**: `va1`
* **Compatibility**: Works with any ComfyUI pipeline accepting `IMAGE` and `MASK` inputs.

---
