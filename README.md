# 🧩 Pad Image by Aspect for Outpaint — Custom ComfyUI Node

A versatile ComfyUI node designed to **expand images to specific or randomized aspect ratios** with intelligent spatial placement and feathered masking — ideal for **outpainting, image composition, and directional canvas control**.

---

## 🌟 Features

- 🔁 **Random or fixed aspect ratios** (16:9, 3:2, 4:5, etc.)
- 🧭 **Placement control**: center, random, left, right, up, down —  directional placement only applies when valid for AR shape
- 🪶 **Feathered mask** for seamless outpainting transitions
- 🔢 **Outputs used aspect ratio** as a `STRING` for logging or chaining

---

## 🧠 Primary Use Case: Outpainting

This node is purpose-built for **inpainting and outpainting workflows**, allowing you to:
- Expand a canvas in specific directions
- Randomize aspect ratio selection per generation
- Use precise control for storytelling layout and composition
- Automatically mask newly padded areas for targeted image editing

---

## 🔧 Inputs

| Name | Type | Description |
|------|------|-------------|
| `image` | `IMAGE` | The input image to be padded |
| `aspect_ratio` | `["16:9", "9:16", "3:2", "2:3", "4:5", "5:4"]` | Aspect ratio to pad the image to. Randomized if seed changes. |
| `placement` | `["center", "random", "left", "right", "up", "down"]` | Placement of the original image inside the new canvas. Invalid directions fall back to center. |
| `seed` | `INT` | Changing this triggers random AR selection (Control-After-Generate supported) |
| `feathering` | `INT` | Softens mask edges for smooth inpainting blending |

---

## 📤 Outputs

| Name | Type | Description |
|------|------|-------------|
| `Image` | `IMAGE` | The padded image |
| `Mask` | `MASK` | Feathered mask showing padded regions |
| `Used Aspect Ratio` | `STRING` | The final AR used (e.g., `"4:5"`), chainable downstream |

---

## ⚙️ Smart Behavior

### 🔁 Seed-Based Randomization

- Each time the `seed` changes, a new aspect ratio is selected randomly from the list.
- Fully compatible with `Control-After-Generate` for batch diversity.

### 🧭 Placement Logic

- Landscape-only placements: `"left"`, `"right"`
- Portrait-only placements: `"up"`, `"down"`
- Invalid placements (e.g., `"left"` on 9:16) fall back to `"center"`

### 🪶 Mask Feathering

- Padded edges are softly blended with the original content
- Prevents hard seams when used in outpainting pipelines
- `feathering = 0` produces a binary mask

---

## 🧪 Example Workflows

### ➕ Expand a Portrait Canvas Upward

```text
AR = "9:16", Placement = "up", Feathering = 64
