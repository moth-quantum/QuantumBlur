// (C) Copyright Moth Quantum 2025.
//
// This code is licensed under the Apache License, Version 2.0. You may
// obtain a copy of this license in the LICENSE.txt file in the root directory
// of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
//
// Any modifications or derivative works of this code must retain this
// copyright notice, and modified files need to carry a notice indicating
// that they have been altered from the originals.

// (C) Copyright @kaleb-hutchy 2020.
//
// This code is licensed under the Apache License, Version 2.0. You may
// obtain a copy of this license in the LICENSE.txt file in the root directory
// of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
//
// Any modifications or derivative works of this code must retain this
// copyright notice, and modified files need to carry a notice indicating
// that they have been altered from the originals.

const r2 = 0.70710678118;

export default class QuantumCircuit {
    #data;

    constructor(n, m) {
        this.num_qubits = n;
        this.num_clbits = m;
        this.name = '';

        this.#data = [];
    };

    getData() {
        return this.#data;
    }

    // Pauli-X gate
    x(q) {
        this.#data.push(['x', q]);
        return this;
    };

    // Hadamard gate
    h(q) {
        this.#data.push(['h', q]);
        return this;
    };

    // CX gate (Control-X gate)
    cx(s, t) { // source, target
        this.#data.push(['cx', s, t]);
        return this;
    };

    // Rotation-X gate
    rx(theta, q) {
        this.#data.push(['rx', theta, q]);
        return this;
    };

    // Rotation-Y gate
    ry(theta, q) {
        this.rx(Math.PI / 2, q);
        this.rz(theta, q);
        this.rx(-Math.PI / 2, q);
        return this;
    };

    // Rotation-Z gate
    rz(theta, q) {
        this.h(q);
        this.rx(theta, q);
        this.h(q);
        return this;
    };

    // Y gate
    y(q) {
        this.rz(Math.PI, q);
        this.x(q);
        return this;
    };

    // Pauli-Z gate
    z(q) {
        this.rz(Math.PI, q);
        return this;
    };

    // T gate
    t(q) {
        this.rz(Math.PI / 4, q);
    };

    crx(theta, s, t) {
        this.#data.push('crx', theta, s, t);
    };

    crz(theta, s, t) {
        this.#data.push('crz', theta, s, t);
    }; 
    
    swap(s, t) {
        this.#data.push('swap', s, t);
    };

    measure(q, b) {
        if (q >= this.num_qubits) {
            throw 'Select the right index of qubits.';
        }

        if (b >= this.num_clbits) {
            throw 'Select the right index of classical bits.';
        }

        this.#data.push(['m', q, b]);
        return this;
    };
};

function simulate(qc, shots, get) {

};

function rotate(x, y, theta) {

};

function superposition(x, y) {

};

function phaseturn(x, y, tt) {

};

export { simulate, rotate, superposition, phaseturn };