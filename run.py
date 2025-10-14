'''
import quantumblur as qb
import cv2
import time
import numpy as np
from PIL import Image
import os

def init():
    while True:
        boot = input('Activate: ')
        if boot == 'quantumblur':
            run()
            break
        else:
            print('Invalid.')

def create_display_with_camera_roll(frame, camera_roll, thumbnail_height=120):
    """Create a composite display with camera feed and thumbnail roll at bottom"""
    if not camera_roll:
        return frame, []
    
    frame_height, frame_width = frame.shape[:2]
    
    # Create a larger canvas to fit frame + camera roll
    canvas_height = frame_height + thumbnail_height + 10
    canvas = np.zeros((canvas_height, frame_width, 3), dtype=np.uint8)
    
    # Place the camera frame at the top
    canvas[0:frame_height, 0:frame_width] = frame
    
    # Add separator line
    cv2.line(canvas, (0, frame_height), (frame_width, frame_height), (100, 100, 100), 2)
    
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
                    
                    # Store the region for click detection
                    thumbnail_regions.append({
                        'path': photo_path,
                        'x1': x_pos,
                        'y1': y_pos,
                        'x2': x_pos + thumb_width,
                        'y2': y_pos + thumbnail_height
                    })
                    
                    # Add border around most recent photo
                    if i == len(recent_photos) - 1:
                        cv2.rectangle(canvas, (x_pos, y_pos), 
                                    (x_pos+thumb_width, y_pos+thumbnail_height), 
                                    (0, 255, 0), 3)
    
    return canvas, thumbnail_regions

def run():
    while True:
        enable = input('Camera: ')
        strength = 0.5 # default value for Quantum Blur
        camera_roll = []  # Store paths to processed images
        photo_counter = 0  # Counter for unique filenames
        thumbnail_regions = []  # Store clickable regions
        
        # Mouse click handler
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                # Check if click is on a thumbnail
                for region in thumbnail_regions:
                    if region['x1'] <= x <= region['x2'] and region['y1'] <= y <= region['y2']:
                        # Display the full-size image
                        full_image = cv2.imread(region['path'])
                        if full_image is not None:
                            # View loop for the full-size image
                            while True:
                                # Create a copy to add instructions
                                display_img = full_image.copy()
                                cv2.putText(display_img, 'L: Print | Any other key: Return to camera', 
                                           (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                cv2.imshow('Quantum Blur', display_img)
                                key = cv2.waitKey(0)  # Wait for key press
                                
                                if key == ord('l') or key == ord('L'):
                                    # Print the image
                                    print(f'Printing: {region["path"]}')
                                    
                                    # *** Now send this to the printer
                                    
                                    # For macOS, you can use: os.system(f'lp "{region["path"]}"')
                                    # For now, just show a confirmation
                                    confirm_img = full_image.copy()
                                    cv2.putText(confirm_img, 'Sent to printer.', 
                                               (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                                    cv2.imshow('Quantum Blur', confirm_img)
                                    cv2.waitKey(1000)  # Show confirmation for 2 seconds
                                else:
                                    # Any other key returns to camera
                                    break
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
                cv2.putText(frame, str(strength), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 3)
                
                # Display controls info
                cv2.putText(frame, 'Space: Capture | W/S: Blur +/- | D: Delete Last | P: Exit', 
                           (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # Create display with camera roll at bottom
                display_frame, thumbnail_regions = create_display_with_camera_roll(frame, camera_roll)
                
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
                            cv2.putText(countdown_display, str(countdown), (250, 300), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 10, (255, 255, 0), 15)
                            
                            # Add camera roll to countdown display
                            display_frame, _ = create_display_with_camera_roll(countdown_display, camera_roll)
                            cv2.imshow('Quantum Blur', display_frame) # The name of the window
                            cv2.waitKey(1)  # Small delay to refresh display
                    
                    # Capture fresh frame to display the message
                    ret, processing_frame = cap.read()
                    cv2.putText(processing_frame, 'Processing... Standby!', (250, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 15)
                    processing_display, _ = create_display_with_camera_roll(processing_frame, camera_roll)
                    cv2.imshow('Quantum Blur', processing_display)
                    cv2.waitKey(1) # Small delay to refresh display
                    
                    # Take the photo
                    ret, final_frame = cap.read()
                    cv2.imwrite('quantumblur.jpg', final_frame)
                    
                    # ========== Image is saved in local storage ===========
                    # Now, let's do something to this image.
                    
                    # Modify the size so that QB won't take forever.
                    original = Image.open('quantumblur.jpg') 
                    new_size = (int(original.width * 0.4), int(original.height * 0.4))
                    original = original.resize(new_size, Image.LANCZOS)
                    # MacBook Pro: Modified from 1920x1080 -> Dramatically faster!
                    # If we buy a 720p webcam, we can adjust the scale factor from 0.4 to 0.2, etc.
                    
                    # Built-in blur effect: xi = 0 (no blur) <-> xi = 1 (strong blur effect)
                    blurred = qb.circuits2image(qb.blur_image(original, strength))
                    
                    # Save with unique filename
                    photo_counter += 1
                    result_filename = f'result_{photo_counter}.jpg'
                    blurred.save(result_filename)
                    camera_roll.append(result_filename)
                    
                    print(f'Photo saved: {result_filename} (Total: {len(camera_roll)})')
                
                    
                elif k == ord('w') or k == ord('W'):
                    print('Increasing QB strengh...')
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
                elif k == ord('d') or k == ord('D'):
                    if camera_roll:
                        deleted_photo = camera_roll.pop()
                        if os.path.exists(deleted_photo):
                            os.remove(deleted_photo)
                            print(f'Deleted: {deleted_photo}')
                    else:
                        print('No photos to delete.')
                elif k == ord('p') or k == ord('P'):
                    print('Finish the loop.')
                    cap.release()
                    cv2.destroyAllWindows()
                    cv2.waitKey(1)  # Allow time for closing the window
                    break
                
                
        elif enable == 'exit':
            print('Quantum Blur - Ended.')
            break
        else:
            print('Invalid.')

init()
'''

import quantumblur as qb
import cv2
import time
import numpy as np
from PIL import Image
import os

def init():
    while True:
        boot = input('Activate: ')
        if boot == 'quantumblur':
            run()
            break
        else:
            print('Invalid.')

def create_display_with_camera_roll(frame, camera_roll, thumbnail_height=120, selected_index=-1):
    """Create a composite display with camera feed and thumbnail roll at bottom"""
    if not camera_roll:
        return frame, []
    
    frame_height, frame_width = frame.shape[:2]
    
    # Create a larger canvas to fit frame + camera roll
    canvas_height = frame_height + thumbnail_height + 10
    canvas = np.zeros((canvas_height, frame_width, 3), dtype=np.uint8)
    
    # Place the camera frame at the top
    canvas[0:frame_height, 0:frame_width] = frame
    
    # Add separator line
    cv2.line(canvas, (0, frame_height), (frame_width, frame_height), (100, 100, 100), 2)
    
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

def run():
    while True:
        enable = input('Camera: ')
        strength = 0.5 # default value for Quantum Blur
        camera_roll = []  # Store paths to processed images
        photo_counter = 0  # Counter for unique filenames
        thumbnail_regions = []  # Store clickable regions
        selected_photo_index = -1  # Track selected photo (-1 means most recent)
        
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
                            # Double-click: Open full-size image
                            full_image = cv2.imread(region['path'])
                            if full_image is not None:
                                # View loop for the full-size image
                                while True:
                                    # Create a copy to add instructions
                                    display_img = full_image.copy()
                                    cv2.putText(display_img, 'L: Print | Any other key: Return to camera', 
                                               (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                    cv2.imshow('Quantum Blur', display_img)
                                    key = cv2.waitKey(0)  # Wait for key press
                                    
                                    if key == ord('l') or key == ord('L'):
                                        # Print the image
                                        print(f'Printing: {region["path"]}')
                                        # *** Send to printer here
                                        # For macOS, you can use: os.system(f'lp "{region["path"]}"')
                                        # For now, just show a confirmation
                                        confirm_img = full_image.copy()
                                        cv2.putText(confirm_img, 'Sent to printer! Press any key to continue', 
                                                   (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                                        cv2.imshow('Quantum Blur', confirm_img)
                                        cv2.waitKey(2000)  # Show confirmation for 2 seconds
                                    else:
                                        # Any other key returns to camera
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
                cv2.putText(frame, str(strength), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 3)
                
                # Display controls info
                cv2.putText(frame, 'Space: Capture | W/S: Blur +/- | Backspace: Delete Selected | P: Exit', 
                           (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
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
                            cv2.putText(countdown_display, str(countdown), (250, 300), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 10, (255, 255, 0), 15)
                            
                            # Add camera roll to countdown display
                            display_frame, _ = create_display_with_camera_roll(
                                countdown_display, camera_roll, selected_index=selected_photo_index
                            )
                            cv2.imshow('Quantum Blur', display_frame)
                            cv2.waitKey(1)
                    
                    # Capture fresh frame to display the message
                    ret, processing_frame = cap.read()
                    cv2.putText(processing_frame, 'Processing... Standby!', (250, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 15)
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
                    
                    # Save with unique filename
                    photo_counter += 1
                    result_filename = f'result_{photo_counter}.jpg'
                    blurred.save(result_filename)
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