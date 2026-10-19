Add-Type @"
using System; using System.Runtime.InteropServices;
public class FocusWin { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c); [DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, uint f, UIntPtr e); }
"@
$p = Get-Process Unity -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "Warfare1347*" } | Select-Object -First 1
if (-not $p) { "unity not running"; exit 1 }
[FocusWin]::ShowWindow($p.MainWindowHandle, 3) | Out-Null
[FocusWin]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero); [FocusWin]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)
"focused: " + [FocusWin]::SetForegroundWindow($p.MainWindowHandle)
