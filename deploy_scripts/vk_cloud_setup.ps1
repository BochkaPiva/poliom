# POLIOM HR Assistant - VK Cloud Deployment Script (PowerShell)
# Автоматизация развертывания на VK Cloud

param(
    [switch]$SkipImageBuild,
    [switch]$SkipTests,
    [string]$ConfigFile = "",
    [ValidateSet("mvp", "startup", "business", "enterprise")]
    [string]$ConfigSize = "startup"
)

# Настройка цветов вывода
function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

# Получение конфигурации ресурсов
function Get-ResourceConfig {
    param([string]$Size)
    
    switch ($Size) {
        "mvp" {
            return @{
                BackendReplicas = 1
                FrontendReplicas = 1
                BackendCPU = "100m"
                BackendMemory = "256Mi"
                BackendCPULimit = "200m"
                BackendMemoryLimit = "512Mi"
                FrontendCPU = "50m"
                FrontendMemory = "128Mi"
                FrontendCPULimit = "100m"
                FrontendMemoryLimit = "256Mi"
                Description = "MVP/Тестовая версия (~3,500₽/мес)"
            }
        }
        "startup" {
            return @{
                BackendReplicas = 2
                FrontendReplicas = 1
                BackendCPU = "150m"
                BackendMemory = "384Mi"
                BackendCPULimit = "300m"
                BackendMemoryLimit = "768Mi"
                FrontendCPU = "75m"
                FrontendMemory = "192Mi"
                FrontendCPULimit = "150m"
                FrontendMemoryLimit = "384Mi"
                Description = "Стартап версия (~6,500₽/мес)"
            }
        }
        "business" {
            return @{
                BackendReplicas = 2
                FrontendReplicas = 2
                BackendCPU = "250m"
                BackendMemory = "512Mi"
                BackendCPULimit = "500m"
                BackendMemoryLimit = "1Gi"
                FrontendCPU = "100m"
                FrontendMemory = "256Mi"
                FrontendCPULimit = "200m"
                FrontendMemoryLimit = "512Mi"
                Description = "Бизнес версия (~12,000₽/мес)"
            }
        }
        "enterprise" {
            return @{
                BackendReplicas = 3
                FrontendReplicas = 2
                BackendCPU = "250m"
                BackendMemory = "512Mi"
                BackendCPULimit = "500m"
                BackendMemoryLimit = "1Gi"
                FrontendCPU = "100m"
                FrontendMemory = "256Mi"
                FrontendCPULimit = "200m"
                FrontendMemoryLimit = "512Mi"
                Description = "Enterprise версия (~27,500₽/мес)"
            }
        }
        default {
            return Get-ResourceConfig -Size "startup"
        }
    }
}

# Показать информацию о конфигурации
function Show-ConfigInfo {
    param([string]$Size)
    
    $config = Get-ResourceConfig -Size $Size
    
    Write-Host "🎯 Выбранная конфигурация: $($config.Description)" -ForegroundColor Cyan
    Write-Host "   Backend реплики: $($config.BackendReplicas)" -ForegroundColor Gray
    Write-Host "   Frontend реплики: $($config.FrontendReplicas)" -ForegroundColor Gray
    Write-Host "   Ресурсы оптимизированы для экономии" -ForegroundColor Gray
    Write-Host ""
    
    # Показать стоимость с welcome bonus
    $costs = @{
        "mvp" = @{ Monthly = 3500; WithBonus = "БЕСПЛАТНО + остаток 1,500₽" }
        "startup" = @{ Monthly = 6500; WithBonus = "1,500₽" }
        "business" = @{ Monthly = 12000; WithBonus = "7,000₽" }
        "enterprise" = @{ Monthly = 27500; WithBonus = "22,500₽" }
    }
    
    $cost = $costs[$Size]
    Write-Host "💰 Стоимость:" -ForegroundColor Green
    Write-Host "   Ежемесячно: ~$($cost.Monthly)₽" -ForegroundColor Green
    Write-Host "   Первый месяц с bonus: $($cost.WithBonus)" -ForegroundColor Green
    Write-Host ""
}

# Проверка зависимостей
function Test-Dependencies {
    Write-Info "Проверка зависимостей..."
    
    $dependencies = @("kubectl", "docker")
    $missing = @()
    
    foreach ($dep in $dependencies) {
        if (!(Get-Command $dep -ErrorAction SilentlyContinue)) {
            $missing += $dep
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-ErrorMsg "Не найдены следующие зависимости: $($missing -join ', ')"
        Write-Info "Установите недостающие компоненты:"
        Write-Info "- kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/"
        Write-Info "- Docker Desktop: https://www.docker.com/products/docker-desktop"
        exit 1
    }
    
    Write-Success "Все зависимости найдены"
}

# Настройка переменных окружения
function Set-Environment {
    Write-Info "Настройка переменных окружения..."
    
    if ($ConfigFile -and (Test-Path $ConfigFile)) {
        Write-Info "Загрузка конфигурации из файла: $ConfigFile"
        $config = Get-Content $ConfigFile | ConvertFrom-Json
        
        $global:VK_PROJECT_NAME = $config.VK_PROJECT_NAME
        $global:POSTGRES_HOST = $config.POSTGRES_HOST
        $global:POSTGRES_USER = $config.POSTGRES_USER
        $global:POSTGRES_PASSWORD = $config.POSTGRES_PASSWORD
        $global:POSTGRES_DB = $config.POSTGRES_DB
        $global:S3_ACCESS_KEY = $config.S3_ACCESS_KEY
        $global:S3_SECRET_KEY = $config.S3_SECRET_KEY
        $global:S3_BUCKET_NAME = $config.S3_BUCKET_NAME
        $global:S3_ENDPOINT = $config.S3_ENDPOINT
    } else {
        # Интерактивный ввод
        $global:VK_PROJECT_NAME = Read-Host "Введите название проекта VK Cloud"
        $global:POSTGRES_HOST = Read-Host "Введите endpoint PostgreSQL"
        $global:POSTGRES_USER = Read-Host "Введите имя пользователя PostgreSQL"
        $global:POSTGRES_PASSWORD = Read-Host "Введите пароль PostgreSQL" -AsSecureString | ConvertFrom-SecureString -AsPlainText
        $global:POSTGRES_DB = Read-Host "Введите название базы данных"
        $global:S3_ACCESS_KEY = Read-Host "Введите Access Key для Object Storage"
        $global:S3_SECRET_KEY = Read-Host "Введите Secret Key для Object Storage" -AsSecureString | ConvertFrom-SecureString -AsPlainText
        $global:S3_BUCKET_NAME = Read-Host "Введите имя bucket"
        $global:S3_ENDPOINT = Read-Host "Введите endpoint Object Storage"
    }
    
    Write-Success "Переменные окружения настроены"
}

# Создание namespace
function New-Namespace {
    Write-Info "Создание namespace poliom-hr..."
    
    try {
        kubectl create namespace poliom-hr --dry-run=client -o yaml | kubectl apply -f -
        kubectl config set-context --current --namespace=poliom-hr
        Write-Success "Namespace создан и установлен как текущий"
    } catch {
        Write-ErrorMsg "Ошибка создания namespace: $_"
        exit 1
    }
}

# Создание ConfigMap
function New-ConfigMap {
    Write-Info "Создание ConfigMap..."
    
    $configMapYaml = @"
apiVersion: v1
kind: ConfigMap
metadata:
  name: poliom-config
  namespace: poliom-hr
data:
  POSTGRES_HOST: "$global:POSTGRES_HOST"
  POSTGRES_DB: "$global:POSTGRES_DB"
  POSTGRES_PORT: "5432"
  S3_ENDPOINT: "$global:S3_ENDPOINT"
  S3_BUCKET_NAME: "$global:S3_BUCKET_NAME"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  CONFIG_SIZE: "$ConfigSize"
"@

    $configMapYaml | kubectl apply -f -
    Write-Success "ConfigMap создан с конфигурацией: $ConfigSize"
}

# Создание Secret
function New-Secret {
    Write-Info "Создание Secret..."
    
    # Генерация JWT секрета
    $jwtSecret = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString()))
    
    try {
        kubectl create secret generic poliom-secrets `
            --from-literal=POSTGRES_USER="$global:POSTGRES_USER" `
            --from-literal=POSTGRES_PASSWORD="$global:POSTGRES_PASSWORD" `
            --from-literal=S3_ACCESS_KEY="$global:S3_ACCESS_KEY" `
            --from-literal=S3_SECRET_KEY="$global:S3_SECRET_KEY" `
            --from-literal=JWT_SECRET="$jwtSecret" `
            --namespace=poliom-hr `
            --dry-run=client -o yaml | kubectl apply -f -
        
        Write-Success "Secret создан"
    } catch {
        Write-ErrorMsg "Ошибка создания Secret: $_"
        exit 1
    }
}

# Развертывание Redis с оптимизированными ресурсами
function Deploy-Redis {
    Write-Info "Развертывание Redis..."
    
    $config = Get-ResourceConfig -Size $ConfigSize
    
    # Определяем ресурсы Redis в зависимости от размера
    $redisMemory = switch ($ConfigSize) {
        "mvp" { "128Mi"; "256Mi" }
        "startup" { "256Mi"; "512Mi" }
        default { "256Mi"; "512Mi" }
    }
    
    $redisYaml = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: poliom-hr
  labels:
    app: redis
    config-size: $ConfigSize
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "$($redisMemory[0])"
            cpu: "50m"
          limits:
            memory: "$($redisMemory[1])"
            cpu: "100m"
        command: ["redis-server"]
        args: ["--maxmemory", "$(($redisMemory[0] -replace 'Mi',''))m", "--maxmemory-policy", "allkeys-lru"]
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: poliom-hr
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
"@

    $redisYaml | kubectl apply -f -
    Write-Success "Redis развернут с оптимизированной конфигурацией"
}

# Создание HPA (Horizontal Pod Autoscaler)
function New-HPA {
    Write-Info "Создание автомасштабирования..."
    
    $config = Get-ResourceConfig -Size $ConfigSize
    
    $hpaYaml = @"
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: poliom-backend-hpa
  namespace: poliom-hr
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: poliom-backend
  minReplicas: $($config.BackendReplicas)
  maxReplicas: $([math]::max(3, $config.BackendReplicas * 2))
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: poliom-frontend-hpa
  namespace: poliom-hr
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: poliom-frontend
  minReplicas: $($config.FrontendReplicas)
  maxReplicas: $([math]::max(2, $config.FrontendReplicas * 2))
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
"@

    $hpaYaml | kubectl apply -f -
    Write-Success "Автомасштабирование настроено"
}

# Проверка подключения к PostgreSQL
function Test-PostgreSQL {
    if ($SkipTests) {
        Write-Warning "Пропуск тестов PostgreSQL"
        return
    }
    
    Write-Info "Проверка подключения к PostgreSQL..."
    
    try {
        $connectionString = "postgresql://$global:POSTGRES_USER`:$global:POSTGRES_PASSWORD@$global:POSTGRES_HOST`:5432/$global:POSTGRES_DB"
        
        kubectl run postgres-test --rm -i --restart=Never --image=postgres:16 -- `
            psql $connectionString `
            -c "SELECT version();" `
            -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
        
        Write-Success "Подключение к PostgreSQL успешно"
    } catch {
        Write-ErrorMsg "Ошибка подключения к PostgreSQL: $_"
        exit 1
    }
}

# Сборка Docker образов
function Build-Images {
    if ($SkipImageBuild) {
        Write-Warning "Пропуск сборки образов"
        return
    }
    
    Write-Info "Сборка Docker образов..."
    
    try {
        # Backend
        Write-Info "Сборка backend образа..."
        docker build -t poliom-backend:latest -f backend/Dockerfile .
        
        # Frontend
        Write-Info "Сборка frontend образа..."
        docker build -t poliom-frontend:latest -f frontend/Dockerfile .
        
        Write-Success "Образы собраны"
        
        # Опциональная загрузка в registry
        $uploadToRegistry = Read-Host "Хотите загрузить образы в registry? (y/n)"
        if ($uploadToRegistry -eq "y" -or $uploadToRegistry -eq "Y") {
            $registryUrl = Read-Host "Введите URL registry"
            
            docker tag poliom-backend:latest "$registryUrl/poliom-backend:latest"
            docker tag poliom-frontend:latest "$registryUrl/poliom-frontend:latest"
            docker push "$registryUrl/poliom-backend:latest"
            docker push "$registryUrl/poliom-frontend:latest"
            
            Write-Success "Образы загружены в registry"
        }
    } catch {
        Write-ErrorMsg "Ошибка сборки образов: $_"
        exit 1
    }
}

# Применение конфигураций Kubernetes
function Deploy-Application {
    Write-Info "Применение конфигураций Kubernetes..."
    
    $k8sFiles = @("k8s/backend-deployment.yaml", "k8s/frontend-deployment.yaml", "k8s/ingress.yaml")
    
    foreach ($file in $k8sFiles) {
        if (Test-Path $file) {
            kubectl apply -f $file
            Write-Success "Применен файл: $file"
        } else {
            Write-Warning "Файл не найден: $file"
        }
    }
}

# Проверка статуса развертывания
function Test-DeploymentStatus {
    Write-Info "Проверка статуса развертывания..."
    
    Write-Info "Pods:"
    kubectl get pods -n poliom-hr
    
    Write-Info "Services:"
    kubectl get services -n poliom-hr
    
    Write-Info "Ingress:"
    kubectl get ingress -n poliom-hr
    
    Write-Info "Ожидание готовности подов..."
    kubectl wait --for=condition=ready pod --all -n poliom-hr --timeout=300s
    
    Write-Success "Развертывание завершено!"
}

# Вывод информации о доступе
function Show-AccessInfo {
    Write-Info "Информация о доступе:"
    
    try {
        $ingressIp = kubectl get ingress -n poliom-hr -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>$null
        if (-not $ingressIp) { $ingressIp = "не найден" }
    } catch {
        $ingressIp = "не найден"
    }
    
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host "🌐 IP адрес приложения: $ingressIp" -ForegroundColor Cyan
    Write-Host "📊 Мониторинг: http://$ingressIp/grafana" -ForegroundColor Cyan
    Write-Host "🔍 Логи: kubectl logs -n poliom-hr -l app=poliom-backend" -ForegroundColor Cyan
    Write-Host "⚙️  Статус: kubectl get all -n poliom-hr" -ForegroundColor Cyan
    Write-Host "==================================" -ForegroundColor Cyan
}

# Сохранение конфигурации
function Save-Configuration {
    $saveConfig = Read-Host "Сохранить конфигурацию для повторного использования? (y/n)"
    if ($saveConfig -eq "y" -or $saveConfig -eq "Y") {
        $config = @{
            VK_PROJECT_NAME = $global:VK_PROJECT_NAME
            POSTGRES_HOST = $global:POSTGRES_HOST
            POSTGRES_USER = $global:POSTGRES_USER
            POSTGRES_PASSWORD = $global:POSTGRES_PASSWORD
            POSTGRES_DB = $global:POSTGRES_DB
            S3_ACCESS_KEY = $global:S3_ACCESS_KEY
            S3_SECRET_KEY = $global:S3_SECRET_KEY
            S3_BUCKET_NAME = $global:S3_BUCKET_NAME
            S3_ENDPOINT = $global:S3_ENDPOINT
        }
        
        $configPath = "vk-cloud-config.json"
        $config | ConvertTo-Json | Out-File -FilePath $configPath -Encoding UTF8
        Write-Success "Конфигурация сохранена в файл: $configPath"
        Write-Warning "ВНИМАНИЕ: Файл содержит пароли! Не загружайте его в публичные репозитории."
    }
}

# Показать экономию
function Show-CostSavings {
    Write-Host "💰 Экономия относительно Enterprise конфигурации:" -ForegroundColor Green
    
    $savings = @{
        "mvp" = @{ Percent = 87; Monthly = 24000 }
        "startup" = @{ Percent = 76; Monthly = 21000 }
        "business" = @{ Percent = 57; Monthly = 15500 }
        "enterprise" = @{ Percent = 0; Monthly = 0 }
    }
    
    $saving = $savings[$ConfigSize]
    if ($saving.Percent -gt 0) {
        Write-Host "   Экономия: $($saving.Percent)% (~$($saving.Monthly)₽/мес)" -ForegroundColor Green
        Write-Host "   С welcome bonus первый месяц: дополнительная скидка 5,000₽" -ForegroundColor Green
    } else {
        Write-Host "   Полная конфигурация - максимальная производительность" -ForegroundColor Cyan
    }
    Write-Host ""
}

# Основная функция
function Main {
    Write-Host "🚀 POLIOM HR Assistant - VK Cloud Deployment" -ForegroundColor Magenta
    Write-Host "=============================================" -ForegroundColor Magenta
    
    Show-ConfigInfo -Size $ConfigSize
    Show-CostSavings
    
    try {
        Test-Dependencies
        Set-Environment
        New-Namespace
        New-ConfigMap
        New-Secret
        Deploy-Redis
        New-HPA
        Test-PostgreSQL
        Build-Images
        Deploy-Application
        Test-DeploymentStatus
        Show-AccessInfo
        Save-Configuration
        
        Write-Success "🎉 Развертывание завершено успешно!"
        Write-Info "Конфигурация: $ConfigSize"
        Write-Info "Используйте 'kubectl get all -n poliom-hr' для проверки статуса"
        Write-Info "Для управления: .\vk_cloud_utils.ps1 -Action status"
        
    } catch {
        Write-ErrorMsg "Ошибка развертывания: $_"
        Write-Info "Проверьте логи и повторите попытку"
        exit 1
    }
}

# Обработка прерывания
try {
    Main
} catch {
    Write-ErrorMsg "Развертывание прервано: $_"
    exit 1
} 