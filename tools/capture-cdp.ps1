param(
  [string]$OutDir = (Join-Path $PSScriptRoot '..\screenshots'),
  [int]$Port = 9335,
  [int]$Width = 390,
  [int]$Height = 844,
  [int]$Scale = 2,
  [switch]$CloseBrowser
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$appPath = Join-Path $root 'power-calculator\app\assets\index.html'
$pageUri = ([System.Uri]::new($appPath)).AbsoluteUri
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$ct = [System.Threading.CancellationToken]::None

$targets = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/json/list" -UseBasicParsing -TimeoutSec 5
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
  if ($result.exceptionDetails) {
    throw ("Page JS error: " + ($result.exceptionDetails | ConvertTo-Json -Depth 8 -Compress))
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
  Write-Output "saved $Name"
}

function Capture-Tab {
  param([string]$Tab, [string]$Name)
  Evaluate-Js "window.PowerApp.setTab('$Tab')" | Out-Null
  Start-Sleep -Milliseconds 450
  Save-Shot $Name
}

function Scroll-Stage {
  param([string]$Selector)
  $js = "(function(){var st=document.getElementById('stage');var el=document.querySelector('$Selector');if(!el)return false;var sr=st.getBoundingClientRect();var er=el.getBoundingClientRect();st.scrollTop+=er.top-sr.top-14;return true;}())"
  $ok = Evaluate-Js $js
  Start-Sleep -Milliseconds 400
  if (-not $ok) { throw "Could not scroll to $Selector" }
}

try {
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
  Start-Sleep -Milliseconds 1700

  $onboardingOpen = Evaluate-Js "!document.getElementById('profileModal').hidden"
  if ($onboardingOpen) {
    Start-Sleep -Milliseconds 250
    Save-Shot 'app-onboarding.png'
    Evaluate-Js @'
(function(){
  document.getElementById('profileAge').value='30';
  document.getElementById('profileHeight').value='170';
  document.getElementById('profileWeight').value='68';
  document.getElementById('saveProfileButton').click();
}())
'@ | Out-Null
    Start-Sleep -Milliseconds 700
  }

  Evaluate-Js "document.getElementById('resetButton').click(); document.getElementById('toast').classList.remove('is-visible');" | Out-Null
  Start-Sleep -Milliseconds 350

  $metrics = Evaluate-Js @'
(function(){
  var d=window.PowerModel.calc(window.PowerApp.getState());
  return {
    viewport:[innerWidth,innerHeight,devicePixelRatio],
    ready:document.documentElement.classList.contains('is-ready'),
    tab:document.documentElement.getAttribute('data-tab'),
    hero:document.getElementById('heroKwh').textContent,
    deviceCount:document.querySelectorAll('[data-device-card]').length,
    applianceCount:document.querySelectorAll('[data-appliance-card]').length,
    sliderTrips:document.querySelectorAll('#transitList .trip-card, #transitExtraList .trip-card').length,
    inputTrips:document.querySelectorAll('#transitInputList .trip-input-card').length,
    total:d.totalKwh.toFixed(2),
    device:d.device.kwh.toFixed(3),
    surrounding:d.transit.kwh.toFixed(2),
    pageBg:getComputedStyle(document.documentElement).getPropertyValue('--page-bg').trim()
  };
}())
'@
  Write-Output ("metrics " + ($metrics | ConvertTo-Json -Compress))

  Capture-Tab 'body' 'app-body.png'
  Evaluate-Js "document.getElementById('stage').scrollTop=document.getElementById('stage').scrollHeight" | Out-Null
  Start-Sleep -Milliseconds 350
  Save-Shot 'app-body-detail.png'
  Evaluate-Js "document.getElementById('stage').scrollTop=0;document.getElementById('settingsButton').click();" | Out-Null
  Start-Sleep -Milliseconds 500
  Save-Shot 'app-settings.png'
  Evaluate-Js "document.getElementById('closeProfileButton').click();" | Out-Null
  Start-Sleep -Milliseconds 350

  Capture-Tab 'device' 'app-device.png'
  Evaluate-Js "(function(){document.querySelector('[data-toggle-device=phone]').click();document.getElementById('toast').classList.remove('is-visible');}())" | Out-Null
  Start-Sleep -Milliseconds 250
  Save-Shot 'app-fixed.png'
  Evaluate-Js "(function(){var b=document.querySelector('[data-toggle-device=phone]');b.click();b.click();document.getElementById('toast').classList.remove('is-visible');}())" | Out-Null
  Start-Sleep -Milliseconds 250
  Scroll-Stage '[data-device-card="desktop"]'
  Save-Shot 'app-device-desktop.png'
  Evaluate-Js "document.getElementById('deviceExpandButton').click()" | Out-Null
  Start-Sleep -Milliseconds 250
  Scroll-Stage '[data-device-card="powerbank"]'
  Save-Shot 'app-device-extra.png'
  Evaluate-Js "document.getElementById('deviceExpandButton').click()" | Out-Null
  Start-Sleep -Milliseconds 150

  Capture-Tab 'transit' 'app-transit.png'
  Scroll-Stage '#applianceHeading'
  Save-Shot 'app-appliances.png'
  Scroll-Stage '#travelHeading'
  Save-Shot 'app-travel.png'
  Evaluate-Js "document.getElementById('tripExpandButton').click()" | Out-Null
  Start-Sleep -Milliseconds 250
  Scroll-Stage '[data-trip-card="taxiEv"]'
  Save-Shot 'app-taxis.png'
  Scroll-Stage '#intercityGroup'
  Save-Shot 'app-intercity.png'
  Evaluate-Js "document.getElementById('tripExpandButton').click()" | Out-Null
  Start-Sleep -Milliseconds 150

  Capture-Tab 'overview' 'app-overview.png'
  Scroll-Stage '.history-card'
  Save-Shot 'app-history.png'
  Evaluate-Js "document.getElementById('stage').scrollTop=0" | Out-Null
  Start-Sleep -Milliseconds 250
  Evaluate-Js "document.getElementById('infoButton').click()" | Out-Null
  Start-Sleep -Milliseconds 500
  Save-Shot 'app-info.png'
  Evaluate-Js "document.getElementById('closeInfo').click()" | Out-Null
  Start-Sleep -Milliseconds 350

  $testJs = @'
(function(){
  var M=window.PowerModel;
  function q(id){return document.getElementById(id);}
  function setRange(id,v){var el=q(id);el.value=v;el.dispatchEvent(new Event('input',{bubbles:true}));}
  function setNumber(key,v){var el=document.querySelector('[data-trip-number="'+key+'"]');el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}));}
  function byKey(items,key){for(var i=0;i<items.length;i++){if(items[i].key===key)return items[i];}return null;}
  function enable(kind,key){var el=document.querySelector('[data-toggle-'+kind+'="'+key+'"]');if(el && el.getAttribute('data-state')==='off')el.click();}
  q('resetButton').click();
  var defaultState=PowerApp.getState();
  var defaultCalc=M.calc(defaultState);
  var counts={
    devices:document.querySelectorAll('[data-device-card]').length,
    appliances:document.querySelectorAll('[data-appliance-card]').length,
    sliders:document.querySelectorAll('#transitList .trip-card, #transitExtraList .trip-card').length,
    inputs:document.querySelectorAll('#transitInputList .trip-input-card').length
  };

  enable('device','laptop');
  enable('appliance','ac');
  enable('trip','cityBus');
  enable('trip','evCar');
  enable('trip','plane');
  setRange('device-cap-tablet',12000);
  setRange('device-cap-laptop',100);
  setRange('device-cycles-laptop',0.5);
  setRange('device-power-desktop',500);
  setRange('device-hours-desktop',3);
  setRange('appliance-power-ac',1500);
  setRange('appliance-hours-ac',2);
  setRange('trip-cityBus',50);
  setRange('trip-evCar',20);
  setNumber('plane',800);

  var state=PowerApp.getState();
  var d=M.calc(state);
  PowerApp.setTab('overview');

  var deviceTablet=byKey(d.device.items,'tablet');
  var deviceLaptop=byKey(d.device.items,'laptop');
  var deviceDesktop=byKey(d.device.items,'desktop');
  var applianceAc=byKey(d.appliance.items,'ac');
  var tripBus=byKey(d.transit.items,'cityBus');
  var tripEv=byKey(d.transit.items,'evCar');
  var tripPlane=byKey(d.transit.items,'plane');
  var planeCard=document.querySelector('[data-trip-card="plane"]');
  var planeInput=document.querySelector('[data-trip-number="plane"]');

  var result={
    defaultTotal:defaultCalc.totalKwh.toFixed(2),
    defaultDevice:defaultCalc.device.kwh.toFixed(3),
    defaultSurrounding:defaultCalc.transit.kwh.toFixed(2),
    counts:counts,
    displayedTotal:q('heroKwh').textContent,
    expectedTotal:d.totalKwh.toFixed(2),
    tabletKwh:deviceTablet.kwh.toFixed(4),
    laptopKwh:deviceLaptop.kwh.toFixed(4),
    desktopKwh:deviceDesktop.kwh.toFixed(4),
    acKwh:applianceAc.kwh.toFixed(2),
    busKwh:tripBus.kwh.toFixed(2),
    evKwh:tripEv.kwh.toFixed(2),
    planeKwh:tripPlane.kwh.toFixed(2),
    planeInputValue:planeInput.value,
    planeCardHasSlider:!!planeCard.querySelector('input[type="range"]'),
    gradeLabel:q('gradeLabel').textContent,
    gradeText:q('gradeText').textContent,
    gradeMetric:q('gradeMetric').textContent,
    gradeLevel:q('gradeCard').getAttribute('data-level'),
    historyBars:document.querySelectorAll('#historyBars .history-day').length,
    historyCount:PowerApp.getHistory().length,
    historyTotal:(PowerApp.getHistory()[0]||{}).total,
    profileSummary:q('profileSummary').textContent,
    enabledLaptop:document.querySelector('[data-toggle-device="laptop"]').getAttribute('data-state'),
    enabledAc:document.querySelector('[data-toggle-appliance="ac"]').getAttribute('data-state'),
    enabledPlane:document.querySelector('[data-toggle-trip="plane"]').getAttribute('data-state'),
    fixedSubtotal:q('fixedSubtotal').textContent,
    applianceSubtotal:q('applianceSubtotal').textContent,
    travelSubtotal:q('travelSubtotal').textContent,
    tabletDisplay:document.querySelector('[data-device-kwh="tablet"]').textContent,
    acDisplay:document.querySelector('[data-appliance-kwh="ac"]').textContent,
    planeDisplay:document.querySelector('[data-trip-kwh="plane"]').textContent,
    modalClosed:document.getElementById('infoModal').hidden
  };

  q('resetButton').click();
  document.querySelector('[data-met="7.0"]').click();
  result.presetMet=document.getElementById('metOut').textContent;
  result.presetActive=(document.querySelector('[data-met].is-active')||{}).textContent||'';
  document.querySelector('[data-steps="15000"]').click();
  result.stepPresetMet=document.getElementById('stepsOut').textContent;
  result.stepPresetActive=(document.querySelector('[data-steps].is-active')||{}).textContent||'';
  q('resetButton').click();

  document.getElementById('deviceExpandButton').click();
  result.deviceExpanded=!document.getElementById('deviceExtraList').hidden &&
    document.getElementById('deviceExpandButton').getAttribute('aria-expanded')==='true';
  document.getElementById('deviceExpandButton').click();
  result.deviceCollapsed=document.getElementById('deviceExtraList').hidden;

  var laptopToggle=document.querySelector('[data-toggle-device="laptop"]');
  var laptopCard=document.querySelector('[data-device-card="laptop"]');
  laptopToggle.click();
  result.laptopCycleOn=laptopToggle.getAttribute('data-state');
  result.laptopOnEditable=!laptopCard.querySelector('input[type="range"]').disabled;
  laptopToggle.click();
  result.laptopCycleFixed=laptopToggle.getAttribute('data-state');
  result.laptopFixedFrozen=laptopCard.querySelector('input[type="range"]').disabled;
  result.otherCardEditable=!document.querySelector('[data-device-card="phone"] input[type="range"]').disabled;
  result.lockStored=(JSON.parse(localStorage.getItem('powercalc.itemLocks.v1')||'{}').device||{}).laptop===true;
  laptopToggle.click();
  result.laptopCycleOff=laptopToggle.getAttribute('data-state');
  result.lockCleared=!(JSON.parse(localStorage.getItem('powercalc.itemLocks.v1')||'{}').device||{}).laptop;

  var phoneToggle=document.querySelector('[data-toggle-device="phone"]');
  phoneToggle.click();
  result.phoneCycleFixed=phoneToggle.getAttribute('data-state');
  phoneToggle.click();
  result.phoneCycleOff=phoneToggle.getAttribute('data-state');
  phoneToggle.click();
  result.phoneCycleOn=phoneToggle.getAttribute('data-state');
  q('resetButton').click();

  document.getElementById('settingsButton').click();
  result.settingsOpened=!document.getElementById('profileModal').hidden && !document.getElementById('closeProfileButton').hidden;
  result.defaultSex=PowerApp.getState().sex;
  result.sexOptions=document.querySelectorAll('[data-sex]').length;
  document.querySelector('[data-sex="female"]').click();
  document.getElementById('saveProfileButton').click();
  result.femaleSex=PowerApp.getState().sex;
  result.femaleBmr=PowerModel.calc(PowerApp.getState()).body.bmrKcal.toFixed(1);
  result.femaleSummary=document.getElementById('profileSummary').textContent;
  document.getElementById('settingsButton').click();
  document.querySelector('[data-sex="male"]').click();
  document.getElementById('saveProfileButton').click();
  result.maleSex=PowerApp.getState().sex;
  result.maleBmr=PowerModel.calc(PowerApp.getState()).body.bmrKcal.toFixed(1);

  document.getElementById('settingsButton').click();
  document.getElementById('profileAge').value='31';
  document.getElementById('saveProfileButton').click();
  result.settingsAge=document.getElementById('profileSummary').textContent;
  result.settingsBmr=PowerModel.calc(PowerApp.getState()).body.bmrKcal.toFixed(1);
  document.getElementById('settingsButton').click();
  document.getElementById('profileAge').value='30';
  document.getElementById('saveProfileButton').click();
  result.settingsRestored=document.getElementById('profileSummary').textContent;

  document.getElementById('settingsButton').click();
  result.configSectionVisible=!document.getElementById('profileSettingsExtra').hidden;
  var configToggle=document.getElementById('configLockToggle');
  configToggle.click();
  result.configOn=PowerApp.getState().configLocked;
  result.capacityLocked=document.getElementById('device-cap-phone').disabled;
  result.cyclesEditable=!document.getElementById('device-cycles-phone').disabled;
  result.appliancePowerLocked=document.getElementById('appliance-power-fridge').disabled;
  result.applianceHoursEditable=!document.getElementById('appliance-hours-fridge').disabled;
  result.fixedInputCount=document.querySelectorAll('[data-fixed-number]').length;
  var fixedPhone=document.querySelector('[data-fixed-kind="device"][data-fixed-key="phone"][data-fixed-field="capacity"]');
  var fixedFridge=document.querySelector('[data-fixed-kind="appliance"][data-fixed-key="fridge"][data-fixed-field="watts"]');
  result.fixedCapacityLocked=fixedPhone.disabled;
  result.fixedApplianceLocked=fixedFridge.disabled;
  configToggle.click();
  result.configOff=!PowerApp.getState().configLocked;
  result.capacityUnlocked=!document.getElementById('device-cap-phone').disabled;
  result.fixedCapacityUnlocked=!fixedPhone.disabled;

  fixedPhone.value='4321';
  fixedPhone.dispatchEvent(new Event('change',{bubbles:true}));
  result.manualPhoneCapacity=PowerApp.getState().devices.phone.capacity;
  result.manualPhoneInput=fixedPhone.value;
  var fixedDesktop=document.querySelector('[data-fixed-kind="device"][data-fixed-key="desktop"][data-fixed-field="watts"]');
  fixedDesktop.value='437';
  fixedDesktop.dispatchEvent(new Event('change',{bubbles:true}));
  result.manualDesktopWatts=PowerApp.getState().devices.desktop.watts;
  fixedFridge.value='73';
  fixedFridge.dispatchEvent(new Event('change',{bubbles:true}));
  result.manualFridgeWatts=PowerApp.getState().appliances.fridge.watts;

  var nav=document.querySelector('.tabbar');
  var navStyle=getComputedStyle(nav);
  result.navPosition=navStyle.position;
  result.navRadius=navStyle.borderRadius;
  result.liquidCards=document.querySelectorAll('.liquid-card').length;
  result.liquidBackdrop=(getComputedStyle(document.querySelector('.liquid-card')).backdropFilter||'').indexOf('blur')>=0;
  q('resetButton').click();
  document.getElementById('closeProfileButton').click();

  result.profileStored=(JSON.parse(localStorage.getItem('powercalc.profile.v1')||'{}').complete===true);
  result.profileSex=(JSON.parse(localStorage.getItem('powercalc.profile.v1')||'{}').sex||'');
  result.onboardingDismissed=!document.getElementById('profileModal').classList.contains('is-open');
  return result;
}())
'@
  $test = Evaluate-Js $testJs
  Write-Output ("uitest " + ($test | ConvertTo-Json -Compress -Depth 8))

  Start-Sleep -Milliseconds 400
  Evaluate-Js "document.getElementById('toast').classList.remove('is-visible');" | Out-Null
  Evaluate-Js "window.PowerApp.setTab('overview')" | Out-Null
  Start-Sleep -Milliseconds 350
  Evaluate-Js "(function(){var b=document.querySelector('[data-toggle-trip=taxi]');if(b&&b.getAttribute('data-state')==='off')b.click();var el=document.getElementById('trip-taxi');el.value=8;el.dispatchEvent(new Event('input',{bubbles:true}));document.getElementById('toast').classList.remove('is-visible');}())" | Out-Null
  Start-Sleep -Milliseconds 350
  Save-Shot 'app-overview-warm.png'
  Evaluate-Js "(function(){var el=document.getElementById('trip-taxi');el.value=80;el.dispatchEvent(new Event('input',{bubbles:true}));}())" | Out-Null
  Start-Sleep -Milliseconds 350
  Save-Shot 'app-overview-high.png'
  Evaluate-Js "document.getElementById('resetButton').click();document.getElementById('toast').classList.remove('is-visible');" | Out-Null
  Start-Sleep -Milliseconds 250
  Evaluate-Js "document.getElementById('toast').classList.remove('is-visible');" | Out-Null

  Send-Cdp -Method 'Page.reload' | Out-Null
  Start-Sleep -Milliseconds 1700
  $reloadState = Evaluate-Js @'
(function(){
  return {
    noOnboarding:!document.getElementById('profileModal').classList.contains('is-open'),
    profileSummary:(document.getElementById('profileSummary')||{}).textContent||'',
    persistedProfile:JSON.parse(localStorage.getItem('powercalc.profile.v1')||'{}').complete===true
  };
}())
'@
  Write-Output ("reload " + ($reloadState | ConvertTo-Json -Compress))

  # Simulate reopening on a later day. This script runs at the start of the
  # next document, before app.js, so the unload-time save cannot overwrite it.
  Send-Cdp -Method 'Page.addScriptToEvaluateOnNewDocument' -Params @{
    source = @'
(function(){
  try {
    var s=JSON.parse(localStorage.getItem('powercalc.state.v2')||'{}');
    s.day='2020-01-01';
    s.configLocked=true;
    s.steps=12345;
    s.devices.phone.cycles=2;
    s.devices.phone.capacity=4321;
    s.devices.desktop.watts=437;
    s.appliances.fridge.hours=5;
    s.appliances.fridge.watts=73;
    s.trips.subway=50;
    localStorage.setItem('powercalc.state.v2',JSON.stringify(s));
  } catch (error) {}
}())
'@
  } | Out-Null
  Send-Cdp -Method 'Page.reload' | Out-Null
  Start-Sleep -Milliseconds 1700
  $rollover = Evaluate-Js @'
(function(){
  var s=PowerApp.getState();
  return {
    day:s.day,
    steps:s.steps,
    met:s.met,
    phoneCycles:s.devices.phone.cycles,
    fridgeHours:s.appliances.fridge.hours,
    subway:s.trips.subway,
    configLocked:s.configLocked,
    phoneCapacity:s.devices.phone.capacity,
    desktopWatts:s.devices.desktop.watts,
    fridgeWatts:s.appliances.fridge.watts,
    capacityDisabled:document.getElementById('device-cap-phone').disabled,
    baseline:PowerModel.calc(s).totalKwh.toFixed(2),
    toast:(document.getElementById('toast')||{}).textContent||'',
    profile:(document.getElementById('profileSummary')||{}).textContent||''
  };
}())
'@
  Write-Output ("rollover " + ($rollover | ConvertTo-Json -Compress))
}
finally {
  try { $ws.Dispose() } catch { }
  if ($CloseBrowser) {
    try {
      $t = $targets | Where-Object { $_.type -eq 'page' } | Select-Object -First 1
      $ws2 = [System.Net.WebSockets.ClientWebSocket]::new()
      $ws2.ConnectAsync([Uri]$t.webSocketDebuggerUrl, $ct).GetAwaiter().GetResult()
      $msg = @{ id = 1; method = 'Browser.close'; params = @{} } | ConvertTo-Json -Compress
      $b = [System.Text.Encoding]::UTF8.GetBytes($msg)
      $ws2.SendAsync([System.ArraySegment[byte]]::new($b), [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $ct).GetAwaiter().GetResult()
      $ws2.Dispose()
    } catch { }
  }
}
