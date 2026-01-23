Add-Type @"
using System;
using System.Runtime.InteropServices;
public class User32 {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
    [DllImport("user32.dll")]
    public static extern int GetWindowThreadProcessId(IntPtr hWnd, out int processId);
}
"@

$hwnd = [User32]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 256
[User32]::GetWindowText($hwnd, $sb, 256) | Out-Null
$processId = 0
[User32]::GetWindowThreadProcessId($hwnd, [ref]$processId) | Out-Null
$process = Get-Process -Id $processId -ErrorAction SilentlyContinue

$result = @{
    processName = $process.ProcessName
    windowTitle = $sb.ToString()
} | ConvertTo-Json -Compress

Write-Output $result
