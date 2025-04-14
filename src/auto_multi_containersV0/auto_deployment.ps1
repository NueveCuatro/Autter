Write-Host "---------- DOCKER AI Pipeline ----------" -ForegroundColor Cyan

if ($args[0] -eq "--build") {
    Write-Host "Deployment with Building Image Steps" -ForegroundColor Green
    docker build -f Dockerfile.base -t demo_base_image .

    Set-Location -Path "./modules"
    docker compose up --build
} else {
    Write-Host "Deploying without rebuilding images" -ForegroundColor Yellow

    Set-Location -Path "./modules"
    docker compose up
}
