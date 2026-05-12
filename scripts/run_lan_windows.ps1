$ErrorActionPreference = "Stop"

$addressInfo = Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object {
    $_.IPAddress -notlike "127.*" -and
    $_.IPAddress -notlike "169.254.*" -and
    $_.PrefixOrigin -ne "WellKnown" -and
    $_.InterfaceAlias -notlike "vEthernet*"
  }

$fallbackAddressInfo = Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object {
    $_.IPAddress -notlike "127.*" -and
    $_.IPAddress -notlike "169.254.*" -and
    $_.PrefixOrigin -ne "WellKnown"
  }

$addresses = @($addressInfo | Select-Object -ExpandProperty IPAddress)
if (-not $addresses) {
  $addresses = @($fallbackAddressInfo | Select-Object -ExpandProperty IPAddress)
}
$primaryAddress = $addresses | Select-Object -First 1
if ($primaryAddress) {
  $env:KLASBOT_PUBLIC_BASE_URL = "http://$primaryAddress`:8000"
}

Write-Host "Starting KlasBot on all local network interfaces..."
Write-Host "Open on this laptop: http://127.0.0.1:8000"
foreach ($address in $addresses) {
  Write-Host "PDF share links can be opened from a phone at: http://$address`:8000/share/<token>"
}
Write-Host "The full KlasBot app is intentionally blocked from phones; use it only on this laptop."
Write-Host "If the phone cannot connect, allow Python through Windows Defender Firewall for Private networks."

python -m uvicorn klasbot.main:app --host 0.0.0.0 --port 8000
