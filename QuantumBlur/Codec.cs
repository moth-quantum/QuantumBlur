namespace QuantumBlur;
using Moth.MicroMoth;
using System.Numerics;

/// <summary>
/// From heightmap of the image to quantum circuits...
/// ...and vice versa to construct the image back again...
/// </summary>

public static class Codec
{
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
}