using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;

partial class Film
{
    const int Frames = Fps * 12;

    static Bitmap PaperTexture()
    {
        var bitmap = new Bitmap(W, H, PixelFormat.Format32bppArgb);
        var rect = new Rectangle(0, 0, W, H);
        var bits = bitmap.LockBits(rect, ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
        var bytes = new byte[W * H * 4];
        var random = new Random(1407);
        for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
        {
            int i = (y * W + x) * 4;
            double value = random.NextDouble() - .5;
            value += .12 * S(x * .75 + y * .31) + .07 * S(x * .15 - y * .8);
            bool light = value >= 0;
            bytes[i] = (byte)(light ? 198 : 58);
            bytes[i + 1] = (byte)(light ? 243 : 56);
            bytes[i + 2] = (byte)(light ? 255 : 64);
            bytes[i + 3] = (byte)(Math.Abs(value) * 53);
        }
        Marshal.Copy(bytes, 0, bits.Scan0, bytes.Length);
        bitmap.UnlockBits(bits);
        return bitmap;
    }

    static bool InWater(float x, float y, int shot)
    {
        if (shot == 0) return x > Math.Max(280 + y * .44f, 445) && y > (x < 610 ? 344 : 245);
        if (shot == 1) return y > 246 && y < 571 + x * .18f && y < 746 - Math.Max(0, x - 1000) * .79f;
        return y > 227 + 158 * (float)Math.Pow(1 - Clamp(x / W, 0, 1), 3) &&
               y < 567 + x * .54f && y < 720 - Math.Max(0, x - 1130) * .53f;
    }

    static void Current(float t, int shot)
    {
        rng = new Random(131 + shot * 28);
        for (int i = 0; i < 253; i++)
        {
            float y = R(200, 727);
            float x = (R(0, 1460) + t * (11 + y * .052f) * R(.72f, 1.45f)) % 1460 - 90;
            float w = R(5, i % 5 == 0 ? 111 : 48) * (.36f + y / 850);
            float h = R(.7f, i % 7 == 0 ? 3.4f : 1.6f);
            float shimmer = .57f + .43f * S(i * 3.42 + t * R(1.1f, 3.7f));
            if (!InWater(x, y, shot) || !InWater(x + w, y, shot)) continue;
            int strength = (int)((x > 770 ? 129 : 86) * shimmer);
            string c = i % 5 == 0 ? "#508a88" : x > 770 ? "#fff3bd" : "#dbe5be";
            using (var pen = PenFor(c, h, strength))
                g.DrawBezier(pen, x, y, x + w * .34f, y - 2.7f, x + w * .63f, y + 2.3f, x + w, y);
            if (i % 9 == 0) Oval(x + w * .37f, y - 1.5f, w * .28f, h + .7f, "#fff0bc", strength);
        }
        for (int i = 0; i < 15; i++)
        {
            float x = (R(0, 1400) + t * R(22, 63)) % 1400 - 55;
            float y = R(267, 692) + S(t * 1.1 + i) * 7;
            float scale = R(.17f, .58f);
            var colors = new[] { "#b57c61", "#bd9557", "#d0ad62", "#787f55" };
            if (!InWater(x, y, shot)) continue;
            Oval(x - 18 * scale, y + 3, 41 * scale, 6 * scale, "#396f71", 70);
            BrushLeaf(x, y, scale, i * 27 + t * 9 + 16 * S(t * 2 + i), colors[i % 4], true);
        }
    }

    static void Wake(float x, float y, float scale, float t, float amount)
    {
        for (int i = 0; i < 5; i++)
        {
            float phase = (t * .68f + i / 5f) % 1;
            float w = (54 + phase * 117) * scale;
            float h = (13 + phase * 25) * scale;
            int opacity = (int)(162 * (1 - phase) * amount);
            Arc(x - phase * 102 * scale - w / 2, y + phase * 10 - h / 2, w, h, 17, 148,
                "#f8efc9", 1.5f + (1 - phase) * .7f, opacity);
            Arc(x - phase * 105 * scale - w / 2, y + phase * 10 - h / 2, w, h, 190, 126,
                "#c6dcb6", 1.6f, opacity / 2);
        }
    }

    static void EdgeRock(float x, float y, float scale, int variant, float t)
    {
        Wake(x + 12 * scale, y + 8 * scale, scale, t + variant * .3f, .83f);
        rng = new Random(93 + variant * 113);
        Rock(x, y, scale, variant);
    }

    static void SunOnWater(float t)
    {
        rng = new Random(7604);
        for (int i = 0; i < 47; i++)
        {
            float y = R(258, 576);
            float spread = 31 + (y - 258) * .54f;
            float x = 1106 - (y - 258) * .37f + R(-spread, spread) + 16 * S(i * 2.81 + t * .9);
            float width = R(2, 28) * (.27f + (y - 250) / 240);
            float pulse = .23f + .77f * Math.Max(0, S(t * R(1.3f, 4.4f) + i * 5.16));
            Oval(x, y, width, R(1, 3.5f), "#fff4c6", (int)(150 * pulse));
        }
    }

    static void Foreground(float t, int shot)
    {
        rng = new Random(868 + shot * 21);
        for (int i = 0; i < 29; i++)
        {
            float x = shot == 0 ? R(-26, 628) : i < 19 ? R(-23, 228) : R(1140, 1298);
            float y = shot == 0 ? R(602, 735)
                : i < 19 ? R(648, 754) + x * .19f : R(694, 769) - (x - 1140) * .19f;
            float size = R(.56f, 1.34f);
            if (shot == 0 && x > 449 && y < 648 + (x - 500) * .6f) continue;
            Sprigs(x, y, size, i, R(-29, 26) + 3.4f * S(t * 1.8 + i * .39));
        }
        rng = new Random(811);
        for (int i = 0; i < 28; i++)
        {
            float x = (R(0, 1340) + t * R(4, 17)) % 1340;
            float y = R(33, 562) + S(t * .67 + i) * R(7, 16);
            float size = R(.8f, 4.4f);
            int fade = (int)(R(22, 135) * (.5 + .5 * S(t * 2.2 + i * .49)));
            Oval(x, y, size, size * .89f, "#fff1c1", fade);
        }
        if (shot != 1) Glow(1112, 101, 682, 391, "#fff2c9", shot == 2 ? 112 : 41);
    }

    static void Scene(Bitmap target, int shot, float t)
    {
        using (g = Setup(target))
        {
            g.DrawImageUnscaled(plates[shot], 0, 0);
            Current(t, shot);
            if (shot == 0)
            {
                float release = Math.Max(0, t - 1.53f);
                float lift = 1 - Ease(t / 1.29f);
                float x = 584 + 26 * lift + 52 * release + 26 * release * release / (1 + release);
                float y = 512 + 2.7f * S(t * 4.2) - 43 * lift + release * 5;
                Wake(x - 12, y + 6, .83f, release, Ease((t - 1.05f) / .7f));
                PaperBoat(x, y, .88f, -3 + 2.4f * S(t * 3.1) + lift * 3, Ease((t - .98f) / .4f));
                rng = new Random(171);
                Child(t);
                float ring = (t - 1.21f) / .9f;
                if (ring > 0 && ring < 1)
                {
                    float radius = 29 + ring * 124;
                    Arc(566 - radius / 2, 513 - radius * .12f, radius, radius * .24f, -2, 302,
                        "#fff0c7", 1.7f, (int)(192 * (1 - ring)));
                    for (int i = 0; i < 4; i++)
                        Oval(541 + i * 11 + ring * i * 4, 506 - 27 * S(ring * Math.PI) + i * 2,
                             3, 4, "#f9edc6", (int)(182 * (1 - ring)));
                }
            }
            if (shot == 1)
            {
                EdgeRock(301, 369, .81f, 1, t);
                EdgeRock(610, 393, .84f, 2, t);
                EdgeRock(685, 347, .41f, 4, t);
                EdgeRock(950, 336, .64f, 5, t);
                EdgeRock(1110, 543, .99f, 1, t);
                float x = 229 + t * 178;
                float curve = (float)Math.Exp(-Math.Pow((t - 1.71) / .78, 2));
                float y = 442 + 32 * curve - 28 * Ease((t - 2.5f) / 1.4f) + 3.5f * S(t * 5);
                Wake(x - 26, y + 7, 1.07f, t, 1);
                PaperBoat(x, y, 1.17f, S(t * 4.2) * (3 + curve * 4));
                EdgeRock(441, 583, 1.28f, 3, t);
                EdgeRock(802, 616, .85f, 2, t);
                BrushLeaf(410 + 98 * t, 402 + 16 * S(t * 1.46), .58f, 38 + 25 * S(t * 2.2), "#bd8658", true);
                BrushLeaf(101 + 103 * t, 499 - 15 * S(t * 1.15), .72f, -28 + 27 * S(t * 1.6), "#c7a161", true);
            }
            if (shot == 2)
            {
                const float contact = 2.18f;
                float bump = Math.Max(0, t - contact);
                float x = 629 + 24 * t + 117 * bump - 32 * bump * bump / (1 + bump);
                float y = 449 - 12 * t + 2.8f * S(t * 4) - 6 * Ease(bump / 2);
                float duckFollowX = x - 224;
                float dx = duckFollowX - Math.Max(0, contact - t) * (174 - 17 * t);
                float dip = (float)Math.Exp(-Math.Pow((t - contact - .03) / .25, 2));
                float glide = Ease((t - 3.24f) / 1.68f);
                dx -= 85 * glide;
                float dy = y + 18 + 104 * (1 - Ease(t / contact)) + 2 * S(t * 8) - 21 * dip + 21 * glide;
                SunOnWater(t);
                Wake(dx - 50, dy + 13, 1.1f, t, .95f);
                Wake(x - 37, y + 8, .99f, t + .71f, .57f + .43f * dip);
                Duck(dx, dy, 1.16f, t, dip);
                PaperBoat(x, y, 1.1f, S(t * 3.6) * 3 + dip * 4);
                Glow(1043, 408, 382, 205, "#ffedb2", (int)(18 + 39 * Ease((t - .5f) / 4)));
                for (int i = 0; i < 15; i++)
                {
                    float sparkle = Math.Max(0, S(i * 8.12 + t * 3.2f));
                    if (sparkle < .55f) continue;
                    float sx = 891 + (i * 73) % 327 + t * 9;
                    float sy = 306 + (i * 49) % 193;
                    float radius = (2 + i % 6) * sparkle;
                    int alpha = (int)(122 * sparkle);
                    Line(sx - radius * 2, sy, sx + radius * 2, sy, "#fff5d0", 1.35f, alpha);
                    Line(sx, sy - radius * .63f, sx, sy + radius * .63f, "#fff6d2", 1.1f, alpha);
                }
            }
            Foreground(t, shot);
        }
    }

    static void Render(Bitmap frame, Bitmap next, float clock)
    {
        const float cut1 = 3.95f, cut2 = 7.70f, dissolve = .32f;
        int shot = clock < cut1 ? 0 : clock < cut2 ? 1 : 2;
        float local = shot == 0 ? clock : clock - (shot == 1 ? cut1 : cut2) + dissolve;
        Scene(frame, shot, local);
        float untilCut = shot == 0 ? cut1 - clock : shot == 1 ? cut2 - clock : 1;
        if (untilCut < dissolve)
        {
            Scene(next, shot + 1, dissolve - untilCut);
            float opacity = Ease(1 - untilCut / dissolve);
            using (g = Setup(frame))
            using (var attr = new ImageAttributes())
            {
                attr.SetColorMatrix(new ColorMatrix { Matrix33 = opacity });
                g.DrawImage(next, new Rectangle(0, 0, W, H), 0, 0, W, H, GraphicsUnit.Pixel, attr);
            }
        }
        using (g = Setup(frame)) g.DrawImageUnscaled(grain, 0, 0);
    }

    static int Main(string[] args)
    {
        try
        {
            if (args.Length == 2 && args[0] == "sound")
            {
                Sound.Create(args[1]);
                return 0;
            }
            if (args.Length == 0 || args[0] != "render" && args[0] != "preview")
                throw new ArgumentException("Use render, preview <seconds> <output.png>, or sound <output.wav>.");
            for (int i = 0; i < plates.Length; i++) plates[i] = Background(i);
            grain = PaperTexture();
            using (var frame = new Bitmap(W, H, PixelFormat.Format32bppArgb))
            using (var next = new Bitmap(W, H, PixelFormat.Format32bppArgb))
            {
                if (args[0] == "preview")
                {
                    for (int i = 1; i < args.Length; i += 2)
                    {
                        Render(frame, next, float.Parse(args[i], CultureInfo.InvariantCulture));
                        frame.Save(args[i + 1], ImageFormat.Png);
                    }
                }
                else
                {
                    var rect = new Rectangle(0, 0, W, H);
                    var bytes = new byte[W * H * 4];
                    using (var output = Console.OpenStandardOutput())
                    for (int i = 0; i < Frames; i++)
                    {
                        Render(frame, next, (float)i / Fps);
                        var bits = frame.LockBits(rect, ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
                        try { Marshal.Copy(bits.Scan0, bytes, 0, bytes.Length); }
                        finally { frame.UnlockBits(bits); }
                        output.Write(bytes, 0, bytes.Length);
                        if (i % 48 == 0) Console.Error.WriteLine("Painted frame {0}/{1}", i + 1, Frames);
                    }
                }
            }
            foreach (var plate in plates) plate.Dispose();
            grain.Dispose();
            return 0;
        }
        catch (Exception e)
        {
            Console.Error.WriteLine(e);
            return 1;
        }
    }
}
