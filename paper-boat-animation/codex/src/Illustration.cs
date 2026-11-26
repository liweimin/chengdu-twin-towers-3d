using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;

// Original vector paintings. All coordinates are in a 1280 × 720 picture plane.
partial class Film
{
    const int W = 1280, H = 720, Fps = 24;
    static Graphics g;
    static Random rng;
    static Bitmap[] plates = new Bitmap[3];
    static Bitmap grain;
    const string Ink = "#514b4b";

    static Color C(string hex, int alpha = 255)
    {
        return Color.FromArgb(alpha, ColorTranslator.FromHtml(hex));
    }

    static float R(float min, float max) { return min + (max - min) * (float)rng.NextDouble(); }
    static float S(double a) { return (float)Math.Sin(a); }
    static float Clamp(float x, float lo, float hi) { return Math.Max(lo, Math.Min(hi, x)); }
    static float Ease(float x)
    {
        x = Clamp(x, 0, 1);
        return x * x * (3 - 2 * x);
    }

    static GraphicsPath Path(string commands)
    {
        string[] parts = commands.Split(' ');
        int i = 0;
        var p = new GraphicsPath();
        PointF at = PointF.Empty;
        Func<float> num = () => float.Parse(parts[i++], CultureInfo.InvariantCulture);
        Func<PointF> pt = () => new PointF(num(), num());
        while (i < parts.Length)
        {
            switch (parts[i++])
            {
                case "M": p.StartFigure(); at = pt(); break;
                case "L": var end = pt(); p.AddLine(at, end); at = end; break;
                case "C":
                    var a = pt(); var b = pt(); var c = pt();
                    p.AddBezier(at, a, b, c); at = c; break;
                case "Z": p.CloseFigure(); break;
                default: throw new ArgumentException(commands);
            }
        }
        return p;
    }

    static Pen PenFor(string color, float width, int alpha)
    {
        return new Pen(C(color, alpha), width) {
            StartCap = LineCap.Round, EndCap = LineCap.Round, LineJoin = LineJoin.Round
        };
    }

    static void Fill(string path, string fill, string edge = null, float width = 1.7f)
    {
        using (var p = Path(path))
        using (var b = new SolidBrush(C(fill)))
        {
            g.FillPath(b, p);
            if (edge != null) using (var pen = PenFor(edge, width, 235)) g.DrawPath(pen, p);
        }
    }

    static void Wash(string path, string top, string bottom, string edge = null)
    {
        using (var p = Path(path))
        {
            var bounds = p.GetBounds();
            using (var b = new LinearGradientBrush(bounds, C(top), C(bottom), 82f))
                g.FillPath(b, p);
            if (edge != null) using (var pen = PenFor(edge, 1.9f, 232)) g.DrawPath(pen, p);
        }
    }

    static void Stroke(string path, string color, float width = 1.5f, int alpha = 255)
    {
        using (var p = Path(path))
        using (var pen = PenFor(color, width, alpha)) g.DrawPath(pen, p);
    }

    static void Line(float x, float y, float x2, float y2, string color, float width, int alpha)
    {
        using (var pen = PenFor(color, width, alpha)) g.DrawLine(pen, x, y, x2, y2);
    }

    static void Oval(float x, float y, float w, float h, string color, int alpha = 255)
    {
        using (var b = new SolidBrush(C(color, alpha))) g.FillEllipse(b, x, y, w, h);
    }

    static void Arc(float x, float y, float w, float h, float angle, float length,
                    string color, float width, int alpha)
    {
        if (w <= 0 || h <= 0) return;
        using (var pen = PenFor(color, width, alpha)) g.DrawArc(pen, x, y, w, h, angle, length);
    }

    static Graphics Setup(Bitmap image)
    {
        var canvas = Graphics.FromImage(image);
        canvas.SmoothingMode = SmoothingMode.AntiAlias;
        canvas.PixelOffsetMode = PixelOffsetMode.HighQuality;
        canvas.InterpolationMode = InterpolationMode.HighQualityBilinear;
        return canvas;
    }

    static void Mottle(string outline, string light, string dark, int count, float size)
    {
        var state = g.Save();
        using (var p = Path(outline))
        {
            g.SetClip(p, CombineMode.Intersect);
            var bounds = p.GetBounds();
            for (int i = 0; i < count; i++)
            {
                float x = R(bounds.Left - size, bounds.Right);
                float y = R(bounds.Top - size, bounds.Bottom);
                float d = R(size * .12f, size);
                Oval(x, y, d, d * R(.24f, .78f), i % 2 == 0 ? light : dark, (int)R(7, 33));
            }
        }
        g.Restore(state);
    }

    static void Glow(float x, float y, float w, float h, string color, int alpha)
    {
        using (var p = new GraphicsPath())
        {
            p.AddEllipse(x - w / 2, y - h / 2, w, h);
            using (var b = new PathGradientBrush(p))
            {
                b.CenterColor = C(color, alpha);
                b.SurroundColors = new[] { C(color, 0) };
                g.FillPath(b, p);
            }
        }
    }

    static void BrushLeaf(float x, float y, float scale, float angle, string color, bool vein)
    {
        var state = g.Save();
        g.TranslateTransform(x, y);
        g.RotateTransform(angle);
        g.ScaleTransform(scale, scale);
        Fill("M -18 1 C -10 -10 5 -13 19 -3 C 15 8 -3 12 -18 1 Z", color);
        if (vein)
        {
            Stroke("M -20 3 C -8 2 6 -1 16 -3", "#fff0ba", 1.15f, 167);
            Stroke("M -1 0 L 4 -6 M 4 -1 L 11 2", "#fff0ba", .7f, 113);
        }
        g.Restore(state);
    }

    static void Canopy(float x, float y, float spread, string[] palette, int count)
    {
        for (int i = 0; i < count; i++)
        {
            double angle = R(0, 6.284f);
            float radius = (float)Math.Sqrt(R(0, 1)) * spread;
            float width = R(spread * .10f, spread * .43f);
            float xx = x + (float)Math.Cos(angle) * radius;
            float yy = y + S(angle) * radius * .57f;
            Oval(xx, yy, width, width * R(.35f, .81f), palette[i % palette.Length], (int)R(48, 152));
            if (i % 4 == 0)
                BrushLeaf(xx, yy, R(.19f, .55f), R(-48, 38), palette[(i + 1) % palette.Length], false);
        }
    }

    static void Woods(int shot)
    {
        using (var brush = new LinearGradientBrush(new Rectangle(0, 0, W, H),
                   C(shot == 2 ? "#f9d9a4" : "#f9dfb6"), C("#9ea981"), 90f))
            g.FillRectangle(brush, 0, 0, W, H);
        Glow(1010, 100, 630, 440, "#fff2c5", 226);
        var haze = new[] { "#b6ab87", "#c6bd8c", "#dad099", "#e7d39c", "#f6dfaa" };
        for (int i = 0; i < 32; i++)
        {
            float x = R(-50, 1270), y = R(55, 232);
            Canopy(x, y, R(65, 175), haze, 26);
        }
        for (int i = 0; i < 36; i++)
        {
            float x = R(-25, 1280), y = R(198, 335), dx = R(-54, 36);
            string c = i % 2 == 0 ? "#807d71" : "#a0987a";
            using (var p = PenFor(c, R(2, 15), (int)R(42, 123)))
                g.DrawBezier(p, x, y, x + dx * .23f, y - 100, x + dx, 40, x + dx * 1.1f, -30);
            Line(x + dx * .5f, y - 99, x + dx - R(30, 90), y - 177, c, R(1, 4), 63);
        }
        if (shot != 1)
        {
            Wash("M 0 0 L 113 0 C 84 63 82 158 91 221 C 97 262 105 287 131 329 L 1 344 Z",
                 "#716f63", "#a69367");
            Wash("M 43 142 C 133 98 187 35 220 0 L 252 0 C 187 84 98 155 65 170 Z",
                 "#7e7963", "#a8916b");
            Stroke("M 36 5 C 7 92 32 172 24 251 M 61 126 C 49 189 59 239 73 265 M 25 64 C 34 83 37 101 34 121",
                 "#d0ad7e", 3, 115);
        }
        var leaves = new[] { "#898e63", "#a0a067", "#b4ad69", "#d5be78", "#e1c88a" };
        Canopy(55, 42, 234, leaves, 220);
        Canopy(332, -35, 250, leaves, 165);
        Canopy(672, -52, 195, leaves, 109);
        Canopy(1237, -17, 180, new[] { "#a9a068", "#c0ae73", "#d7ba78", "#e5c88a" }, 135);
        Glow(1110, 72, 414, 320, "#fff3ca", 149);
        Glow(1130, 100, 208, 200, "#fff0c3", 171);
        Oval(1105, 68, 55, 54, "#fff2c6", shot == 2 ? 239 : 177);
    }

    static void Rock(float x, float y, float scale, int style)
    {
        var state = g.Save();
        g.TranslateTransform(x, y);
        g.ScaleTransform(scale, scale);
        Oval(-55, -5, 129, 24, "#336b6b", 57);
        const string outline = "M -58 5 C -53 -11 -46 -22 -32 -29 C -19 -32 -6 -47 16 -43 C 34 -42 57 -24 62 -7 C 69 4 49 13 31 14 C 5 17 -39 16 -58 5 Z";
        if (style % 2 == 0) Wash(outline, "#aaa38f", "#786f77", "#676d68");
        else Wash(outline, "#b7b199", "#858282", "#737469");
        Mottle(outline, "#f3dcb4", "#665c6d", 120, 19);
        Fill("M -54 1 C -42 -8 -19 -4 -9 -12 C 0 -15 17 -9 26 -16 C 35 -25 49 -18 56 -17 C 67 1 62 6 40 11 C 7 18 -38 17 -54 1 Z",
             style % 2 == 0 ? "#817b7a" : "#8e8c80");
        Stroke("M -42 -14 C -34 -24 -24 -23 -17 -29 M -13 -12 C 5 -15 2 -24 16 -26 M 21 4 C 34 4 38 1 45 -1",
               "#e4ceb0", 1.3f, 108);
        Stroke("M 12 -33 L 9 -26 L -1 -21 M -37 2 L -23 -2", "#5e6466", 1.1f, 113);
        for (int i = 0; i < 35; i++)
        {
            float a = R(-43, 38), b = -14 + S(a * .065) * 6 + R(-5, 5);
            if (i % 4 != 0) Oval(a, b, R(1, 7), R(1, 3.6f), i % 2 == 0 ? "#c8bb7f" : "#a8a474", (int)R(50, 148));
        }
        g.Restore(state);
    }

    static void Sprigs(float x, float y, float scale, int kind, float sway)
    {
        var state = g.Save();
        g.TranslateTransform(x, y);
        g.RotateTransform(sway);
        g.ScaleTransform(scale, scale);
        Stroke("M 0 2 C -5 -20 -12 -45 -29 -54 M 0 1 C 2 -17 5 -42 17 -65 M 0 1 C 8 -12 24 -26 37 -29 M 0 0 C -8 -13 -19 -19 -29 -19",
               kind % 2 == 0 ? "#637857" : "#858953", 1.4f, 224);
        Fill("M -4 -17 C -14 -37 -30 -40 -39 -38 C -30 -24 -17 -20 -4 -17 Z", "#8d985c");
        Fill("M 5 -27 C 7 -41 21 -48 35 -46 C 34 -36 21 -31 5 -27 Z", "#a6a969");
        Fill("M 2 -11 C 13 -27 25 -25 36 -22 C 30 -13 19 -9 2 -11 Z", "#758458");
        Fill("M -10 -29 C -12 -44 -24 -55 -29 -54 C -31 -44 -23 -36 -10 -29 Z", "#b9ac69");
        if (kind % 3 == 0)
        {
            for (int i = 0; i < 5; i++)
            {
                float a = i * 6.283f / 5;
                Oval(17 + S(a) * 5 - 3, -65 + S(a + 1.571) * 5 - 3, 6.5f, 6.5f, "#f2dfae");
            }
            Oval(14, -68, 6, 6, "#ca944c");
        }
        g.Restore(state);
    }

    static void Meadow(string region, bool front)
    {
        Wash(region, front ? "#b1ad72" : "#a3a26d", front ? "#747c58" : "#726f55");
        Mottle(region, "#f8d899", "#485d53", 2100, front ? 24 : 15);
        using (var p = Path(region))
        {
            var state = g.Save();
            g.SetClip(p);
            var bounds = p.GetBounds();
            for (int i = 0; i < 690; i++)
            {
                float x = R(bounds.Left, bounds.Right), y = R(bounds.Top, bounds.Bottom);
                float d = R(2, front ? 13 : 8);
                if (i % 3 == 0)
                    Oval(x, y, d, d * .32f, i % 2 == 0 ? "#e3ca8e" : "#535f4f", (int)R(55, 164));
                else
                    Line(x, y, x + R(-4, 6), y - d, i % 2 == 0 ? "#ddd395" : "#637754", R(.6f, 1.65f), (int)R(70, 186));
            }
            g.Restore(state);
        }
    }

    static Bitmap Background(int shot)
    {
        var plate = new Bitmap(W, H, PixelFormat.Format32bppPArgb);
        rng = new Random(621 + shot * 73);
        using (g = Setup(plate))
        {
            Woods(shot);
            string river = shot == 1
                ? "M -15 216 C 236 222 370 180 638 205 C 843 214 1111 142 1290 176 L 1290 730 L -15 730 Z"
                : "M -15 448 C 259 303 558 242 730 230 C 965 212 1103 163 1290 198 L 1290 730 L -15 730 Z";
            Wash(river, shot == 2 ? "#c3c899" : "#a8bc94", shot == 1 ? "#478486" : "#5a9491");
            Mottle(river, "#f3d9a1", "#286d79", 2800, 61);
            using (var p = Path(river))
            {
                var state = g.Save();
                g.SetClip(p);
                Glow(1064, 425, 810, 505, "#f2d79a", shot == 2 ? 225 : 133);
                Glow(1178, 296, 512, 353, "#fff0b1", shot == 2 ? 183 : 121);
                for (int i = 0; i < 1150; i++)
                {
                    float x = R(1, 1279), y = R(175, 720);
                    float w = R(2, 48) * (.36f + y / 780);
                    string c = i % 3 == 0 ? "#fff1be" : i % 3 == 1 ? "#d8ddac" : "#578887";
                    Oval(x, y, w, R(.6f, 4.2f), c, (int)R(13, x > 760 ? 86 : 57));
                }
                g.Restore(state);
            }
            string bank = shot == 1
                ? "M -5 153 C 191 152 329 192 466 181 C 690 154 787 217 956 184 C 1109 145 1201 137 1290 145 L 1290 168 C 1144 167 1067 190 976 211 C 807 244 699 186 500 213 C 339 236 182 210 -5 236 Z"
                : "M -5 275 C 224 229 366 247 526 210 C 729 160 834 201 1000 170 C 1123 147 1226 143 1290 166 L 1290 201 C 1135 174 1082 210 948 227 C 803 245 731 214 589 248 C 397 291 216 293 -5 472 Z";
            Meadow(bank, false);
            for (int i = 0; i < 83; i++)
            {
                float x = 14 + i * 15.7f + R(-13, 13);
                float y = shot == 1
                    ? 201 + S(i * .159) * 20 - x * .018f
                    : 182 + 205 * (float)Math.Pow(1 - Clamp(x / W, 0, 1), 3.2) + S(x * .011) * 10;
                float size = R(.17f, .43f);
                if (i % 8 == 0) Rock(x, y + 11, size, i);
                else Sprigs(x, y, size, i, R(-21, 18));
            }
            if (shot == 0)
            {
                const string near = "M -15 296 C 65 309 224 338 322 380 C 383 402 414 433 434 459 C 449 484 441 510 471 535 C 514 566 510 605 581 638 C 631 658 637 700 661 729 L -15 729 Z";
                Fill("M -15 402 C 176 340 330 411 424 463 C 456 491 447 516 475 545 C 519 572 523 617 586 645 C 640 673 661 700 686 729 L -15 729 Z", "#777d63");
                Meadow(near, true);
                Stroke("M 325 394 C 388 421 404 440 419 466 M 438 510 C 446 525 465 539 477 552 M 482 585 C 504 615 526 622 560 643",
                       "#e5c18b", 4, 119);
                Rock(426, 561, 1.04f, 0);
                Rock(514, 651, 1.34f, 1);
                Rock(80, 640, 1.2f, 1);
                Rock(1100, 510, .75f, 0);
            }
            if (shot == 1)
            {
                Meadow("M -10 573 C 81 574 129 638 224 659 C 283 674 348 688 435 729 L -10 729 Z", true);
                Meadow("M 1019 729 C 1044 681 1145 660 1164 608 C 1201 549 1243 559 1290 510 L 1290 729 Z", true);
            }
            if (shot == 2)
            {
                Meadow("M -10 557 C 88 574 121 631 182 655 C 240 678 269 700 297 729 L -10 729 Z", true);
                Meadow("M 1131 729 C 1162 681 1229 692 1290 638 L 1290 729 Z", true);
                Rock(101, 620, .86f, 1);
                Rock(1133, 681, .79f, 0);
            }
        }
        return plate;
    }
}
