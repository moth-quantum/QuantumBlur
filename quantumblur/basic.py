from .quantumblur import *
from PIL import Image
from io import BytesIO
import logging
import numpy as np

logger = logging.getLogger(__name__)

"""
This is the main image processing function for Quantum Blur. This will be called from Archaeo API.

(1) Input
- "style": str
- "strength" float
- "imgFormat": str
- "region": dict

(2) Output
- "params_received": params
- "msg": "Quantum Blur is done its job."
- "output": imgShouldBe
- "isOutputcorrect": imgShouldBe == params.get("imgFormat")

c.f. The misleading input/output information will be automatically filtered out in the API call step.
Thus, no job will be created and overload the system. Nice!
"""

# Get the required input for API.
def run(blurStyle, blurStrength, imgForm, imgData, imgCoor, callback=None):
    """Callback signature
        callback(current step: int, total_steps: int) -> None
        
        Steps (8 total):
            1   - image loaded
            2-4 - blur circuit built per RGB channel (from blur_image)
            5-7 - quantum simulation run per RGB channel (from circuits2image)
            8   - output encoded
    """
    
    step, total = 0, 8
    
    def _fire():
        nonlocal step
        step += 1
        if callback:
            callback(step, total)
    
    logger.info("Loading image")
    prevImg = Image.open(BytesIO(imgData)).convert("RGB")
    logger.debug("Image size: %s, mode: %s", prevImg.size, prevImg.mode)

    # blurStrength is a float between 0.0 and 1.0 so it could be used for blur_image's 'xi' param.
    style = blurStyle
    # *** SIMPLEST OPERATION for test ***
    if (style == 'whole'):
        # Process the image
        logger.info("Building blur circuits (whole image, strength=%.2f)", blurStrength)
        blur_circuits = blur_image(prevImg, blurStrength,
                                   callback=lambda c, t: _fire())
        
        logger.debug("Built %d blur circuits", len(blur_circuits))
        
    elif (style == 'partial'): # c.f. Dealing with the selected region.
        # *** Dummy file ***
        region = imgCoor
        logger.info("Building blur circuits (partial region=%s, strength=%.2f)", region, blurStrength)
        circuits = image2circuits(prevImg)
        logger.debug("Built %d base circuits before blur", len(circuits))
        blur_circuits = blur_image(prevImg, xi=blurStrength, circuits=circuits,
                                   callback=lambda c, t: _fire())
        logger.debug("Built %d blur circuits", len(blur_circuits))

    elif (style == 'swirl'): # c.f. This is for the new swirl effect! (It's unnecessary - test purpose)
        logger.info("Building circuits...for swirl. (strength=%.2f)", blurStrength)
        blur_circuits = swirl_image(prevImg, blurStrength, callback=lambda c, t: _fire())
        logger.debug("Built %d swirl circuits", len(blur_circuits))

    logger.info("Applying quantum blur")
    resultImg = circuits2image(blur_circuits,
                               callback=lambda c, t:_fire()) # Returns the RGB image.
    
    logger.debug("Result image size: %s", resultImg.size)
    
    buffer = BytesIO()
    # format = resultImg.format
    # This processing is already done. Should the API call handle this?
    logger.info("Encoding result as %s", imgForm)
    resultImg.save(buffer, format=imgForm) # So that the output PNG e.g. can be also a PNG.
    output = buffer.getvalue()
    logger.debug("Output size: %d bytes", len(output))
    
    _fire() # step 8: encoded!

    # Return the required output for API.
    return {
        "output": output,
    }


def _to_pow2(n):
    """Round up to the nearest power of 2."""
    return 1 << (n - 1).bit_length() # Bitshift operation for faster calculation


def teleport(img1Data, img2Data, num_frames=20, duration=120, callback=None):
    """Teleportation effect — morphs between two images via quantum rx rotations.

    Images can be any size. Both are resized to matching power-of-2
    dimensions so that:
      - equal widths: the teleportation boundary falls exactly between the two images
      - power-of-2: int(np.log2()) targets the correct qubit
    Output dimensions equal the shared power-of-2 size.

    Callback signature
        callback(current_step: int, total_steps: int) -> None

        Steps (num_frames + 2 total): # e.g. 22
            1. images loaded and combined
            2. frames rendered on quantum circuit
            3. output encoded
    """

    step, total = 0, num_frames + 2

    def _fire():
        nonlocal step
        step += 1
        if callback:
            callback(step, total)

    logger.info("Loading images for teleportation")
    img1 = Image.open(BytesIO(img1Data)).convert("RGB")
    img2 = Image.open(BytesIO(img2Data)).convert("RGB")

    # Resize both to matching power-of-2 dimensions so that:
    # 1. Equal widths -> teleportation boundary aligns with the image boundary
    # 2. Power-of-2 -> int(np.log2()) gives the correct qubit (matches notebook)
    target_w = _to_pow2(max(img1.width, img2.width)) # This must be less than 1024px (current API)
    target_h = _to_pow2(max(img1.height, img2.height)) # This must be less than 1024px (current API)
    # It's already filtered on the API side: MAX_WIDTH 512 (Half of 1024) so it should be fine.
    img1 = img1.resize((target_w, target_h), Image.LANCZOS)
    img2 = img2.resize((target_w, target_h), Image.LANCZOS)
    img2 = img2.transpose(Image.FLIP_LEFT_RIGHT) # flip so that effect unflips
    logger.debug("Resized to power-of-2: %dx%d", target_w, target_h)

    # Combine side-by-side — canvas is (2 * target_w, target_h), both powers of 2
    both = Image.new("RGB", (target_w * 2, target_h))
    both.paste(img1)
    both.paste(img2, (target_w, 0))
    logger.debug("Combined canvas size: %s", both.size)

    _fire()  # images loaded and combined

    # int(np.log2()) — matches notebook; always correct because target_h is a power of 2
    first_horiz_q = int(np.log2(both.size[1]))
    logger.debug("first_horiz_q: %d", first_horiz_q)

    frames = []
    for f in range(num_frames):
        fraction = f / (num_frames - 1) if num_frames > 1 else 0
        qcs = image2circuits(both)

        for qc in qcs:
            for q in range(qc.num_qubits):
                if q == first_horiz_q:
                    theta = np.pi * fraction  # swap left and right (teleportation comes from here)
                elif q == first_horiz_q + 1:
                    theta = 0 * np.pi * fraction  # flip each image to the correct orientation (if needed)
                elif q < first_horiz_q:
                    theta = 2 * np.pi * fraction  # apply an effect vertically
                else:
                    theta = 0
                qc.rx(theta, q)

        img = circuits2image(qcs)
        # Crop left half
        # the teleported result at (target_w, target_h)
        frames.append(img.crop((0, 0, target_w, target_h)))
        logger.debug("Frame %d/%d (fraction=%.3f)", f + 1, num_frames, fraction)

        _fire()  # frame rendered

    logger.info("Encoding GIF (%d frames, %dms/frame)", num_frames, duration)
    buffer = BytesIO()
    frames[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
    )
    output = buffer.getvalue()
    logger.debug("Output size: %d bytes", len(output))

    _fire()  # output encoded

    return {
        "output": output,
    }
