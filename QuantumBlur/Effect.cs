using Moth.MicroMoth;
namespace QuantumBlur;

/// <summary>
/// Which single-qubit rotation that Quantum Blur will use?
/// Rx/Ry rotation in Python
/// </summary>
public enum Where
{
    RotationX, // Rx rotations: the standard smooth blur
    RotationY, // Ry rotation: Mixes phase modification as a blur effect
}

/// <summary>
/// Quantum effects applied on top of encoded image (height maps)
/// </summary>
public static class Effect
{
    public static QuantumCircuit BlurHeight(HeightMap heightmap, double xi, Where axis = Where.RotationX, QuantumCircuit? circuit = null, bool log = false, Grid? grid = null)
    {
        var (lx, ly) = Helper.GetSize(heightmap);
        grid ??= Encoding.MakeGrid(lx, ly);
        int n = grid.BitStringLength;

        // Invert the grid
        var quad = new Dictionary<(int X, int Y), string>(grid.EncodedImage.Count);
        foreach (var (bitstring, pos) in grid.EncodedImage) quad[pos] = bitstring;

        // Each qubit's rotation angle accumulates the brightness of every pixel
        var rate = new double[n];
        var offset = new (int Dx, int Dy)[] { (0, 1), (0, -1), (1, 0), (-1, 0) };
        for (int x = 0; x < lx; x++)
        {
            for (int y = 0; y < ly; y++)
            {
                if (!heightmap.TryGetValue((x, y), out double h)) continue;
                string bits = quad[(x, y)];
                foreach (var (dx, dy) in offset)
                {
                    if (!quad.TryGetValue((x + dx, y + dy), out var neighbor)) continue;
                    for (int j = 0; j < n; j++)
                    {
                        // Bit j of the string (left -> right) is qubit number n-j-1
                        if (neighbor[j] != bits[j]) rate[n-j-1] += h;
                    }
                } 
            }
        }

        // Normalise the rate so that it could be mapped onto the rotation angle.
        double max = 0;
        foreach (var r in rate) max = Math.Max(max, r);

        if (max == 0) Array.Fill(rate, 1.0);
        else for (int j = 0; j < n; j++) rate[j] /= max;

        QuantumCircuit rotated = new QuantumCircuit(n);
        for (int j = 0; j < n; j++)
        {
            // theta = pi * rate * xi
            double theta = Math.PI * rate[j] * xi;
            if (axis == Where.RotationX) rotated.Rx(theta, j);
            else rotated.Ry(theta, j);
        }

        circuit ??= Codec.HeightToCircuit(heightmap, log: log, grid: grid);
        var blurred = circuit.Compose(rotated);
        blurred.Name = $"({lx},{ly})";
        return blurred;
    }

    /// <summary>
    /// The easiest way of using Quantum Blur!
    /// </summary>
    public static Image BlurImage(Image img, double xi, Where axis = Where.RotationX, bool log = false, int maxQubits = 20)
    {
        // If the image is too big (the ones require more than 20 qubits)
        // resize the image (downscale -> process -> rescale to original)
        var (oldW, oldH) = img.Size;
        bool isBig = Encoding.Bits(oldW) + Encoding.Bits(oldH) > maxQubits;
        if (isBig) img = img.Resize(Downscale(oldW, oldH, maxQubits));

        var height = Codec.ImageToHeight(img);
        var (lx, ly) = img.Size;
        var grid = Encoding.MakeGrid(lx, ly);

        for (int j = 0; j < height.Length; j++)
        {
            // A unit-norm quantum state cannot remember absolute brightness,
            // so the decoded height map always comes back with max 1.
            // Save the channel's true maximum and restore it.
            double maxH = 0;
            foreach (var h in height[j].Values) maxH = Math.Max(maxH, h);

            // An all-zero channel has nothing to blur (all-black image)
            // In this case, skip the entire pipeline.
            // But who would try to blur all-black image?!
            if (maxH == 0) continue;

            var blurred = Codec.CircuitToHeight(BlurHeight(height[j], xi, axis, log: log, grid: grid), log: log, grid: grid);
            foreach (var pos in blurred.Keys) blurred[pos] *= maxH;
            height[j] = blurred;
        }
        
        var result = Codec.HeightToImage(height);
        return isBig ? result.Resize((oldW, oldH)) : result;
    }

    // implementation of the blur-api's _downscaled_size
    private static (int, int) Downscale(int w, int h, int maxQubits)
    {
        if (maxQubits < 2) throw new ArgumentOutOfRangeException(nameof(maxQubits), "An image needs at least one qubit per axis.");

        double spare = maxQubits - (Math.Log(w) + Math.Log(h)) / Math.Log(2);
        double scale = Math.Min(1.0, Math.Pow(2, spare / 2));
        int nw = Math.Max(1, (int)(w * scale)), nh = Math.Max(1, (int)(h * scale));

        while (Encoding.Bits(nw) + Encoding.Bits(nh) > maxQubits)
        {
            if (Encoding.Bits(nw) >= Encoding.Bits(nh)) nw = Math.Max(1, nw / 2);
            else nh = Math.Max(1, nh / 2);
        }

        return (nw, nh);
    }
}