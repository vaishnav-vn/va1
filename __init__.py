from .aspect_outpaint_node import RandomAspectRatioMask

NODE_CLASS_MAPPINGS = {
    "RandomAspectRatioMask": RandomAspectRatioMask
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RandomAspectRatioMask": "Pad Image by Aspect for Outpaint"
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
