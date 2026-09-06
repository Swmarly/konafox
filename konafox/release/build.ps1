# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}

$releaseRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $releaseRoot
if (-not $env:MOZILLABUILD) { $env:MOZILLABUILD = 'C:\mozilla-build' }
if (-not $env:MOZBUILD_STATE_PATH) { $env:MOZBUILD_STATE_PATH = Join-Path $env:USERPROFILE '.mozbuild' }
$buildPython = Join-Path $env:MOZILLABUILD 'python3/python.exe'
$bash = Join-Path $env:MOZILLABUILD 'msys2/usr/bin/bash.exe'
$clang = Join-Path $env:USERPROFILE '.mozbuild/clang-22/bin/clang-cl.exe'
foreach ($required in @($buildPython, $bash, $clang, (Join-Path $env:USERPROFILE '.mozbuild/sysroot-wasm32-wasi'))) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Runner needs MozillaBuild and Waterfox's Clang 22/WASI tools: $required. See KONAFOX_RELEASE.md." }
}
if ((Get-PSDrive -Name ([IO.Path]::GetPathRoot($releaseRoot).TrimEnd('\', ':'))).Free -lt 80GB) {
    throw 'The release checkout needs at least 80 GB free disk space.'
}
$env:PATH = "$(Split-Path $buildPython);$(Split-Path $bash);$(Join-Path $env:USERPROFILE '.cargo/bin');$env:PATH"
$env:MOZCONFIG = 'konafox/build/mozconfig.release.windows'
$env:PYTHONIOENCODING = 'utf-8'
$env:MOZ_BUILD_DATE = [DateTime]::UtcNow.ToString('yyyyMMddHHmmss')
$env:RUSTUP_TOOLCHAIN = '1.97.1'
New-Item -ItemType Directory -Force -Path artifacts | Out-Null
Invoke-Checked rustup @('toolchain', 'install', $env:RUSTUP_TOOLCHAIN, '--profile', 'minimal')
Invoke-Checked $buildPython @('-m', 'venv', 'artifacts/release-venv')
$releasePython = Join-Path $releaseRoot 'artifacts/release-venv/Scripts/python.exe'
Invoke-Checked $releasePython @('-m', 'pip', 'install', '-r', 'konafox/release/requirements.txt')
Invoke-Checked $releasePython @('konafox/release/release.py', 'check-key')

foreach ($command in @('bootstrap', 'build', 'package')) {
    $arguments = switch ($command) {
        'bootstrap' { @('mach', '--no-interactive', 'bootstrap', '--application-choice', 'browser', '--no-system-changes') }
        default { @('mach', $command) }
    }
    & $buildPython @arguments *> "artifacts/release-$command.log"
    if ($LASTEXITCODE -ne 0) {
        Get-Content -LiteralPath "artifacts/release-$command.log" -Tail 80
        throw "$command failed; see the release logs artifact."
    }
}

$dist = Join-Path $releaseRoot 'obj-konafox-release/dist'
$install = Join-Path $dist 'konafox'
$infoText = & $releasePython konafox/release/release.py describe $install $env:MOZ_BUILD_DATE $env:GITHUB_SHA
if ($LASTEXITCODE -ne 0) { throw 'Package identity validation failed' }
$infoText | Set-Content -Encoding utf8 artifacts/release-build-info.json
$info = $infoText | ConvertFrom-Json
$smokeProfile = Join-Path $releaseRoot "artifacts/release-smoke-$($info.buildID)"
$screenshot = Join-Path $releaseRoot "artifacts/release-smoke-$($info.buildID).png"
$smokeArguments = @('-headless', '-no-remote', '-profile', "`"$smokeProfile`"", '-screenshot', "`"$screenshot`"", 'about:blank')
$smoke = Start-Process -FilePath (Join-Path $install 'konafox.exe') -ArgumentList $smokeArguments -WindowStyle Hidden -PassThru
if (-not $smoke.WaitForExit(120000)) {
    Stop-Process -Id $smoke.Id -Force
    throw 'Packaged browser startup timed out'
}
if ($smoke.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $screenshot)) { throw 'Packaged browser startup failed' }
$prefix = "KonaFox-$($info.appVersion)-$($info.buildID)-win64"
$output = Join-Path $releaseRoot "artifacts/release-$($info.buildID)"
New-Item -ItemType Directory -Path $output | Out-Null
$installers = @(Get-ChildItem -LiteralPath $dist -Filter 'konafox-*.en-US.win64.installer.exe' -File)
$packages = @(Get-ChildItem -LiteralPath $dist -Filter 'konafox-*.en-US.win64.zip' -File)
if ($installers.Count -ne 1 -or $packages.Count -ne 1) { throw 'Expected exactly one fresh installer and ZIP package' }
Copy-Item -LiteralPath $installers[0].FullName -Destination (Join-Path $output "$prefix.exe")
Copy-Item -LiteralPath $packages[0].FullName -Destination (Join-Path $output "$prefix.zip")
$env:MOZ_PRODUCT_VERSION = $info.appVersion
$env:MAR_CHANNEL_ID = 'konafox-release'
Invoke-Checked $bash @('konafox/release/make-mar.sh')
Invoke-Checked $releasePython @('konafox/release/release.py', 'sign', 'artifacts/unsigned.complete.mar', (Join-Path $output "$prefix.complete.mar"), $info.appVersion)
Invoke-Checked (Join-Path $dist 'bin/signmar.exe') @('-D', (Join-Path $PSScriptRoot 'update-cert.der'), '-v', (Join-Path $output "$prefix.complete.mar"))
Invoke-Checked $releasePython @('konafox/release/release.py', 'metadata', $output, 'artifacts/release-build-info.json')
"release-directory=$output" >> $env:GITHUB_OUTPUT
"release-tag=$($info.tag)" >> $env:GITHUB_OUTPUT
