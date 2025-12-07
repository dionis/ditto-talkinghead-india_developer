"""
Blend module for image compositing.
Uses pure Python/NumPy fallback on Windows when Cython build fails.
"""

import numpy as np

try:
    # Try to import the Cython version
    import pyximport
    pyximport.install()
    from .blend import blend_images_cy
except Exception:
    # Fallback to pure Python/NumPy implementation
    def blend_images_cy(
        mask_warped: np.ndarray,
        frame_warped: np.ndarray,
        frame_rgb: np.ndarray,
        result: np.ndarray
    ) -> None:
        """
        Blend warped frame with original frame using mask.
        
        Pure NumPy implementation as fallback for when Cython build fails.
        
        Args:
            mask_warped: 2D float32 mask array (H, W)
            frame_warped: 3D float32 warped frame (H, W, 3)
            frame_rgb: 3D uint8 original frame (H, W, 3)
            result: 3D uint8 output array (H, W, 3) - modified in place
        """
        # Expand mask to 3 channels
        mask_3ch = mask_warped[:, :, np.newaxis]
        
        # Convert frame_rgb to float for blending
        frame_rgb_float = frame_rgb.astype(np.float32)
        
        # Blend: result = mask * warped + (1 - mask) * original
        blended = mask_3ch * frame_warped + (1 - mask_3ch) * frame_rgb_float
        
        # Clip and convert back to uint8
        np.clip(blended, 0, 255, out=blended)
        result[:] = blended.astype(np.uint8)