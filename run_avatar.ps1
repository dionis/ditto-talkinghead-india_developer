# Run the real-time avatar with Gemini AI
# Make sure to set your API key first!

# Check for API key
if (-not $env:GOOGLE_API_KEY) {
    Write-Host "ERROR: GOOGLE_API_KEY environment variable not set." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please set it first with:"
    Write-Host "  `$env:GOOGLE_API_KEY=`"your-api-key-here`"" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Get an API key at: https://aistudio.google.com/apikey"
    exit 1
}

# Navigate to project directory
Set-Location "A:\local avatar"

# Activate conda and run
conda activate ditto
python realtime_avatar.py --image "./example/image.png" @args
