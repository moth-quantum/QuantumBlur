/// <summary>
/// Welcome to Quantum Blur's C# version! This is the first class that you should keep in mind.
/// This Image class replaces PIL.Image's Image(), that stores encoded image data as 2D pixels.
/// For Quantum Blur, it's important to separate pixel data as RGB(A), as a format of dictionary
/// which keys follow (x,y) format.
/// 
/// Based on the image type that you want to encode, it supports either bitmap images or RGB(A)
/// images. 
/// </summary>

namespace QuantumBlur;
public enum ImageType // This makes the mode selection more robust, like we've done in MicroMoth for Arduino.
{
    L, // Pixel values are a single integer. 
    Rgb, // A tuple of three integers.
    Rgba, // RGB plus an alpha (transparency) plane.
}

public sealed class Image
{
    
    private readonly (int R, int G, int B)[] _pixels;
    private readonly int[]? _alpha; // allocated only for RGBA; alpha kept as a separate plane

    public ImageType Mode;
    public int Width { get; }
    public int Height { get; }
    public (int Width, int Height) Size => (Width, Height);
    
    public Image(ImageType mode, int width, int height)
    {
        if (width <= 0 || height <= 0) throw new ArgumentOutOfRangeException("The width or height of the image must be bigger than at least 1 pixel.");

        Mode = mode;
        Width = width;
        Height = height;
        _pixels = new (int, int, int)[width * height]; // Fill up each pixel in the certain size of image black.
        if (mode == ImageType.Rgba)
        {
            _alpha = new int[width * height];
            Array.Fill(_alpha, 255); // opaque by default
        }
    }

    public (int R, int G, int B) GetPixel(int x, int y) => _pixels[Index(x, y)];

    public int GetPixelL(int x, int y) => _pixels[Index(x, y)].R; // technically it's not the 'R' value, but to indicate the single-channel value. (limitation of transition from Python to C#.)

    public void SetPixel(int x, int y, (int R, int G, int B) value) => _pixels[Index(x, y)] = value;

    public void SetPixel(int x, int y, int value) => _pixels[Index(x, y)] = (value, value, value); // to indicate the one value within one pixel during the L mode.

    public int GetAlpha(int x, int y) => _alpha is null ? 255 : _alpha[Index(x, y)]; // non-RGBA images are fully opaque

    public void SetAlpha(int x, int y, int value) { if (_alpha is not null) _alpha[Index(x, y)] = value; }

    // Prints all coordinates and pixel values to replace PIL's image display.
    public void Show()
    {
        for (int x = 0; x < Width; x++)
        {
            for (int y = 0; y < Height; y++)
            {
                Console.WriteLine(Mode == ImageType.L ? 
                $"({x}, {y}): {GetPixelL(x, y)}" :
                $"({x}, {y}): {GetPixel(x, y)}");
            }
        }
    }

    public Image Resize((int NewWidth, int NewHeight) newSize)
    {
        var (nw, nh) = newSize;
        if (nw <= 0 || nh <= 0) throw new ArgumentOutOfRangeException(nameof(newSize));
        var resized = new Image(Mode, nw, nh);

        double sx = (double)Width / nw, sy = (double)Height / nh;
        for (int x = 0; x < nw; x++)
        {
            for (int y = 0; y < nh; y++)
            {
                // Map the centre of the target pixel back into source coordinates.
                double srcX = (x + 0.5) * sx - 0.5;
                double srcY = (y + 0.5) * sy - 0.5;
                
                int x0 = Math.Clamp((int)Math.Floor(srcX), 0, Width - 1);
                int y0 = Math.Clamp((int)Math.Floor(srcY), 0, Height - 1);
                int x1 = Math.Min(x0 + 1, Width - 1);
                int y1 = Math.Min(y0 + 1, Height - 1);
                
                double fx = Math.Clamp(srcX - x0, 0, 1), fy = Math.Clamp(srcY - y0, 0, 1);

                var p00 = GetPixel(x0, y0); var p10 = GetPixel(x1, y0);
                var p01 = GetPixel(x0, y1); var p11 = GetPixel(x1, y1);

                // Define the local function to mix the pixel values altogether (2x2)
                int Blend(int c00, int c10, int c01, int c11) => (int)Math.Round((1 - fx) * (1 - fy) * c00 + fx * (1- fy) * c10 + (1 - fx) * fy * c01 + fx * fy * c11);
                resized.SetPixel(x, y, (Blend(p00.R, p10.R, p01.R, p11.R), Blend(p00.G, p10.G, p01.G, p11.G), Blend(p00.B, p10.B, p01.B, p11.B)));
                if (Mode == ImageType.Rgba)
                    resized.SetAlpha(x, y, Blend(GetAlpha(x0, y0), GetAlpha(x1, y0), GetAlpha(x0, y1), GetAlpha(x1, y1)));

            }
        }

        return resized;
    }

    private int Index(int x, int y)
    {
        if (x < 0 || x >= Width) throw new ArgumentOutOfRangeException(nameof(x));
        if (y < 0 || y >= Height) throw new ArgumentOutOfRangeException(nameof(y));
        return y * Width + x;
    }
}