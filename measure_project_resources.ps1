param(
    [ValidateRange(1, 1440)]
    [int]$DurationMinutes = 60,

    [ValidateRange(1, 3600)]
    [int]$IntervalSeconds = 5
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$sampleFile = Join-Path (Get-Location) "resource_samples_$timestamp.csv"
$processFile = Join-Path (Get-Location) "resource_processes_$timestamp.csv"
$summaryFile = Join-Path (Get-Location) "resource_summary_$timestamp.csv"

$computer = Get-CimInstance Win32_ComputerSystem
$logicalProcessors = [int]$computer.NumberOfLogicalProcessors
if ($logicalProcessors -lt 1) { $logicalProcessors = 1 }

function Get-ProjectSnapshot {
    # Identify processes running the project's Django management commands.
    $allProcesses = @(Get-CimInstance Win32_Process)
    $selectedPids = New-Object 'System.Collections.Generic.HashSet[int]'

    foreach ($process in $allProcesses) {
        $commandLine = [string]$process.CommandLine
        if ($commandLine -match '(?i)manage\.py.*\b(devserver|monitor_pppoe|runserver)\b') {
            [void]$selectedPids.Add([int]$process.ProcessId)
        }
    }

    # Include descendants of those commands (for example, a child worker).
    $changed = $true
    while ($changed) {
        $changed = $false
        foreach ($process in $allProcesses) {
            $pidValue = [int]$process.ProcessId
            $parentPid = [int]$process.ParentProcessId
            if ($selectedPids.Contains($parentPid) -and
                -not $selectedPids.Contains($pidValue)) {
                [void]$selectedPids.Add($pidValue)
                $changed = $true
            }
        }
    }

    $rows = @()
    foreach ($process in $allProcesses) {
        $pidValue = [int]$process.ProcessId
        if (-not $selectedPids.Contains($pidValue)) { continue }

        $liveProcess = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
        if ($null -eq $liveProcess) { continue }

        $cpuSeconds = 0.0
        if ($null -ne $liveProcess.CPU) {
            $cpuSeconds = [double]$liveProcess.CPU
        }

        $workingMB = [math]::Round(([double]$liveProcess.WorkingSet64 / 1MB), 2)
        $privateMB = [math]::Round(([double]$liveProcess.PrivateMemorySize64 / 1MB), 2)

        $rows += [PSCustomObject]@{
            PID         = $pidValue
            ParentPID   = [int]$process.ParentProcessId
            Name        = [string]$process.Name
            CommandLine = [string]$process.CommandLine
            CPUSeconds  = $cpuSeconds
            WorkingMB   = $workingMB
            PrivateMB   = $privateMB
        }
    }

    # Return individual process objects, not a nested array.
    foreach ($row in $rows) { Write-Output $row }
}

Write-Host ""
Write-Host "=== JUJIEDSO AC MONITORING RESOURCE MEASUREMENT ===" -ForegroundColor Cyan
Write-Host "Duration: $DurationMinutes minute(s)"
Write-Host "Sampling interval: $IntervalSeconds second(s)"
Write-Host "Logical processors: $logicalProcessors"
Write-Host "Output folder: $(Get-Location)"
Write-Host ""
Write-Host "Keep the monitoring application running during the test."
Write-Host "The script measures Django management processes and their descendants."
Write-Host "Separate/shared database or Redis services are not automatically attributed."
Write-Host ""

$startTime = Get-Date
$endTime = $startTime.AddMinutes($DurationMinutes)
$previousCpuByPid = @{}
$previousSampleTime = $null
$sampleCount = 0
$validCpuSamples = 0
$cpuSum = 0.0
$cpuPeak = 0.0
$workingSum = 0.0
$workingPeak = 0.0
$privateSum = 0.0
$privatePeak = 0.0
$noProcessWarnings = 0

while ((Get-Date) -lt $endTime) {
    $sampleTime = Get-Date
    $currentProcesses = @(Get-ProjectSnapshot)

    if ($currentProcesses.Count -eq 0) {
        $noProcessWarnings++
        Write-Warning "No project processes found. Start the project and run this script again if this continues."
        Start-Sleep -Seconds $IntervalSeconds
        continue
    }

    # Sum memory using explicit scalar conversions to avoid PowerShell array coercion.
    $workingTotalMB = 0.0
    $privateTotalMB = 0.0
    foreach ($processRow in $currentProcesses) {
        $workingTotalMB += [double]$processRow.WorkingMB
        $privateTotalMB += [double]$processRow.PrivateMB
    }
    $workingTotalMB = [math]::Round($workingTotalMB, 2)
    $privateTotalMB = [math]::Round($privateTotalMB, 2)

    # Calculate CPU percentage from CPU-time deltas since the previous sample.
    # Percent is normalized to total logical CPU capacity (0-100%).
    $cpuPercent = $null
    if ($null -ne $previousSampleTime) {
        $elapsedSeconds = ($sampleTime - $previousSampleTime).TotalSeconds
        $cpuDeltaSeconds = 0.0

        if ($elapsedSeconds -gt 0) {
            foreach ($processRow in $currentProcesses) {
                $pidKey = [string]$processRow.PID
                if ($previousCpuByPid.ContainsKey($pidKey)) {
                    $delta = [double]$processRow.CPUSeconds - [double]$previousCpuByPid[$pidKey]
                    if ($delta -gt 0) { $cpuDeltaSeconds += $delta }
                }
            }

            $cpuPercent = [math]::Round(
                (100.0 * $cpuDeltaSeconds / ($elapsedSeconds * $logicalProcessors)), 2
            )
        }
    }

    $sampleCount++

    $sampleRow = [PSCustomObject]@{
        Timestamp          = $sampleTime.ToString("yyyy-MM-dd HH:mm:ss")
        ProjectCPU_Pct     = $cpuPercent
        WorkingSet_MB      = $workingTotalMB
        PrivateMemory_MB   = $privateTotalMB
        ProcessCount       = $currentProcesses.Count
    }
    $sampleRow | Export-Csv -LiteralPath $sampleFile -NoTypeInformation -Append

    foreach ($processRow in $currentProcesses) {
        [PSCustomObject]@{
            Timestamp        = $sampleTime.ToString("yyyy-MM-dd HH:mm:ss")
            PID              = $processRow.PID
            ParentPID        = $processRow.ParentPID
            Process          = $processRow.Name
            WorkingSet_MB    = $processRow.WorkingMB
            PrivateMemory_MB = $processRow.PrivateMB
            CPUSeconds       = $processRow.CPUSeconds
            CommandLine      = $processRow.CommandLine
        } | Export-Csv -LiteralPath $processFile -NoTypeInformation -Append
    }

    if ($null -ne $cpuPercent) {
        $validCpuSamples++
        $cpuSum += [double]$cpuPercent
        $cpuPeak = [math]::Max($cpuPeak, [double]$cpuPercent)
    }

    $workingSum += $workingTotalMB
    $workingPeak = [math]::Max($workingPeak, $workingTotalMB)
    $privateSum += $privateTotalMB
    $privatePeak = [math]::Max($privatePeak, $privateTotalMB)

    $previousCpuByPid = @{}
    foreach ($processRow in $currentProcesses) {
        $previousCpuByPid[[string]$processRow.PID] = [double]$processRow.CPUSeconds
    }
    $previousSampleTime = $sampleTime

    Clear-Host
    Write-Host "JUJIEDSO AC MONITORING - LIVE RESOURCE USAGE" -ForegroundColor Cyan
    Write-Host "Started: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "Elapsed: $([math]::Round(($sampleTime - $startTime).TotalMinutes, 1)) / $DurationMinutes minutes"
    if ($null -eq $cpuPercent) {
        Write-Host "Project CPU: collecting baseline..."
    } else {
        Write-Host "Project CPU: $cpuPercent % of total logical CPU capacity"
    }
    Write-Host "Project working set: $workingTotalMB MB"
    Write-Host "Project private memory: $privateTotalMB MB"
    Write-Host "Processes counted: $($currentProcesses.Count)"
    Write-Host "Samples recorded: $sampleCount"
    Write-Host ""
    Write-Host "Sample CSV:   $sampleFile"
    Write-Host "Process CSV:  $processFile"

    $remaining = ($endTime - (Get-Date)).TotalSeconds
    if ($remaining -gt 0) {
        Start-Sleep -Seconds ([math]::Max(1, [math]::Min($IntervalSeconds, [math]::Ceiling($remaining))))
    }
}

$finishTime = Get-Date

if ($sampleCount -gt 0) {
    $averageWorkingMB = [math]::Round($workingSum / $sampleCount, 2)
    $averagePrivateMB = [math]::Round($privateSum / $sampleCount, 2)
    $averageCpuPercent = $null
    if ($validCpuSamples -gt 0) {
        $averageCpuPercent = [math]::Round($cpuSum / $validCpuSamples, 2)
    }

    [PSCustomObject]@{
        Project               = "Jujiedso AC Monitoring"
        StartTime             = $startTime.ToString("yyyy-MM-dd HH:mm:ss")
        EndTime               = $finishTime.ToString("yyyy-MM-dd HH:mm:ss")
        DurationMinutes       = [math]::Round(($finishTime - $startTime).TotalMinutes, 2)
        SamplingIntervalSec   = $IntervalSeconds
        Samples               = $sampleCount
        ValidCPUSamples       = $validCpuSamples
        LogicalProcessors     = $logicalProcessors
        AverageCPU_Pct        = $averageCpuPercent
        PeakCPU_Pct           = $(if ($validCpuSamples -gt 0) { $cpuPeak } else { $null })
        AverageWorkingSet_MB  = $averageWorkingMB
        PeakWorkingSet_MB     = $workingPeak
        AveragePrivateMemory_MB = $averagePrivateMB
        PeakPrivateMemory_MB  = $privatePeak
        NoProcessWarnings     = $noProcessWarnings
        MeasurementNote       = "CPU is normalized to total logical CPU capacity. RAM sums process working sets/private memory. Shared service usage is excluded unless explicitly attributed."
    } | Export-Csv -LiteralPath $summaryFile -NoTypeInformation

    Write-Host ""
    Write-Host "Measurement completed." -ForegroundColor Green
    Write-Host "Summary:  $summaryFile"
    Write-Host "Samples:  $sampleFile"
    Write-Host "Details:  $processFile"
    Write-Host ""
    Write-Host "Note: review the process CSV to verify all project components were included." -ForegroundColor Yellow
} else {
    Write-Warning "No samples were collected. No summary was created."
}
