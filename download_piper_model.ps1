# Piper TTS 模型下载脚本 (Windows PowerShell)
# 用于快速下载推荐的语音模型

$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Green
Write-Host "Piper TTS 模型下载脚本" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# 创建模型目录
if (-not (Test-Path "models")) {
    New-Item -ItemType Directory -Path "models" | Out-Null
}
Set-Location "models"

Write-Host "请选择要下载的模型:"
Write-Host ""
Write-Host "=== 英文模型 ===" -ForegroundColor Blue
Write-Host "1) 英文 lessac - medium (推荐，~80MB)"
Write-Host "2) 英文 lessac - small (轻量，~30MB)"
Write-Host "3) 英文 amy - medium (女声，~80MB)"
Write-Host ""
Write-Host "=== 中文模型 ===" -ForegroundColor Blue
Write-Host "4) 中文 花檐 - medium (推荐，~80MB)"
Write-Host "5) 中文 花檐 - small (轻量，~30MB)"
Write-Host "6) 中文 小雅 - medium (女声，~80MB)"
Write-Host "7) 中文 朝文 - medium (~80MB)"
Write-Host ""
Write-Host "=== 批量下载 ===" -ForegroundColor Blue
Write-Host "8) 下载全部英文模型"
Write-Host "9) 下载全部中文模型"
Write-Host "10) 下载全部模型"
Write-Host ""

$choice = Read-Host "请输入选项 (1-10)"

function Download-Model {
    param(
        [string]$Url,
        [string]$FileName
    )

    Write-Host "下载 $FileName..." -ForegroundColor Yellow
    try {
        # 使用 curl 下载（Windows 10+ 内置）
        $curlArgs = @("-L", "-o", $FileName, "-C", "-", $Url)
        & curl $curlArgs
        Write-Host "  完成: $FileName" -ForegroundColor Green
    } catch {
        Write-Host "  失败: $FileName - $_" -ForegroundColor Red
    }
}

function Download-English-Models {
    param([switch]$All)

    if ($All) {
        Write-Host "下载全部英文模型..." -ForegroundColor Yellow
    }

    Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -FileName "en_US-lessac-medium.onnx"
    Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -FileName "en_US-lessac-medium.onnx.json"

    if ($All) {
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/small/en_US-lessac-small.onnx" -FileName "en_US-lessac-small.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/small/en_US-lessac-small.onnx.json" -FileName "en_US-lessac-small.onnx.json"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx" -FileName "en_US-amy-medium.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json" -FileName "en_US-amy-medium.onnx.json"
    }
}

function Download-Chinese-Models {
    param([switch]$All)

    if ($All) {
        Write-Host "下载全部中文模型..." -ForegroundColor Yellow
    }

    Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx" -FileName "zh_CN-huayan-medium.onnx"
    Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json" -FileName "zh_CN-huayan-medium.onnx.json"

    if ($All) {
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/small/zh_CN-huayan-small.onnx" -FileName "zh_CN-huayan-small.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/small/zh_CN-huayan-small.onnx.json" -FileName "zh_CN-huayan-small.onnx.json"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx" -FileName "zh_CN-xiao_ya-medium.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx.json" -FileName "zh_CN-xiao_ya-medium.onnx.json"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx" -FileName "zh_CN-chaowen-medium.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx.json" -FileName "zh_CN-chaowen-medium.onnx.json"
    }
}

switch ($choice) {
    "1" {
        Write-Host "下载英文 lessac medium 模型..." -ForegroundColor Yellow
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -FileName "en_US-lessac-medium.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -FileName "en_US-lessac-medium.onnx.json"
    }
    "2" {
        Write-Host "下载英文 lessac small 模型..." -ForegroundColor Yellow
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/small/en_US-lessac-small.onnx" -FileName "en_US-lessac-small.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/small/en_US-lessac-small.onnx.json" -FileName "en_US-lessac-small.onnx.json"
    }
    "3" {
        Write-Host "下载英文 amy medium 模型（女声）..." -ForegroundColor Yellow
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx" -FileName "en_US-amy-medium.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json" -FileName "en_US-amy-medium.onnx.json"
    }
    "4" {
        Write-Host "下载中文 花檐 medium 模型..." -ForegroundColor Yellow
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx" -FileName "zh_CN-huayan-medium.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json" -FileName "zh_CN-huayan-medium.onnx.json"
    }
    "5" {
        Write-Host "下载中文 花檐 small 模型..." -ForegroundColor Yellow
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/small/zh_CN-huayan-small.onnx" -FileName "zh_CN-huayan-small.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/small/zh_CN-huayan-small.onnx.json" -FileName "zh_CN-huayan-small.onnx.json"
    }
    "6" {
        Write-Host "下载中文 小雅 medium 模型（女声）..." -ForegroundColor Yellow
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx" -FileName "zh_CN-xiao_ya-medium.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx.json" -FileName "zh_CN-xiao_ya-medium.onnx.json"
    }
    "7" {
        Write-Host "下载中文 朝文 medium 模型..." -ForegroundColor Yellow
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx" -FileName "zh_CN-chaowen-medium.onnx"
        Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx.json" -FileName "zh_CN-chaowen-medium.onnx.json"
    }
    "8" {
        Download-English-Models -All
    }
    "9" {
        Download-Chinese-Models -All
    }
    "10" {
        Write-Host "下载全部模型..." -ForegroundColor Yellow
        Download-English-Models -All
        Download-Chinese-Models -All
    }
    default {
        Write-Host "无效选项" -ForegroundColor Red
        Set-Location ".."
        exit 1
    }
}

Set-Location ".."

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "下载完成！" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "模型文件已下载到 models/ 目录"
Write-Host ""
Write-Host "已下载的模型:"
Get-ChildItem -Path "models\*.onnx" -ErrorAction SilentlyContinue | ForEach-Object {
    $size = [math]::Round($_.Length / 1MB, 2)
    Write-Host "  $($_.Name) ($($size)MB)"
}
Write-Host ""
Write-Host "下一步:"
Write-Host "1. 运行测试: python test_piper.py"
Write-Host "2. 启动 GUI: python -m novel_reader"
Write-Host ""
