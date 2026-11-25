param(
    [ValidateRange(800, 4800)] [int] $Width = 3840,
    [int] $Seed = 241125,
    [string] $Output = (Join-Path $PSScriptRoot 'Chengdu-Aerial.png'),
    [string] $Preview
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -eq 'Core') {
    $windowsPowerShell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-Width', $Width, '-Seed', $Seed, '-Output', $Output)
    if ($Preview) { $arguments += @('-Preview', $Preview) }
    & $windowsPowerShell @arguments
    if ($LASTEXITCODE -ne 0) { throw "The renderer exited with code $LASTEXITCODE." }
    return
}

$outputPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Output)
$previewPath = if ($Preview) { $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Preview) }
if ($previewPath -eq $outputPath) { throw 'Output and preview require distinct paths.' }
if (-not ('ChengduAerial' -as [type])) {
    Add-Type -Path (Join-Path $PSScriptRoot 'ChengduAerial.cs') -ReferencedAssemblies System.Drawing
}
[ChengduAerial]::Render($outputPath, $previewPath, $Width, $Seed)
Write-Output $outputPath

