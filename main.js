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
        previewCanvas.getContext('2d').drawImage(img, 0, 0);
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
    // FIX: This ensures the first frame of the source video is always shown.
    videoSource.onseeked = () => {
        previewCanvas.getContext('2d').drawImage(videoSource, 0, 0, previewCanvas.width, previewCanvas.height);
    };
    videoSource.onloadeddata = () => {
        videoSource.pause();
        videoSource.currentTime = 0; // Seeking to 0 will trigger the 'onseeked' event above.
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

// --- STAGE 1: Render all frames and store them ---
async function renderAllFrames() {
    const processedFrames = [];
    const FPS = 30;
    const frameDuration = 1 / FPS;
    videoSource.currentTime = 0;

    const offscreenCanvas = document.createElement('canvas');
    offscreenCanvas.width = resultCanvas.width;
    offscreenCanvas.height = resultCanvas.height;
    const offscreenCtx = offscreenCanvas.getContext('2d');

    async function processNextFrameToMemory() {
        if (videoSource.currentTime >= videoSource.duration) {
            statusText.textContent = 'All frames rendered. Now encoding video...';
            encodeVideoFromFrames(processedFrames, FPS);
            return;
        }

        const progress = (videoSource.currentTime / videoSource.duration) * 100;
        statusText.textContent = `Stage 1: Rendering frame... ${Math.round(progress)}%`;

        await new Promise(resolve => { videoSource.onseeked = resolve; videoSource.currentTime += frameDuration; });

        previewCanvas.getContext('2d', { willReadFrequently: true }).drawImage(videoSource, 0, 0, previewCanvas.width, previewCanvas.height);
        const resultImageData = quantumblur(strengthVal.value);
        
        // FIX: Show the first processed frame immediately for user feedback.
        if (processedFrames.length === 0) {
            resultCanvas.getContext('2d').putImageData(resultImageData, 0, 0);
        }

        offscreenCtx.putImageData(resultImageData, 0, 0);
        const blob = await new Promise(resolve => offscreenCanvas.toBlob(resolve, 'image/jpeg', 0.9));
        processedFrames.push(blob);

        requestAnimationFrame(processNextFrameToMemory);
    }
    
    const strengthVal = document.getElementById('strength');
    await processNextFrameToMemory();
}

// --- STAGE 2: Encode the stored frames into a video at the correct speed ---
function encodeVideoFromFrames(frames, fps) {
    const resultStream = resultCanvas.captureStream(fps);
    const mediaRecorder = new MediaRecorder(resultStream, { mimeType: 'video/webm; codecs=vp9' });
    const recordedChunks = [];

    mediaRecorder.ondataavailable = (event) => recordedChunks.push(event.data);
    mediaRecorder.onstop = () => {
        const blob = new Blob(recordedChunks, { type: 'video/webm' });
        downloadLink.href = URL.createObjectURL(blob);
        downloadLink.download = 'quantum-blur-video.webm';
        downloadLink.style.display = 'block';
        statusText.textContent = 'Video encoding complete!';
        processBtn.disabled = false;
    };

    mediaRecorder.start();

    let frameIndex = 0;
    const resultCtx = resultCanvas.getContext('2d');
    
    // FIX: Use a timed interval instead of requestAnimationFrame to ensure the correct framerate.
    const interval = setInterval(() => {
        if (frameIndex >= frames.length) {
            clearInterval(interval);
            mediaRecorder.stop();
            return;
        }
        
        const progress = (frameIndex / frames.length) * 100;
        statusText.textContent = `Stage 2: Encoding video... ${Math.round(progress)}%`;

        const img = new Image();
        img.onload = () => {
            resultCtx.drawImage(img, 0, 0);
            URL.revokeObjectURL(img.src);
        };
        img.src = URL.createObjectURL(frames[frameIndex]);
        
        frameIndex++;
    }, 1000 / fps);
}