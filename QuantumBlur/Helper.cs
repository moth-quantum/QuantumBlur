namespace QuantumBlur;
using System.Numerics;

internal static class Helper
{
    /// <summary> Tensor product of two state vectors. 
    /// This is useful when you combine two inputs altogether to generate
    /// another combined output, but it is not used in the original Quantum Blur.
    /// But it could be helpful in the future so I would leave this here.
    /// </summary>
    internal static Complex[] Kron(ReadOnlySpan<Complex> a, ReadOnlySpan<Complex> b)
    {
        var result = new Complex[a.Length * b.Length];
        int k = 0;
        foreach (var amp0 in a)
        {
            foreach (var amp1 in b)
            {
                result[k++] = amp0 * amp1;
            }
        }

        return result;
    }
    
    internal static (int Lx, int Ly) GetSize(Dictionary<(int x, int y), double> height)
    {
        int lx = 0, ly = 0;
        foreach (var (x, y) in height.Keys)
        {
            lx = Math.Max(x + 1, lx);
            ly = Math.Max(y + 1, ly);
        }
        return (lx, ly);
    }

    /// <summary>
    /// Normalises a real statevector to the things between unit L2 norm
    /// </summary>
    internal static void Normalize(Span<double> ket)
    {
        double n = 0;
        foreach (var a in ket) n += a * a;
        if (n == 0) return; // All-black image (avoid the DivisionByZero)
        
        double inv = 1.0 / Math.Sqrt(n);
        for (int i = 0; i < ket.Length; i++) ket[i] *= inv;
    }

    internal static (int Lx, int Ly) MakeSquare(Dictionary<string, double> prob)
    {
        int length = prob.Keys.First().Length;
        int l = (int)Math.Pow(2, length / 2.0);
        return (l, l);
    }

    internal static (int Lx, int Ly)? Eval(string name)
    {
        var trimmed = name.Trim();
        if (trimmed.Length < 5 || trimmed[0] != '(' || trimmed[^1] != ')') return null;
        var parts = trimmed[1..^1].Split(','); // Split the name

        // Correctly split the (x, y)
        if (parts.Length == 2 && int.TryParse(parts[0], out int lx) && int.TryParse(parts[1], out int ly) && lx > 0 && ly > 0) return (lx, ly);

        return null;
    }
}


