namespace QuantumBlur;
using Moth.MicroMoth;
using System.Numerics;

/// <summary>
/// From heightmap of the image to quantum circuits...
/// ...and vice versa to construct the image back again...
/// </summary>

public static class Codec
{
    private static int ToByte(HeightMap height, (int X, int Y) pos)
    {
        double h = height.TryGetValue(pos, out double v) ? v : 0;
        return Math.Clamp((int)Math.Round(h), 0, 255);
    }

    /// <summary>
    /// Encodes an image as one circuit per colour channel.
    /// </summary>
    public static QuantumCircuit[] ImageToCircuit(Image img, bool log = false, Grid? grid = null)
    {
        var height = ImageToHeight(img);
        var circuits = new QuantumCircuit[height.Length];
        for (int j = 0; j < height.Length; j++)
        {
            circuits[j] = HeightToCircuit(height[j], log: log, grid: grid);
        }

        return circuits;
    }

    /// <summary>
    /// Renders an image from one circuit per colour channel.
    /// Paired with ImageToCircuit().
    /// </summary>
    public static Image CircuitToImage(QuantumCircuit[] circuits, bool log = false, Grid? grid = null)
    {
        if (circuits.Length != 1 && circuits.Length != 3 && circuits.Length != 4)
            throw new ArgumentException("Expected 1 (L), 3 (RGB), or 4 (RGBA) circuits.", nameof(circuits));
        
        var height = new HeightMap[circuits.Length];
        for (int j = 0; j < circuits.Length; j++)
        {
            var h = CircuitToHeight(circuits[j], log: log, grid: grid); // maximum 1.0
            foreach (var pos in h.Keys) h[pos] *= 255.0; // map it to 0-255 values
            height[j] = h;
        }

        return HeightToImage(height);
    }

    public static QuantumCircuit HeightToCircuit(HeightMap height, bool log = false, double eps = 1e-2, Grid? grid = null) {
        var (lx, ly) = Helper.GetSize(height); // returns (int, int)
        grid ??= Encoding.MakeGrid(lx, ly);
        int n = grid.BitStringLength;

        // prepare the statevector that the length of 2 ** n (Python)
        double[] statevector = new double[1 << n];

        double maxH = 0;
        // This one especially deals with the all-black image (just in case)
        foreach (var h in height.Values) maxH = Math.Max(maxH, h);
        bool allBlack = maxH == 0;

        // log encoding: the smallest height sets the baseline
        double minH = 1, logBase = 1;
        if (log && !allBlack)
        {
            minH = double.MaxValue;
            foreach (var h in height.Values)
            {
                double relative = h / maxH;
                if (relative > eps && relative < minH) minH = relative;
            }
            logBase = 1.0 / minH;
        }

        foreach (var (bitstring, pos) in grid.EncodedImage)
        {
            if (!height.TryGetValue(pos, out double h)) continue;
            int index = Convert.ToInt32(bitstring, 2);
            if (allBlack) statevector[index] = 1;
            else if (log) statevector[index] = Math.Sqrt(Math.Pow(logBase, h / maxH / minH ));
            else statevector[index] = Math.Sqrt(h);
        }

        Helper.Normalize(statevector);

        Complex[] amplitudes = new Complex[statevector.Length];
        for (int j = 0; j < statevector.Length; j++) amplitudes[j] = statevector[j];

        QuantumCircuit qc = new QuantumCircuit(n).Init(amplitudes);
        qc.Name = $"({lx},{ly})";

        return qc;
    }
    public static Dictionary<string, double> CircuitToProb(QuantumCircuit qc) => Simulator.Probabilities(qc);
    // Moth.MicroMoth's Statevector.Probabilities will return Dictionary<string, double>.
    public static HeightMap ProbToHeight(Dictionary<string, double> prob, (int Lx, int Ly)? size = null, bool log = false, Grid? grid = null)
    {
        (int lx, int ly) = size ?? Helper.MakeSquare(prob);
        grid ??= Encoding.MakeGrid(lx, ly);

        // Rescale so the maximum is 1; an all-sero distribution stays zero
        // instead of ZeroDivision
        double max = 0;
        foreach (var p in prob.Values) max = Math.Max(max, p);
        if (max == 0) max = 1;

        var heightmap = new HeightMap(lx * ly);
        for (int x = 0; x < lx; x++)
        {
            for (int y = 0; y < ly; y++)
            {
                heightmap[(x, y)] = 0.0; // initialisation
            }
        }

        foreach (var (bitstring, p) in prob) if (grid.EncodedImage.TryGetValue(bitstring, out var pos)) heightmap[pos] = p / max;

        if (log)
        {
            double min = double.MaxValue;
            foreach (var h in heightmap.Values) if (h > 1e-100 && h < min) min = h;

            if (min >= 1) return heightmap;
            double logBase = 1.0 / min;
            for (int x = 0; x < lx; x++)
            {
                for (int y = 0; y < ly; y++)
                {
                    double h = heightmap[(x, y)];
                    heightmap[(x, y)] = h > 1e-100 ? Math.Max(Math.Log(h / min) / Math.Log(logBase), 0) : 0.0;
                }
            }
        }
        return heightmap;
    }
    public static HeightMap CircuitToHeight(QuantumCircuit qc, bool log = false, Grid? grid = null)
    {
        var prob = CircuitToProb(qc);
        var size = Helper.Eval(qc.Name) ?? Helper.MakeSquare(prob);
        return ProbToHeight(prob, size, log, grid);
    }

    /// <summary>
    /// One heightmap per colour channel. (0-255) vs L mode is for a single heightmap.
    /// This function does not change the brightness.
    /// </summary>
    public static HeightMap[] ImageToHeight(Image img)
    {
        var (lx, ly) = img.Size;
        int channels = img.Mode switch { ImageType.L => 1, ImageType.Rgba => 4, _ => 3 };
        var height = new HeightMap[channels];
        for (int j = 0; j < channels; j++) height[j] = new HeightMap(lx * ly);

        for (int x = 0; x < lx; x++)
        {
            for (int y = 0; y < ly; y++)
            {
                if (img.Mode == ImageType.L) height[0][(x, y)] = img.GetPixelL(x, y);
                else
                {
                    var (r, g, b) = img.GetPixel(x, y);
                    height[0][(x, y)] = r;
                    height[1][(x, y)] = g;
                    height[2][(x, y)] = b;
                    if (channels == 4) height[3][(x, y)] = img.GetAlpha(x, y);
                }
            }
        }

        return height;
    }

    /// <summary>
    /// Constructs an image from the height map.
    /// The values will be rounded to the pixel values between 0-255. (RGB mode)
    /// This function does not change the brightness.
    /// </summary>
    public static Image HeightToImage(HeightMap[] height)
    {
        if (height.Length != 1 && height.Length != 3 && height.Length != 4) throw new ArgumentException("Expected 1 (L), 3 (RGB), or 4 (RGBA) height maps.", nameof(height));

        var (lx, ly) = Helper.GetSize(height[0]);
        var mode = height.Length switch { 1 => ImageType.L, 4 => ImageType.Rgba, _ => ImageType.Rgb };
        var img = new Image(mode, lx, ly);

        for (int x = 0; x < lx; x++)
        {
            for (int y = 0; y < ly; y++)
            {
                if (height.Length == 1) { img.SetPixel(x, y, ToByte(height[0], (x, y))); continue; }
                img.SetPixel(x, y, (ToByte(height[0], (x, y)), ToByte(height[1], (x, y)), ToByte(height[2], (x, y))));
                if (height.Length == 4) img.SetAlpha(x, y, ToByte(height[3], (x, y)));
            }
        }
        
        return img; // return the constructed image back to the canvas
    }
}