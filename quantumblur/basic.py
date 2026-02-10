from .quantumblur import *
from PIL import Image
from io import BytesIO

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
def run(blurStyle, blurStrength, imgForm, imgData, imgCoor):
    prevImg = Image.open(BytesIO(imgData))
    
    # blurStrength is a float between 0.0 and 1.0 so it could be used for blur_image's 'xi' param.
    style = blurStyle
    # *** SIMPLEST OPERATION for test ***
    if (style == 'whole'):
        # Process the image
        blur_circuits = blur_image(prevImg, blurStrength)   
    elif (style == 'partial'): # c.f. Dealing with the selected region.
        # *** Dummy file *** 
        region = imgCoor
        circuits = image2circuits(prevImg)
        blur_circuits = blur_image(prevImg, xi=blurStrength, circuits=circuits)
    
    resultImg = circuits2image(blur_circuits) # Returns the RGB image.
    buffer = BytesIO()
    # format = resultImg.format
    # This processing is already done. Should the API call handle this?
    resultImg.save(buffer, format=imgForm) # So that the output PNG e.g. can be also a PNG.
    output = buffer.getvalue()
        
    # Return the required output for API.
    return {
        "msg": 'End process for Quantum Blur.',
        "output": output, # This is the byte representation of the blurred image
        # "format": format, # '.png' or something like that
        # "isFormatCorrect": imgForm == format # true/false
    }