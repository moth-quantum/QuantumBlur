namespace QuantumBlur;

/// <summary>
/// A mapping between bitstrings and 2D grid with pixels
/// The length of bitstrings will be the length of every key in EncodedImage
/// </summary>

public sealed record Grid(IReadOnlyDictionary<string, (int X, int Y)> EncodedImage, int BitStringLength);

/// <summary>
/// Gray-code encodings of lines and grids
/// Python: make_line, make_grid, make_strip
public static class Encoding
{
    public static List<string> MakeLine(int length)
    {
        if (length < 1) throw new ArgumentOutOfRangeException(nameof(length));

        int n = (int)Math.Ceiling(Math.Log2(length));
        // Iteratively build the gray code
        // Mirror the current list, then extend the first half with 0 and the mirrored version with 1.
        var line = new List<string> { "0", "1" };
        for (int j = 1; j < n; j++)
        {
            int half = line.Count; // 1
            for (int k = half - 1; k >= 0; k--) line.Add(line[k]);
            for (int k = 0; k < half; k++) line[k] += "0"; // front half
            for (int k = half; k < line.Count; k++) line[k] += "1"; // botton half
        }
        return line;
    }

    public static Grid MakeGrid(int lx, int? ly = null)
    {
        int Ly = ly ?? lx;
        var lineX = MakeLine(lx);
        var lineY = MakeLine(Ly);

        var encoded = new Dictionary<string, (int X, int Y)>(lx * Ly);
        for (int x = 0; x < lx; x++)
        {
            for (int y = 0; y < Ly; y++)
            {
                encoded[lineX[x] + lineY[y]] = (x, y);
            }
        }

        return new Grid(encoded, lineX[0].Length + lineY[0].Length);
        // Return the encoded image as a customised grid data structure with its width and height
    }
}