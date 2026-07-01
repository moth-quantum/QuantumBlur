namespace QuantumBlur;

internal class Image
{
    /// <summary>
    /// A minimal reimplementation of the PIL Image.Image class, optimised for C#, to allow all image-based tools to function even when only the standard library is available.
    /// To initialise an Image object, use the 'newImage' function that is defined within QuantumBlur.
    /// - mode (string): If L, pixel values are a single integer. If 'RGB', they are a tuple of three integers.
    /// - size (tuple): Specifies width and height.
    /// </summary>

    internal string mode;
    internal (double width, double height) size;
    // (x, y) as a coordinate,
    // (r, g, b) as a pixel value.
    internal Dictionary<(int xloc, int yloc), (int red, int green, int blue)> image_dict;
    
    internal Image()
    {
        // Make the instance first
        // Again, use createImage() in QuantumBlur.
    }

    public (int, int, int) getPixel(int x, int y)
    {
        // Returns the pixel value at the given coordinate.
        return image_dict[(x, y)];
    }

    public void setPixel(int x, int y, (int, int, int) value)
    {
        image_dict[(x, y)] = value;
    }

    public Dictionary<(int, int), (int, int, int)> getDictValue()
    {
        // Returns dictionary of pixel values with coordinates as keys. Not present in PIL.
        return image_dict;
    }

    public void show()
    {
        /// Simply prints all coordinates and pixel values,
        /// rather than PIL, that creates a PNG file and displays it.
        for (int x = 0; x < size.width; x++)
        {
            for (int y = 0; y < size.height; y++)
            {
                Console.WriteLine();
            }
        }
    }

    public void resize()
    {
        Console.WriteLine("This funcionality has not been implemented.");
    }
}