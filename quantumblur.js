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
import { simulate, norm, kron } from './micromoth.js'; // rotate, superposition, phaseturn also exist.

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

export function quantumblur(strength = 0.5) {
    const user = document.getElementById('preview');
    const ctx = user.getContext('2d', { willReadFrequently: true});
    let d = ctx.getImageData(0, 0, user.width, user.height);

    // const ctx = uploadedImage.getContext("2d"); // Access to the canvas (canvas.img => The thing the user uploaded)
    // const uploadedImageData = ctx.getImageData(0, 0, uploadedImage.width, uploadedImage.height);

    // Convert strength (1 to 10) to xi parameter (0.1 to 1.0)
    const xi = strength / 10.0
    // console.log('xi: ', xi); // [CHECKED]

    // Apply Quantum Blur!
    const circuits = blurImage(d, xi);
    console.log('circuits: ', circuits);

    // Convert the result back to image
    const qbImageData = circuits2image(circuits);

    console.log('qbImageData: ', qbImageData);

    return qbImageData;
}

// 1. blurImage(): QB effect itself -> image2heights(), blurHeight()
function blurImage(d, xi, circuits = null, axis = 'x', log = false) {
    const heights = image2heights(d);

    // console.log('Heights: ', heights); // [CHECKED]

    if (circuits == null) circuits = [null, null, null];

    for (let j = 0; j < heights.length; j++) {
        circuits[j] = blurHeight(heights[j], xi, axis, circuits[j], log);
    }

    console.log('Circuits: ', circuits);

    return circuits;
}

// 2. blurHeight(): Apply Quantum Blur effect to the height map
function blurHeight(height, xi, axis = 'x', circuit = null, log = false, grid = null) {
    const [Lx, Ly] = getSize(height);
    let gridData, n;

    if (grid == null) {
        [gridData, n] = makeGrid(Lx, Ly);
    }
    else if (typeof grid == 'object') {
        gridData = grid;
        const keys = Object.keys(grid);
        if (keys.length == 0) throw new Error ('Grid has no keys');
        n = keys[0].length;
    }
    else throw new Error('Grid is not an object.');

    // Invert grid to coordinates as keys
    const coordGrid = {};
    for (const string in gridData) {
        const [x, y] = gridData[string];
        coordGrid[`${x},${y}`] = string;
    }

    const rates = Array(n).fill(0);

    for (let x = 0; x < Lx; x++) {
        for (let y = 0; y < Ly; y++) {
            const key = `${x},${y}`;
            if( !(key in coordGrid) ) continue;

            const string = coordGrid[key];
            const axes = [];

            // Check neighbours
            for (const [dX, dY] of [
                [0, 1],
                [0, -1], 
                [1, 0],
                [-1, 0],
            ]) {
                const closeKey = `${x + dX}, ${y + dY}`;
                if (closeKey in coordGrid) {
                    const nString = coordGrid[closeKey];

                    // Find differing bits
                    for (let j = 0; j < nString.length; j++) {
                        if (nString[j] !== string[j]) axes.push(n - j - 1);
                    }
                }
            }

            // Add height contribution to rates
            for (const j of axes) {
                if (key in height) rates[j] += height[key];
            }
        }
    }

    // Normalise rates
    const maxRate = Math.max(...rates);
    if (maxRate > 0) {
        for (let j = 0; j < n; j++) rates[j] /= maxRate;
    }

    // CREATE ROTATION CIRCUIT
    const qcRot = new QuantumCircuit(n, n);
    for (let j = 0; j < n; j++) {
        const theta = Math.PI * rates[j] * Math.PI * xi;

        if (axis == 'x') qcRot.rx(theta, j);
        else qcRot.ry(theta, j);
    }

    // Combine with INITIAL CIRCUIT
    let resultCircuit;
    if (circuit) {
        // In a full implementation, we'd compose the circuits
        resultCircuit = circuit;
        // Add rotation operations to existing circuit
        for (const gate of qcRot.getData()) resultCircuit.getData().push(gate);
    }
    else {
        const initCircuit = height2circuit(height, log);
        resultCircuit = initCircuit;
        // Add rotation operations
        for (const gate of qcRot.getData()) resultCircuit.getData().push(gate);
    }

    resultCircuit.name = `(${Lx}, ${Ly})`;

    return resultCircuit;
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

            heights[0][`${x},${y}`] = r;
            heights[1][`${x},${y}`] = g;
            heights[2][`${x},${y}`] = b;
        }
    }

    return heights;
}

// image2circuits(): Convert image to quantum circuits (one circuit per each channel)
function image2circuits(imageData, log = false, grid = null) {
    const heights = image2heights(imageData);
    const circuits = [];

    for (const height of heights) circuits.push(height2circuit(height, log, 1e-2, grid));

    return circuits;
}

// height2circuit(): Convert height dictionary to quantum circuit
function height2circuit(height, log = false, eps = 1e-2, grid = null) {
    const [Lx, Ly] = getSize(height);
    let gridData, n;

    if (grid == null) {
        [gridData, n] = makeGrid(Lx, Ly);
    }
    else if (typeof grid === 'object') {
        gridData = grid;
        const keys = Object.keys(grid);
        if (keys.length === 0) throw new Error("Grid has no keys");
        n = keys[0].length;
    }
    else {
        throw new Error("Grid is not an object");
    }

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
            const key = `${x},${y}`;

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
            const key = `${x},${y}`;

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

// circuits2image(): Bring out Quantum circuits so that we could translate them.
function circuits2image(circuits, log = false) {
    const heights = [];
    for (const qc of circuits) heights.push(circuits2height(qc, log));

    return heights2image(heights);
}

// circuits2height: Convert circuit back to height dictionary
function circuits2height(qc, log = false, grid = null) {
    const probs = circuit2probs(qc)
    let size;

    try {
        // Parse the name manually instead of using eval()

        // JavaScript returns 5 from eval('(4, 5)') while Python returns [4, 5].
        // That's why while probs2height() destructures [Lx, Ly] = size where size is just 5 (e.g.), ...

        // ... I get the 'number ___ is not iterable' error.
        // c.f. qc.name format is "(Lx,Ly)".
        const match = qc.name.match(/$$(\d+),\s*(\d+)$$/)
        if (match) {
            size = [Number.parseInt(match[1]), Number.parseInt(match[2])]
        } else {
            throw new Error("Cannot parse circuit name")
        }
    }
    catch {
        const L = Math.floor(2 ** (qc.num_qubits / 2))
        size = [L, L]
    }

    return probs2height(probs, size, log, grid) 
}

function probs2height(probs, size = null, log = false, grid = null) {
    let Lx, Ly;

    if (typeof probs != 'object' || probs == null) throw new Error('probs must be an object with bitstring keys');

    if (size) {
        [Lx, Ly] = size; // ++++++++++ Critical number error was happening here. ++++++++++++
    }
    else {
        const n = Object.keys(probs)[0].length;
        Lx = Ly = Math.floor(2 ** (n / 2));
    }

    let gridData, n;
    if (grid == null) {
        [gridData, n] = makeGrid(Lx, Ly);
    }
    else if (typeof grid === 'object' && grid !== null) {
        gridData = grid;
        const keys = Object.keys(grid);

        if (keys.length === 0) {
            throw new Error('Grid has no keys');
        }

        n = keys[0].length;
    }
    else {
        throw new Error('Grid is not a valid object.');
    }

    const probValues = Object.values(probs);
    console.log('Number of probability values: ', probValues.length);

    let maxH = 0;
    for (const prob of probValues) {
        if (prob > maxH) maxH = prob;
    }
    // const maxH = Math.max(...Object.values(probs)); // (128 x 128) The image was too big to be spreaded.

    const height = {};
    for (let x = 0; x < Lx; x++) {
        for (let y = 0; y < Ly; y++) {
            height[`${x},${y}`] = 0.0;
        }
    }

    for (const bitstring in probs) {
        if (bitstring in gridData) {
            const [x, y] = gridData[bitstring];
            const key = `${x},${y}`;
            height[key] = probs[bitstring] / maxH;
        }
    }

    if (log) {
        const minH = Math.min(...Object.values(height).filter((h) => h > 1e-100))
        const base = 1 / minH;

        for (const pos in height) {
            if (height[pos] > 1e-100) {
                height[pos] = Math.max(Math.log(height[pos] / minH) / Math.log(base), 0)
            }
            else {
                height[pos] = 0.0;
            }
        }
    }

    return height;
}

// heights2image(): Convert height dict back to image data so that the HTML canvas instance can draw the result.
function heights2image(heights) {
    const [Lx, Ly] = getSize(heights[0]);

    let max = 0;
    const hMax = heights.map((h) => {
        for (const val of Object.values(h)) {
            if (val > max) max = val;
        }
    });

    // const hMax = heights.map((h) => Math.max(...Object.values(h))); // Also preventing potential spread operator issue here.

    const rd = new ImageData(Lx, Ly);

    for (let x = 0; x < Lx; x++) {
        for (let y = 0; y < Ly; y++) {
            const idx = (y * Lx + x) * 4; // index

            for (let j = 0; j < 3; j++) {
                const key = `${x},${y}`;
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
    for (const [x, y] of Object.keys(height).map((k) => k.split(',').map(Number))) {
        Lx = Math.max(x + 1, Lx); 
        Ly = Math.max(y + 1, Ly);
    }

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
    console.log('makeGrid() is called.');
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