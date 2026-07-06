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
internal enum ImageType // This makes the mode selection more robust, like we've done in MicroMoth for Arduino.
{
    L, // Pixel values are a single integer. 
    Rgb, // A tuple of three integers.
}

internal sealed class Image
{
    
    private readonly (int R, int G, int B)[] _pixels;

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
    }

    public (int R, int G, int B) GetPixel(int x, int y) => _pixels[Index(x, y)];

    public int GetPixelL(int x, int y) => _pixels[Index(x, y)].R; // technically it's not the 'R' value, but to indicate the single-channel value. (limitation of transition from Python to C#.)

    public void SetPixel(int x, int y, (int R, int G, int B) value) => _pixels[Index(x, y)] = value;

    public void SetPixel(int x, int y, int value) => _pixels[Index(x, y)] = (value, value, value); // to indicate the one value within one pixel during the L mode.

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

    public Image Resize((int NewWidth, int NewHeight) newSize) => throw new NotImplementedException();

    private int Index(int x, int y)
    {
        if (x < 0 || x >= Width) throw new ArgumentOutOfRangeException(nameof(x));
        if (y < 0 || y >= Height) throw new ArgumentOutOfRangeException(nameof(y));
        return y * Width + x;
    }
}