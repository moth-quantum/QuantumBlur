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
}