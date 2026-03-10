import quantumblur as qb
import cv2
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

import threading
import subprocess

def init():
    while True:
        boot = input('Activate: ')
        if boot == 'quantumblur':
            run()
            break
        else:
            print('Invalid.')
            
def draw_text_with_custom_font(cv_image, text, position, font_path, font_size, color=(255, 255, 255)):
    """
    Draws text on an OpenCV image using a custom TTF font.

    :param cv_image: The OpenCV image (NumPy array).
    :param text: The text string to draw.
    :param position: A tuple (x, y) for the top-left corner of the text.
    :param font_path: The path to the .ttf font file.
    :param font_size: The size of the font.
    :param color: The text color in BGR format.
    :return: The OpenCV image with the text drawn on it.
    """
    # Convert the OpenCV image from BGR to RGB color space
    rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    
    # Create a Pillow Image object from the NumPy array
    pil_image = Image.fromarray(rgb_image)
    
    # Create a Draw object to allow drawing on the image
    draw = ImageDraw.Draw(pil_image)
    
    # Load the custom font
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"Font not found at {font_path}. Using default font.")
        font = ImageFont.load_default()

    # Draw the text on the Pillow image
    # Note: Pillow uses RGB color format, so we convert the BGR input
    draw.text(position, text, font=font, fill=(color[2], color[1], color[0]))
    
    # Convert the Pillow image back to a NumPy array
    final_np_image = np.array(pil_image)
    
    # Convert the color space back from RGB to BGR for OpenCV
    final_cv_image = cv2.cvtColor(final_np_image, cv2.COLOR_RGB2BGR)
    
    return final_cv_image

def add_branding(base_image, logo_path, text, font_path):
    """
    Adds a logo and text overlay to a PIL image with proportional sizing and positioning.

    :param base_image: The base PIL Image to draw on.
    :param logo_path: The path to the transparent logo PNG file.
    :param text: The marketing text to display.
    :param font_path: The path to the .ttf font file.
    :return: The base_image with branding applied.
    """
    try:
        # Open the logo image, ensuring it has an alpha channel for transparency
        logo = Image.open(logo_path).convert("RGBA")
    except FileNotFoundError:
        print(f"Error: Logo file not found at {logo_path}. Skipping overlay.")
        return base_image

    # --- 1. Proportional Sizing ---
    # Set the logo's height to be 8% of the base image's height
    logo_height = int(base_image.height * 0.08)
    # Calculate the logo's width to maintain its original aspect ratio
    logo_aspect_ratio = logo.width / logo.height
    logo_width = int(logo_height * logo_aspect_ratio)
    
    # Resize the logo using a high-quality filter for smoothness
    logo = logo.resize((logo_width, logo_height), Image.LANCZOS)

    # --- 2. Proportional Positioning ---
    # Create a 2% margin from the bottom-right corner of the image
    margin = int(base_image.width * 0.02)
    logo_x = base_image.width - logo_width - margin
    logo_y = base_image.height - logo_height - margin

    # Paste the logo onto the base image. The 'logo' argument passed as the mask
    # ensures that the transparent parts of the PNG are handled correctly.
    base_image.paste(logo, (logo_x, logo_y), logo)

    # --- 3. Proportional Font and Text ---
    try:
        # Set the font size to be 40% of the logo's height for visual consistency
        font_size = int(logo_height * 0.4)
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"Error: Font file not found at {font_path}. Using default font.")
        font = ImageFont.load_default()

    # Position the text to the left of the logo
    draw = ImageDraw.Draw(base_image)
    
    # Get the bounding box of the text to calculate its width and height
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Position text to be left of the logo, with a small gap, and vertically centered with it
    text_x = logo_x - text_width - int(margin * 0.5)
    text_y = logo_y + (logo_height - text_height) // 2
    
    # Draw the text (white with slight transparency for a softer look)
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 220))

    return base_image

def create_display_with_camera_roll(frame, camera_roll, thumbnail_height=120, selected_index=-1):
    """Create a composite display with camera feed and thumbnail roll at bottom"""
    frame_height, frame_width = frame.shape[:2]
    
    # Always create a larger canvas to fit frame + camera roll (for consistent window size)
    canvas_height = frame_height + thumbnail_height + 10
    canvas = np.zeros((canvas_height, frame_width, 3), dtype=np.uint8)
    
    # Place the camera frame at the top
    canvas[0:frame_height, 0:frame_width] = frame
    
    # Add separator line
    cv2.line(canvas, (0, frame_height), (frame_width, frame_height), (100, 100, 100), 2)
    
    # If no photos yet, return the canvas with empty thumbnail area
    if not camera_roll:
        return canvas, []
    
    # Calculate thumbnail dimensions
    max_thumbnails = 5  # Show last 5 photos
    recent_photos = camera_roll[-max_thumbnails:]  # Get most recent photos
    
    thumb_width = thumbnail_height  # Square thumbnails
    spacing = 10
    start_x = spacing
    
    # Store thumbnail regions for click detection
    thumbnail_regions = []
    
    for i, photo_path in enumerate(recent_photos):
        if os.path.exists(photo_path):
            thumb_img = cv2.imread(photo_path)
            if thumb_img is not None:
                # Resize to thumbnail
                thumb_resized = cv2.resize(thumb_img, (thumb_width, thumbnail_height))
                
                x_pos = start_x + i * (thumb_width + spacing)
                y_pos = frame_height + 5
                
                # Check if thumbnail fits in canvas
                if x_pos + thumb_width <= frame_width:
                    canvas[y_pos:y_pos+thumbnail_height, x_pos:x_pos+thumb_width] = thumb_resized
                    
                    # Calculate the actual index in camera_roll
                    # We're showing recent_photos which is camera_roll[-max_thumbnails:]
                    # So the first photo shown (i=0) corresponds to camera_roll[len(camera_roll)-len(recent_photos)]
                    actual_index = len(camera_roll) - len(recent_photos) + i
                    
                    # Store the region for click detection
                    thumbnail_regions.append({
                        'path': photo_path,
                        'index': actual_index,
                        'x1': x_pos,
                        'y1': y_pos,
                        'x2': x_pos + thumb_width,
                        'y2': y_pos + thumbnail_height
                    })
                    
                    # Add green border around selected photo
                    if actual_index == selected_index:
                        cv2.rectangle(canvas, (x_pos, y_pos), 
                                    (x_pos+thumb_width, y_pos+thumbnail_height), 
                                    (0, 255, 0), 3)
    
    return canvas, thumbnail_regions

def print_in_background(photo_path, printer_name, job_tracker):
    """
    Sends a photo to the specified CUPS printer in a background thread
    using the more robust subprocess module.
    """
    job_tracker.add(photo_path)
    print(f"Adding {photo_path} to the print queue for '{printer_name}'...")

    try:
        # Create the command as a list of arguments
        command_args = [
            "/usr/bin/lp",
            "-d", printer_name,
            "-o", "fit-to-page",
            photo_path
        ]

        # Run the command
        result = subprocess.run(
            command_args, 
            capture_output=True,  # Captures the output and errors
            text=True             # Decodes output and errors as text
        )

        # Check if the command was successful
        if result.returncode == 0:
            print(f"Successfully sent {photo_path} to the printer.")
        else:
            # If there was an error, print the details
            print("--- PRINTING ERROR ---")
            print(f"Command failed with exit code: {result.returncode}")
            print(f"Standard Output: {result.stdout}")
            print(f"Standard Error: {result.stderr}")
            print("----------------------")

    except Exception as e:
        print(f"A Python exception occurred while trying to print: {e}")
        
    finally:
        job_tracker.remove(photo_path)

def run():
    moth_font = '/Users/astrydpark/Documents/GitHub/QuantumPhotoBooth/fonts/ttf/Sohne/sohne.ttf'
    
    while True:
        enable = input('Camera: ')
        strength = 0.5 # default value for Quantum Blur
        camera_roll = []  # Store paths to processed images
        photo_counter = 0  # Counter for unique filenames
        thumbnail_regions = []  # Store clickable regions
        selected_photo_index = -1  # Track selected photo (-1 means most recent)
        
        printing_jobs = set()
        
        # Variables for double-click detection
        last_click_time = 0
        last_click_region = None
        double_click_threshold = 0.5  # seconds
        
        # Mouse click handler
        def mouse_callback(event, x, y, flags, param):
            nonlocal last_click_time, last_click_region, selected_photo_index
            
            if event == cv2.EVENT_LBUTTONDOWN:
                current_time = time.time()
                
                # Check if click is on a thumbnail
                for region in thumbnail_regions:
                    if region['x1'] <= x <= region['x2'] and region['y1'] <= y <= region['y2']:
                        # Check for double-click
                        is_double_click = (
                            last_click_region == region['index'] and 
                            (current_time - last_click_time) < double_click_threshold
                        )
                        
                        if is_double_click:
                            # Double-click: Open full-size image in separate window
                            full_image = cv2.imread(region['path'])
                            if full_image is not None:
                                # Create a separate window for photo viewing
                                cv2.namedWindow('Photo Viewer', cv2.WINDOW_NORMAL)
                                
                                # View loop for the full-size image
                                while True:
                                    # Create a copy to add instructions
                                    display_img = full_image.copy()
                                    
                                    
                                    display_img = draw_text_with_custom_font (
                                        cv_image = display_img,
                                        text = 'Press L to Print',
                                        position = (20, 40),
                                        font_path = moth_font,
                                        font_size = 20,
                                        color = (255, 255, 255)
                                    )
                                    
                                    display_img = draw_text_with_custom_font (
                                        cv_image = display_img,
                                        text = 'Press any key to return',
                                        position = (20, 60),
                                        font_path = moth_font,
                                        font_size = 20,
                                        color = (255, 255, 255)
                                    )
                                    
                                    cv2.imshow('Photo Viewer', display_img)
                                    key = cv2.waitKey(0)  # Wait for key press
                                    
                                    if key == ord('l') or key == ord('L'):
                                        # Print the image
                                        print(f'Printing: {region['path']}')
                                        
                                        # *** PRINTER ***
                                        
                                        printer_name = 'Canon_SELPHY_CP1500' # lpstat -p -d => printer Canon_SELPHY_CP1500 is idle. etc...
                                        # photo_to_print = region['path']
                                        photo_to_print = os.path.abspath(region['path']) # Recommended setting: Using the absolute path
                                        # Because of the Python script execution path ({$HOME}) VS lp command path (/usr/bin/)
                                        
                                        if photo_to_print in printing_jobs:
                                            print(f"{photo_to_print} is already in the print queue.")
                                        else:
                                            print_thread = threading.Thread(
                                                target=print_in_background,
                                                args=(photo_to_print, printer_name, printing_jobs)
                                            )
                                            print_thread.start()   
                                        
                                    else:
                                        # Any other key returns to camera
                                        cv2.destroyWindow('Photo Viewer')
                                        break
                            # Reset double-click tracking
                            last_click_time = 0
                            last_click_region = None
                        else:
                            # Single click: Select the photo
                            selected_photo_index = region['index']
                            print(f'Selected photo {selected_photo_index + 1}: {region["path"]}')
                            last_click_time = current_time
                            last_click_region = region['index']
                        
                        break
        
        if enable == 'photobooth':
            cap = cv2.VideoCapture(0) # *** Modify the number based on the port number of a USB webcam!
            
            # Set up mouse callback
            cv2.namedWindow('Quantum Blur')
            cv2.setMouseCallback('Quantum Blur', mouse_callback)
            
            while True:
                ret, frame = cap.read()
                
                # ========== The camera window is now opened ===========
                # Display strength value on frame
                frame = draw_text_with_custom_font (
                    cv_image = frame,
                    text = f'{strength:.1f}', # Adjusted the value because of floating-point imprecision.
                    position = (50, 50),
                    font_path = moth_font,
                    font_size = 20,
                    color = (255, 255, 255)
                )
                # cv2.putText(frame, f'{strength:.1f}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 3)
                
                # Display controls info
                frame = draw_text_with_custom_font (
                    cv_image = frame,
                    text = 'Space or Enter to take photo, Backspace to delete photo', 
                    position = (10, frame.shape[0] - 90),
                    font_path = moth_font,
                    font_size = 16,
                    color = (255, 255, 255)
                )
                
                frame = draw_text_with_custom_font (
                    cv_image = frame,
                    text = 'W or S for adding  more or less strength to Quantum Blur', 
                    position = (10, frame.shape[0] - 60),
                    font_path = moth_font,
                    font_size = 16,
                    color = (255, 255, 255)
                )
                
                frame = draw_text_with_custom_font (
                    cv_image = frame,
                    text = 'Backspace to delete photo from photo roll', 
                    position = (10, frame.shape[0] - 30),
                    font_path = moth_font,
                    font_size = 16,
                    color = (255, 255, 255)
                )
                
                # Update selected_photo_index if it's out of bounds
                if selected_photo_index >= len(camera_roll):
                    selected_photo_index = len(camera_roll) - 1
                
                # Create display with camera roll at bottom
                display_frame, thumbnail_regions = create_display_with_camera_roll(
                    frame, camera_roll, selected_index=selected_photo_index
                )
                
                cv2.imshow('Quantum Blur', display_frame)
                k = 0xFF & cv2.waitKey(1)
                
                if k == 32 or k == 13:  # Space or Enter key
                    # 3 seconds of countdown
                    for countdown in range(3, 0, -1):
                        start_time = time.time()
                        while time.time() - start_time < 1.0:
                            ret, countdown_frame = cap.read()
                            # Display countdown on frame
                            countdown_display = countdown_frame.copy()
                            countdown_display = draw_text_with_custom_font (
                                cv_image = countdown_display,
                                text = str(countdown),
                                position = (250, 300),
                                font_path = moth_font,
                                font_size = 20,
                                color = (255, 255, 255)
                            )
                            
                            # Add camera roll to countdown display
                            display_frame, _ = create_display_with_camera_roll(
                                countdown_display, camera_roll, selected_index=selected_photo_index
                            )
                            cv2.imshow('Quantum Blur', display_frame)
                            cv2.waitKey(1)
                    
                    # Capture fresh frame to display the message
                    ret, processing_frame = cap.read()
                    
                    processing_frame = draw_text_with_custom_font(
                        cv_image = processing_frame,
                        text = 'Image Processing with Quantum...',
                        position = (250, 300),
                        font_path = moth_font,
                        font_size = 20,
                        color = (255, 255, 255)
                    )
                    
                    processing_display, _ = create_display_with_camera_roll(
                        processing_frame, camera_roll, selected_index=selected_photo_index
                    )
                    cv2.imshow('Quantum Blur', processing_display)
                    cv2.waitKey(1)
                    
                    # Take the photo
                    ret, final_frame = cap.read()
                    cv2.imwrite('quantumblur.jpg', final_frame)
                    
                    # ========== Image is saved in local storage ===========
                    # Now, let's do something to this image.
                    
                    # Modify the size so that QB won't take forever.
                    original = Image.open('quantumblur.jpg') 
                    new_size = (int(original.width * 0.4), int(original.height * 0.4))
                    original = original.resize(new_size, Image.LANCZOS)
                    
                    # Built-in blur effect: xi = 0 (no blur) <-> xi = 1 (strong blur effect)
                    blurred = qb.circuits2image(qb.blur_image(original, strength))
                    
                    # *** MOTH Quantum *** => For branding (Logo & MSG)
                    hello = 'made with Quantum Blur, by MOTH'
                    logo = '/Users/astrydpark/Documents/GitHub/QuantumPhotoBooth/MOTH.png'
                    final_final = add_branding(
                        base_image=blurred,
                        logo_path=logo,
                        text=hello,
                        font_path=moth_font
                    )
                    
                    # Save with unique filename
                    photo_counter += 1
                    result_filename = f'result_{photo_counter}.jpg'
                    final_final.save(result_filename)
                    camera_roll.append(result_filename)
                    
                    # Select the newly captured photo
                    selected_photo_index = len(camera_roll) - 1
                    
                    print(f'Photo saved: {result_filename} (Total: {len(camera_roll)})')
                    
                elif k == ord('w') or k == ord('W'):
                    print('Increasing QB strength...')
                    strength += 0.1
                    if (strength > 1.0):
                        strength = 1.0
                    elif (strength < 0.0):
                        strength = 0.0
                elif k == ord('s') or k == ord('S'):
                    print('Decreasing QB strength...')
                    strength -= 0.1
                    if (strength > 1.0):
                        strength = 1.0
                    elif (strength < 0.0):
                        strength = 0.0
                elif k == 8 or k == 127:  # Backspace (8) or Delete (127)
                    if camera_roll:
                        # If no photo is selected or index is invalid, select the last photo
                        if selected_photo_index < 0 or selected_photo_index >= len(camera_roll):
                            selected_photo_index = len(camera_roll) - 1
                        
                        deleted_photo = camera_roll[selected_photo_index]
                        if os.path.exists(deleted_photo):
                            os.remove(deleted_photo)
                            print(f'Deleted: {deleted_photo}')
                        else:
                            print(f'File not found: {deleted_photo}')
                        
                        camera_roll.pop(selected_photo_index)
                        
                        # Adjust selected index after deletion
                        if camera_roll:
                            # If we deleted the last photo, select the new last photo
                            if selected_photo_index >= len(camera_roll):
                                selected_photo_index = len(camera_roll) - 1
                            # Otherwise keep the same index (which now points to the next photo)
                        else:
                            selected_photo_index = -1
                            print('Camera roll is now empty.')
                    else:
                        print('No photos to delete.')
                elif k == ord('p') or k == ord('P'):
                    print('Finish the loop.')
                    cap.release()
                    cv2.destroyAllWindows()
                    cv2.waitKey(1)
                    break
                
        elif enable == 'exit':
            print('Quantum Blur - Ended.')
            break
        else:
            print('Invalid.')

init()