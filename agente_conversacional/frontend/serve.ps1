param([int]$Port = 8080)

$Listener = New-Object System.Net.HttpListener
$Listener.Prefixes.Add("http://127.0.0.1:$Port/")
$Listener.Start()
Write-Host "Servidor do chat ativo em: http://127.0.0.1:$Port/"

$Root = $PSScriptRoot

try {
    while ($Listener.IsListening) {
        $Context = $Listener.GetContext()
        $Request = $Context.Request
        $Response = $Context.Response

        $Path = $Request.Url.LocalPath.TrimStart('/')
        if ([string]::IsNullOrEmpty($Path)) { $Path = "index.html" }
        $FilePath = [System.IO.Path]::Combine($Root, $Path)

        if (Test-Path $FilePath -PathType Leaf) {
            $Bytes = [System.IO.File]::ReadAllBytes($FilePath)
            $Ext = [System.IO.Path]::GetExtension($FilePath).ToLower()
            switch ($Ext) {
                ".html" { $Response.ContentType = "text/html; charset=utf-8" }
                ".css"  { $Response.ContentType = "text/css; charset=utf-8" }
                ".js"   { $Response.ContentType = "application/javascript; charset=utf-8" }
                ".json" { $Response.ContentType = "application/json; charset=utf-8" }
                default { $Response.ContentType = "application/octet-stream" }
            }
            $Response.AddHeader("Access-Control-Allow-Origin", "*")
            $Response.ContentLength64 = $Bytes.Length
            $Response.OutputStream.Write($Bytes, 0, $Bytes.Length)
        } else {
            $Response.StatusCode = 404
        }
        $Response.OutputStream.Close()
    }
} finally {
    $Listener.Stop()
}
