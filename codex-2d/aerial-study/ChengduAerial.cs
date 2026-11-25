using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public sealed class ChengduAerial
{
    const int W = 1600, H = 1067;
    readonly int seed;
    readonly Random random;
    Graphics g;

    ChengduAerial(int seed) { this.seed = seed; random = new Random(seed); }

    static double Clamp(double x) { return Math.Max(0, Math.Min(1, x)); }
    static double Mix(double a, double b, double t) { return a + (b - a) * t; }
    static double S(double a, double b, double x) { double t = Clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); }
    static double Bell(double x) { return Math.Exp(-x * x); }
    static Color C(double r, double g, double b, int a = 255)
    {
        return Color.FromArgb(a, (int)Math.Max(0, Math.Min(255, r + .5)),
            (int)Math.Max(0, Math.Min(255, g + .5)), (int)Math.Max(0, Math.Min(255, b + .5)));
    }
    static Color A(Color c, int a) { return Color.FromArgb(a, c); }
    static Color Blend(Color a, Color b, double t)
    {
        return C(Mix(a.R, b.R, t), Mix(a.G, b.G, t), Mix(a.B, b.B, t));
    }
    static Color Tone(Color c, double t) { return C(c.R + t, c.G + t, c.B + t); }
    static PointF P(double x, double y) { return new PointF((float)x, (float)y); }
    double R(double lo, double hi) { return Mix(lo, hi, random.NextDouble()); }

    double Hash(int x, int y)
    {
        unchecked {
            uint z = (uint)(x * 374761393 + y * 668265263 + seed * 69069);
            z = (z ^ (z >> 13)) * 1274126177;
            z ^= z >> 16;
            return (z & 0xffffff) / 16777215.0;
        }
    }
    double Noise(double x, double y)
    {
        int ix = (int)Math.Floor(x), iy = (int)Math.Floor(y);
        double tx = x - ix, ty = y - iy;
        tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty);
        return Mix(Mix(Hash(ix, iy), Hash(ix + 1, iy), tx), Mix(Hash(ix, iy + 1), Hash(ix + 1, iy + 1), tx), ty);
    }

    void Poly(Color color, params PointF[] points)
    {
        using (var b = new SolidBrush(color)) g.FillPolygon(b, points);
    }
    void Line(Color color, double width, params PointF[] points)
    {
        using (var p = new Pen(color, (float)width)) {
            p.LineJoin = LineJoin.Round;
            g.DrawLines(p, points);
        }
    }
    void Rect(Color color, double x, double y, double w, double h)
    {
        using (var b = new SolidBrush(color)) g.FillRectangle(b, (float)x, (float)y, (float)w, (float)h);
    }
    void Oval(Color color, double x, double y, double rx, double ry)
    {
        using (var b = new SolidBrush(color)) g.FillEllipse(b, (float)(x - rx), (float)(y - ry), (float)(2 * rx), (float)(2 * ry));
    }
    void Glow(Color color, double x, double y, double rx, double ry, int alpha)
    {
        using (var path = new GraphicsPath()) {
            path.AddEllipse((float)(x - rx), (float)(y - ry), (float)(2 * rx), (float)(2 * ry));
            using (var b = new PathGradientBrush(path)) {
                b.InterpolationColors = new ColorBlend {
                    Positions = new[] { 0f, .48f, .76f, 1f },
                    Colors = new[] { A(color, 0), A(color, alpha / 6), A(color, alpha / 2), A(color, alpha) }
                };
                g.FillPath(b, path);
            }
        }
    }

    static void DrawScaled(Graphics canvas, Bitmap source, Rectangle destination)
    {
        using (var attributes = new ImageAttributes()) {
            attributes.SetWrapMode(WrapMode.TileFlipXY);
            canvas.InterpolationMode = InterpolationMode.HighQualityBicubic;
            canvas.DrawImage(source, destination, 0, 0, source.Width, source.Height, GraphicsUnit.Pixel, attributes);
        }
    }

    delegate Color Pixel(double x, double y);
    void Raster(Bitmap bitmap, Pixel paint)
    {
        int width = bitmap.Width, height = bitmap.Height;
        var bounds = new Rectangle(0, 0, width, height);
        var data = bitmap.LockBits(bounds, ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
        try {
            var pixels = new int[data.Stride / 4 * height];
            double sx = (double)W / width, sy = (double)H / height;
            System.Threading.Tasks.Parallel.For(0, height, y => {
                int row = y * data.Stride / 4;
                for (int x = 0; x < width; x++) pixels[row + x] = paint((x + .5) * sx, (y + .5) * sy).ToArgb();
            });
            Marshal.Copy(pixels, 0, data.Scan0, pixels.Length);
        } finally { bitmap.UnlockBits(data); }
    }

    double Fbm(double x, double y)
    {
        return .54 * Noise(x, y) + .26 * Noise(2.07 * x + 17, 2.11 * y)
            + .12 * Noise(4.21 * x, 4.39 * y + 71) + .055 * Noise(8.91 * x, 8.93 * y)
            + .025 * Noise(17.8 * x - 28, 18.1 * y);
    }

    Color Sky(double x, double y)
    {
        if (y >= 360) return C(26, 30, 46);
        double v = y - 10 * Math.Sin((x - 220) / 560);
        Color zenith = Blend(C(64, 143, 197), C(146, 180, 197), S(-16, 103, v));
        Color dusk = Blend(zenith, C(255, 169, 131), S(67, 159, v));
        dusk = Blend(dusk, C(209, 104, 89), S(138, 189, v));
        dusk = Blend(dusk, C(82, 86, 120), S(174, 220, v));
        dusk = Blend(dusk, C(88, 91, 120), S(225, 296, v));

        double bend = 31 * Math.Sin(x / 216 + 1.4) + 14 * (Noise(x / 122 + 9, y / 55) - .5);
        double n = Fbm(x / 162 + 77, (y + bend) / 35 + 26);
        double high = Bell((y - (20 + 98 * S(0, 580, x))) / (22 + 5 * Math.Sin(x / 80))) * (1 - .71 * S(270, 876, x));
        double fingers = Bell((y - (101 + 22 * Math.Sin(x / 189))) / 23) * (.37 + .61 * Bell((x - 610) / 360));
        double right = Bell((x - 1380) / 270) * Bell((y - 110 + 17 * Math.Sin(x / 120)) / 19);
        double field = n + .22 * high + .16 * fingers + .13 * right;
        double cloud = S(.51, .80, field) * (1 - .96 * S(156, 217, y));
        cloud *= .62 + .38 * Bell((x - 230) / 720);
        double wisps = S(.53, .68, field) * (1 - S(.65, .78, field));
        Color cloudColor = Blend(C(27, 63, 98), C(75, 62, 78), S(42, 169, y));
        dusk = Blend(dusk, cloudColor, cloud * .89);
        dusk = Blend(dusk, C(244, 167, 142), wisps * .13 * S(74, 149, y) * (1 - S(160, 212, y)));
        double ridge = 213 + 9 * Noise(x / 130 + 30, 21) + 18 * Noise(x / 325 + 2, 11);
        double mountain = S(ridge - 4, ridge + 13, y) * (1 - S(248, 293, y));
        return Blend(dusk, C(65, 73, 108), .45 * mountain);
    }

    static PointF Lerp(PointF a, PointF b, double t) { return P(Mix(a.X, b.X, t), Mix(a.Y, b.Y, t)); }

    sealed class Quad
    {
        readonly PointF a, b, c, d;
        public Quad(PointF a, PointF b, PointF c, PointF d) { this.a = a; this.b = b; this.c = c; this.d = d; }
        public PointF At(double u, double v) { return Lerp(Lerp(a, b, u), Lerp(d, c, u), v); }
        public PointF[] Pane(double a, double b, double top, double bottom)
        { return new[] { At(a, top), At(b, top), At(b, bottom), At(a, bottom) }; }
    }

    void Light(double x, double y, Color color, double strength, double size)
    {
        if (size > 1.25) Glow(color, x, y, size * 5.9, size * 3.8, (int)(73 * strength));
        Oval(A(color, (int)(232 * strength)), x, y, size, Math.Max(.37, size * .53));
        if (size > 1.15) Oval(A(Blend(color, C(255, 255, 232), .63), (int)(230 * strength)), x - .18, y - .12, size * .48, size * .27);
    }

    void HorizonCity()
    {
        var skyline = new PointF[205];
        skyline[0] = P(0, 530);
        for (int i = 0; i < skyline.Length - 2; i++) {
            double x = i * W / (skyline.Length - 3.0);
            double y = 257 + .022 * x + 13 * Noise(x / 59, 4) + R(-4, 5);
            skyline[i + 1] = P(x, y);
        }
        skyline[skyline.Length - 1] = P(W, 530);
        using (var brush = new LinearGradientBrush(new Rectangle(0, 245, W, 286), C(91, 97, 123), C(34, 42, 58), 90f))
            g.FillPolygon(brush, skyline);
        for (int i = 0; i < 8500; i++) {
            double x = R(-5, W + 5), minimum = 263 + x * .022;
            double dy = Math.Pow(R(0, 1), 1.85) * 249;
            double y = minimum + dy;
            double n = Fbm(x / 46, y / 22);
            if (n + .10 * Math.Sin((x - y * 2) / 32) < .33) continue;
            double depth = Clamp(dy / 240);
            if (i % 3 == 0) Rect(A(Blend(C(26, 31, 51), C(98, 91, 118), n), 154), x, y - R(1, 5), R(1, 8), 1 + depth * R(1, 7));
            Color c = i % 6 == 0 ? C(242, 117, 100) : (i % 4 == 0 ? C(236, 182, 136) : C(177, 197, 221));
            Light(x, y, c, R(.32, .92) * (.78 + .22 * depth), R(.42, 1.53) + depth * .4);
        }
        for (int i = 0; i < 23; i++) {
            double x = R(30, 1600), y = 298 + x * .021 + R(-10, 60);
            Glow(i % 3 == 0 ? C(237, 100, 114) : C(224, 162, 115), x, y, R(13, 45), R(2, 6), 44);
        }
    }

    enum Wall { Concrete, Glass, TowerRed, TowerBlue, Housing, Stone }

    Color Surface(Color color, Wall style, double u, double v, int col, int row)
    {
        double reflected = (Fbm(u * 5 + color.R * .09, v * 12 + color.B * .11) - .5) * 35;
        double streak = 6 * Math.Sin(col * 1.68) + 8 * Math.Pow(v, 4);
        Color c = Tone(color, reflected + streak + R(-8, 8) + 8 * S(.72, 1, v));
        if (style == Wall.TowerBlue) c = Blend(c, C(48, 120, 180), .30 + .3 * Math.Sin(u * Math.PI));
        if (style == Wall.TowerRed) c = Blend(c, C(113, 53, 31), .67 * Bell(v / .10));
        if (style == Wall.Stone) c = Tone(c, 12 * Math.Sin(col * .92) * Math.Cos(row * 1.15));
        return c;
    }

    void WallFace(Quad q, Color color, Wall style, int cols, int rows, double occupancy)
    {
        Poly(color, q.Pane(0, 1, 0, 1));
        for (int j = 0; j < rows; j++) {
            double v = j / (double)rows, band = R(.31, 1.5);
            for (int i = 0; i < cols; i++) {
                double u = i / (double)cols;
                Color c = Surface(color, style, u, v, i, j);
                Poly(c, q.Pane(u, Math.Min(1, u + 1.06 / cols), v, Math.Min(1, v + 1.05 / rows)));
                bool lit = R(0, 1) < occupancy * band;
                Color lamp = R(0, 1) < .38 ? C(237, 207, 153) : C(145, 192, 219);
                if (style == Wall.TowerRed && j < 3) lamp = C(253, 148, 69);
                if (style == Wall.TowerBlue && R(0, 1) < .67) lamp = C(97, 173, 244);
                double slit = style == Wall.Housing ? .27 : .11;
                double top = style == Wall.Stone ? .33 : .15;
                double end = style == Wall.Concrete ? .66 : (style == Wall.Stone ? .79 : .86);
                Poly(lit ? Blend(c, lamp, R(.31, .91)) : Tone(c, R(-22, -5)),
                    q.Pane(u + slit / cols, u + R(.70, .93) / cols, v + top / rows, v + end / rows));
                if (lit && R(0, 1) < .52) {
                    PointF p = q.At(u + .41 / cols, v + top / rows);
                    Light(p.X, p.Y, lamp, R(.25, .67), style == Wall.Stone ? R(.36, 1.6) : R(.45, 1.55));
                }
            }
            Color mullion = style == Wall.TowerRed ? C(178, 140, 129) : Tone(color, style == Wall.Housing ? 58 : 23);
            if (style != Wall.Stone) Line(A(mullion, j % 4 == 0 ? 155 : 80), j % 5 == 0 ? .95 : .57, q.At(0, v), q.At(1, v));
        }
        if (style == Wall.Stone) return;
        for (int i = 1; i < cols; i++) {
            double u = i / (double)cols;
            int alpha = i % (style == Wall.Housing ? 2 : 4) == 0 ? 149 : 88;
            Line(A(Tone(color, style == Wall.TowerBlue ? 65 : 34), alpha), i % 3 == 0 ? .95 : .60, q.At(u, 0), q.At(u, 1));
        }
    }

    void Block(double x, double y, double w, double h, double side, double pitch, Wall style, Color color, int cols, int rows, double occupancy)
    {
        double shift = (x + w * .5 - 770) * .031 * (h / 260);
        PointF a = P(x, y), b = P(x + w, y + pitch), c = P(x + w - shift, y + pitch + h), d = P(x - shift, y + h);
        PointF e = P((side > 0 ? b.X : a.X) + side, (side > 0 ? b.Y : a.Y) - Math.Abs(side) * .45);
        PointF f = P(e.X - shift, e.Y + h);
        Quad flank = side > 0 ? new Quad(b, e, f, c) : new Quad(e, a, d, f);
        WallFace(flank, Tone(color, -13), style, Math.Max(2, (int)(Math.Abs(side) / w * cols)), rows, occupancy * .82);
        PointF k = side > 0 ? P(a.X + side, a.Y - Math.Abs(side) * .45) : P(b.X + side, b.Y - Math.Abs(side) * .45);
        Poly(Tone(color, -3), a, b, side > 0 ? e : k, side > 0 ? k : e);
        WallFace(new Quad(a, b, c, d), color, style, cols, rows, occupancy);
        Line(A(Tone(color, 49), 162), .85, a, b);
        if (h > 59) {
            double rx = x + .35 * w, ry = y + pitch * .38 - Math.Abs(side) * .17;
            Rect(Tone(color, -8), rx, ry - 3, w * .43, 4);
            if (R(0, 1) < .48) Light(rx + w * .36, ry - 3, C(251, 80, 64), .69, .80);
        }
    }

    void CityBlocks()
    {
        for (int layer = 0; layer < 3; layer++) {
            for (int i = 0; i < 35 - layer * 8; i++) {
                double x = i * (W / (35 - layer * 8.0)) + R(-28, 31), building = R(15, 39) + layer * R(2, 16);
                double y = 309 + .035 * x + layer * 24 + R(-15, 30);
                double h = R(16, 48) + layer * R(25, 75);
                double street = 510 + (y - 360) * .42;
                if (layer > 0 && Math.Abs(x - street) < 42 + layer * 4) continue;
                Color color = Blend(C(71, 76, 96), C(125, 116, 125), R(0, .92));
                color = Tone(color, -layer * 10);
                Block(x, y, building, h, R(-15, 18), R(-6, 5), i % 3 == 0 ? Wall.Housing : Wall.Concrete,
                    color, (int)R(3, 7), (int)R(7, 12) + layer * 4, R(.15, .34));
            }
        }
        Block(-21, 384, 80, 213, 26, -17, Wall.TowerBlue, C(41, 67, 101), 11, 28, .19);
        Block(124, 345, 89, 255, 20, -4, Wall.Glass, C(20, 32, 47), 11, 30, .21);
        Glow(C(208, 242, 198), 164, 343, 51, 19, 55);
        for (int i = 0; i < 15; i++) Light(139 + i * 4.4, 341 - .1 * i, C(203, 236, 196), R(.45, .95), R(.65, 2));
        Block(228, 367, 84, 232, 22, 10, Wall.Housing, C(48, 57, 75), 9, 24, .24);
        Block(437, 355, 88, 220, -27, 7, Wall.Glass, C(37, 54, 66), 9, 25, .22);
        Block(552, 363, 61, 166, -18, 10, Wall.Housing, C(91, 95, 104), 10, 24, .31);
        Block(603, 392, 59, 162, -13, 7, Wall.Housing, C(71, 75, 102), 8, 24, .29);
        Block(936, 414, 83, 242, -28, 14, Wall.Glass, C(24, 45, 59), 11, 27, .30);
        Block(1056, 419, 103, 203, -23, 12, Wall.Housing, C(107, 109, 120), 14, 23, .24);
        Block(1018, 464, 55, 159, -15, 6, Wall.Housing, C(82, 89, 113), 7, 21, .22);
        Block(1212, 418, 101, 180, -38, 7, Wall.Glass, C(29, 41, 56), 12, 23, .26);
        Block(1292, 419, 101, 160, -21, 3, Wall.Concrete, C(110, 110, 115), 13, 22, .18);
        Block(1423, 434, 69, 175, 25, 9, Wall.Housing, C(60, 81, 93), 9, 22, .27);
        Block(1511, 472, 100, 155, -19, 5, Wall.Glass, C(28, 48, 73), 12, 21, .31);
        Block(1236, 553, 226, 102, -45, 20, Wall.Concrete, C(84, 73, 69), 23, 11, .17);
        PointF[] roof = { P(1207, 539), P(1429, 551), P(1465, 567), P(1242, 559) };
        Poly(C(28, 34, 46), roof);
        Line(A(C(157, 146, 147), 145), 1.2, P(1207, 539), P(1429, 551), P(1465, 567));
        Glow(C(255, 159, 67), 1360, 623, 125, 50, 101);
        PaintLowBlocks();
    }

    void PaintLowBlocks()
    {
        Block(173, 543, 71, 76, 19, 6, Wall.Concrete, C(58, 66, 75), 8, 9, .29);
        Block(185, 609, 50, 50, 18, 8, Wall.Concrete, C(50, 63, 66), 8, 6, .32);
        Block(479, 492, 49, 47, -13, 7, Wall.Concrete, C(51, 57, 69), 7, 7, .28);
        Block(533, 511, 64, 48, -19, 8, Wall.Housing, C(75, 70, 68), 7, 7, .25);
        Block(472, 552, 72, 52, -15, -4, Wall.Stone, C(47, 55, 59), 10, 7, .24);
        Block(565, 573, 64, 39, -14, 4, Wall.Concrete, C(70, 67, 59), 9, 5, .34);
        Block(508, 622, 68, 39, -18, 6, Wall.Concrete, C(67, 65, 58), 9, 5, .34);
        Block(574, 674, 74, 44, -21, -7, Wall.Glass, C(40, 46, 54), 9, 6, .23);
        Block(914, 587, 96, 86, -29, 8, Wall.Glass, C(37, 43, 52), 12, 10, .13);
        Block(1013, 600, 97, 52, -16, 14, Wall.Concrete, C(58, 67, 70), 12, 7, .27);
        Block(1140, 579, 67, 61, -24, 6, Wall.Housing, C(60, 70, 69), 8, 8, .27);
        Block(1379, 602, 129, 51, -27, 7, Wall.Stone, C(51, 51, 59), 13, 8, .16);
        for (int i = 0; i < 24; i++) {
            double t = i / 23.0;
            double x = Mix(1060, 1153, t), y = Mix(417, 433, t);
            Light(x, y, C(214, 226, 216), R(.38, .90), R(.59, 1.48));
        }
        Glow(C(201, 215, 238), 1085, 422, 61, 14, 75);
        Glow(C(242, 111, 54), 1301, 617, 71, 23, 104);
    }
    PointF OnRoute(PointF[] route, double t)
    {
        double k = Clamp(t) * (route.Length - 1);
        int part = Math.Min(route.Length - 2, (int)k);
        double u = k - part;
        PointF b = route[part], c = route[part + 1];
        PointF a = route[Math.Max(0, part - 1)], d = route[Math.Min(route.Length - 1, part + 2)];
        return P(Cubic(a.X, b.X, c.X, d.X, u), Cubic(a.Y, b.Y, c.Y, d.Y, u));
    }

    static double Cubic(double a, double b, double c, double d, double u)
    { return b + .5 * u * (c - a + u * (2 * a - 5 * b + 4 * c - d + u * (3 * b - a - 3 * c + d))); }

    void Avenue(PointF[] route, double near, double far, bool median, double brightness)
    {
        Color asphalt = C(57, 49, 52), amber = C(255, 141, 41), pearl = C(255, 224, 154);
        for (int pass = 0; pass < 3; pass++) {
            for (int i = 0; i < 100; i++) {
                double t = i / 100.0;
                PointF a = OnRoute(route, t), b = OnRoute(route, (i + 1.12) / 100);
                double width = Mix(far, near, t);
                double light = Bell((t - .42) / .16) + .28 * Noise(t * 17, near);
                if (pass == 0) Line(C(37, 36, 39), width + 6, a, b);
                if (pass == 1) Line(Blend(asphalt, C(160, 90, 43), brightness * (.16 + .30 * light)), width, a, b);
                if (pass == 2 && i % 14 == 1) Glow(amber, a.X, a.Y, 12 + width * .72, 6 + width * .30, (int)(91 * brightness));
            }
        }
        for (int i = 0; i < 2; i++) {
            double sign = i == 0 ? -1 : 1;
            for (int j = 1; j < 105; j++) {
                double t = j / 105.0;
                PointF p = OnRoute(route, t);
                PointF next = OnRoute(route, Math.Min(1, t + .014));
                double angle = Math.Atan2(next.Y - p.Y, next.X - p.X);
                double half = .44 * Mix(far, near, t);
                double x = p.X - Math.Sin(angle) * half * sign, y = p.Y + Math.Cos(angle) * half * sign;
                if (j % 3 == 0) {
                    Glow(amber, x, y, Mix(6, 24, t), Mix(4, 14, t), (int)(145 * brightness * R(.48, 1)));
                    Light(x, y, pearl, R(.56, .99) * brightness, Mix(.70, 2.45, t));
                }
                if (R(0, 1) < .69) {
                    double track = R(.17, .78);
                    double carX = Mix(x, p.X, track), carY = Mix(y, p.Y, track);
                    double spread = Mix(1.15, 7.45, t) * R(.38, 1.67);
                    Color c = i == 0 ? C(250, 198, 111) : C(249, 104, 57);
                    Line(A(c, (int)R(68, 204)), Mix(.65, 1.45, t), P(carX, carY), P(carX + Math.Cos(angle) * spread, carY + Math.Sin(angle) * spread));
                }
                if (median && j % 2 == 0) {
                    PointF end = Lerp(p, next, .52);
                    Line(A(C(193, 162, 121), 110), .65, p, end);
                }
            }
        }
    }

    void Ground()
    {
        Poly(C(24, 36, 39), P(0, 556), P(410, 492), P(795, 507), P(1235, 513), P(W, 535), P(W, H), P(0, H));
        for (int i = 0; i < 12000; i++) {
            double y = R(490, H), x = R(0, W);
            double n = Fbm(x / 53 + 28, y / 29 + 66);
            double scale = Mix(.8, 4, S(480, H, y));
            Color turf = Blend(C(7, 17, 24), C(52, 60, 45), S(.25, .69, n));
            Oval(A(Tone(turf, R(-6, 14)), (int)R(75, 175)), x, y, R(.55, 2.8) * scale, R(.4, 1.4) * scale);
        }
        Avenue(new[] { P(519, 387), P(522, 439), P(555, 489), P(623, 529), P(667, 592), P(723, 653), P(806, 747), P(926, 838) }, 42, 12, true, .97);
        Avenue(new[] { P(147, 416), P(124, 497), P(102, 583), P(79, 651), P(40, 760) }, 36, 8, true, .86);
        Avenue(new[] { P(1607, 776), P(1483, 773), P(1371, 789), P(1240, 803), P(1151, 818), P(1010, 838), P(907, 885), P(800, 922), P(660, 950), P(585, 1004), P(535, 1081) }, 40, 29, true, 1);
        Avenue(new[] { P(-21, 915), P(71, 957), P(135, 994), P(186, 1023), P(230, 1075) }, 28, 15, false, .90);
        Avenue(new[] { P(1580, 940), P(1477, 972), P(1426, 987), P(1358, 1005), P(1292, 1066) }, 59, 33, false, 1);
        Avenue(new[] { P(920, 856), P(845, 898), P(786, 946), P(712, 1009), P(667, 1075) }, 13, 10, false, .58);
    }

    void RedBuilding()
    {
        Block(330, 268, 113, 343, 40, 5, Wall.TowerRed, C(36, 30, 41), 14, 44, .14);
        var front = new Quad(P(332, 265), P(442, 272), P(444, 302), P(332, 292));
        Poly(C(88, 43, 32), front.Pane(0, 1, 0, 1));
        for (int i = 0; i < 15; i++) {
            double u = i / 15.0;
            PointF a = front.At(u, 0), b = front.At(u, 1);
            Line(C(156, 85 + 25 * Math.Sin(i), 48), 1.6, a, b);
            Light(a.X, a.Y, C(255, 49, 32), R(.63, .90), R(1.4, 2.3));
            if (i % 3 == 1) Light(b.X, b.Y - 3, C(246, 175, 70), .9, 1.35);
        }
        Glow(C(244, 69, 26), 379, 284, 82, 33, 67);
        Line(A(C(229, 157, 78), 145), 1, P(330, 292), P(443, 302), P(482, 287));
    }

    // Left and right boundaries are hand-plotted in image space from the
    // reference silhouette. Interpolating between corresponding heights
    // lets the floor bands, glass panes and metal ribs share the outline.
    sealed class Twin
    {
        readonly PointF[] left, right;
        readonly bool broad;
        public Twin(bool broad)
        {
            this.broad = broad;
            if (broad) {
                left = new[] { P(675, 161), P(666, 220), P(660, 304), P(657, 411), P(660, 534), P(667, 644), P(675, 720), P(690, 755) };
                right = new[] { P(720, 174), P(768, 236), P(781, 318), P(792, 421), P(800, 540), P(802, 646), P(798, 719), P(797, 751) };
            } else {
                left = new[] { P(850, 178), P(839, 221), P(835, 304), P(834, 401), P(838, 517), P(842, 611), P(845, 689), P(854, 742) };
                right = new[] { P(914, 177), P(923, 222), P(930, 303), P(935, 401), P(935, 506), P(934, 606), P(933, 684), P(931, 730) };
            }
        }
        static PointF Edge(PointF[] p, double t)
        {
            double k = Clamp(t) * (p.Length - 1);
            int i = Math.Min(p.Length - 2, (int)k);
            double u = k - i;
            PointF a = p[Math.Max(0, i - 1)], b = p[i], c = p[i + 1], d = p[Math.Min(i + 2, p.Length - 1)];
            return P(Cubic(a.X, b.X, c.X, d.X, u), Cubic(a.Y, b.Y, c.Y, d.Y, u));
        }
        public PointF At(double u, double v)
        {
            PointF p = Lerp(Edge(left, v), Edge(right, v), u);
            double arch = Math.Sin(Math.PI * u);
            return P(p.X, p.Y + arch * (Mix(broad ? -7 : -14, 12, S(0, .54, v))));
        }
        public PointF[] Strip(double a, double b, double t, double u, int samples = 7)
        {
            PointF[] p = new PointF[2 * (samples + 1)];
            for (int i = 0; i <= samples; i++) {
                double x = Mix(a, b, (double)i / samples);
                p[i] = At(x, t);
                p[p.Length - 1 - i] = At(x, u);
            }
            return p;
        }
        public PointF[] Outline()
        {
            var p = new PointF[176];
            for (int i = 0; i < 24; i++) p[i] = At(i / 24.0, 0);
            for (int i = 0; i < 64; i++) p[i + 24] = At(1, i / 64.0);
            for (int i = 0; i < 24; i++) p[i + 88] = At(1 - i / 24.0, 1);
            for (int i = 0; i < 64; i++) p[i + 112] = At(0, 1 - i / 64.0);
            return p;
        }
    }

    Color TwinGlass(double u, double v, bool broad)
    {
        double edge = broad ? .15 : .34;
        double evening = Bell((u - edge) / .32);
        double reflection = Bell((v - .61 + .035 * Math.Sin(u * 8)) / .076);
        double haze = Bell((v - .72) / .36);
        double n = 36 * (Fbm(u * 4 + 9, v * 8 + (broad ? 72 : 31)) - .5);
        return C(20 + 29 * evening + 4 * reflection + 14 * haze + n,
            26 + 24 * evening + 30 * reflection + 15 * haze + n,
            34 + 29 * evening + 52 * reflection + 18 * haze + n);
    }

    void Ribs(Twin t, double from, double to, double width, Color c, double curve)
    {
        var p = new PointF[89];
        for (int i = 0; i < p.Length; i++) {
            double v = i / (p.Length - 1.0);
            p[i] = t.At(Mix(from, to, S(0, .31, v)) + curve * Math.Sin(Math.PI * v), v);
        }
        Line(A(c, 44), width * 4.1, p);
        Line(A(c, 84), width * 2.15, p);
        Line(A(c, 171), width, p);
    }

    void PaintTwin(bool broad)
    {
        var t = new Twin(broad);
        PointF[] outline = t.Outline();
        using (var path = new GraphicsPath()) {
            path.AddPolygon(outline);
            GraphicsState state = g.Save();
            g.SetClip(path);
            Poly(C(27, 34, 42), outline);
            int cols = broad ? 29 : 25, rows = broad ? 52 : 58;
            double y0 = .023;
            for (int j = 0; j < rows; j++) {
                double a = Mix(y0, 1, j / (double)rows), b = Mix(y0, 1, (j + 1.0) / rows);
                double occupancy = R(.052, .37) + .17 * S(.89, 1, a);
                if (j % 7 == 1) occupancy += .22;
                bool section = false;
                for (int i = 0; i < cols; i++) {
                    double u = i / (double)cols, v = (i + 1.0) / cols;
                    if (i % 3 == 0) section = R(0, 1) < occupancy;
                    Color glass = Tone(TwinGlass((u + v) * .5, a, broad), R(-9, 11));
                    Poly(glass, t.Strip(u, v + .0012, a, b + .0008, 1));
                    if (section ? R(0, 1) < .69 : R(0, 1) < .036) {
                        Color lamp = R(0, 1) < .51 ? C(234, 207, 148) : C(147, 190, 216);
                        double inset = R(.08, .28), high = R(.35, .65);
                        Poly(Blend(glass, lamp, R(.28, .83)), t.Strip(Mix(u, v, inset), Mix(u, v, R(.67, .89)), Mix(a, b, high), Mix(a, b, .84), 1));
                        PointF p = t.At(Mix(u, v, .48), Mix(a, b, high));
                        if (R(0, 1) < .31) Light(p.X, p.Y, lamp, R(.62, .91), R(.65, 1.6));
                    }
                    Line(A(C(12, 22, 32), 148), .64, t.At(u, a), t.At(u, b));
                    for (int k = 0; k < 2; k++) {
                        double jitter = R(.15, .84);
                        Line(A(C(154, 176, 181), (int)R(23, 79)), R(.26, .61), t.At(u, Mix(a, b, jitter)), t.At(Mix(u, v, .69), Mix(a, b, R(.14, .91))), t.At(v, Mix(a, b, 1 - jitter)));
                    }
                }
                for (int i = 0; i < 20; i++) {
                    double u = i / 20.0, v = (i + 1.0) / 20;
                    Line(A(Tone(TwinGlass((u + v) * .5, a, broad), j % 4 == 0 ? 48 : 16), 178), j % 4 == 0 ? .93 : .56, t.At(u, a), t.At(v, a));
                }
            }
            Poly(C(49, 39, 44), t.Strip(0, 1, 0, .094, 18));
            for (int j = 1; j < 7; j++) {
                double v = .0137 * j;
                var p = new PointF[36];
                for (int i = 0; i < p.Length; i++) p[i] = t.At(i / (p.Length - 1.0), v);
                Line(A(j < 3 ? C(229, 98, 66) : C(194, 159, 123), j < 3 ? 145 : 125), j < 3 ? 1.6 : .91, p);
            }
            Ribs(t, broad ? .055 : .08, broad ? .024 : .26, broad ? .95 : 1.46, C(218, 193, 151), broad ? -.007 : .020);
            Ribs(t, broad ? .90 : .92, broad ? .936 : .73, broad ? 2.15 : 1.48, C(255, 227, 173), broad ? .017 : -.063);
            if (broad) Ribs(t, .76, .998, .86, C(172, 176, 160), -.003);
            g.Restore(state);
        }
        var crown = new PointF[41];
        for (int i = 0; i < crown.Length; i++) crown[i] = t.At(i / 40.0, 0);
        Line(A(C(255, 207, 154), 176), 1.45, crown);
        for (int i = 0; i < 4; i++) {
            PointF p = t.At(broad ? .11 + .13 * i : .11 + .24 * i, broad ? .036 : .018);
            Light(p.X, p.Y, C(253, 61, 38), broad ? .95 : .86, broad ? 2.45 : 1.67);
        }
        PointF middle = t.At(broad ? .24 : .51, broad ? .058 : .042);
        Glow(C(250, 59, 27), middle.X, middle.Y, broad ? 41 : 31, 20, broad ? 141 : 99);
        if (broad) Glow(C(255, 107, 56), middle.X - 3, middle.Y - 7, 21, 9, 150);
        PointF foot = t.At(.53, .995);
        Glow(C(255, 183, 78), foot.X, foot.Y, broad ? 81 : 62, 35, 112);
        Poly(C(114, 98, 68), t.Strip(.03, .97, .974, 1, 19));
        for (int i = 0; i < 28; i++) {
            PointF p = t.At(.06 + .89 * i / 27, R(.980, .995));
            Light(p.X, p.Y, C(255, 220, 147), R(.49, .95), R(1.1, 2.15));
        }
    }
    PointF WedgePoint(double u, double v)
    {
        PointF top = P(Mix(149, 683, u), 628 + 178 * Math.Pow(u, 1.64));
        PointF bottom = P(Mix(204, 676, u), 882 + 17 * Math.Sin(u * 2.47));
        return Lerp(top, bottom, v);
    }

    PointF[] WedgeBand(double start, double end, double top, double bottom, int steps = 1)
    {
        var p = new PointF[(steps + 1) * 2];
        for (int i = 0; i <= steps; i++) {
            double u = Mix(start, end, (double)i / steps);
            p[i] = WedgePoint(u, top);
            p[p.Length - 1 - i] = WedgePoint(u, bottom);
        }
        return p;
    }

    void Wedge()
    {
        var roof = new Quad(P(160, 629), P(683, 802), P(716, 755), P(345, 580));
        Poly(C(35, 39, 49), roof.Pane(0, 1, 0, 1));
        const int roofRows = 6, roofCols = 19;
        for (int j = 0; j < roofRows; j++) {
            for (int i = 0; i < roofCols; i++) {
                double u = i / (double)roofCols, v = j / (double)roofRows;
                Color metal = Tone(C(61, 66, 75), R(-24, 13) + j * 1.5);
                Color inset = Tone(C(18, 24, 35), R(-8, 10));
                Poly(metal, roof.Pane(u, u + 1.0 / roofCols, v, v + 1.0 / roofRows));
                Poly(inset, roof.Pane(u + .10 / roofCols, u + .84 / roofCols, v + .14 / roofRows, v + .84 / roofRows));
                Line(A(C(98, 101, 116), 159), .72, roof.At(u, v), roof.At(u + 1.0 / roofCols, v));
            }
        }
        Poly(C(59, 63, 72), WedgeBand(0, 1, 0, 1, 45));
        const int rows = 28, cols = 88;
        for (int j = 0; j < rows; j++) {
            for (int i = 0; i < cols; i++) {
                double u = i / (double)cols, v = j / (double)rows;
                double speckle = (Fbm(u * 13 + 27, v * 7 + 9) - .5) * 35;
                double amber = Bell((u - .71) / .23) * Bell((v - .74) / .35);
                Color baseColor = C(66 + 23 * amber + speckle, 69 + 8 * amber + speckle, 83 - 11 * amber + speckle);
                Color c = Tone(baseColor, R(-13, 13));
                Poly(c, WedgeBand(u, (i + 1.10) / cols, v, (j + 1.08) / rows));
                double inset = R(.11, .43);
                Line(A(Tone(c, R(20, 54)), (int)R(35, 115)), R(.33, .73), WedgePoint((i + inset) / cols, v), WedgePoint((i + .15) / cols, (j + .81) / rows));
                double rooms = .036 * Bell((u - .69) / .19) + .029 * Bell((u - .81) / .09) * Bell((v - .37) / .28);
                if (R(0, 1) < .026 + .059 * amber + rooms) {
                    PointF p = WedgePoint((i + .5) / cols, (j + .58) / rows);
                    Color light = R(0, 1) < .35 ? C(210, 212, 180) : C(245, 185, 103);
                    Light(p.X, p.Y, light, R(.31, .88), R(.63, 2.7));
                }
            }
        }
        for (int j = 0; j < 4; j++) {
            double v = .19 + j * .18;
            var line = new PointF[40];
            for (int i = 0; i < line.Length; i++) line[i] = WedgePoint(i / 39.0, v);
            Line(A(C(39, 44, 56), 96), 1.3, line);
        }
        Glow(C(251, 123, 73), 650, 874, 58, 37, 83);
        Glow(C(247, 193, 95), 495, 893, 49, 23, 79);
    }

    void Canopy(double x, double y, double rx, double ry, double warmth, double scale)
    {
        int clumps = (int)(10 + rx * .63);
        Color dark = C(9, 20, 25), lit = Blend(C(39, 57, 42), C(135, 85, 29), warmth);
        Oval(A(dark, 148), x, y, rx * .81, ry * .8);
        for (int i = 0; i < clumps; i++) {
            double angle = R(0, Math.PI * 2), r = Math.Sqrt(R(0, 1));
            double xx = x + Math.Cos(angle) * r * rx, yy = y + Math.Sin(angle) * r * ry;
            double light = R(.17, .91) * (1 - .63 * S(.28, 1, r)) + .15 * Math.Sin(angle + .7);
            Color baseColor = Blend(dark, lit, Clamp(light));
            double sx = Math.Min(rx * .28, R(1.6, 6) * scale), sy = Math.Min(ry * .42, R(1, 4) * scale);
            Oval(A(baseColor, (int)R(100, 214)), xx, yy, sx, sy);
            for (int j = 0; j < 11; j++) {
                double t = R(0, Math.PI * 2), d = Math.Sqrt(R(0, 1));
                double size = R(.32, 1.48) * scale;
                Oval(A(Tone(baseColor, R(-15, 28)), (int)R(80, 187)), xx + Math.Cos(t) * d * sx, yy + Math.Sin(t) * d * sy, size, size * R(.59, .88));
            }
        }
    }

    void Landscape(bool near)
    {
        double[,] groves = near ? new double[,] {
            {35, 837, 83, 42, .19}, {116, 889, 103, 44, .22}, {334, 925, 98, 43, .14},
            {449, 943, 99, 46, .19}, {522, 975, 76, 56, .31}, {649, 1020, 83, 46, .38},
            {763, 1029, 92, 62, .24}, {846, 1035, 64, 47, .21}, {1569, 901, 67, 55, .14},
            {1470, 941, 60, 39, .30}, {937, 923, 51, 33, .43}, {764, 872, 60, 25, .34},
            {115, 1012, 50, 39, .22}, {13, 970, 48, 36, .18}
        } : new double[,] {
            {1165, 774, 120, 46, .18}, {1285, 735, 93, 43, .24}, {1517, 744, 120, 51, .20},
            {1511, 657, 114, 41, .14}, {1346, 685, 100, 48, .38}, {1241, 696, 92, 35, .17},
            {961, 775, 85, 31, .45}, {918, 715, 49, 25, .31}, {725, 783, 60, 31, .46},
            {646, 734, 53, 28, .41}, {520, 658, 39, 24, .60}, {110, 688, 61, 29, .39}
        };
        for (int i = 0; i < groves.GetLength(0); i++) {
            double x = groves[i, 0], y = groves[i, 1], rx = groves[i, 2], ry = groves[i, 3];
            for (int j = 0; j < (near ? 21 : 17); j++) {
                double phi = R(0, Math.PI * 2), r = Math.Sqrt(R(0, 1));
                Canopy(x + Math.Cos(phi) * r * rx, y + Math.Sin(phi) * r * ry,
                    R(9, 27) * (near ? 1.16 : .85), R(5, 15), groves[i, 4], near ? 1.18 : .84);
            }
        }
    }

    PointF PodPoint(double cx, double cy, double r, double h, double u, double v)
    {
        double round = Math.Pow(Math.Max(0, Math.Sin(Math.PI * v)), .68);
        double x = cx + (u * 2 - 1) * r * round + 42 * (1 - v);
        double y = cy + h * (v - .5) - 14 * (u - .5) * round - 11 * Math.Sin(Math.PI * u) * round;
        return P(x, y);
    }

    void Pod(double cx, double cy, double r, double h)
    {
        var outline = new PointF[64];
        for (int i = 0; i < 32; i++) {
            double v = i / 31.0;
            outline[i] = PodPoint(cx, cy, r, h, 0, v);
            outline[63 - i] = PodPoint(cx, cy, r, h, 1, v);
        }
        for (int i = 0; i < 36; i++) {
            double v = i / 36.0, w = (i + 1.0) / 36;
            PointF a = PodPoint(cx, cy, r, h, 1, v), b = PodPoint(cx, cy, r, h, 1, w);
            double sideA = 27 * Math.Pow(Math.Sin(v * Math.PI), .66), sideB = 27 * Math.Pow(Math.Sin(w * Math.PI), .66);
            Poly(Tone(C(57, 63, 74), R(-11, 12)), a, P(a.X + sideA, a.Y + 11 * Math.Sin(v * Math.PI)),
                P(b.X + sideB, b.Y + 11 * Math.Sin(w * Math.PI)), b);
            if (i % 3 == 0) Line(A(C(133, 137, 127), 110), .77, a, P(a.X + sideA, a.Y + 11 * Math.Sin(v * Math.PI)));
        }
        Poly(C(27, 32, 39), outline);
        for (int i = 1; i < 19; i++) {
            double v = i / 20.0;
            for (int j = 0; j < 12; j++) {
                double a = j / 12.0, b = (j + .88) / 12;
                Color c = Blend(C(36, 42, 55), C(145, 153, 102), Bell((a - .41) / .35) * R(0, .88));
                if (i % 4 == 1) c = Tone(c, R(-22, -11));
                Poly(c, PodPoint(cx, cy, r, h, a, v), PodPoint(cx, cy, r, h, b, v),
                    PodPoint(cx, cy, r, h, b, v + .027), PodPoint(cx, cy, r, h, a, v + .027));
            }
            Line(A(C(100, 107, 113), 121), 1, PodPoint(cx, cy, r, h, 0, v), PodPoint(cx, cy, r, h, .5, v), PodPoint(cx, cy, r, h, 1, v));
        }
        for (int j = 0; j <= 7; j++) {
            var rib = new PointF[31];
            for (int i = 0; i < rib.Length; i++) rib[i] = PodPoint(cx, cy, r, h, j / 7.0, i / 30.0);
            Line(A(C(119, 125, 134), j == 0 || j == 7 ? 170 : 89), j == 7 ? 2.2 : .8, rib);
        }
        Glow(C(225, 190, 71), cx - r * .42, cy + h * .46, r * .72, h * .14, 77);
    }

    PointF DomePoint(double theta, double rad, double level)
    {
        double dx = 220 * rad * Math.Cos(theta), dy = 66 * rad * Math.Sin(theta);
        double cap = -34 * Math.Sqrt(Math.Max(0, 1 - rad * rad));
        return P(1165 + dx + .31 * dy, 919 + dy - .24 * dx + cap + level);
    }

    PointF[] DomeStrip(double from, double to, double radius, double radius2, double level, double level2, int count)
    {
        var p = new PointF[2 * (count + 1)];
        for (int i = 0; i <= count; i++) {
            double a = Mix(from, to, i / (double)count);
            p[i] = DomePoint(a, radius, level);
            p[p.Length - i - 1] = DomePoint(a, radius2, level2);
        }
        return p;
    }

    void DomeLine(double from, double to, double radius, double level, double width, Color color)
    {
        var p = new PointF[122];
        for (int i = 0; i < p.Length; i++) p[i] = DomePoint(Mix(from, to, i / (p.Length - 1.0)), radius, level);
        Line(color, width, p);
    }

    void GoldDome()
    {
        Glow(C(242, 143, 34), 1171, 984, 270, 98, 102);
        Glow(C(255, 184, 74), 1172, 975, 233, 80, 111);
        Poly(C(110, 70, 33), DomeStrip(-.21, 3.05, 1, 1, -8, 77, 140));
        for (int ring = 0; ring < 6; ring++) {
            double y = ring * 11;
            for (int j = 0; j < 124; j++) {
                double a = Mix(-.21, 3.05, j / 124.0), b = Mix(-.21, 3.05, (j + .91) / 124);
                double reflected = .52 + .26 * Math.Sin(a + .6) + R(-.19, .27) - ring * .015;
                Color panel = Blend(C(93, 56, 39), C(254, 165, 62), Clamp(reflected));
                Poly(panel, DomeStrip(a, b, 1, 1, y, y + R(7, 10), 1));
                if (R(0, 1) < .68) {
                    PointF p = DomePoint((a + b) * .5, 1, y + 4.5);
                    Light(p.X, p.Y, C(253, 191, 91), R(.33, .71), R(.5, 1.37));
                }
            }
            DomeLine(-.21, 3.05, 1, y + 2, 4.8, A(C(252, 138, 43), 58));
            DomeLine(-.21, 3.05, 1, y + 2, 1.05, A(C(255, 208, 119), 218));
        }
        // The curved roof uses a dense lattice in the same image coordinates.
        for (int ring = 0; ring < 24; ring++) {
            double r = (ring + 1) / 24.0, low = ring / 24.0;
            for (int j = 0; j < 110; j++) {
                double a = 2 * Math.PI * j / 110.0, b = 2 * Math.PI * (j + 1.02) / 110;
                double specular = Bell((a - 3.95) / .87) + .19 * Math.Sin(a * 2.2);
                Color baseColor = Blend(C(33, 36, 48), C(76, 77, 86), Clamp(specular * .57 + R(.04, .31)));
                Poly(baseColor, DomeStrip(a, b, r, low, 0, 0, 1));
            }
        }
        using (var path = new GraphicsPath()) {
            var roof = new PointF[140];
            for (int i = 0; i < roof.Length; i++) roof[i] = DomePoint(2 * Math.PI * i / roof.Length, 1, 0);
            path.AddPolygon(roof);
            GraphicsState state = g.Save();
            g.SetClip(path);
            for (int j = 0; j < 48; j++) {
                double y = 816 + j * 4.34;
                Line(A(C(169, 150, 146), (int)R(55, 109)), R(.48, .92), P(930, y + 44), P(1065, y - 3), P(1210, y - 35), P(1397, y - 63));
            }
            for (int j = 0; j < 83; j++) {
                double x = 884 + j * 6.75;
                Line(A(C(136, 142, 160), (int)R(42, 98)), R(.48, .73), P(x, 793), P(x + 60, 890), P(x + 102, 1005));
            }
            g.Restore(state);
        }
        DomeLine(0, 2 * Math.PI, 1, 0, 2.2, C(227, 193, 125));
        DomeLine(2.38, 5.44, .87, 0, 8.2, A(C(255, 204, 112), 98));
        DomeLine(2.38, 5.44, .87, 0, 2.8, C(245, 227, 165));
        DomeLine(2.68, 5.25, .78, 0, 2.2, A(C(252, 219, 134), 193));
    }
    void Courtyard()
    {
        PointF[] plaza = { P(684, 775), P(743, 746), P(809, 742), P(856, 723), P(939, 732), P(975, 768), P(925, 801), P(850, 807), P(765, 823) };
        Poly(C(57, 53, 48), plaza);
        Line(A(C(184, 162, 124), 131), 1.15, P(699, 772), P(740, 762), P(805, 763), P(841, 741), P(891, 746), P(934, 752), P(965, 765));
        for (int i = 0; i < 57; i++) {
            double x = R(706, 960), y = 779 + R(-9, 12) - (x - 760) * .098;
            if (i % 3 == 0) Oval(C(29, 38, 35), x + 2, y + 4, R(2.5, 8), R(1.4, 4));
            if (i % 2 == 0) Light(x, y, R(0, 1) < .6 ? C(251, 192, 86) : C(185, 211, 143), R(.48, .86), R(.74, 1.7));
        }
        Poly(C(40, 76, 101), P(909, 797), P(918, 788), P(936, 786), P(967, 797), P(972, 803), P(949, 813), P(932, 812));
        Line(A(C(118, 157, 178), 166), 1.25, P(909, 797), P(918, 788), P(936, 786), P(967, 797), P(972, 803));
        for (int i = 0; i < 14; i++) {
            double x = 914 + i * 4.15;
            double y = 794 + 9 * Math.Pow((i - 4) / 10.0, 2);
            Light(x, y, C(100, 163, 198), .63, R(.60, 1.05));
        }
    }

    void NearLights()
    {
        double[,] concentrations = {
            {520, 469, 50, 23, 45}, {556, 534, 65, 41, 100}, {616, 593, 50, 40, 84}, {638, 649, 31, 21, 66},
            {90, 682, 25, 44, 57}, {67, 761, 39, 31, 40}, {133, 975, 76, 22, 68}, {812, 932, 39, 21, 54},
            {922, 882, 56, 23, 74}, {1234, 788, 60, 20, 65}, {1474, 765, 84, 19, 70}, {1410, 1008, 88, 20, 66},
            {730, 776, 60, 17, 61}, {906, 750, 38, 19, 64}, {1351, 625, 74, 24, 74}
        };
        for (int i = 0; i < concentrations.GetLength(0); i++) {
            double x = concentrations[i, 0], y = concentrations[i, 1], rx = concentrations[i, 2], ry = concentrations[i, 3];
            int count = (int)concentrations[i, 4];
            Color amber = i % 4 == 0 ? C(236, 176, 74) : C(255, 141, 51);
            Glow(amber, x, y, rx * 1.32, ry * 1.48, 105);
            for (int j = 0; j < count; j++) {
                double angle = R(0, 2 * Math.PI), r = Math.Pow(R(0, 1), .75);
                double xx = x + rx * r * Math.Cos(angle), yy = y + ry * r * Math.Sin(angle);
                Color c = j % 8 == 0 ? C(164, 218, 203) : Blend(amber, C(255, 228, 151), R(.14, .76));
                if (j % 7 == 0) Glow(c, xx, yy, R(5, 14), R(3, 7), (int)R(58, 124));
                Light(xx, yy, c, R(.51, .93), R(.56, 2.01));
            }
        }
    }

    sealed class GlowField
    {
        readonly int width, height, step;
        readonly float[] field;

        public GlowField(int[] pixels, int stride, int imageWidth, int imageHeight)
        {
            step = Math.Max(2, imageWidth / 400);
            width = (imageWidth + step - 1) / step;
            height = (imageHeight + step - 1) / step;
            field = new float[width * height * 3];
            for (int y = imageHeight / 4; y < imageHeight; y++) {
                for (int x = 0; x < imageWidth; x++) {
                    int pixel = pixels[y * stride + x], r = (pixel >> 16) & 255, g = (pixel >> 8) & 255, b = pixel & 255;
                    double light = S(127, 247, Math.Max(r, Math.Max(g, b))) * S(61, 147, .29 * r + .52 * g + .19 * b);
                    int i = 3 * ((y / step) * width + x / step);
                    double weight = light / (step * step);
                    field[i] += (float)(r * weight);
                    field[i + 1] += (float)(g * weight);
                    field[i + 2] += (float)(b * weight);
                }
            }
            var horizontal = new float[field.Length];
            int[] kernel = { 1, 4, 6, 4, 1 };
            for (int y = 2; y < height - 2; y++) {
                for (int x = 2; x < width - 2; x++) {
                    int i = 3 * (y * width + x);
                    for (int c = 0; c < 3; c++)
                        for (int k = -2; k <= 2; k++) horizontal[i + c] += field[i + c + 3 * k] * kernel[k + 2] / 16;
                }
            }
            Array.Clear(field, 0, field.Length);
            for (int y = 2; y < height - 2; y++) {
                for (int x = 2; x < width - 2; x++) {
                    int i = 3 * (y * width + x);
                    for (int c = 0; c < 3; c++)
                        for (int k = -2; k <= 2; k++) field[i + c] += horizontal[i + c + 3 * k * width] * kernel[k + 2] / 16;
                }
            }
        }

        public double At(int x, int y, int channel)
        {
            int ax = x / step, ay = y / step;
            int bx = Math.Min(width - 1, ax + 1), by = Math.Min(height - 1, ay + 1);
            double u = (x % step) / (double)step, v = (y % step) / (double)step;
            return Mix(Mix(field[3 * (ay * width + ax) + channel], field[3 * (ay * width + bx) + channel], u),
                Mix(field[3 * (by * width + ax) + channel], field[3 * (by * width + bx) + channel], u), v);
        }
    }

    void ColorGrade(Bitmap bitmap)
    {
        int width = bitmap.Width, height = bitmap.Height;
        var data = bitmap.LockBits(new Rectangle(0, 0, width, height), ImageLockMode.ReadWrite, PixelFormat.Format32bppArgb);
        try {
            int stride = data.Stride / 4;
            var pixels = new int[stride * height];
            Marshal.Copy(data.Scan0, pixels, 0, pixels.Length);
            var glow = new GlowField(pixels, stride, width, height);
            System.Threading.Tasks.Parallel.For(0, height, y => {
                double v = y / (double)height;
                for (int x = 0; x < width; x++) {
                    double u = x / (double)width;
                    int index = y * stride + x;
                    int p = pixels[index];
                    double r = (p >> 16) & 255, green = (p >> 8) & 255, b = p & 255;
                    double luma = .25 * r + .52 * green + .23 * b;
                    double grain = (Hash(x * 3, y * 7) + Hash(y * 11 + 32, x * 17) - 1) * (1.3 + 2.7 * Bell((luma - 61) / 54));
                    double vignette = 1 - .115 * Clamp(Math.Pow((u - .49) / .61, 2) + Math.Pow((v - .44) / .91, 2));
                    double contrast = 1.04 - .045 * S(.22, .33, v) * (1 - S(.45, .74, v));
                    double bloom = .24 * S(.27, .32, v);
                    pixels[index] = C(((r - 27) * contrast + 27) * vignette + grain + glow.At(x, y, 0) * bloom,
                        ((green - 27) * contrast + 27) * vignette + grain * .91 + glow.At(x, y, 1) * bloom,
                        ((b - 27) * contrast + 27) * vignette + grain * 1.05 + glow.At(x, y, 2) * bloom).ToArgb();
                }
            });
            Marshal.Copy(pixels, 0, data.Scan0, pixels.Length);
        } finally { bitmap.UnlockBits(data); }
    }

    void Paint(string output, string preview, int width)
    {
        int height = (int)Math.Round(width * 2.0 / 3);
        int sampling = width < 2500 ? 2 : 1;
        using (var plate = new Bitmap(width * sampling, height * sampling, PixelFormat.Format32bppArgb)) {
            Raster(plate, Sky);
            using (g = Graphics.FromImage(plate)) {
                g.ScaleTransform(plate.Width / (float)W, plate.Height / (float)H);
                g.SmoothingMode = SmoothingMode.AntiAlias;
                g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                HorizonCity();
                Ground();
                CityBlocks();
                RedBuilding();
                Landscape(false);
                Courtyard();
                Pod(1106, 679, 61, 208);
                Pod(1461, 717, 69, 151);
                PaintTwin(false);
                PaintTwin(true);
                NearLights();
                Wedge();
                Landscape(true);
                Block(-31, 959, 86, 114, 12, 47, Wall.Concrete, C(51, 56, 75), 10, 9, .11);
                GoldDome();
            }
            using (var final = new Bitmap(width, height, PixelFormat.Format32bppArgb)) {
                using (var canvas = Graphics.FromImage(final)) DrawScaled(canvas, plate, new Rectangle(0, 0, width, height));
                ColorGrade(final);
                final.Save(output, ImageFormat.Png);
                if (String.IsNullOrEmpty(preview)) return;
                int size = Math.Min(1440, width), previewHeight = (int)Math.Round(size * 2.0 / 3);
                using (var thumb = new Bitmap(size, previewHeight, PixelFormat.Format24bppRgb)) {
                    using (var canvas = Graphics.FromImage(thumb)) DrawScaled(canvas, final, new Rectangle(0, 0, size, previewHeight));
                    thumb.Save(preview, ImageFormat.Png);
                }
            }
        }
    }

    public static void Render(string output, string preview, int width, int seed)
    {
        new ChengduAerial(seed).Paint(output, preview, width);
    }
}
