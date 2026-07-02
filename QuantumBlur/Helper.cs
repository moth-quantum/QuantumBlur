namespace QuantumBlur;
using System.Numerics;

using Moth.MicroMoth;

internal static class Helper
{
    // <summary> Tensor product of two state vectors. </summary>
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
}


