from .quantumblur import *
from PIL import Image
from io import BytesIO
import logging

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

    elif (style == 'swirl'): # c.f. This is for the new swirl effect!
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

# This one is for teleportation effect.
def teleport(img1, img2, n_frame=16, duration=100, loop=0, callback=None):
    """
    Apply the teleportation algorithm to morph between two images into a GIF.

    1. Combines both images side-by-side, encodes it into quantum circuits.
    2. Applies per-frame RX rotations to create an interpolation.
    3. The result is cropped to img2's dimensions (the half-left of the canvas)

    Callback signature:
        callback(current_frame: int, total_frames: int) -> None

        Fires once per frame (* n_frames)

    Args:
        img1: bytes - first image
        img2: bytes - second image
        n_frames: frame number in GIF animation (default: 16)
        duration: per-frame duration in milliseconds (default: 100ms)
        loop: number of GIF loops, 0 = infinite (default 0)
        callback: for UI

    Returns:
        dict with "output" key containing animated GIF bytes
    """

    import math

    logger.info("Loading images...")
    i1 = Image.open(BytesIO(img1)).convert("RGB"); i2 = Image.open(BytesIO(img2)).convert("RGB")

    # Make a big canvas that puts i1 on the right and i2 on the left.
    h = max(i1.height, i2.height)
    canvas = Image.new("RGB", (i1.width+i2.width, h))
    canvas.paste(i1, (0, 0)); canvas.paste(i2, (i1.width, 0))

    # Encode the canvas once; copy circuits per frame to avoid re-encoding
    base_circuits = image2circuits(canvas)

    # Number of y-axis qubits
    # The notebook uses int(np.log2(height)) which gives the wrong index for non-power-of-2 heights. math.ceil matches the actual qubit count in make_grid.
    q = math.ceil(math.log2(h))
    frames = []
    for frame in range(n_frame):
        f = frame / (n_frame - 1)
        logger.debug("Teleportation frame %d/%d (fraction=%.3f)", frame + 1, n_frame, f)

        frame_circuits = []
        for qc in base_circuits:
            frame_qc = qc.copy()
            for quantum in range(frame_qc.num_qubits):
                if quantum == q:
                    frame_qc.rx(math.pi * f, quantum) # swaps two images
                elif quantum < q:
                    frame_qc.rx(2 * math.pi * f, quantum)
                # qubits beyond q: no rotation
            frame_circuits.append(frame_qc)
        
        results = circuits2image(frame_circuits)
        # Crop to i2's dimensions - the left portion of the output canvas

        frames.append(results.crop((0, 0, i2.width, i2.height)))

        if callback:
            callback(frame + 1, n_frame)

    buffer = BytesIO()
    frames[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=loop,
    )
    return {"output": buffer.getvalue()}


        