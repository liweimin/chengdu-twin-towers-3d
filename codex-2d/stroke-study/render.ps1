param(
    [ValidateRange(400, 4800)] [int] $Width = 3840,
    [ValidateRange(400, 1800)] [int] $FitWidth = 1200,
    [int] $Seed = 241125,
    [string] $Plan = (Join-Path $PSScriptRoot 'chengdu-brushes.bin.gz'),
    [string] $Output = (Join-Path $PSScriptRoot 'Chengdu-Brushes.png'),
    [string] $Preview,
    [string] $Reference
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -eq 'Core') {
    $classic = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-Width', $Width,
        '-FitWidth', $FitWidth, '-Seed', $Seed, '-Plan', $Plan, '-Output', $Output)
    if ($Preview) { $arguments += @('-Preview', $Preview) }
    if ($Reference) { $arguments += @('-Reference', $Reference) }
    & $classic @arguments
    if ($LASTEXITCODE -ne 0) { throw "The renderer exited with code $LASTEXITCODE." }
    return
}

$planPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Plan)
$outputPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Output)
$previewPath = if ($Preview) { $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Preview) }
if ($planPath -eq $outputPath -or ($previewPath -and $previewPath -in @($planPath, $outputPath))) {
    throw 'Use distinct paths for the stroke plan, image and preview.'
}
if (-not ('StrokeStudy' -as [type])) {
    Add-Type -Path (Join-Path $PSScriptRoot 'StrokeStudy.cs') -ReferencedAssemblies System.Drawing
}
if ($Reference) {
    $referencePath = (Resolve-Path -LiteralPath $Reference).ProviderPath
    if ($referencePath -in @($planPath, $outputPath, $previewPath)) { throw 'Use a separate input image path.' }
    [StrokeStudy]::Fit($referencePath, $planPath, $FitWidth, $Seed)
}
[StrokeStudy]::Render($planPath, $outputPath, $previewPath, $Width)
Write-Output $outputPath
