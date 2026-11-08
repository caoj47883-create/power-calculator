# Build a signed release APK for the Power Ledger app.
# Portable toolchain lives in ../.tools; run with:
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
$ErrorActionPreference = 'Continue'

$root = $PSScriptRoot
$appDir = Join-Path $root 'app'
$resDir = Join-Path $appDir 'res'
$assetsDir = Join-Path $appDir 'assets'
$javaDir = Join-Path $appDir 'java'
$buildDir = Join-Path $root 'build'
$genDir = Join-Path $buildDir 'gen'
$classDir = Join-Path $buildDir 'classes'
$dexDir = Join-Path $buildDir 'dex'
$distDir = Join-Path $root 'dist'
$keystoreDir = Join-Path $root 'keystore'
$keystore = Join-Path $keystoreDir 'powercalc-release.jks'
$passwordFile = Join-Path $keystoreDir 'keystore.password'
$keyAlias = 'powercalc'
$storePass = $null
$keyPass = $null
$finalName = 'power-calculator-v2.3.0.apk'

function Fail([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Assert-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) {
        Fail "$Step failed with exit code $LASTEXITCODE."
    }
}

# --- Locate toolchain -------------------------------------------------------
$jdkHome = $env:JAVA_HOME
if (-not $jdkHome -or -not (Test-Path (Join-Path $jdkHome 'bin\javac.exe'))) {
    $jdkCandidate = Get-ChildItem (Join-Path $root '..\.tools\jdk') -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1
    if ($jdkCandidate) { $jdkHome = $jdkCandidate.FullName }
}
if (-not $jdkHome -or -not (Test-Path (Join-Path $jdkHome 'bin\javac.exe'))) {
    Fail 'JDK 17 was not found. Set JAVA_HOME or place a JDK under .tools/jdk.'
}
$env:JAVA_HOME = $jdkHome

$sdkRoot = $env:ANDROID_SDK_ROOT
if (-not $sdkRoot -or -not (Test-Path $sdkRoot)) {
    $sdkRoot = Join-Path $root '..\.tools\android-sdk'
}
$buildToolsVersion = '35.0.1'
$platform = 'android-35'
$buildTools = Join-Path $sdkRoot "build-tools\$buildToolsVersion"
$platformDir = Join-Path $sdkRoot "platforms\$platform"
$androidJar = Join-Path $platformDir 'android.jar'
$aapt2 = Join-Path $buildTools 'aapt2.exe'
$zipalign = Join-Path $buildTools 'zipalign.exe'
$apksigner = Join-Path $buildTools 'apksigner.bat'
$d8 = Join-Path $buildTools 'd8.bat'
$javac = Join-Path $jdkHome 'bin\javac.exe'
$keytool = Join-Path $jdkHome 'bin\keytool.exe'
$jarTool = Join-Path $jdkHome 'bin\jar.exe'

foreach ($tool in @($aapt2, $zipalign, $apksigner, $d8, $javac, $keytool)) {
    if (-not (Test-Path $tool)) { Fail "Required build tool is missing: $tool" }
}
if (-not (Test-Path $androidJar)) { Fail "Android platform jar is missing: $androidJar" }

Write-Host '=== Power Ledger build ===' -ForegroundColor Cyan
Write-Host "Java:         $jdkHome"
Write-Host "Android SDK:  $sdkRoot"
Write-Host "Build tools:  $buildToolsVersion"
Write-Host "Platform:     $platform"

# --- Clean ------------------------------------------------------------------
if (Test-Path $buildDir) {
    $resolvedBuild = (Resolve-Path $buildDir).Path
    if ($resolvedBuild -ne $buildDir) { Fail 'Unexpected build directory path.' }
    Remove-Item -LiteralPath $buildDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $buildDir, $genDir, $classDir, $dexDir, $distDir | Out-Null

# --- Resources --------------------------------------------------------------
Write-Host '[1/7] Compiling Android resources...'
& $aapt2 compile --dir $resDir -o (Join-Path $buildDir 'res.zip')
Assert-Exit 'aapt2 compile'

Write-Host '[2/7] Linking resources and assets...'
$unsigned = Join-Path $buildDir 'app-unsigned.apk'
& $aapt2 link -o $unsigned -I $androidJar --manifest (Join-Path $appDir 'AndroidManifest.xml') -R (Join-Path $buildDir 'res.zip') -A $assetsDir --java $genDir --auto-add-overlay --min-sdk-version 23 --target-sdk-version 34 --version-code 15 --version-name 2.3.0
Assert-Exit 'aapt2 link'

# --- Java -> DEX ------------------------------------------------------------
Write-Host '[3/7] Compiling Java...'
$javaFiles = @()
$javaFiles += @(Get-ChildItem $javaDir -Recurse -Filter '*.java' | ForEach-Object { $_.FullName })
$javaFiles += @(Get-ChildItem $genDir -Recurse -Filter '*.java' | ForEach-Object { $_.FullName })
if ($javaFiles.Count -eq 0) { Fail 'No Java sources found.' }
& $javac -encoding UTF-8 -source 8 -target 8 -bootclasspath $androidJar -d $classDir @javaFiles
Assert-Exit 'javac'

Write-Host '[4/7] Converting bytecode to DEX...'
$classFiles = @(Get-ChildItem $classDir -Recurse -Filter '*.class' | ForEach-Object { $_.FullName })
if ($classFiles.Count -eq 0) { Fail 'No compiled classes found.' }
& $d8 --min-api 23 --lib $androidJar --output $dexDir @classFiles
Assert-Exit 'd8'

$dexPath = Join-Path $dexDir 'classes.dex'
if (-not (Test-Path $dexPath)) { Fail 'd8 did not produce classes.dex.' }

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($unsigned, 'Update')
try {
    $existing = $zip.GetEntry('classes.dex')
    if ($existing) { $existing.Delete() }
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
        $zip, $dexPath, 'classes.dex',
        [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
} finally {
    $zip.Dispose()
}

# --- Align and sign ---------------------------------------------------------
Write-Host '[5/7] Aligning APK...'
$aligned = Join-Path $buildDir 'app-aligned.apk'
& $zipalign -f -p 4 $unsigned $aligned
Assert-Exit 'zipalign'

New-Item -ItemType Directory -Force -Path $keystoreDir | Out-Null
if (-not $storePass) { $storePass = $env:POWERCALC_KEYSTORE_PASSWORD }
if (-not $storePass -and (Test-Path $passwordFile)) {
    $storePass = (Get-Content -LiteralPath $passwordFile -Raw -Encoding UTF8).Trim()
}
if (-not $storePass -and -not (Test-Path $keystore)) {
    # First local build: generate a random password and keep it beside the ignored keystore.
    $storePass = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N'))
    Set-Content -LiteralPath $passwordFile -Value $storePass -Encoding ascii
    Write-Host '[6/7] Generated local keystore password file (not tracked by git).'
}
if (-not $storePass) {
    Fail 'Keystore password is missing. Set POWERCALC_KEYSTORE_PASSWORD or create keystore/keystore.password.'
}
$keyPass = $storePass

if (-not (Test-Path $keystore)) {
    Write-Host '[6/7] Creating local release keystore...'
    & $keytool -genkeypair -v -keystore $keystore -alias $keyAlias -keyalg RSA -keysize 2048 -validity 10000 -storepass $storePass -keypass $keyPass -dname 'CN=Power Calculator, OU=Offline Apps, O=PowerCalc, L=Shanghai, ST=Shanghai, C=CN'
    Assert-Exit 'keytool'
} else {
    Write-Host '[6/7] Using existing local release keystore.'
}

$finalApk = Join-Path $distDir $finalName
if (Test-Path $finalApk) { Remove-Item -LiteralPath $finalApk -Force }

Write-Host '[7/7] Signing APK...'
& $apksigner sign --ks $keystore --ks-key-alias $keyAlias --ks-pass "pass:$storePass" --key-pass "pass:$keyPass" --min-sdk-version 23 --v1-signing-enabled true --v2-signing-enabled true --out $finalApk $aligned
Assert-Exit 'apksigner sign'

# --- Verify -----------------------------------------------------------------
$verifyLog = Join-Path $buildDir 'verify.txt'
& $apksigner verify --verbose --print-certs $finalApk 2>&1 | Tee-Object -FilePath $verifyLog
Assert-Exit 'apksigner verify'
& $zipalign -c -v 4 $finalApk | Out-Null
Assert-Exit 'zipalign check'

$badging = & $aapt2 dump badging $finalApk 2>&1
$badging | Set-Content -Path (Join-Path $buildDir 'badging.txt') -Encoding UTF8
$permissions = $badging | Where-Object { $_ -match '^uses-permission:' }
if ($permissions) {
    Fail "The APK unexpectedly requests permissions: $permissions"
}

$hash = (Get-FileHash $finalApk -Algorithm SHA256).Hash.ToLower()
"$hash  $finalName" | Set-Content -Path (Join-Path $distDir 'SHA256SUMS.txt') -Encoding ASCII

Write-Host ''
Write-Host 'BUILD OK' -ForegroundColor Green
Write-Host "APK:    $finalApk"
Write-Host "SHA256: $hash"
Write-Host "Size:   $((Get-Item $finalApk).Length) bytes"
$badging | Where-Object { $_ -match '^(package|sdkVersion|targetSdkVersion|application-label)' } | ForEach-Object { Write-Host $_ }
