// (C) Copyright Moth Quantum 2025.
//
// This code is licensed under the Apache License, Version 2.0. You may
// obtain a copy of this license in the LICENSE.txt file in the root directory
// of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
//
// Any modifications or derivative works of this code must retain this
// copyright notice, and modified files need to carry a notice indicating
// that they have been altered from the originals.

// (C) Copyright IBM 2020s.

//
// This code is licensed under the Apache License, Version 2.0. You may
// obtain a copy of this license in the LICENSE.txt file in the root directory
// of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
//
// Any modifications or derivative works of this code must retain this
// copyright notice, and modified files need to carry a notice indicating
// that they have been altered from the originals.


// (Don't need to import anything in JS) Math.random() VS import math; import random

import QuantumCircuit from './micromoth.js';
import { simulate } from './micromoth.js'; // rotate, superposition, phaseturn also exist.

// =================================================
// ============== Test functions ===================
// =================================================

function imgtest() {
    const user = document.getElementById('preview');
    const ctx = user.getContext('2d', { willReadFrequently: true });

    let d = ctx.getImageData(0, 0, user.width, user.height);
    const pixels = d.data;

    console.log(pixels);
}

// Test the connection toward micromoth.js with Bell state and GHZ state
function innertest() {
    let qc = new QuantumCircuit(3, 3);
    // Bell state
    qc.h(0);
    qc.cx(0, 1);

    // GHZ state
    qc.cx(1, 2);

    let c = simulate(qc, 1024, 'statevector');
    console.log(c);
}

export function test() {
    console.log('foo');

    innertest();

    imgtest();
}

// ==============================================
// ============*** Quantum Blur ***==============
// ==============================================

export function quantumblur(uploadedImage, strength = 0.5) {
    const ctx = uploadedImage.getContext("2d"); // Access to the canvas (canvas.img => The thing the user uploaded)
    const uploadedImageData = ctx.getImageData(0, 0, uploadedImage.width, uploadedImage.height);

    // Convert strength (1 to 10) to xi parameter (0.1 to 1.0)
    const xi = strength / 10.0

    // Apply Quantum Blur!
    const circuits = blurImage(uploadedImageData, xi);

    // Convert the result back to image
    const qbImageData = circuits2image(circuits);

    return qbImageData;
}

// 1. blurImage(): QB effect itself -> image2heights(), blurHeight()
function blurImage(d, xi, circuits = null, axis = 'x', log = false) {
    const heights = image2heights(d);

    if (circuits == null) circuits = [null, null, null];

    for (let j = 0; j < heights.length; j++) circuits[j] = blurHeight(heights[j], xi, axis, circuits[j], log);

    return circuits;
}

// 2. blurHeight(): 
function blurHeight(height, xi, axis = 'x', circuit = null, log = false, grid = null) {
    const [Lx, Ly] = getSize(height);
    let gridData, n;

    if (grid == null) [gridData, n] = makeGrid(Lx, Ly);
    else gridData = grid; n = Object.keys(grid)[0].length;
}

// =================== 2 series ====================

// image2heights(): Convert RGB image to height dictionaries for each colour channel
function image2heights(d) {
    const { width, height, data } = d;
    const heights = [{}, {}, {}]

    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = (y * width + x) * 4; // index
            const r = data[idx]; // Red
            const g = data[idx + 1]; // Green
            const b = data[idx + 2]; // Blue

            heights[0][`${x}, ${y}`] = r;
            heights[1][`${x}, ${y}`] = r;
            heights[2][`${x}, ${y}`] = r;
        }
    }

    return heights;
}

function height2circuit(height, log = false, eps = 1e-2, grid = null) {
    const [Lx, Ly] = getSize(height);
    let gridData, n;

    if (grid == null) [gridData, n] = makeGrid(Lx, Ly);
    else gridData = grid; n = Object.keys(grid)[0].length;

    // Create statevector
    let statevector = Array(2 ** n).fill(null).map(() => [0, 0]);

    if (log) {
        // Logarithmic encoding
        const maxH = Math.max(...Object.values(height));
        const normalisedHeight = {};

        for (const pos in height) normalisedHeight[pos] = height[pos] / maxH;

        const minH = Math.min(...Object.values(normalisedHeight).filter((h) => h > eps));
        const baseline = 1.0 / minH;

        for (const bitstring in gridData) {
            const [x, y] = gridData[bitstring];
            const key = `${x}, ${y}`;

            if (key in height) {
                const h = normalisedHeight[key];
                const amp = Math.sqrt(Math.pow(baseline, h / minH));
                statevector[Number.parseInt(bitstring, 2)] = [amp, 0]
            }
        }
    }
    else {
        // Linear engoding
        for (const bitstring in gridData) {
            const [x, y] = gridData[bitstring]
            const key = `${x}, ${y}`;

            if (key in height) {
                const amp = Math.sqrt(height[key]);
                statevector[Number.parseInt(bitstring, 2)] = [amp, 0];
            }
        }
    }

    statevector = norm(statevector);

    // CREATE Quantum CIRCUIT!
    const quantumcircuit = new QuantumCircuit(n, n);
    quantumcircuit.name = `(${Lx}, ${Ly})`;
    quantumcircuit.initialize(statevector);

    return quantumcircuit;
}

// circuit2probs: ACTUAL SIMULATION of the constructed circuit.
function circuit2probs(qc) {
    const result = simulate(qc, 1024, 'probability_dictionary');
    
    return result;
}

function probs2height(probes, size = null, log = false, grid = null) {
    let Lx, Ly;
    if (size) {
        [Lx, Ly] = size;
    }
}

// circuits2image(): Bring out Quantum circuits so that we could translate them.
function circuits2image(circuits, log = false) {
    const heights = [];
    for (const qc of circuits) heights.push(circuits2height(qc, log));

    return heights2image(heights);
}

// heights2image(): Convert height dict back to image data so that the HTML canvas instance can draw the result.
function heights2image(heights) {
    const [Lx, Ly] = getSize(heights[0]);
    const hMax = heights.map((h) => Math.max(...Object.values(h)));

    const rd = new ImageData(Lx, Ly);

    for (let x = 0; x < Lx; x++) {
        for (let y = 0; y < Ly; y++) {
            const idx = (y * Lx + x) * 4; // index

            for (let j = 0; j < 3; j++) {
                const key = `${x}, ${y}`;
                const h = heights[j][key] || 0
                const normalised = hMax[j] > 0 ? h / hMax[j] : 0
                rd.data[idx + j] = Math.floor(255 * normalised);
            }
            rd.data[idx + 3] = 255; // (Alpha)
        }
    }

    return rd; // The result!
}

// ============== Image Processing ===============

// getSize(): Get size of grid from height dict
function getSize(height) {
    let Lx = 0, Ly = 0;
    for (const [x, y] of Object.keys(height).map((k) => k.split(',').map(Number))) Lx = Math.max(x + 1, Lx); Ly = Math.max(y + 1, Ly);

    return [Lx, Ly];
}

// ===== Subsection: Basic Image Maths for Quantum Blur =====
// makeLine(): Create a line of bitstrings for Grey encoding
function makeLine(leng) {
    const num = Math.ceil(Math.log2(leng));
    let line = ['0', '1'];

    for (let j = 0; j < num - 1; j++) {
        const reversed = [...line].reverse();
        line = line.concat(reversed);

        const halved = Math.floor(line.length / 2);
        for (let k = 0; k < halved; k++) line[k] += '0';
        for (let k = halved; k < line.length; k++) line[k] += '1';
    }

    return line;
}

// makeGrid(): Create grid mapping for coordinates to bitstrings
function makeGrid(Lx, Ly = null) {
    if (Ly == null) Ly = Lx;

    const lineX = makeLine(Lx);
    const lineY = makeLine(Ly);

    const grid = {};
    for (let x = 0; x < Lx; x++) {
        for (let y = 0; y < Ly; y++) {
            const bitstring = lineX[x] + lineY[y];
            grid[bitstring] = [x, y];
        }
    }

    const n = lineX[0].length + lineY[0].length;

    return [grid, n];
}