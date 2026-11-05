# Offline EVTX -> JSONL. Requires Windows PowerShell and installed event-provider support.
param(
    [Parameter(Mandatory=$true)][string]$InputPath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$stream = [System.IO.File]::Open($OutputPath, [System.IO.FileMode]::CreateNew)
$writer = [System.IO.StreamWriter]::new($stream, [System.Text.UTF8Encoding]::new($false))
try {
    Get-WinEvent -Path $InputPath -Oldest | ForEach-Object {
        [xml]$xml = $_.ToXml()
        $record = [ordered]@{
            Provider = $_.ProviderName
            Id = $_.Id
            RecordId = $_.RecordId
            SystemTime = [string]$xml.Event.System.TimeCreated.SystemTime
            Xml = $_.ToXml()
        }
        $writer.WriteLine(($record | ConvertTo-Json -Compress -Depth 5))
    }
} finally {
    $writer.Dispose()
}
