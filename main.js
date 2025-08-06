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

// =======================================================
// === FILE HANDLING
// =======================================================

userMediaInput.addEventListener('change', (e) => {
    let file = e.target.files[0];
    if (!file) return;

    statusArea.style.display = 'none';
    downloadLink.style.display = 'none';
    processBtn.disabled = false;

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
        videoSource.pause();
        videoSource.currentTime = 0;
        previewCanvas.getContext('2d').drawImage(videoSource, 0, 0, previewCanvas.width, previewCanvas.height);
    };
}

// =======================================================
// === PROCESSING LOGIC
// =======================================================

processBtn.onclick = function() {
    if (!mediaType) {
        alert('Please upload an image or video first.');
        return;
    }
    processBtn.disabled = true;
    statusArea.style.display = 'block';
    downloadLink.style.display = 'none';

    if (mediaType === 'image') {
        processImage();
    } else if (mediaType === 'video') {
        // Start the new two-stage process for video
        renderAllFrames();
    }
};

function processImage() {
    statusText.textContent = 'Processing image...';
    setTimeout(() => {
        const strengthVal = document.getElementById('strength').value;
        const resultImageData = quantumblur(strengthVal);
        resultCanvas.getContext('2d').putImageData(resultImageData, 0, 0);
        statusText.textContent = 'Image processing complete!';
        processBtn.disabled = false;
    }, 50);
}

// --- STAGE 1: Render all frames and store them in memory ---
async function renderAllFrames() {
    const processedFrames = [];
    const frameDuration = 1 / 30; // Assuming 30fps
    videoSource.currentTime = 0;

    // A hidden canvas to do the off-screen drawing
    const offscreenCanvas = document.createElement('canvas');
    offscreenCanvas.width = resultCanvas.width;
    offscreenCanvas.height = resultCanvas.height;
    const offscreenCtx = offscreenCanvas.getContext('2d');

    async function processNextFrameToMemory() {
        if (videoSource.currentTime >= videoSource.duration) {
            // Finished rendering, now start encoding
            statusText.textContent = 'All frames rendered. Now encoding video...';
            encodeVideoFromFrames(processedFrames);
            return;
        }

        const progress = (videoSource.currentTime / videoSource.duration) * 100;
        statusText.textContent = `Stage 1: Rendering frame... ${Math.round(progress)}%`;

        // Seek the video and wait for it to be ready
        videoSource.currentTime = Math.min(videoSource.duration, videoSource.currentTime + frameDuration);
        await new Promise(resolve => { videoSource.onseeked = resolve; });

        // Apply quantum blur
        previewCanvas.getContext('2d', { willReadFrequently: true }).drawImage(videoSource, 0, 0, previewCanvas.width, previewCanvas.height);
        const resultImageData = quantumblur(strengthVal.value);

        // Draw the result to our hidden canvas and store it as a blob
        offscreenCtx.putImageData(resultImageData, 0, 0);
        const blob = await new Promise(resolve => offscreenCanvas.toBlob(resolve, 'image/jpeg', 0.9));
        processedFrames.push(blob);

        // Process the next frame
        requestAnimationFrame(processNextFrameToMemory);
    }
    
    const strengthVal = document.getElementById('strength');
    await processNextFrameToMemory();
}


// --- STAGE 2: Encode the stored frames into a video file ---
function encodeVideoFromFrames(frames) {
    const resultStream = resultCanvas.captureStream(30);
    const mediaRecorder = new MediaRecorder(resultStream, { mimeType: 'video/webm; codecs=vp9' });
    const recordedChunks = [];

    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) recordedChunks.push(event.data);
    };

    mediaRecorder.onstop = () => {
        const blob = new Blob(recordedChunks, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.download = 'quantum-blur-video.webm';
        downloadLink.style.display = 'block';
        statusText.textContent = 'Video encoding complete!';
        processBtn.disabled = false;
    };

    mediaRecorder.start();

    // This loop plays back the stored frames in real-time
    let frameIndex = 0;
    const resultCtx = resultCanvas.getContext('2d');
    
    function drawNextFrame() {
        if (frameIndex >= frames.length) {
            mediaRecorder.stop();
            return;
        }
        
        const progress = (frameIndex / frames.length) * 100;
        statusText.textContent = `Stage 2: Encoding video... ${Math.round(progress)}%`;

        // Create an image from the blob and draw it to the canvas being recorded
        const img = new Image();
        img.onload = () => {
            resultCtx.drawImage(img, 0, 0);
            URL.revokeObjectURL(img.src); // Clean up memory
            frameIndex++;
            requestAnimationFrame(drawNextFrame);
        };
        img.src = URL.createObjectURL(frames[frameIndex]);
    }

    drawNextFrame();
}