using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.IO.Compression;
using System.Runtime.InteropServices;

public static class StrokeStudy
{
    const int Format = 0x53543244;
    const int Ground = 0x343A49;

    struct Stroke
    {
        public float X, Y, A, B, Angle, Alpha;
        public int Paint;

        public Stroke(float x, float y, float a, float b, float angle, float alpha, int paint)
        { X = x; Y = y; A = a; B = b; Angle = angle; Alpha = alpha; Paint = paint; }

        public void Write(BinaryWriter writer)
        {
            writer.Write(X); writer.Write(Y); writer.Write(A); writer.Write(B);
            writer.Write(Angle); writer.Write(Alpha); writer.Write(Paint);
        }

        public static Stroke Read(BinaryReader reader)
        {
            return new Stroke(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle(),
                reader.ReadSingle(), reader.ReadSingle(), reader.ReadInt32());
        }
    }

    sealed class Canvas
    {
        public readonly int Width, Height;
        public readonly float[] R, G, B;

        public Canvas(int w, int h, int color)
        {
            Width = w; Height = h;
            R = new float[w * h]; G = new float[R.Length]; B = new float[R.Length];
            for (int i = 0; i < R.Length; i++) Set(i, color);
        }

        public void Set(int i, int color)
        { R[i] = (color >> 16) & 255; G[i] = (color >> 8) & 255; B[i] = color & 255; }

        public void Stamp(Stroke s, float scale)
        {
            var shape = new Brush(s, scale, Width, Height);
            float r = (s.Paint >> 16) & 255, g = (s.Paint >> 8) & 255, b = s.Paint & 255;
            for (int y = shape.Y0; y <= shape.Y1; y++) {
                int i = y * Width + shape.X0;
                float dy = y - shape.Y;
                for (int x = shape.X0; x <= shape.X1; x++, i++) {
                    float a = shape.Weight(x - shape.X, dy);
                    if (a < .001f) continue;
                    R[i] += (r - R[i]) * a;
                    G[i] += (g - G[i]) * a;
                    B[i] += (b - B[i]) * a;
                }
            }
        }

        public Bitmap Image()
        {
            var bitmap = new Bitmap(Width, Height, PixelFormat.Format32bppArgb);
            var data = bitmap.LockBits(new Rectangle(0, 0, Width, Height), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            try {
                var row = new int[Width];
                for (int y = 0; y < Height; y++) {
                    int i = y * Width;
                    for (int x = 0; x < Width; x++, i++) row[x] = unchecked((int)0xff000000) | Pack(R[i], G[i], B[i]);
                    Marshal.Copy(row, 0, IntPtr.Add(data.Scan0, data.Stride * y), Width);
                }
            } finally { bitmap.UnlockBits(data); }
            return bitmap;
        }
    }

    struct Brush
    {
        public readonly int X0, X1, Y0, Y1;
        public readonly float X, Y;
        readonly float xx, xy, yy, alpha;

        public Brush(Stroke s, float scale, int width, int height)
        {
            X = (s.X + .5f) * scale - .5f; Y = (s.Y + .5f) * scale - .5f;
            float a = s.A * scale, b = s.B * scale;
            float c = (float)Math.Cos(s.Angle), t = (float)Math.Sin(s.Angle);
            float ai = 1 / (a * a), bi = 1 / (b * b);
            xx = c * c * ai + t * t * bi;
            xy = 2 * c * t * (ai - bi);
            yy = t * t * ai + c * c * bi;
            float rx = (float)Math.Sqrt(a * a * c * c + b * b * t * t);
            float ry = (float)Math.Sqrt(a * a * t * t + b * b * c * c);
            X0 = Math.Max(0, (int)Math.Ceiling(X - rx)); X1 = Math.Min(width - 1, (int)Math.Floor(X + rx));
            Y0 = Math.Max(0, (int)Math.Ceiling(Y - ry)); Y1 = Math.Min(height - 1, (int)Math.Floor(Y + ry));
            alpha = s.Alpha;
        }

        public float Weight(float dx, float dy)
        {
            float inside = 1 - (xx * dx * dx + xy * dx * dy + yy * dy * dy);
            return inside <= 0 ? 0 : alpha * inside * inside * (3 - 2 * inside);
        }
    }

    static int Byte(float x) { return x < 0 ? 0 : x > 255 ? 255 : (int)(x + .5f); }
    static int Pack(float r, float g, float b) { return (Byte(r) << 16) | (Byte(g) << 8) | Byte(b); }

    static void DrawScaled(Graphics canvas, Image source, Rectangle destination)
    {
        using (var attributes = new ImageAttributes()) {
            attributes.SetWrapMode(WrapMode.TileFlipXY);
            canvas.InterpolationMode = InterpolationMode.HighQualityBicubic;
            canvas.DrawImage(source, destination, 0, 0, source.Width, source.Height, GraphicsUnit.Pixel, attributes);
        }
    }

    static Canvas ReadReference(string path, int maxWidth)
    {
        using (var input = Image.FromFile(path)) {
            int w = Math.Min(maxWidth, input.Width), h = Math.Max(1, (int)Math.Round((double)input.Height * w / input.Width));
            using (var bitmap = new Bitmap(w, h, PixelFormat.Format32bppArgb)) {
                using (var g = Graphics.FromImage(bitmap)) {
                    g.Clear(Color.FromArgb(unchecked((int)0xff000000) | Ground));
                    DrawScaled(g, input, new Rectangle(0, 0, w, h));
                }
                var target = new Canvas(w, h, Ground);
                var data = bitmap.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
                try {
                    var row = new int[w];
                    for (int y = 0; y < h; y++) {
                        Marshal.Copy(IntPtr.Add(data.Scan0, data.Stride * y), row, 0, w);
                        for (int x = 0; x < w; x++) target.Set(y * w + x, row[x]);
                    }
                } finally { bitmap.UnlockBits(data); }
                return target;
            }
        }
    }

    static float[] Smooth(float[] source, int width, int height, int r)
    {
        var result = new float[source.Length];
        var horizontal = new float[source.Length];
        float inverse = 1f / (2 * r + 1);
        for (int y = 0; y < height; y++) {
            int offset = y * width;
            float sum = 0;
            for (int k = -r; k <= r; k++) sum += source[offset + Math.Max(0, Math.Min(width - 1, k))];
            for (int x = 0; x < width; x++) {
                horizontal[offset + x] = sum * inverse;
                sum += source[offset + Math.Min(width - 1, x + r + 1)] - source[offset + Math.Max(0, x - r)];
            }
        }
        for (int x = 0; x < width; x++) {
            float sum = 0;
            for (int k = -r; k <= r; k++) sum += horizontal[Math.Max(0, Math.Min(height - 1, k)) * width + x];
            for (int y = 0; y < height; y++) {
                result[y * width + x] = sum * inverse;
                sum += horizontal[Math.Min(height - 1, y + r + 1) * width + x] - horizontal[Math.Max(0, y - r) * width + x];
            }
        }
        return result;
    }

    sealed class Fitter
    {
        readonly Canvas target, canvas;
        readonly Random random;
        readonly float[] luma;
        readonly int[] indices = new int[16384];
        readonly float[] weights = new float[16384];
        public readonly List<Stroke> Strokes = new List<Stroke>();

        public Fitter(Canvas target, int seed)
        {
            this.target = target;
            canvas = new Canvas(target.Width, target.Height, Ground);
            random = new Random(seed);
            luma = new float[target.R.Length];
            for (int i = 0; i < luma.Length; i++) luma[i] = .23f * target.R[i] + .55f * target.G[i] + .22f * target.B[i];
        }

        float Pick(float lo, float hi) { return lo + (hi - lo) * (float)random.NextDouble(); }

        bool TryStroke(Stroke stroke, float minimumGain)
        {
            var brush = new Brush(stroke, 1, canvas.Width, canvas.Height);
            int count = 0;
            float denom = 0, pr = 0, pg = 0, pb = 0, dcR = 0, dcG = 0, dcB = 0;
            for (int y = brush.Y0; y <= brush.Y1; y++) {
                int i = y * canvas.Width + brush.X0;
                float dy = y - brush.Y;
                for (int x = brush.X0; x <= brush.X1; x++, i++) {
                    float a = brush.Weight(x - brush.X, dy);
                    if (a < .001f) continue;
                    indices[count] = i; weights[count++] = a;
                    float sq = a * a;
                    denom += sq;
                    pr += a * (target.R[i] - canvas.R[i]); pg += a * (target.G[i] - canvas.G[i]); pb += a * (target.B[i] - canvas.B[i]);
                    dcR += sq * canvas.R[i]; dcG += sq * canvas.G[i]; dcB += sq * canvas.B[i];
                }
            }
            // Each brush affects several nearby samples. Fit one pigment for all of them.
            if (count < 4 || denom <= 0) return false;
            float tr = pr + dcR, tg = pg + dcG, tb = pb + dcB;
            int r = Byte(tr / denom), g = Byte(tg / denom), b = Byte(tb / denom);
            double gain = 0;
            for (int k = 0; k < count; k++) {
                int i = indices[k]; float a = weights[k];
                float cr = canvas.R[i], cg = canvas.G[i], cb = canvas.B[i];
                float dr = a * (r - cr), dg = a * (g - cg), db = a * (b - cb);
                gain += dr * (2 * (target.R[i] - cr) - dr) + dg * (2 * (target.G[i] - cg) - dg)
                    + db * (2 * (target.B[i] - cb) - db);
            }
            if (gain < minimumGain * count) return false;
            stroke.Paint = (r << 16) | (g << 8) | b;
            Strokes.Add(stroke);
            for (int k = 0; k < count; k++) {
                int i = indices[k]; float a = weights[k];
                canvas.R[i] += (r - canvas.R[i]) * a;
                canvas.G[i] += (g - canvas.G[i]) * a;
                canvas.B[i] += (b - canvas.B[i]) * a;
            }
            return true;
        }

        public void Pass(float major, float minor, float spacing, int sweeps, float alpha, float gain)
        {
            int w = canvas.Width, h = canvas.Height;
            float[] l = Smooth(luma, w, h, Math.Max(1, (int)(major * .33f)));
            int cols = (int)Math.Ceiling(w / spacing), rows = (int)Math.Ceiling(h / spacing);
            var order = new int[cols * rows];
            for (int i = 0; i < order.Length; i++) order[i] = i;
            for (int sweep = 0; sweep < sweeps; sweep++) {
                for (int i = order.Length - 1; i > 0; i--) {
                    int j = random.Next(i + 1), value = order[i]; order[i] = order[j]; order[j] = value;
                }
                float dx = Pick(-.44f, .44f), dy = Pick(-.44f, .44f);
                foreach (int index in order) {
                    float x = Math.Min(w - 1, Math.Max(0, (index % cols + .5f + dx + Pick(-.38f, .38f)) * spacing));
                    float y = Math.Min(h - 1, Math.Max(0, (index / cols + .5f + dy + Pick(-.38f, .38f)) * spacing));
                    int ix = (int)(x + .5f), iy = (int)(y + .5f), at = iy * w + ix;
                    float gx = l[iy * w + Math.Min(w - 1, ix + 1)] - l[iy * w + Math.Max(0, ix - 1)];
                    float gy = l[Math.Min(h - 1, iy + 1) * w + ix] - l[Math.Max(0, iy - 1) * w + ix];
                    float strength = gx * gx + gy * gy;
                    float a = major * Pick(.91f, 1.08f), b = minor * Pick(.92f, 1.08f);
                    float angle = strength > 2.5f ? (float)Math.Atan2(gy, gx) + 1.5707963f + Pick(-.21f, .21f) : Pick(0, 3.141593f);
                    float er = target.R[at] - canvas.R[at], eg = target.G[at] - canvas.G[at], eb = target.B[at] - canvas.B[at];
                    if (major > 5 || er * er + eg * eg + eb * eb > gain) {
                        TryStroke(new Stroke(x, y, a, b, angle, alpha * Pick(.88f, 1), 0), gain);
                    }
                }
            }
            Console.WriteLine("Brush {0:0.00} px | {1:N0} accepted | RGB PSNR {2:0.00} dB", major, Strokes.Count, PSNR());
        }

        public double PSNR()
        {
            double error = 0;
            for (int i = 0; i < canvas.R.Length; i++) {
                double r = canvas.R[i] - target.R[i], g = canvas.G[i] - target.G[i], b = canvas.B[i] - target.B[i];
                error += r * r + g * g + b * b;
            }
            return 10 * Math.Log10(255.0 * 255 * 3 * canvas.R.Length / error);
        }
    }

    public static void Fit(string reference, string plan, int width, int seed)
    {
        Canvas target = ReadReference(reference, width);
        var fit = new Fitter(target, seed);
        Console.WriteLine("Fitting {0} x {1}", target.Width, target.Height);
        fit.Pass(37, 24, 23, 3, .87f, 2.5f);
        fit.Pass(21, 12, 12.2f, 3, .84f, 2.5f);
        fit.Pass(11, 6.1f, 6.35f, 3, .83f, 2.2f);
        fit.Pass(6.2f, 3.25f, 3.65f, 4, .81f, 1.7f);
        fit.Pass(3.4f, 2.05f, 2.34f, 4, .77f, 1.4f);
        fit.Pass(2.06f, 1.58f, 1.62f, 4, .78f, 1.25f);
        fit.Pass(1.87f, 1.53f, 1.65f, 3, .75f, .85f);
        using (var file = File.Create(plan))
        using (var compressed = new GZipStream(file, CompressionMode.Compress))
        using (var writer = new BinaryWriter(compressed)) {
            writer.Write(Format); writer.Write(target.Width); writer.Write(target.Height);
            writer.Write(Ground); writer.Write(fit.Strokes.Count);
            foreach (Stroke s in fit.Strokes) s.Write(writer);
        }
    }

    public static void Render(string plan, string output, string preview, int width)
    {
        Canvas canvas;
        using (var file = File.OpenRead(plan))
        using (var compressed = new GZipStream(file, CompressionMode.Decompress))
        using (var reader = new BinaryReader(compressed)) {
            if (reader.ReadInt32() != Format) throw new InvalidDataException("Invalid stroke plan header.");
            int baseWidth = reader.ReadInt32(), baseHeight = reader.ReadInt32();
            if (baseWidth <= 0 || baseHeight <= 0) throw new InvalidDataException("Invalid canvas dimensions.");
            float scale = (float)width / baseWidth;
            canvas = new Canvas(width, Math.Max(1, (int)Math.Round(baseHeight * (double)width / baseWidth)), reader.ReadInt32());
            int count = reader.ReadInt32();
            if (count < 0 || count > 12000000) throw new InvalidDataException("Invalid stroke count.");
            for (int i = 0; i < count; i++) canvas.Stamp(Stroke.Read(reader), scale);
            Console.WriteLine("Rendered {0:N0} strokes at {1} x {2}", count, canvas.Width, canvas.Height);
        }
        using (var result = canvas.Image()) {
            result.Save(output, ImageFormat.Png);
            if (String.IsNullOrEmpty(preview)) return;
            int w = Math.Min(1440, result.Width), h = Math.Max(1, (int)Math.Round((double)result.Height * w / result.Width));
            using (var thumb = new Bitmap(w, h, PixelFormat.Format24bppRgb)) {
                using (var painter = Graphics.FromImage(thumb)) DrawScaled(painter, result, new Rectangle(0, 0, w, h));
                thumb.Save(preview, ImageFormat.Png);
            }
        }
    }
}
