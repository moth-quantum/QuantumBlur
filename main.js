import { test } from './quantumblur.js';

document.getElementById('userImage').addEventListener('change', (e) => {
    let files = e.target.files;
    let preview = document.getElementById('preview'); // Already a HTML canvas instance

    preview.innerHTML = ''; // Clear any existing content

    for (let i = 0; i < files.length; i++) {
        let file = files[i];

        if (!file.type.match('image.*')) continue;

        /*
        // Create a HTML canvas instance
        const canvas = document.createElement('canvas');
        canvas.setAttribute('id', 'sketchbook');
        preview.appendChild(canvas); // Make the element exists in the DOM.
        */

        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);

        img.onload = () => {

            preview.width = img.naturalWidth;
            preview.height = img.naturalHeight;
            const ctx = preview.getContext('2d');

            ctx.drawImage(img, 0, 0);

            // const d = ctx.getImageData(0, 0, preview.width, preview.height);
            // console.log('Pixel data: ', d.data);

            URL.revokeObjectURL(img.src);
        }

        preview.appendChild(img);
    }
});

document.getElementById('qbBtn').onclick = function() {
    let before = document.getElementById('userImage');
    if (before.files.length === 0) {
        alert('Upload an image first.');
        return;
    }

    let strengthVal = document.getElementById('strength').value;
    // console.log(`Quantum Blur strength: ${strengthVal}`);

    // test();
};