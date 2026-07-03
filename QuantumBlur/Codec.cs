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
        qc.Name = $"({lx}, {ly})";

        return qc;
    }
    public static Dictionary<string, double> CircuitToProbs(QuantumCircuit qc) => Simulator.Probabilities(qc);
    // Moth.MicroMoth's Statevector.Probabilities will return Dictionary<string, double>.
    public static HeightMap ProbToHeight(Dictionary<string, double> prob, (int Lx, int Ly)? size = null, bool log = false, Grid? grid = null)
    {
        (int lx, int ly) = size ?? Helper.MakeSquare(prob);

    }
    public static HeightMap CircuitToHeight(QuantumCircuit qc, bool log = false, Grid? grid = null) => throw new NotImplementedException();
}