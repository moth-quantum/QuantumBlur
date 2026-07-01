namespace QuantumBlur;

using Moth.MicroMoth;

class QuantumBlur
{
    private List<float> kron (List<float> vec0, List<float> vec1)
    {
        List<float> new_vec = [];
        foreach (float amp0 in vec0)
        {
            foreach (float amp1 in vec1)
            {
                new_vec.Add(amp0 * amp1);
            }
        }

        return new_vec;
    }
    public Image createImage(string mode, (double, double) size)
    {
        Image img = new Image();
        img.mode = mode;
        img.size = size;

        object blank;
        if (mode == "L")
        {
            blank = 0;
        } else if (mode == "RGB")
        {
            blank = (0, 0, 0);
        }

        foreach ((int, int) coordinate in img.image_dict.Keys)
        {
            // Set up the image
            img.image_dict[coordinate] = (0, 0, 0);
        }

        return img;
    }
}


