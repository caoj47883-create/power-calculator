param(
  [string]$OutDir = (Join-Path $PSScriptRoot '..\screenshots'),
  [int]$Port = 9333,
  [int]$Width = 390,
  [int]$Height = 844,
  [int]$Scale = 2
)

$ErrorActionPreference = 'Stop'
$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path $edge)) { throw "Edge not found: $edge" }

$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$appPath = Join-Path $root 'power-calculator\app\assets\index.html'
$pageUri = ([System.Uri]::new($appPath)).AbsoluteUri
$profile = Join-Path $root ".tools\edge-cdp-$Port"
New-Item -ItemType Directory -Force -Path $profile, $OutDir | Out-Null

$argList = @(
  '--headless=new',
  '--no-sandbox',
  '--hide-scrollbars',
  '--no-first-run',
  '--allow-file-access-from-files',
  '--remote-debugging-port=' + $Port,
  '--remote-allow-origins=*',
  '--user-data-dir=' + $profile,
  'about:blank'
)
$edgeProc = Start-Process -FilePath $edge -ArgumentList $argList -PassThru -WindowStyle Hidden
$ct = [System.Threading.CancellationToken]::None

try {
  $targets = $null
  for ($i = 0; $i -lt 40; $i++) {
    try {
      $targets = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/json/list" -UseBasicParsing -TimeoutSec 2
      if ($targets) { break }
    } catch {
      Start-Sleep -Milliseconds 250
    }
  }
  if (-not $targets) { throw 'Could not reach Edge DevTools endpoint.' }
  $target = $targets | Where-Object { $_.type -eq 'page' } | Select-Object -First 1
  if (-not $target) { throw 'No page target found.' }

  $ws = [System.Net.WebSockets.ClientWebSocket]::new()
  $ws.ConnectAsync([Uri]$target.webSocketDebuggerUrl, $ct).GetAwaiter().GetResult()
  $script:cdpId = 0

  function Send-Cdp {
    param([string]$Method, [hashtable]$Params = @{})
    $script:cdpId += 1
    $message = @{ id = $script:cdpId; method = $Method; params = $Params } | ConvertTo-Json -Depth 20 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($message)
    $segment = [System.ArraySegment[byte]]::new($bytes)
    $ws.SendAsync($segment, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $ct).GetAwaiter().GetResult()
    while ($true) {
      $memory = [System.IO.MemoryStream]::new()
      do {
        $buffer = New-Object byte[] 1048576
        $receive = $ws.ReceiveAsync([System.ArraySegment[byte]]::new($buffer), $ct).GetAwaiter().GetResult()
        if ($receive.MessageType -eq [System.Net.WebSockets.WebSocketMessageType]::Close) {
          throw 'DevTools WebSocket closed unexpectedly.'
        }
        $memory.Write($buffer, 0, $receive.Count)
      } while (-not $receive.EndOfMessage)
      $text = [System.Text.Encoding]::UTF8.GetString($memory.ToArray())
      $memory.Dispose()
      $response = $text | ConvertFrom-Json
      if ($response.id -eq $script:cdpId) {
        if ($response.error) { throw ("CDP error: " + ($response.error | ConvertTo-Json -Compress)) }
        return $response.result
      }
    }
  }

  function Evaluate-Js {
    param([string]$Expression)
    $result = Send-Cdp -Method 'Runtime.evaluate' -Params @{
      expression = $Expression
      returnByValue = $true
      awaitPromise = $true
    }
    return $result.result.value
  }

  function Save-Shot {
    param([string]$Name)
    $shot = Send-Cdp -Method 'Page.captureScreenshot' -Params @{
      format = 'png'
      fromSurface = $true
      captureBeyondViewport = $false
    }
    $path = Join-Path $OutDir $Name
    [System.IO.File]::WriteAllBytes($path, [Convert]::FromBase64String($shot.data))
    Write-Output "saved $path"
  }

  Send-Cdp -Method 'Page.enable' | Out-Null
  Send-Cdp -Method 'Runtime.enable' | Out-Null
  Send-Cdp -Method 'Emulation.setDeviceMetricsOverride' -Params @{
    width = $Width
    height = $Height
    deviceScaleFactor = $Scale
    mobile = $true
    screenWidth = $Width
    screenHeight = $Height
    screenOrientation = @{ type = 'portraitPrimary'; angle = 0 }
  } | Out-Null
  Send-Cdp -Method 'Emulation.setTouchEmulationEnabled' -Params @{ enabled = $true; maxTouchPoints = 5 } | Out-Null
  Send-Cdp -Method 'Page.navigate' -Params @{ url = $pageUri } | Out-Null
  Start-Sleep -Milliseconds 1800

  $metrics = Evaluate-Js "JSON.stringify({iw:innerWidth,ih:innerHeight,dpr:devicePixelRatio,ready:document.documentElement.classList.contains('is-ready'),total:document.getElementById('totalKwh').textContent})"
  Write-Output "metrics $metrics"

  Evaluate-Js "window.PowerApp.setTab('body')" | Out-Null
  Start-Sleep -Milliseconds 650
  Save-Shot 'app-body.png'

  Evaluate-Js "window.PowerApp.setTab('device')" | Out-Null
  Start-Sleep -Milliseconds 650
  Save-Shot 'app-device.png'

  Evaluate-Js "window.PowerApp.setTab('transit')" | Out-Null
  Start-Sleep -Milliseconds 650
  Save-Shot 'app-transit.png'

  Evaluate-Js "document.getElementById('infoButton').click()" | Out-Null
  Start-Sleep -Milliseconds 650
  Save-Shot 'app-info.png'
  Evaluate-Js "document.getElementById('closeInfo').click()" | Out-Null
  Start-Sleep -Milliseconds 400

  $uiTest = Evaluate-Js @"
(function () {
  function setRange(id, value) {
    var el = document.getElementById(id);
    el.value = value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }
  setRange('weightInput', 80);
  setRange('trip-taxi', 20);
  var total = document.getElementById('totalKwh').textContent;
  var avg = document.getElementById('averagePower').textContent;
  var taxiEnergy = document.querySelector('[data-trip-kwh="taxi"]').textContent;
  document.querySelector('[data-go-tab="transit"]').click();
  var activePanel = document.querySelector('.panel.is-active').getAttribute('data-panel');
  document.querySelector('[data-count="phone"][data-dir="1"]').click();
  var phoneCount = document.querySelector('[data-count-value="phone"]').textContent;
  return JSON.stringify({ total: total, avg: avg, taxiEnergy: taxiEnergy, activePanel: activePanel, phoneCount: phoneCount });
})()
"@
  Write-Output "uitest $uiTest"
}
finally {
  try { Send-Cdp -Method 'Browser.close' | Out-Null } catch { }
  try { $ws.Dispose() } catch { }
  try { if (-not $edgeProc.HasExited) { Stop-Process -Id $edgeProc.Id -Force -ErrorAction SilentlyContinue } } catch { }
}
