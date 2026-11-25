using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public sealed class ChengduDusk
{
    const int W = 1600, H = 1067;
    readonly int seed;
    readonly Random random;
    Graphics g;

    ChengduDusk(int seed) { this.seed = seed; random = new Random(seed); }

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

    Color Atmosphere(double x, double y)
    {
        double u = x / W, v = y / 775;
        double west = Bell((u - .20) / .55);
        double t = Math.Pow(Clamp(v), 1.48);
        double warm = west * S(.28, 1, v);
        double r = Mix(62, 204, t) + 40 * warm;
        double green = Mix(88, 167, t) + 15 * warm;
        double b = Mix(128, 155, t) - 24 * warm;

        double perspective = 1 + 1.85 * Math.Pow(Clamp(v), 3);
        double warp = Noise(x / 290 + 24, y / 79) - .5;
        double cloudY = y + 59 * warp + 22 * u + 18 * Math.Sin(u * 5.2);
        double cloudX = (x - 650) / (235 / perspective) + 31;
        double ty = cloudY / (51 / perspective);
        double n = .53 * Noise(cloudX, ty) + .25 * Noise(cloudX * 2.03, ty * 2.1 + 21)
            + .13 * Noise(cloudX * 4.2 + 18, ty * 4.4) + .06 * Noise(cloudX * 9, ty * 8.8) + .03 * Noise(cloudX * 19, ty * 17);
        double banks = .16 * Bell((cloudY - 198 - 53 * u) / 113)
                     + .15 * Bell((cloudY - 444 + 40 * u) / 74)
                     + .11 * Bell((cloudY - 583 - 16 * u) / 54);
        double opacity = S(.51, .84, n + banks) * (1 - .67 * S(.74, 1.06, v));
        double scatter = S(.18, .95, v);
        double edge = S(.49, .65, n + banks) * (1 - S(.61, .78, n + banks));
        double rose = west * S(.22, .82, v);
        double fray = (Noise(x / 24 + 109, cloudY / 13) - .5) * edge * 6;
        double opening = Bell((x - 478) / 360) * Bell((y - 681) / 61) * (1 - opacity);
        r = Mix(r, 55 + 74 * scatter + 40 * rose, opacity * .86) + edge * (9 + 28 * rose) + fray;
        green = Mix(green, 65 + 52 * scatter + 4 * rose, opacity * .86) + edge * (4 + 9 * rose) + fray;
        b = Mix(b, 100 + 42 * scatter - 15 * rose, opacity * .86) + edge * 4 + fray;
        double horizon = Bell((x - 360) / 530) * Bell((y - 732) / 138);
        return C(r + 9 * horizon + 16 * opening, green + 4 * horizon + 8 * opening, b - 6 * horizon + 2 * opening);
    }

    void Building(double x, double y, double w, double bottom, double side, Color face, int floors, int bays, double light)
    {
        double skew = Math.Sign(side) * Math.Min(24, Math.Abs(side) * .38);
        int style = (int)(Hash((int)x + 169, (int)y + 87) * 4);
        double sx = side > 0 ? x + w : x;
        double sy = y - skew * (side > 0 ? 1 : 0);
        Poly(Tone(face, -15), P(sx, sy), P(sx + side, sy + Math.Abs(skew)), P(sx + side, bottom), P(sx, bottom));
        Poly(face, P(x, y), P(x + w, y - skew), P(x + w, bottom), P(x, bottom));
        double step = (bottom - y) / floors;
        for (int j = 0; j < floors; j++) {
            double fy = y + j * step;
            double tilt = skew * (1 - (double)j / floors);
            Color belt = Tone(face, j % 5 == 0 ? -13 : -5);
            Line(belt, j % 5 == 0 ? 1.4 : .65, P(x, fy), P(x + w, fy - tilt));
            double sideY = fy - (side > 0 ? tilt : 0);
            Line(Tone(face, -20), .65, P(sx, sideY), P(sx + side, sideY + Math.Abs(tilt)));
            if (Math.Abs(side) >= 16) {
                int sideBays = Math.Max(2, (int)(Math.Abs(side) / (w / bays)));
                for (int k = 0; k < sideBays; k++) {
                    double a = (k + .16) / sideBays, b = (k + .81) / sideBays;
                    double py = sideY + step * .21;
                    double rise = Math.Abs(tilt), hh = step * .56;
                    double z = Hash(j * 21 + k, (int)x + 8);
                    Color pane = Tone(face, -22 + 16 * z + 6 * Math.Sin(k));
                    if (z > .97 && step > 5) pane = Blend(pane, C(244, 202, 151), .55);
                    Poly(pane, P(sx + side * a, py + a * rise), P(sx + side * b, py + b * rise),
                        P(sx + side * b, py + b * rise + hh), P(sx + side * a, py + a * rise + hh));
                }
            }
            for (int i = 0; i < bays; i++) {
                double a = (i + (style == 1 ? .07 : .13)) / bays, b = (i + (style == 1 ? .96 : .85)) / bays;
                double yy = fy + step * (style == 2 ? .12 : .24);
                double hh = step * R(style == 2 ? .62 : .32, style == 2 ? .89 : .64);
                bool lit = R(0, 1) < light * (.52 + .81 * Bell((j - floors * .63) / (floors * .22)));
                double stripe = style == 1 ? (i % 4 == 0 ? 8 : -8) : 0;
                double reflection = (Noise(i * .55 + 18, j * .43 + x) - .5) * 20;
                Color glass = Tone(face, R(-17, 10) + 5 * Math.Sin(i * .63) + stripe + reflection);
                if (lit) glass = Blend(face, R(0, 1) < .24 ? C(161, 194, 195) : C(242, 192, 132), R(.25, .83));
                Poly(glass, P(x + a * w, yy - a * tilt), P(x + b * w, yy - b * tilt),
                    P(x + b * w, yy + hh - b * tilt), P(x + a * w, yy + hh - a * tilt));
                if (lit && step > 7) Line(A(C(255, 232, 191), 82), .65, P(x + a * w, yy - a * tilt), P(x + b * w, yy - b * tilt));
            }
        }
        for (int i = 0; i <= bays; i++) {
            double a = (double)i / bays;
            Line(A(Tone(face, i % 3 == 0 ? 30 : 12), 105), i % 3 == 0 ? 1.05 : .6,
                P(x + w * a, y - skew * a), P(x + w * a, bottom));
        }
        if (style == 0 && w > 45) {
            for (int i = 0; i < bays; i += 3) {
                double a = (double)i / bays;
                Line(A(Tone(face, 43), 120), 1.45, P(x + w * a, y - skew * a), P(x + w * a, bottom));
            }
        }
        Line(Tone(face, 23), .85, P(x, y), P(x + w, y - skew));
        if (w > 49) {
            double xx = x + R(.24, .59) * w;
            double yy = y - (xx - x) / w * skew;
            Rect(Tone(face, -5), xx, yy - 5, w * .22, 6);
            if (w > 100) {
                Line(Tone(face, 14), .7, P(xx + w * .10, yy - 5), P(xx + w * .10, yy - 18));
                Oval(C(191, 91, 83), xx + w * .10, yy - 18, .9, .9);
            }
        }
    }

    void Skyline()
    {
        for (int i = 0; i < 43; i++) {
            double x = i * 39 + R(-20, 10);
            double y = R(651, 746) - 22 * Bell((x - 1320) / 250);
            Building(x, y, R(21, 50), R(792, 818), R(-13, 10), Blend(C(112, 105, 114), C(148, 125, 123), R(0, 1)), (int)R(9, 21), 4, .06);
        }
        Building(-57, 456, 166, 818, 51, C(66, 76, 88), 35, 17, .11);
        Building(80, 546, 82, 818, 26, C(89, 90, 100), 26, 9, .09);
        Building(155, 614, 99, 807, -22, C(111, 100, 105), 19, 10, .12);
        Building(258, 597, 62, 811, 17, C(105, 97, 106), 22, 7, .10);
        Building(329, 665, 70, 809, 18, C(119, 106, 108), 16, 8, .14);
        Building(335, 690, 122, 811, 17, C(104, 94, 96), 13, 15, .11);
        Building(454, 657, 88, 811, -19, C(92, 92, 105), 16, 9, .14);
        Building(1013, 678, 106, 813, 26, C(90, 89, 102), 14, 12, .15);
        Building(1128, 545, 82, 814, 25, C(89, 93, 111), 28, 10, .13);
        Building(1215, 603, 69, 816, 16, C(101, 92, 104), 23, 8, .19);
        Building(1307, 509, 103, 816, 39, C(76, 86, 104), 28, 14, .13);
        Building(1260, 665, 103, 824, 27, C(82, 81, 96), 17, 13, .14);
        Building(1440, 548, 77, 810, -18, C(85, 90, 106), 25, 8, .15);
        Building(1520, 441, 107, 814, -41, C(71, 81, 100), 36, 11, .16);
        Glow(C(247, 180, 145), 590, 743, 600, 124, 44);
    }

    // A facade chart maps two coordinates directly into the image.
    // Its row curves also place the glass, floor slabs and outer screen.
    sealed class Facade
    {
        readonly double cx, top, foot, radius, lean, rim;
        public Facade(double cx, double top, double foot, double radius, double lean, double rim)
        { this.cx = cx; this.top = top; this.foot = foot; this.radius = radius; this.lean = lean; this.rim = rim; }

        public PointF At(double u, double v)
        {
            double d = u * 2 - 1;
            double fullness = .665 + .34 * Math.Pow(Math.Sin(Math.PI * Clamp(v)), .84) + .09 * v;
            double x = cx + lean * (1 - v) + d * radius * fullness;
            double y = Mix(top, foot, v) + 8 * (1 - d * d) * (1 - .35 * v) + rim * d * (1 - .5 * v);
            return P(x, y);
        }

        public PointF[] Band(double lo, double hi, double va, double vb, int steps = 7)
        {
            var result = new PointF[(steps + 1) * 2];
            for (int i = 0; i <= steps; i++) {
                double u = Mix(lo, hi, (double)i / steps);
                result[i] = At(u, va);
                result[result.Length - i - 1] = At(u, vb);
            }
            return result;
        }

        public PointF[] Silhouette()
        {
            var shape = new PointF[152];
            for (int i = 0; i < 25; i++) shape[i] = At(i / 24.0, 0);
            for (int i = 0; i < 51; i++) shape[25 + i] = At(1, (i + 1) / 51.0);
            for (int i = 0; i < 25; i++) shape[76 + i] = At(1 - i / 24.0, 1);
            for (int i = 0; i < 51; i++) shape[101 + i] = At(0, 1 - (i + 1) / 51.0);
            return shape;
        }
    }

    Color TowerTint(double u, double v, bool west)
    {
        double sunset = Bell((u - (west ? .24 : .28)) / .28);
        double shine = Bell((u - .61) / .20);
        double shadow = S(.64, 1, u);
        double reflection = Noise(u * 6 + 71, v * 9 + (west ? 9 : 31)) - .5;
        double cloud = Bell((v - .48 - u * .07) / .20);
        return C(44 + 42 * sunset + 15 * shine - 19 * shadow + 22 * v + 30 * reflection + 13 * cloud,
            62 + 23 * sunset + 22 * shine - 24 * shadow + 7 * v + 25 * reflection + 4 * cloud,
            87 + 12 * sunset + 27 * shine - 27 * shadow - 9 * v + 28 * reflection);
    }

    void Tower(Facade f, int floors, bool west)
    {
        var silhouette = f.Silhouette();
        using (var clip = new GraphicsPath()) {
            clip.AddPolygon(silhouette);
            var state = g.Save();
            g.SetClip(clip);
            Poly(C(55, 63, 77), silhouette);
            int bays = 44;
            for (int row = 0; row < floors; row++) {
                double va = (double)row / floors, vb = (row + 1.0) / floors;
                double band = R(0, 1);
                bool on = false;
                for (int col = 0; col < bays; col++) {
                    double u = (col + .5) / bays;
                    double a = (double)col / bays, b = (col + 1.0) / bays;
                    if (col % (west ? 3 : 4) == 0) on = R(0, 1) < .09 + .26 * band * band;
                    Color pane = Tone(TowerTint(u, (va + vb) * .5, west), R(-12, 11) + 6 * Math.Sin(col * 1.71));
                    Poly(pane, f.Band(a, b + .0014, va, vb + .0008, 1));
                    if (row > 1 && ((on && R(0, 1) < .84) || R(0, 1) < .036)) {
                        Color interior = R(0, 1) < .19 ? C(179, 207, 213) : C(255, R(175, 225), R(104, 168));
                        double exposure = R(.34, .84) * (1 - .30 * S(.8, 1, u));
                        Color litPane = Blend(pane, interior, exposure);
                        double left = Mix(a, b, .09), right = Mix(a, b, R(.75, .94));
                        double y1 = Mix(va, vb, .20), y2 = Mix(va, vb, R(.69, .90));
                        Poly(litPane, f.Band(left, right, y1, y2, 1));
                        Line(Blend(litPane, interior, .66), .68, f.At(left, y1), f.At(right, y1));
                        if (R(0, 1) < .34) Poly(Blend(pane, litPane, .38), f.Band(Mix(left, right, .48), right, Mix(y1, y2, .54), y2, 1));
                    }
                    Line(A(C(16, 32, 50), 135), .62, f.At(a, va), f.At(a, vb));
                }
                int divisions = 35;
                for (int i = 0; i < divisions; i++) {
                    double u = (i + .5) / divisions;
                    Color seam = Tone(TowerTint(u, va, west), -25);
                    Line(A(seam, 218), .92, f.At((double)i / divisions, va), f.At((i + 1.0) / divisions, va));
                }
            }

            IceScreen(f, west);
            for (int floor = 0; floor <= floors; floor += (west ? 4 : 5)) {
                double v = (double)floor / floors;
                for (int i = 0; i < 26; i++) {
                    double u = i / 26.0;
                    Color metal = Tone(TowerTint(u, v, west), 37);
                    Line(A(metal, 170), .95, f.At(u, v + .0023), f.At((i + 1.0) / 26, v + .0023));
                }
            }
            Poly(A(C(22, 34, 52), 175), f.Band(0, 1, 0, .020));
            for (int i = 0; i < 46; i++) {
                double u = (i + .5) / 46;
                Line(A(C(183, 198, 204), 105), .65, f.At(u, .003), f.At(u, .018));
            }
            g.Restore(state);
        }
        for (int i = 0; i < 24; i++) {
            double a = i / 24.0, b = (i + 1.0) / 24;
            Line(A(C(193, 195, 202), 162), 1.07, f.At(a, 0), f.At(b, 0));
        }
        for (int i = 0; i < 64; i++) {
            double a = i / 64.0, b = (i + 1.0) / 64;
            Line(A(C(224, 194, 174), (int)Mix(130, 48, a)), 1.07, f.At(0, a), f.At(0, b));
            Line(A(C(160, 177, 195), 82), .86, f.At(1, a), f.At(1, b));
        }
        var beacon = f.At(west ? .17 : .80, 0);
        Glow(C(255, 57, 37), beacon.X, beacon.Y - 1, 7, 6, 55);
        Oval(C(255, 131, 105), beacon.X, beacon.Y - 1, 1.07, .94);
    }

    void IceScreen(Facade f, bool west)
    {
        // Each irregular quadrilateral is subdivided around an offset joint.
        // Fine highlights are offset from the dark cut edges by a subpixel.
        const int cols = 17, rows = 67;
        var grid = new PointF[cols + 1, rows + 1];
        for (int j = 0; j <= rows; j++) {
            for (int i = 0; i <= cols; i++) {
                double u = (i + (i == 0 || i == cols ? 0 : R(-.39, .39))) / cols;
                double v = (j + (j == 0 || j == rows ? 0 : R(-.38, .38))) / rows;
                grid[i, j] = P(u, v);
            }
        }
        for (int j = 0; j < rows; j++) {
            for (int i = 0; i < cols; i++) {
                PointF a = grid[i, j], b = grid[i + 1, j], c = grid[i + 1, j + 1], d = grid[i, j + 1];
                PointF mid = P(Mix(a.X, c.X, R(.26, .76)), Mix(a.Y, c.Y, R(.26, .75)));
                double u = (i + .5) / cols, v = (j + .5) / rows;
                Color metal = Tone(TowerTint(u, v, west), 50 + 26 * Bell((u - .28) / .36));
                ScreenEdge(f, a, b, metal, 113);
                ScreenEdge(f, a, d, metal, 111);
                ScreenEdge(f, a, mid, metal, 108);
                ScreenEdge(f, c, mid, metal, 119);
                if (R(0, 1) < .50) ScreenEdge(f, b, mid, metal, 102);
                else ScreenEdge(f, d, mid, metal, 104);
            }
        }
    }

    void ScreenEdge(Facade f, PointF a, PointF b, Color metal, int opacity)
    {
        PointF p = f.At(a.X, a.Y), q = f.At(b.X, b.Y);
        Line(A(C(20, 28, 43), 110), 1.34, p, q);
        Line(A(metal, opacity), .73, P(p.X - .22, p.Y - .26), P(q.X - .22, q.Y - .26));
    }

    Color Pavement(double x, double y)
    {
        double d = Clamp((y - 760) / 307);
        double n = (Noise(x / 18, y / 10) - .5) * 5 + (Noise(x / 2.3, y / 1.9) - .5) * 5;
        double reflectedSky = Bell((x - 798) / (85 + d * 280)) * (1 - .38 * d);
        double dark = 1 - Bell((x - 799) / (250 + d * 390));
        double shade = 16 * Bell((y - 880) / 19) * Bell((x - 805) / 580);
        double reflection = 7 * Bell((y - 930) / 28) * Bell((x - 799) / 430);
        return C(53 - 19 * d + 21 * reflectedSky - 12 * dark + n - shade + reflection,
            53 - 14 * d + 15 * reflectedSky - 11 * dark + n - shade + reflection * .55,
            61 - 12 * d + 16 * reflectedSky - 9 * dark + n - shade + reflection * .30);
    }

    void Street()
    {
        // Ground coordinates are drawn as converging lines in image space.
        using (var pavement = new Bitmap(W, H / 2, PixelFormat.Format32bppArgb)) {
            Raster(pavement, (x, y) => Pavement(x, 768 + y * (H - 768.0) / H));
            DrawScaled(g, pavement, new Rectangle(0, 768, W, H - 768));
        }
        Poly(C(50, 47, 48), P(0, 786), P(690, 770), P(726, 787), P(365, 1067), P(0, 1067));
        Poly(C(52, 49, 49), P(1600, 790), P(911, 771), P(874, 787), P(1284, 1067), P(1600, 1067));
        Poly(C(79, 73, 72), P(712, 788), P(730, 787), P(392, 1067), P(326, 1067));
        Poly(C(75, 70, 71), P(870, 788), P(883, 788), P(1319, 1067), P(1267, 1067));
        Line(C(114, 105, 99), 1.35, P(729, 787), P(392, 1067));
        Line(C(103, 97, 96), 1.2, P(871, 788), P(1267, 1067));
        for (int i = 0; i < 28; i++) {
            double d = Math.Pow(i / 27.0, 1.72), y = 790 + 277 * d;
            double left = Mix(727, 392, d), right = Mix(875, 1267, d);
            double lw = Mix(18, 83, d), rw = Mix(14, 74, d);
            Line(A(C(39, 39, 43), 130), .5 + .65 * d, P(left, y), P(left - lw, y + d * 4));
            Line(A(C(38, 38, 42), 140), .5 + .65 * d, P(right, y), P(right + rw, y - d * 4));
            double yNext = 790 + 277 * Math.Pow(Math.Min(1, (i + 1) / 27.0), 1.72);
            double next = (yNext - 790) / 277;
            if (i % 3 == 0) {
                Line(A(C(148, 121, 93), 112), .46 + .55 * d, P(left - lw * .66, y), P(Mix(727, 392, next) - Mix(18, 83, next) * .66, yNext));
                Line(A(C(148, 121, 93), 112), .46 + .55 * d, P(right + rw * .66, y), P(Mix(875, 1267, next) + Mix(14, 74, next) * .66, yNext));
            }
        }
        for (int i = 0; i < 2800; i++) {
            double x = R(0, W), y = R(788, H);
            double d = (y - 788) / 279;
            bool walkway = x < 729 - 337 * d || x > 871 + 396 * d;
            double size = .40 + 2 * d;
            if (walkway) Rect(A(C(163, 144, 126), (int)R(4, 25)), x, y, size * R(1, 4), .36 + .65 * d);
            else Oval(A(R(0, 1) < .45 ? C(126, 118, 112) : C(14, 18, 28), (int)R(8, 33)), x, y, size, .21 + d * .4);
        }
        double[] marks = { 515, 648, 795, 947, 1100, 1213 };
        for (int i = 0; i < marks.Length; i++) {
            double target = marks[i];
            double y = 816 + i % 2 * 3;
            while (y < H + 5) {
                double d = (y - 772) / 295;
                double tail = y + 2 + 24 * d * d;
                double x = 797 + (target - 797) * (y - 731) / 336;
                double finalX = 797 + (target - 797) * (tail - 731) / 336;
                double thick = .32 + 2.15 * d;
                Poly(C(130 + 35 * d, 123 + 33 * d, 115 + 32 * d), P(x - thick * .76, y), P(x + thick * .76, y),
                    P(finalX + thick, tail), P(finalX - thick, tail));
                y = tail + 2 + 27 * d * d;
            }
        }
        for (int i = 0; i < 16; i++) {
            double x = 651 + i * 18;
            double t = (x - 800) / 150;
            Poly(A(C(184, 171, 160), 91), P(x, 911), P(x + 7, 911), P(x + 7 + 4 * t, 918), P(x + 4 * t, 918));
        }
        for (int i = 0; i < 11; i++) {
            double x = 570 + i * 41;
            Poly(A(C(185, 174, 158), 104), P(x, 1045), P(x + 17, 1045), P(x + 17 + (x - 800) * .065, 1064), P(x + (x - 800) * .065, 1064));
        }
    }

    void Podiums()
    {
        Building(119, 745, 210, 831, -38, C(63, 63, 70), 8, 26, .28);
        Building(360, 757, 181, 828, 17, C(67, 62, 67), 7, 19, .30);
        Building(517, 766, 225, 823, -12, C(63, 62, 70), 7, 30, .27);
        Building(871, 758, 263, 824, 31, C(56, 59, 69), 7, 33, .28);
        Building(1219, 749, 280, 839, -37, C(64, 62, 70), 8, 26, .25);
        for (int i = 0; i < 65; i++) {
            double x = R(70, 1530);
            if (x > 724 && x < 870) continue;
            double y = R(794, 816);
            Color c = R(0, 1) < .28 ? C(188, 213, 220) : C(255, 190, 113);
            Glow(c, x, y, R(4, 14), R(2, 5), 45);
            if (R(0, 1) < .12) Rect(A(c, 143), x, y, R(5, 15), R(.8, 1.8));
            else Oval(A(c, 198), x, y, R(.65, 2.1), R(.45, 1));
        }
    }

    void Plaza()
    {
        Poly(C(54, 54, 49), P(0, 849), P(433, 834), P(591, 847), P(515, 872), P(275, 883), P(0, 896));
        Poly(C(55, 52, 48), P(1600, 846), P(1168, 832), P(1035, 851), P(1108, 880), P(1600, 896));
        Poly(C(42, 45, 40), P(0, 899), P(375, 877), P(498, 878), P(474, 898), P(165, 932), P(0, 952));
        Poly(C(42, 44, 41), P(1600, 906), P(1204, 875), P(1109, 880), P(1147, 906), P(1600, 959));
        Line(A(C(122, 114, 103), 109), 1, P(0, 895), P(279, 882), P(511, 871), P(586, 848));
        Line(A(C(126, 114, 100), 107), 1.1, P(1600, 896), P(1110, 881), P(1036, 851));
        for (int i = 0; i < 75; i++) {
            double x = i % 2 == 0 ? R(-15, 475) : R(1140, 1620);
            double y = 893 + Math.Abs(x - 800) * .043 + R(-13, 16);
            double a = R(3, 17), b = R(1.4, 4.8);
            Color leaf = Blend(C(34, 38, 34), C(69, 68, 49), R(0, 1));
            Oval(A(leaf, 190), x, y, a, b);
            for (int k = 0; k < 8; k++) Oval(A(Tone(leaf, R(-6, 16)), 138), x + R(-.83, .83) * a, y + R(-.65, .65) * b, R(.55, 2.6), R(.55, 1.1));
        }
        // Low lights follow the planted edges and pick out the paving.
        for (int i = 0; i < 24; i++) {
            double t = Math.Pow(i / 23.0, 1.3);
            double x = i % 2 == 0 ? Mix(472, -16, t) : Mix(1120, 1614, t);
            double y = 876 + 19 * t;
            Color light = C(246, 195, 129);
            Glow(light, x, y + 2, 13, 4, 37);
            Rect(A(light, 171), x, y, 1.4, .65);
        }
    }

    void Tree(double x, double y, double width, double height, bool close)
    {
        double lean = R(-.22, .22) * width;
        Color bark = close ? C(39, 35, 37) : C(48, 45, 48);
        Line(bark, Math.Max(.72, width * .025), P(x, y), P(x + lean * .5, y - height * .48), P(x + lean, y - height * .87));
        for (int i = 0; i < 12; i++) {
            double t = R(.38, .89);
            double xx = x + lean * t + R(-.43, .43) * width;
            Line(A(Tone(bark, R(-11, 8)), 220), Math.Max(.5, width * .011), P(x + lean * t, y - height * t), P(xx, y - height * t - R(.12, .28) * height));
        }
        int clusters = close ? 49 : 22;
        double foliageY = y - height * .69;
        for (int i = 0; i < clusters; i++) {
            double angle = R(0, Math.PI * 2), radius = Math.Sqrt(R(0, 1));
            double tx = x + lean * .62 + Math.Cos(angle) * radius * width * .47;
            double ty = foliageY + Math.Sin(angle) * radius * height * .32;
            double spreadX = width * R(.039, .15), spreadY = height * R(.035, .123);
            double exposure = (x > 800 ? -.2 : .15) + .60 * (foliageY - ty) / (height * .33) + R(-.30, .38);
            Color leaf = Blend(C(29, 32, 35), C(89, 83, 60), Clamp(.34 + exposure));
            if (!close) leaf = Blend(leaf, C(131, 110, 106), .17);
            Oval(A(leaf, 145), tx, ty, spreadX * .72, spreadY * .63);
            for (int j = 0; j < (close ? 72 : 32); j++) {
                double p = R(0, Math.PI * 2), q = Math.Sqrt(R(0, 1));
                double xx = tx + Math.Cos(p) * q * spreadX, yy = ty + Math.Sin(p) * q * spreadY;
                double s = R(.45, 2.1) * (close ? .44 + width / 170 : .63);
                Color spot = Tone(leaf, R(-18, 20) + 5 * Math.Cos(p));
                Oval(A(spot, (int)R(55, 202)), xx, yy, s * R(.77, 1.38), s * R(.45, 1.06));
            }
        }
    }

    void GardenStrip()
    {
        for (int i = 0; i < 35; i++) {
            double x = 23 + 45 * i + R(-13, 18);
            if (x > 720 && x < 874) continue;
            double y = R(816, 835);
            Tree(x, y, R(23, 59), R(24, 51), false);
        }
    }

    PointF Ring(double angle, double offset, double rise)
    {
        double x = 804 + (566 + offset) * Math.Cos(angle);
        double y = 808 + (65 + offset * .16) * Math.Sin(angle) + 4 * Math.Cos(angle) - rise;
        return P(x, y);
    }

    void RingBand(double start, double end, double a, double b, double riseA, double riseB, Color color, int steps)
    {
        var points = new PointF[(steps + 1) * 2];
        for (int i = 0; i <= steps; i++) {
            double t = Mix(start, end, (double)i / steps);
            points[i] = Ring(t, a, riseA);
            points[points.Length - 1 - i] = Ring(t, b, riseB);
        }
        Poly(color, points);
    }

    void RingLine(double start, double end, double offset, double rise, double width, Color color)
    {
        var points = new PointF[181];
        for (int i = 0; i < points.Length; i++) points[i] = Ring(Mix(start, end, i / 180.0), offset, rise);
        Line(color, width, points);
    }

    void Person(double x, double y, double s, Color coat)
    {
        Color dark = C(39, 37, 43);
        Line(dark, 1.05 * s, P(x, y - 4.4 * s), P(x - .9 * s, y - 1.7 * s), P(x - 1.35 * s, y));
        Line(Tone(dark, 5), 1.12 * s, P(x + .38 * s, y - 4.3 * s), P(x + .88 * s, y - 1.5 * s), P(x + 1.33 * s, y - .15 * s));
        Poly(coat, P(x - 1.0 * s, y - 8.7 * s), P(x + .68 * s, y - 8.6 * s), P(x + 1.19 * s, y - 4.2 * s), P(x - 1.12 * s, y - 4.05 * s));
        Line(Tone(coat, -12), .7 * s, P(x - .8 * s, y - 8.1 * s), P(x - 1.46 * s, y - 5.7 * s));
        Line(Tone(coat, -14), .7 * s, P(x + .75 * s, y - 8 * s), P(x + 1.60 * s, y - 5.9 * s));
        Oval(C(125, 99, 84), x, y - 9.55 * s, .79 * s, 1 * s);
        Oval(C(47, 40, 39), x - .10 * s, y - 10.08 * s, .83 * s, .60 * s);
    }

    void BridgeHalf(bool front)
    {
        double start = front ? 0 : Math.PI, end = start + Math.PI;
        double boundary = front ? 0 : -49;
        double inner = -49 - boundary;
        // The fascia follows the nearer edge for each half of the painted ellipse.
        if (front) {
            Pier(.59, 912, 16);
            Pier(.97, 936, 22);
            Pier(2.15, 928, 22);
            Pier(2.62, 907, 16);
        } else {
            Pier(3.35, 850, 14);
            Pier(3.93, 840, 10);
            Pier(5.46, 841, 10);
            Pier(6.02, 855, 14);
        }
        RingBand(start, end, 0, -49, 4, 4, front ? C(117, 79, 72) : C(105, 74, 70), 180);
        RingLine(start, end, -37, 4, .75, C(160, 112, 92));
        RingLine(start, end, -14, 4, .70, C(138, 93, 78));
        RingBand(start, end, boundary, boundary, 4, -14, front ? C(98, 51, 49) : C(93, 55, 54), 180);
        for (int i = 0; i < 180; i++) {
            double t = Mix(start, end, i / 180.0);
            double tt = Mix(start, end, (i + 1.03) / 180.0);
            double b = 8 * Math.Cos(t + 2.05) + R(-2, 2);
            RingBand(t, tt, boundary, boundary, 2, -10, Tone(front ? C(126, 62, 55) : C(106, 59, 56), b), 1);
            Line(A(C(63, 47, 50), 130), .64, Ring(t, boundary, 2), Ring(t, boundary, -10));
        }
        RingLine(start, end, boundary, -12, 1.5, C(67, 42, 45));
        RingLine(start, end, boundary, -2.3, 4.15, A(C(241, 97, 53), front ? 75 : 30));
        RingLine(start, end, boundary, -1.9, 1.33, front ? C(245, 165, 119) : C(203, 126, 94));
        RingLine(start, end, boundary, 3.4, .76, C(187, 117, 92));

        RingLine(start, end, inner, 14, .82, C(160, 133, 124));
        for (int i = 0; i <= 86; i++) {
            double t = Mix(start, end, i / 86.0);
            Line(A(C(169, 131, 118), 145), .66, Ring(t, inner, 4), Ring(t, inner, 14));
        }
        for (int i = 0; i < (front ? 24 : 13); i++) {
            double t = Mix(start, end, R(.08, .93));
            PointF p = Ring(t, R(-39, -12), 4);
            Color coat = R(0, 1) < .25 ? C(181, 156, 139) : Blend(C(42, 43, 53), C(128, 75, 70), R(0, 1));
            Person(p.X, p.Y, R(.62, 1.05) * (front ? 1 : .74), coat);
        }
        RingBand(start, end, boundary, boundary, 4, 14, A(C(99, 88, 94), 37), 180);
        RingLine(start, end, boundary, 14, .93, front ? C(176, 147, 137) : C(147, 119, 112));
        for (int i = 0; i <= 114; i++) {
            double t = Mix(start, end, i / 114.0);
            Line(A(C(188, 151, 137), 163), .65, Ring(t, boundary, 4), Ring(t, boundary, 14));
        }
    }

    void Pier(double angle, double foot, double width)
    {
        PointF p = Ring(angle, Math.Sin(angle) > 0 ? -12 : -39, -9);
        double drift = (p.X - 804) * .048;
        double baseX = p.X + drift;
        Oval(A(C(21, 21, 27), 140), baseX + 3, foot, width * .83, width * .18);
        Poly(C(68, 59, 62), P(p.X - width * .53, p.Y), P(p.X + width * .53, p.Y),
            P(baseX + width * .26, foot), P(baseX - width * .22, foot));
        Poly(C(102, 83, 77), P(p.X - width * .53, p.Y), P(p.X - width * .14, p.Y),
            P(baseX - width * .04, foot), P(baseX - width * .22, foot));
        Line(A(C(139, 110, 99), 122), .86, P(p.X - width * .44, p.Y + 3), P(baseX - width * .19, foot));
    }

    void Reflection(double x, double y, Color c, double s)
    {
        Glow(c, x, y + 13 * s, 12 * s, 29 * s, 50);
        for (int i = 0; i < 35; i++) {
            double d = Math.Pow(R(0, 1), 1.8);
            double yy = y + 3 * s + d * s * 38;
            double xx = x + R(-1, 1) * s * (2 + 6 * d);
            Line(A(c, (int)((1 - .83 * d) * R(12, 74))), R(.27, .64) * s, P(xx, yy), P(xx + R(1, 9) * s, yy));
        }
    }

    void TrafficStreak(double x, double y, double length, double width, bool white)
    {
        Color c = white ? C(248, 205, 149) : C(243, 73, 47);
        double slope = (x - 797) / (y - 731);
        for (int i = -1; i <= 1; i += 2) {
            double xx = x + i * width;
            for (int j = 0; j < 16; j++) {
                double t = j / 16.0, q = (j + 1.0) / 16;
                double y0 = y - length * t, y1 = y - length * q;
                double x0 = xx - slope * length * t, x1 = xx - slope * length * q;
                int alpha = (int)(Mix(75, 0, t) * R(.54, 1));
                Line(A(c, alpha / 3), 3.2, P(x0, y0), P(x1, y1));
                Line(A(c, alpha), .71, P(x0, y0), P(x1, y1));
            }
        }
    }

    void Car(double x, double y, double s, bool toward, Color paint)
    {
        Color lamp = toward ? C(255, 231, 192) : C(249, 77, 54);
        Oval(A(C(12, 15, 21), 165), x, y + 1 * s, 19 * s, 3.75 * s);
        Rect(C(22, 23, 28), x - 16 * s, y - 5 * s, 5 * s, 7 * s);
        Rect(C(23, 24, 28), x + 11 * s, y - 5 * s, 5 * s, 7 * s);
        PointF[] outline = { P(x - 17 * s, y - 2 * s), P(x - 18 * s, y - 9 * s), P(x - 12 * s, y - 12 * s),
            P(x - 8 * s, y - 18.4 * s), P(x + 7.5 * s, y - 18.7 * s), P(x + 13 * s, y - 12 * s),
            P(x + 17.6 * s, y - 8 * s), P(x + 16.7 * s, y - 2 * s) };
        Poly(paint, outline);
        Poly(C(56, 63, 76), P(x - 11 * s, y - 12 * s), P(x - 7.5 * s, y - 17.1 * s), P(x + 7 * s, y - 17.2 * s), P(x + 11.4 * s, y - 12 * s));
        Line(A(C(189, 185, 190), 135), .65 * s, P(x - 8.6 * s, y - 18.3 * s), P(x + 7.5 * s, y - 18.5 * s));
        Line(A(C(190, 174, 168), 135), .50 * s, P(x - 16 * s, y - 9 * s), P(x - 10 * s, y - 10.8 * s), P(x + 13 * s, y - 10.7 * s), P(x + 17 * s, y - 8.7 * s));
        Rect(Tone(paint, -18), x - 15 * s, y - 6 * s, 30 * s, 2.5 * s);
        Rect(toward ? C(78, 119, 155) : C(82, 125, 147), x - 3.4 * s, y - 6 * s, 6.8 * s, 2.1 * s);
        for (int i = -1; i <= 1; i += 2) {
            double lx = x + i * 13.1 * s, ly = y - 7 * s;
            Reflection(lx, y + 2 * s, lamp, s);
            Glow(lamp, lx, ly, 16 * s, 9 * s, toward ? 112 : 85);
            Line(lamp, 1.6 * s, P(lx - 2.7 * s, ly + .4 * s), P(lx + 2.7 * s, ly));
            Oval(toward ? C(255, 254, 233) : C(255, 161, 132), lx, ly, 1.2 * s, .72 * s);
        }
    }

    void Lamp(double x, double baseY, double h, int side)
    {
        double y = baseY - h, arm = h * .16 * side;
        double w = Math.Max(.65, h / 66);
        Line(C(47, 44, 47), w, P(x, baseY), P(x + arm * .05, y + 4), P(x + arm * .18, y + 1), P(x + arm, y));
        Line(A(C(160, 135, 115), 115), .55, P(x + w * .32, baseY - h * .1), P(x + arm * .05 + w * .32, y + 5));
        Color warm = C(255, 212, 149);
        Glow(warm, x + arm, y, h * .245, h * .16, 67);
        Line(A(warm, 78), .55, P(x + arm - h * .13, y), P(x + arm + h * .13, y));
        Oval(C(255, 237, 195), x + arm, y, Math.Max(1.0, h * .032), Math.Max(.65, h * .009));
    }

    void StreetDetails()
    {
        Glow(C(190, 161, 139), 799, 789, 118, 39, 47);
        Line(C(73, 67, 69), .78, P(763, 831), P(763, 795), P(785, 794));
        Line(C(67, 62, 65), .82, P(848, 825), P(848, 796), P(831, 795));
        Rect(C(48, 46, 50), 779, 792, 4.8, 2.1);
        Rect(C(48, 46, 50), 830, 794, 4.8, 2.1);
        Oval(C(155, 222, 159), 780, 793, .66, .53);
        Oval(C(247, 111, 87), 831, 795, .63, .53);
        for (int i = 0; i < 33; i++) {
            double y = R(790, 890);
            double d = (y - 772) / 295;
            double x = 797 + R(-380, 399) * d;
            if (y > 853 && y < 887) continue;
            Color c = R(0, 1) < .54 ? C(248, 217, 181) : C(230, 86, 56);
            Glow(c, x, y, 3.8, 2.8, 60);
            Oval(A(c, 228), x, y, R(.53, 1.28), R(.43, .88));
        }
        TrafficStreak(697, 943, 36, 8.0, true);
        TrafficStreak(987, 982, 44, 11.5, false);
        TrafficStreak(867, 1024, 38, 13.8, false);
        Car(758, 901, .44, true, C(94, 103, 106));
        Car(836, 913, .48, false, C(76, 75, 87));
        Car(693, 944, .66, true, C(83, 92, 101));
        Car(849, 963, .74, false, C(123, 113, 111));
        Car(987, 985, .92, false, C(74, 77, 95));
        Car(624, 1006, 1.04, true, C(120, 119, 115));
        Car(867, 1031, 1.18, false, C(84, 78, 87));
        Lamp(691, 893, 54, 1);
        Lamp(931, 906, 61, -1);
        Lamp(594, 945, 73, 1);
        Lamp(1004, 950, 75, -1);
        Lamp(420, 1028, 106, 1);
        Lamp(1193, 1024, 112, -1);
        Lamp(726, 848, 37, 1);
        Lamp(880, 846, 37, -1);
        Line(C(54, 54, 60), 1.1, P(591, 924), P(591, 866), P(611, 864));
        Rect(C(61, 89, 111), 596, 862, 18, 7);
        Rect(A(C(153, 187, 204), 135), 597, 863, 16, .44);
        for (int i = 0; i < 7; i++) Rect(A(C(201, 213, 219), 170), 598 + i * 1.84, 865, 1.14, .70);
        for (int i = 0; i < 19; i++) {
            double y = R(899, 1050), d = (y - 788) / 279;
            double x = i % 2 == 0 ? 710 - 343 * d - R(16, 66) : 880 + 410 * d + R(16, 66);
            Oval(A(C(15, 17, 24), 130), x, y, 3.9 * d, 1.0 * d);
            Person(x, y, .50 + 1.58 * d, i % 5 == 0 ? C(154, 133, 121) : Blend(C(53, 52, 59), C(121, 94, 89), R(0, 1)));
        }
    }

    void Foreground()
    {
        for (int i = 0; i < 14; i++) {
            double d = i / 13.0;
            double y = Mix(860, 1049, d);
            Tree(Mix(390, 292, d) + R(-12, 13), y, Mix(29, 61, d), Mix(28, 73, d), true);
            Tree(Mix(1223, 1413, d) + R(-14, 13), y + 9, Mix(30, 72, d), Mix(28, 79, d), true);
        }
        Tree(-10, 1067, 213, 280, true);
        Tree(97, 1078, 168, 208, true);
        Tree(187, 1031, 112, 139, true);
        Tree(278, 979, 76, 92, true);
        Tree(1363, 987, 85, 96, true);
        Tree(1458, 1038, 131, 162, true);
        Tree(1603, 1084, 252, 282, true);
        for (int i = 0; i < 11; i++) {
            double y = 1041 + R(-20, 34);
            double x = i % 2 == 0 ? R(-10, 287) : R(1350, 1620);
            Tree(x, y + 28, R(32, 83), R(24, 47), true);
        }
        Lamp(201, 1038, 151, 1);
        Lamp(1444, 1041, 143, -1);
    }

    void Finish(Bitmap bitmap)
    {
        int width = bitmap.Width, height = bitmap.Height;
        var bounds = new Rectangle(0, 0, width, height);
        var data = bitmap.LockBits(bounds, ImageLockMode.ReadWrite, PixelFormat.Format32bppArgb);
        try {
            int stride = data.Stride / 4;
            var pixels = new int[stride * height];
            Marshal.Copy(data.Scan0, pixels, 0, pixels.Length);
            System.Threading.Tasks.Parallel.For(0, height, y => {
                double v = (y / (double)height - .47) / .73;
                for (int x = 0; x < width; x++) {
                    double u = (x / (double)width - .50) / .76;
                    double falloff = 1 - .135 * Math.Pow(Math.Min(1, u * u + v * v), 1.15);
                    int index = y * stride + x;
                    int px = pixels[index];
                    double luma = (((px >> 16) & 255) + 2 * ((px >> 8) & 255) + (px & 255)) / 4.0;
                    double grain = (Hash(x * 3 + 17, y * 5 + 83) + Hash(x * 7 + 91, y * 11 - 42) - 1) * (2.4 + 1.5 * Bell((luma - 72) / 65));
                    pixels[index] = C(((px >> 16) & 255) * falloff + grain,
                        ((px >> 8) & 255) * falloff + grain * .94, (px & 255) * falloff + grain * 1.16).ToArgb();
                }
            });
            Marshal.Copy(pixels, 0, data.Scan0, pixels.Length);
        } finally { bitmap.UnlockBits(data); }
    }

    void Paint(string output, string preview, int width)
    {
        int height = (int)Math.Round(width * H / (double)W);
        int sampling = width >= 2600 ? 1 : 2;
        using (var plate = new Bitmap(width * sampling, height * sampling, PixelFormat.Format32bppArgb)) {
            Raster(plate, Atmosphere);
            using (g = Graphics.FromImage(plate)) {
                g.ScaleTransform(plate.Width / (float)W, plate.Height / (float)H);
                g.SmoothingMode = SmoothingMode.AntiAlias;
                g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                Skyline();
                Tower(new Facade(661, 161, 808, 94, 14, 8), 48, true);
                Tower(new Facade(948, 124, 812, 103, -11, -8), 58, false);
                Street();
                Podiums();
                Plaza();
                GardenStrip();
                BridgeHalf(false);
                StreetDetails();
                BridgeHalf(true);
                Foreground();
            }
            using (var image = new Bitmap(width, height, PixelFormat.Format32bppArgb)) {
                using (var final = Graphics.FromImage(image)) {
                    DrawScaled(final, plate, new Rectangle(0, 0, width, height));
                }
                Finish(image);
                image.Save(output, ImageFormat.Png);
                if (String.IsNullOrEmpty(preview)) return;
                int previewWidth = Math.Min(width, 1440);
                int previewHeight = (int)Math.Round(height * previewWidth / (double)width);
                using (var small = new Bitmap(previewWidth, previewHeight, PixelFormat.Format24bppRgb)) {
                    using (var canvas = Graphics.FromImage(small)) {
                        DrawScaled(canvas, image, new Rectangle(0, 0, previewWidth, previewHeight));
                    }
                    small.Save(preview, ImageFormat.Png);
                }
            }
        }
    }

    public static void Render(string output, string preview, int width, int seed)
    {
        new ChengduDusk(seed).Paint(output, preview, width);
    }
}
