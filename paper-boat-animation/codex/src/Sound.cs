using System;
using System.IO;
using System.Text;

// Original score and sound design, synthesized directly to stereo PCM.
static class Sound
{
    const int Rate = 48000, Length = 12 * Rate;
    const double Tau = 2 * Math.PI;
    static readonly double[] Left = new double[Length];
    static readonly double[] Right = new double[Length];

    static double Sin(double x) { return Math.Sin(x); }
    static double Hz(int midi) { return 440 * Math.Pow(2, (midi - 69) / 12.0); }

    // Two quiet, asymmetric room reflections follow the dry signal.
    static void Add(int index, double sample, double pan, bool room)
    {
        double l = sample * Math.Sqrt((1 - pan) * .5);
        double r = sample * Math.Sqrt((1 + pan) * .5);
        if (index < Length) { Left[index] += l; Right[index] += r; }
        if (!room) return;
        if (index + 1871 < Length) Right[index + 1871] += l * .17;
        if (index + 2717 < Length) Left[index + 2717] += r * .16;
        if (index + 5419 < Length) Left[index + 5419] += l * .09;
        if (index + 6277 < Length) Right[index + 6277] += r * .08;
    }

    static void Note(double start, int pitch, double velocity, double pan, bool bell)
    {
        double f = Hz(pitch);
        int offset = (int)(start * Rate);
        int end = Math.Min((int)(Rate * (bell ? 2.7 : 3.7)), Length - offset);
        for (int i = 0; i < end; i++)
        {
            double t = i / (double)Rate;
            double phase = Tau * f * t;
            double attack = 1 - Math.Exp(-t * (bell ? 238 : 113));
            double body = Sin(phase) * Math.Exp(-t * (bell ? 4.2 : 2.5));
            double top = Sin(phase * 2.003) * Math.Exp(-t * 5.8) * .34;
            top += Sin(phase * (bell ? 2.76 : 3.007)) * Math.Exp(-t * 11.5) * (bell ? .27 : .12);
            double chorus = .14 * Sin(phase * 1.0016 + .2) * Math.Exp(-t * 3.5);
            Add(offset + i, velocity * attack * (body + top + chorus), pan, true);
        }
    }

    static void Score()
    {
        // Arpeggiated accompaniment. Pitches written as MIDI notes.
        int[][] chords = {
            new[] { 50, 57, 62, 66 }, new[] { 47, 54, 57, 62 },
            new[] { 43, 50, 59, 66 }, new[] { 45, 52, 59, 62 },
            new[] { 50, 57, 64, 66 }
        };
        double[] starts = { .37, 2.84, 5.13, 7.35, 9.78 };
        double[] attacks = { 0, .14, .37, .63 };
        for (int chord = 0; chord < chords.Length; chord++)
        for (int note = 0; note < attacks.Length; note++)
            Note(starts[chord] + attacks[note], chords[chord][note], .053 - note * .006, -.37 + note * .13, false);

        double[] times = { .91, 1.26, 1.65, 2.22, 3.08, 3.57, 4.08, 4.66, 5.36, 5.76,
                           6.21, 6.83, 7.51, 7.95, 8.48, 8.87, 9.57, 9.83, 10.30, 10.77 };
        int[] notes = { 69, 71, 74, 76, 73, 71, 66, 69, 71, 74, 78, 76, 76, 71, 69, 64, 69, 74, 76, 81 };
        for (int i = 0; i < times.Length; i++)
        {
            Note(times[i], notes[i], .084 + .013 * Sin(i * 1.52), .09 + .21 * Sin(i * .89), false);
            if (i == 2 || i == 10 || i >= 16) Note(times[i] + .021, notes[i] + 12, .022, .38, true);
        }
    }

    static void Creek()
    {
        var random = new Random(818);
        double current = 0, wash = 0, fast = 0, side = 0;
        for (int i = 0; i < Length; i++)
        {
            double t = i / (double)Rate;
            double white = random.NextDouble() * 2 - 1;
            current += .023 * (white - current);
            wash += .0016 * (current - wash);
            fast += .17 * (white - fast);
            side += .033 * (random.NextDouble() * 2 - 1 - side);
            double eddy = .66 + .28 * Sin(t * 4.52 + .57 * Sin(t * 2.22));
            double ripple = .66 + .34 * Sin(t * 8.88 + .88 * Sin(t * 2.87));
            Left[i] += .41 * wash + .230 * current * eddy + .063 * fast * ripple;
            Right[i] += .38 * wash + .199 * current * ripple + .128 * side * eddy + .052 * fast;
        }
        for (int i = 0; i < 82; i++)
        {
            double at = random.NextDouble() * 12;
            Bubble(at, 210 + 800 * random.NextDouble(),
                   .006 + .024 * random.NextDouble(), random.NextDouble() * 1.65 - .825);
        }
        Bubble(1.225, 470, .083, -.16);
        Bubble(1.262, 692, .061, -.06);
        Bubble(1.319, 812, .037, .05);
        Bubble(8.22, 323, .044, -.52);
        Bubble(8.69, 390, .045, -.32);
        Bubble(9.04, 337, .051, -.19);
        Bubble(9.56, 461, .082, .14);
        Bubble(9.61, 592, .059, .27);
        Bubble(9.71, 711, .037, .37);
    }

    static void Bubble(double start, double f, double amplitude, double pan)
    {
        int offset = (int)(start * Rate);
        for (int i = 0; i < Rate * .26 && offset + i < Length; i++)
        {
            double t = i / (double)Rate;
            double phase = Tau * (f * t + 1600 * t * t);
            double envelope = (1 - Math.Exp(-t * 270)) * Math.Exp(-t * 31);
            Add(offset + i, amplitude * envelope * (Sin(phase) + .21 * Sin(2.07 * phase)), pan, false);
        }
    }

    static void Bird(double start, double duration, double low, double high, double gain, double pan)
    {
        int offset = (int)(start * Rate);
        double phase = 0;
        for (int i = 0; i < duration * Rate; i++)
        {
            double u = i / (duration * Rate);
            phase += Tau * (low + (high - low) * Sin(Math.PI * u) + 52 * Sin(u * 29)) / Rate;
            double envelope = Math.Pow(Sin(Math.PI * u), 2) * (.76 + .24 * Sin(u * 44));
            Add(offset + i, gain * envelope * (Sin(phase) + .085 * Sin(phase * 2)), pan, true);
        }
    }

    static void DuckCall(double start, double duration, double gain, double pan)
    {
        int offset = (int)(start * Rate);
        double phase = 0;
        for (int i = 0; i < duration * Rate; i++)
        {
            double u = i / (duration * Rate);
            phase += Tau * (310 - 133 * u + 68 * Sin(Math.PI * u)) / Rate;
            double tone = .21 * Sin(phase) + .4 * Sin(phase * 2) + .28 * Sin(phase * 3) + .13 * Sin(phase * 5);
            double envelope = Math.Pow(Sin(Math.PI * u), .72) * (.71 + .29 * Sin(u * 36));
            Add(offset + i, gain * tone * envelope, pan, true);
        }
    }

    public static void Create(string output)
    {
        Creek();
        Score();
        Bird(.18, .16, 2000, 2650, .028, .53);
        Bird(.42, .19, 1800, 2540, .023, .55);
        Bird(3.78, .15, 2100, 2500, .021, -.68);
        Bird(6.61, .20, 1740, 2240, .027, .54);
        Bird(6.89, .17, 1980, 2680, .019, .56);
        Bird(10.55, .21, 1820, 2440, .019, .66);
        DuckCall(8.34, .145, .063, -.45);
        DuckCall(8.52, .118, .048, -.37);
        DuckCall(10.33, .13, .048, .18);

        double peak = 0;
        for (int i = 0; i < Length; i++) peak = Math.Max(peak, Math.Max(Math.Abs(Left[i]), Math.Abs(Right[i])));
        double gain = .77 / peak;
        using (var writer = new BinaryWriter(File.Create(output), Encoding.ASCII))
        {
            writer.Write(Encoding.ASCII.GetBytes("RIFF")); writer.Write(36 + Length * 4);
            writer.Write(Encoding.ASCII.GetBytes("WAVEfmt ")); writer.Write(16);
            writer.Write((short)1); writer.Write((short)2); writer.Write(Rate);
            writer.Write(Rate * 4); writer.Write((short)4); writer.Write((short)16);
            writer.Write(Encoding.ASCII.GetBytes("data")); writer.Write(Length * 4);
            for (int i = 0; i < Length; i++)
            {
                double fade = Math.Min(1, Math.Min(i / (Rate * .22), (Length - 1 - i) / (Rate * .75)));
                writer.Write((short)(Left[i] * fade * gain * 32767));
                writer.Write((short)(Right[i] * fade * gain * 32767));
            }
        }
    }
}
