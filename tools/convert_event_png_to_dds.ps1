param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$source = [System.Drawing.Image]::FromFile($InputPath)
$width = 1240
$height = 700
$bitmap = New-Object System.Drawing.Bitmap($width, $height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
try {
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.DrawImage($source, 0, 0, $width, $height)
    } finally {
        $graphics.Dispose()
    }

    $rect = New-Object System.Drawing.Rectangle(0, 0, $width, $height)
    $data = $bitmap.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $pixels = New-Object byte[] ($width * $height * 4)
        [System.Runtime.InteropServices.Marshal]::Copy($data.Scan0, $pixels, 0, $pixels.Length)
    } finally {
        $bitmap.UnlockBits($data)
    }

    $stream = [System.IO.File]::Create($OutputPath)
    try {
        $writer = New-Object System.IO.BinaryWriter($stream)
        $writer.Write([System.Text.Encoding]::ASCII.GetBytes('DDS '))
        $writer.Write([uint32]124)
        $writer.Write([uint32]0x100F) # caps, height, width, pitch, pixel format
        $writer.Write([uint32]$height)
        $writer.Write([uint32]$width)
        $writer.Write([uint32]($width * 4))
        $writer.Write([uint32]0)
        $writer.Write([uint32]0)
        1..11 | ForEach-Object { $writer.Write([uint32]0) }
        $writer.Write([uint32]32) # DDS_PIXELFORMAT size
        $writer.Write([uint32]0x41) # RGB and alpha
        $writer.Write([uint32]0)
        $writer.Write([uint32]32)
        $writer.Write([uint32]0x00FF0000) # red
        $writer.Write([uint32]0x0000FF00) # green
        $writer.Write([uint32]0x000000FF) # blue
        $writer.Write([uint32]4278190080) # alpha
        $writer.Write([uint32]0x1000) # texture
        1..4 | ForEach-Object { $writer.Write([uint32]0) }
        $writer.Write($pixels)
    } finally {
        $stream.Dispose()
    }
} finally {
    $bitmap.Dispose()
    $source.Dispose()
}
