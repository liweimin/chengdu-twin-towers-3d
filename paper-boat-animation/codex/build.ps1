$ErrorActionPreference = 'Stop'

$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) {
    $compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
}
if (-not (Test-Path -LiteralPath $compiler)) {
    throw 'The Windows .NET Framework 4.x C# compiler is required.'
}
$ffmpeg = (Get-Command ffmpeg -CommandType Application).Source
$build = Join-Path $PSScriptRoot '.build'
New-Item -ItemType Directory -Force -Path $build | Out-Null
$renderer = Join-Path $build 'film.exe'
$audio = Join-Path $build 'sound.wav'
$encoding = Join-Path $build 'paper-boat.mp4'
$output = Join-Path $PSScriptRoot 'paper-boat.mp4'
$sources = @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'src') -Filter '*.cs' |
    Sort-Object Name | Select-Object -ExpandProperty FullName)

& $compiler /nologo /optimize+ /codepage:65001 /r:System.Drawing.dll "/out:$renderer" @sources
if ($LASTEXITCODE -ne 0) { throw 'C# compilation failed.' }
& $renderer sound $audio
if ($LASTEXITCODE -ne 0) { throw 'Sound synthesis failed.' }

# Copy binary BGRA frames directly so Windows PowerShell never decodes them as text.
$renderInfo = New-Object System.Diagnostics.ProcessStartInfo
$renderInfo.FileName = $renderer
$renderInfo.Arguments = 'render'
$renderInfo.UseShellExecute = $false
$renderInfo.RedirectStandardOutput = $true
$encoderInfo = New-Object System.Diagnostics.ProcessStartInfo
$encoderInfo.FileName = $ffmpeg
$encoderInfo.UseShellExecute = $false
$encoderInfo.RedirectStandardInput = $true
$encoderInfo.Arguments = @(
    '-hide_banner -loglevel warning -y'
    '-f rawvideo -pixel_format bgra -video_size 1280x720 -framerate 24 -i pipe:0'
    "-i `"$audio`" -map 0:v:0 -map 1:a:0 -t 12"
    '-c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p'
    '-vf scale=out_color_matrix=bt709 -colorspace bt709 -color_primaries bt709 -color_trc bt709'
    '-c:a aac -b:a 192k -movflags +faststart'
    "-metadata title=`"Paper Boat in the Sun`" `"$encoding`""
) -join ' '

$paint = $null
$encode = $null
try {
    $encode = [System.Diagnostics.Process]::Start($encoderInfo)
    $paint = [System.Diagnostics.Process]::Start($renderInfo)
    $pipe = $encode.StandardInput.BaseStream
    try { $paint.StandardOutput.BaseStream.CopyTo($pipe) }
    finally { $pipe.Dispose() }
    $paint.WaitForExit()
    $encode.WaitForExit()
    if ($paint.ExitCode -ne 0 -or $encode.ExitCode -ne 0) { throw 'Video rendering failed.' }
    Move-Item -LiteralPath $encoding -Destination $output -Force
    Write-Output $output
}
finally {
    foreach ($process in @($paint, $encode)) {
        if ($null -ne $process) {
            if (-not $process.HasExited) { $process.Kill(); $process.WaitForExit() }
            $process.Dispose()
        }
    }
}
