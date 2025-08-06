import { quantumblur } from './quantumblur.js';

// --- DOM Elements ---
const userMediaInput = document.getElementById('userMedia');
const processBtn = document.getElementById('processBtn');
const previewCanvas = document.getElementById('preview');
const resultCanvas = document.getElementById('result');
const videoSource = document.getElementById('videoSource');
const statusArea = document.getElementById('status-area');
const statusText = document.getElementById('status-text');
const downloadLink = document.getElementById('download-link');

// --- State Variables ---
let mediaType = null;
let mediaRecorder;
let recordedChunks = [];

// =======================================================
// === FILE HANDLING
// =======================================================

userMediaInput.addEventListener('change', (e) => {
    let file = e.target.files[0];
    if (!file) return;

    // Reset UI for new file
    statusArea.style.display = 'none';
    downloadLink.style.display = 'none';
    recordedChunks = [];

    const objectURL = URL.createObjectURL(file);

    if (file.type.startsWith('image/')) {
        mediaType = 'image';
        videoSource.pause();
        videoSource.src = ''; 
        handleImage(objectURL);
    } else if (file.type.startsWith('video/')) {
        mediaType = 'video';
        handleVideo(objectURL);
    }
});

function handleImage(src) {
    const img = new Image();
    img.src = src;
    img.onload = () => {
        previewCanvas.width = img.naturalWidth;
        previewCanvas.height = img.naturalHeight;
        resultCanvas.width = img.naturalWidth;
        resultCanvas.height = img.naturalHeight;
        const ctx = previewCanvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(src);
    };
}

function handleVideo(src) {
    videoSource.src = src;

    videoSource.onloadedmetadata = () => {
        previewCanvas.width = videoSource.videoWidth;
        previewCanvas.height = videoSource.videoHeight;
        resultCanvas.width = videoSource.videoWidth;
        resultCanvas.height = videoSource.videoHeight;
    };
    
    videoSource.onloadeddata = () => {
        const previewCtx = previewCanvas.getContext('2d');
        videoSource.pause();
        videoSource.currentTime = 0;
        previewCtx.drawImage(videoSource, 0, 0, previewCanvas.width, previewCanvas.height);
    };
}


// =======================================================
// === PROCESSING LOGIC
// =======================================================

// --- Main Button Event ---
processBtn.onclick = function() {
    if (!mediaType) {
        alert('Please upload an image or video first.');
        return;
    }

    if (mediaType === 'image') {
        processImage();
    } else if (mediaType === 'video') {
        processVideo();
    }
};

// --- Image Processing ---
function processImage() {
    statusArea.style.display = 'block';
    statusText.textContent = 'Processing image...';
    
    // Use setTimeout to allow UI to update before blocking with calculations
    setTimeout(() => {
        const strengthVal = document.getElementById('strength').value;
        const resultImageData = quantumblur(strengthVal);
        const ctx = resultCanvas.getContext('2d');
        ctx.putImageData(resultImageData, 0, 0);
        statusText.textContent = 'Image processing complete!';
    }, 50);
}

// --- Video Processing ---
async function processVideo() {
    // 1. Setup UI and MediaRecorder
    statusArea.style.display = 'block';
    downloadLink.style.display = 'none';
    processBtn.disabled = true; // Prevent re-clicking during processing

    const resultStream = resultCanvas.captureStream(30); // 30 fps
    mediaRecorder = new MediaRecorder(resultStream, { mimeType: 'video/webm; codecs=vp9' });
    
    recordedChunks = [];
    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            recordedChunks.push(event.data);
        }
    };

    mediaRecorder.onstop = () => {
        const blob = new Blob(recordedChunks, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.download = 'quantum-blur-video.webm';
        downloadLink.style.display = 'block';
        statusText.textContent = 'Video processing complete!';
        processBtn.disabled = false;
    };
    
    mediaRecorder.start();

    // 2. Start frame-by-frame processing
    videoSource.currentTime = 0;
    await processNextFrame();
}

// --- Recursive function to process video frame by frame ---
async function processNextFrame() {
    if (videoSource.currentTime >= videoSource.duration) {
        // Stop when video ends
        mediaRecorder.stop();
        return;
    }

    // Update progress
    const progress = (videoSource.currentTime / videoSource.duration) * 100;
    statusText.textContent = `Processing video... ${Math.round(progress)}%`;

    // Seek the video to the next frame's time
    // For simplicity, we step through based on a fixed frame rate (e.g., 30 fps)
    const frameDuration = 1 / 30; 
    videoSource.currentTime = Math.min(videoSource.duration, videoSource.currentTime + frameDuration);

    // Wait for the seek to complete
    await new Promise(resolve => { videoSource.onseeked = resolve; });
    
    // Draw the new frame to the preview canvas
    const previewCtx = previewCanvas.getContext('2d', { willReadFrequently: true });
    previewCtx.drawImage(videoSource, 0, 0, previewCanvas.width, previewCanvas.height);
    
    // Apply the quantum blur
    const strengthVal = document.getElementById('strength').value;
    const resultImageData = quantumblur(strengthVal);
    
    // Draw the blurred frame to the result canvas (which is being recorded)
    const resultCtx = resultCanvas.getContext('2d');
    resultCtx.putImageData(resultImageData, 0, 0);

    // Schedule the next frame to be processed
    requestAnimationFrame(processNextFrame);
}