import quantumblur as qb
import cv2
import time
from PIL import Image

def init():
    while True:
        boot = input('Activate: ')
        if boot == 'quantumblur':
            run()
            break
        else:
            print('Invalid.')

def run():
    while True:
        enable = input('Camera: ')
        strength = 0.5 # default value for Quantum Blur
        if enable == 'photobooth':
            cap = cv2.VideoCapture(0) # *** Modify the number based on the port number of a USB webcam!
            while True:
                ret, frame = cap.read()
                k = 0xFF & cv2.waitKey(1)
                cv2.imshow('Quantum Blur', frame)
                
                # ========== The camera window is now opened ===========
                
                if k == 32 or k == 13:  # Space or Enter key
                    # 3 seconds of countdown
                    for countdown in range(3, 0, -1):
                        start_time = time.time()
                        while time.time() - start_time < 1.0:
                            ret, countdown_frame = cap.read()
                            # Display countdown on frame
                            display_frame = countdown_frame.copy()
                            cv2.putText(display_frame, str(countdown), (250, 300), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 10, (255, 255, 0), 15)
                            cv2.imshow('Quantum Blur', display_frame) # The name of the window
                            cv2.waitKey(3)  # Small delay to refresh display
                            
                    cv2.putText(display_frame, 'Processing... Standby!', (250, 300), cv2.FONT_HERSHEY_SIMPLEX, 10, (0, 0, 0), 15)
                    cv2.imshow('Quantum Blur', display_frame)
                    cv2.waitKey(1)  # Display the message
                    
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
                    blurred.save('result.jpg')
                    
                    # *** Now send this to the printer
                    
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