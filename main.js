import { test } from './quantumblur.js';

document.getElementById('userImage').addEventListener('change', (e) => {
    let files = e.target.files;
    let preview = document.getElementById('preview');

    preview.innerHTML = ''; // Clear any existing content

    for (let i = 0; i < files.length; i++) {
        let file = files[i];

        if (!file.type.match('image.*')) {
            continue;
        }

        let imgContainer = document.createElement('div');
        // imgContainer.style.marginBottom = '20px';

        let img = document.createElement('img');
        img.src = URL.createObjectURL(file);

        imgContainer.appendChild(img);

        preview.appendChild(imgContainer);

        console.log(`File ${i + 1}: ${file.name}, Size: ${file.size} bytes, Type: ${file.type}`);
    }
});

document.getElementById('qbBtn').onclick = function() {
    let before = document.getElementById('userImage');
    if (before.files.length === 0) {
        alert('Upload an image first.');
        return;
    }

    let strengthVal = document.getElementById('strength').value;
    console.log(`Quantum Blur strength: ${strengthVal}`);

    test();
};