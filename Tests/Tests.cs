using QuantumBlur;
using HeightMap = System.Collections.Generic.Dictionary<(int X, int Y), double>;

int failures = 0;

void Check(string name, bool ok)
{
    Console.WriteLine($"  [{(ok ? "PASS" : "FAIL")}] {name}");
    if (!ok) failures++;
}
bool Approx(double a, double b, double tol = 1e-9) => Math.Abs(a - b) < tol;

// 1. Power-of-two round trip: a 4x4 gradient must come back rescaled so max = 1.
//    This pins the whole pipeline at once: Gray-code layout, bit order agreement
//    with MicroMoth's Probabilities, the Name/Eval size contract, and Normalize.
{
    var height = new HeightMap();
    for (int x = 0; x < 4; x++)
        for (int y = 0; y < 4; y++)
            height[(x, y)] = x + 4 * y; // 0..15, max at (3,3)

    var back = Codec.CircuitToHeight(Codec.HeightToCircuit(height));

    bool ok = back.Count == 16;
    for (int x = 0; x < 4 && ok; x++)
        for (int y = 0; y < 4 && ok; y++)
            ok = Approx(back[(x, y)], (x + 4 * y) / 15.0, 1e-6);
    Check("4x4 round trip: every pixel = original / 15", ok);
}

// 2. Non-power-of-two round trip: 3x5 needs ceil(log2 3) + ceil(log2 5) = 5 qubits,
//    no padding anywhere. Unused basis states must stay empty and decode must
//    return exactly 15 pixels at the right positions.
{
    var height = new HeightMap();
    for (int x = 0; x < 3; x++)
        for (int y = 0; y < 5; y++)
            height[(x, y)] = 1 + x + 3 * y; // 1..15, nothing zero

    var qc = Codec.HeightToCircuit(height);
    var back = Codec.CircuitToHeight(qc);

    bool ok = qc.Qubits == 5 && back.Count == 15;
    for (int x = 0; x < 3 && ok; x++)
        for (int y = 0; y < 5 && ok; y++)
            ok = Approx(back[(x, y)], (1 + x + 3 * y) / 15.0, 1e-6);
    Check("3x5 (non-power-of-two): 5 qubits, 15 pixels, values / 15", ok);
}

// 3. All-black image: a zero vector is not a quantum state, so the codec encodes
//    a uniform state instead. The decode must be finite (no NaN from 0/0) and
//    uniform. What "black in, white out" means for colors is the image layer's
//    problem, not the codec's.
{
    var height = new HeightMap { [(0, 0)] = 0, [(1, 0)] = 0, [(0, 1)] = 0, [(1, 1)] = 0 };
    var back = Codec.CircuitToHeight(Codec.HeightToCircuit(height));
    bool ok = back.Count == 4;
    foreach (var h in back.Values) ok &= !double.IsNaN(h) && Approx(h, 1.0, 1e-9);
    Check("all-black 2x2: decodes uniform 1.0, no NaN", ok);
}

// 4. Renamed circuit: users may overwrite Name. Python's eval() would crash or
//    execute it; our parser must just fall back to the square-size guess.
{
    var height = new HeightMap { [(0, 0)] = 1, [(1, 0)] = 2, [(0, 1)] = 3, [(1, 1)] = 4 };
    var qc = Codec.HeightToCircuit(height);
    qc.Name = "my blurry cat";
    var back = Codec.CircuitToHeight(qc); // 2 qubits -> square guess is 2x2
    Check("renamed circuit: falls back to square inference", back.Count == 4 && Approx(back[(1, 1)], 1.0, 1e-6));
}

// 5. Log mode round trip: encode and decode with log=true. Values must stay
//    finite, the maximum must still be 1, and zero pixels must stay 0.
{
    var height = new HeightMap { [(0, 0)] = 0, [(1, 0)] = 1, [(0, 1)] = 10, [(1, 1)] = 100 };
    var back = Codec.CircuitToHeight(Codec.HeightToCircuit(height, log: true), log: true);
    double max = 0;
    bool finite = true;
    foreach (var h in back.Values) { finite &= double.IsFinite(h); max = Math.Max(max, h); }
    Check("log mode: finite, max = 1, black stays black", finite && Approx(max, 1.0, 1e-6) && Approx(back[(0, 0)], 0.0, 1e-6));
}

// 6. Log mode on a delta distribution (one bright pixel, rest black): only one
//    brightness level survives, so log rescaling is undefined. Python raises
//    ZeroDivisionError here; we return the linear result instead.
{
    var height = new HeightMap { [(0, 0)] = 0, [(1, 0)] = 0, [(0, 1)] = 0, [(1, 1)] = 5 };
    var back = Codec.CircuitToHeight(Codec.HeightToCircuit(height), log: true);
    Check("log mode, single bright pixel: no crash, bright pixel = 1", Approx(back[(1, 1)], 1.0, 1e-6));
}

// 7. Blur with xi = 0 is the identity: the rotation circuit does nothing,
//    so the round trip must match the unblurred one exactly.
{
    var height = new HeightMap();
    for (int x = 0; x < 4; x++)
        for (int y = 0; y < 4; y++)
            height[(x, y)] = x + 4 * y;

    var back = Codec.CircuitToHeight(Effect.BlurHeight(height, 0.0));
    bool ok = true;
    for (int x = 0; x < 4 && ok; x++)
        for (int y = 0; y < 4 && ok; y++)
            ok = Approx(back[(x, y)], (x + 4 * y) / 15.0, 1e-6);
    Check("blur xi=0: identity round trip", ok);
}

// 8. Blur spreads brightness to spatial neighbours: a single bright pixel
//    must leak into its adjacent pixels, stay the maximum itself, and leave
//    the far corner darker than the direct neighbours. This is the physics
//    the Gray-code layout exists for.
{
    var height = new HeightMap();
    for (int x = 0; x < 4; x++)
        for (int y = 0; y < 4; y++)
            height[(x, y)] = 0;
    height[(0, 0)] = 1;

    var back = Codec.CircuitToHeight(Effect.BlurHeight(height, 0.2));
    Check("blur spreads: neighbours lit, source still max, far corner darkest",
        Approx(back[(0, 0)], 1.0, 1e-6)
        && back[(1, 0)] > 0.01 && back[(0, 1)] > 0.01
        && back[(3, 3)] < back[(1, 0)] && back[(3, 3)] < back[(0, 1)]);
}

// 9. More xi, more blur: the neighbour of the bright pixel must be brighter
//    at xi = 0.4 than at xi = 0.1.
{
    var height = new HeightMap();
    for (int x = 0; x < 4; x++)
        for (int y = 0; y < 4; y++)
            height[(x, y)] = 0;
    height[(0, 0)] = 1;

    var soft = Codec.CircuitToHeight(Effect.BlurHeight(height, 0.1));
    var hard = Codec.CircuitToHeight(Effect.BlurHeight(height, 0.4));
    Check("blur strength: xi=0.4 leaks more than xi=0.1", hard[(1, 0)] > soft[(1, 0)]);
}

// 10. All-black blur: rates are all zero, the max_rate guard must kick in
//     (uniform rotation) instead of dividing by zero. Decode stays finite.
{
    var height = new HeightMap { [(0, 0)] = 0, [(1, 0)] = 0, [(0, 1)] = 0, [(1, 1)] = 0 };
    var back = Codec.CircuitToHeight(Effect.BlurHeight(height, 0.3));
    bool ok = back.Count == 4;
    foreach (var h in back.Values) ok &= double.IsFinite(h);
    Check("all-black blur: max_rate guard, finite decode", ok);
}

// 11. Non-power-of-two blur keeps its size: Compose takes the name from the
//     left operand and BlurHeight re-stamps it, so a blurred 3x5 must decode
//     as 3x5, not fall back to the square guess.
{
    var height = new HeightMap();
    for (int x = 0; x < 3; x++)
        for (int y = 0; y < 5; y++)
            height[(x, y)] = 1 + x + 3 * y;

    var back = Codec.CircuitToHeight(Effect.BlurHeight(height, 0.15));
    Check("3x5 blur: still decodes as 15 pixels", back.Count == 15 && back.ContainsKey((2, 4)));
}

// 12. Ry axis: same machinery, different rotation. Must run and still spread.
{
    var height = new HeightMap();
    for (int x = 0; x < 4; x++)
        for (int y = 0; y < 4; y++)
            height[(x, y)] = 0;
    height[(0, 0)] = 1;

    var back = Codec.CircuitToHeight(Effect.BlurHeight(height, 0.2, Where.RotationY));
    Check("blur axis=Y: runs and spreads", back[(1, 0)] > 0.01 && back[(0, 1)] > 0.01);
}

Console.WriteLine(failures == 0 ? "\nAll codec tests passed." : $"\n{failures} test(s) FAILED.");
return failures == 0 ? 0 : 1;