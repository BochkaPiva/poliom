# POLIOM HR Assistant - VK Cloud Utilities
# Дополнительные утилиты для управления развертыванием

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("status", "logs", "scale", "restart", "backup", "restore", "cleanup", "monitor", "update")]
    [string]$Action,
    
    [string]$Component = "all",
    [int]$Replicas = 3,
    [string]$BackupName = "",
    [string]$LogTail = "100"
)

# Настройка цветов
function Write-Info { param([string]$Message); Write-Host "ℹ️  $Message" -ForegroundColor Blue }
function Write-Success { param([string]$Message); Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message); Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-ErrorMsg { param([string]$Message); Write-Host "❌ $Message" -ForegroundColor Red }

# Проверка статуса
function Get-DeploymentStatus {
    Write-Info "📊 Статус развертывания POLIOM HR Assistant"
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    Write-Info "Namespace:"
    kubectl get namespace poliom-hr
    
    Write-Info "Pods:"
    kubectl get pods -n poliom-hr -o wide
    
    Write-Info "Services:"
    kubectl get services -n poliom-hr
    
    Write-Info "Ingress:"
    kubectl get ingress -n poliom-hr
    
    Write-Info "ConfigMaps:"
    kubectl get configmaps -n poliom-hr
    
    Write-Info "Secrets:"
    kubectl get secrets -n poliom-hr
    
    Write-Info "PersistentVolumes:"
    kubectl get pv,pvc -n poliom-hr
    
    # Проверка состояния подов
    Write-Info "Детальный статус подов:"
    $pods = kubectl get pods -n poliom-hr -o json | ConvertFrom-Json
    foreach ($pod in $pods.items) {
        $name = $pod.metadata.name
        $status = $pod.status.phase
        $ready = ($pod.status.containerStatuses | Where-Object { $_.ready -eq $true }).Count
        $total = $pod.status.containerStatuses.Count
        
        $statusColor = switch ($status) {
            "Running" { "Green" }
            "Pending" { "Yellow" }
            "Failed" { "Red" }
            default { "White" }
        }
        
        Write-Host "  📦 $name`: $status ($ready/$total ready)" -ForegroundColor $statusColor
    }
}

# Просмотр логов
function Get-Logs {
    param([string]$ComponentFilter = "all")
    
    Write-Info "📋 Просмотр логов компонентов"
    
    if ($ComponentFilter -eq "all") {
        $components = @("backend", "frontend", "redis")
    } else {
        $components = @($ComponentFilter)
    }
    
    foreach ($component in $components) {
        Write-Info "Логи для компонента: $component"
        Write-Host "-" * 30 -ForegroundColor Gray
        
        try {
            kubectl logs -n poliom-hr -l app=poliom-$component --tail=$LogTail
        } catch {
            Write-Warning "Не удалось получить логи для $component"
        }
        
        Write-Host ""
    }
}

# Масштабирование
function Set-Scale {
    param(
        [string]$ComponentName,
        [int]$ReplicaCount
    )
    
    Write-Info "🔄 Масштабирование $ComponentName до $ReplicaCount реплик"
    
    try {
        kubectl scale deployment $ComponentName -n poliom-hr --replicas=$ReplicaCount
        Write-Success "Масштабирование выполнено"
        
        # Ожидание применения изменений
        kubectl rollout status deployment/$ComponentName -n poliom-hr
        
    } catch {
        Write-ErrorMsg "Ошибка масштабирования: $_"
    }
}

# Перезапуск компонентов
function Restart-Components {
    param([string]$ComponentFilter = "all")
    
    Write-Info "🔄 Перезапуск компонентов"
    
    if ($ComponentFilter -eq "all") {
        $deployments = kubectl get deployments -n poliom-hr -o name
    } else {
        $deployments = @("deployment/poliom-$ComponentFilter")
    }
    
    foreach ($deployment in $deployments) {
        Write-Info "Перезапуск: $deployment"
        try {
            kubectl rollout restart $deployment -n poliom-hr
            kubectl rollout status $deployment -n poliom-hr
            Write-Success "Перезапуск $deployment завершен"
        } catch {
            Write-ErrorMsg "Ошибка перезапуска $deployment`: $_"
        }
    }
}

# Создание backup
function New-Backup {
    param([string]$Name)
    
    if (-not $Name) {
        $Name = "poliom-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    }
    
    Write-Info "💾 Создание backup: $Name"
    
    try {
        # Backup с помощью Velero (если установлен)
        if (Get-Command velero -ErrorAction SilentlyContinue) {
            velero backup create $Name --include-namespaces poliom-hr
            Write-Success "Backup создан с помощью Velero"
        } else {
            # Альтернативный метод - экспорт YAML
            $backupDir = "backups/$Name"
            New-Item -ItemType Directory -Path $backupDir -Force
            
            # Экспорт всех ресурсов
            $resources = @("deployments", "services", "configmaps", "secrets", "ingress", "pvc")
            foreach ($resource in $resources) {
                kubectl get $resource -n poliom-hr -o yaml > "$backupDir/$resource.yaml"
            }
            
            Write-Success "Backup сохранен в: $backupDir"
        }
    } catch {
        Write-ErrorMsg "Ошибка создания backup: $_"
    }
}

# Восстановление из backup
function Restore-Backup {
    param([string]$Name)
    
    Write-Info "🔄 Восстановление из backup: $Name"
    
    try {
        if (Get-Command velero -ErrorAction SilentlyContinue) {
            velero restore create "$Name-restore" --from-backup $Name
            Write-Success "Восстановление запущено с помощью Velero"
        } else {
            $backupDir = "backups/$Name"
            if (Test-Path $backupDir) {
                Get-ChildItem "$backupDir/*.yaml" | ForEach-Object {
                    kubectl apply -f $_.FullName
                }
                Write-Success "Восстановление из $backupDir завершено"
            } else {
                Write-ErrorMsg "Backup не найден: $backupDir"
            }
        }
    } catch {
        Write-ErrorMsg "Ошибка восстановления: $_"
    }
}

# Очистка ресурсов
function Remove-Deployment {
    Write-Warning "⚠️  Удаление всех ресурсов POLIOM HR Assistant"
    $confirm = Read-Host "Вы уверены? Введите 'DELETE' для подтверждения"
    
    if ($confirm -eq "DELETE") {
        Write-Info "Удаление namespace poliom-hr..."
        kubectl delete namespace poliom-hr
        Write-Success "Ресурсы удалены"
    } else {
        Write-Info "Операция отменена"
    }
}

# Мониторинг ресурсов
function Start-Monitoring {
    Write-Info "📊 Запуск мониторинга ресурсов"
    
    while ($true) {
        Clear-Host
        Write-Host "🚀 POLIOM HR Assistant - Мониторинг" -ForegroundColor Magenta
        Write-Host "Время: $(Get-Date)" -ForegroundColor Gray
        Write-Host "=" * 50 -ForegroundColor Cyan
        
        # CPU и память подов
        Write-Info "Использование ресурсов:"
        kubectl top pods -n poliom-hr --no-headers | ForEach-Object {
            $parts = $_ -split '\s+'
            $podName = $parts[0]
            $cpu = $parts[1]
            $memory = $parts[2]
            Write-Host "  📦 $podName`: CPU: $cpu, Memory: $memory" -ForegroundColor White
        }
        
        Write-Host ""
        
        # Статус подов
        Write-Info "Статус подов:"
        kubectl get pods -n poliom-hr --no-headers | ForEach-Object {
            $parts = $_ -split '\s+'
            $podName = $parts[0]
            $ready = $parts[1]
            $status = $parts[2]
            $restarts = $parts[3]
            
            $color = switch ($status) {
                "Running" { "Green" }
                "Pending" { "Yellow" }
                "Error" { "Red" }
                "CrashLoopBackOff" { "Red" }
                default { "White" }
            }
            
            Write-Host "  🔍 $podName`: $ready $status (restarts: $restarts)" -ForegroundColor $color
        }
        
        Write-Host ""
        Write-Host "Нажмите Ctrl+C для выхода..." -ForegroundColor Gray
        Start-Sleep -Seconds 10
    }
}

# Обновление приложения
function Update-Application {
    Write-Info "🔄 Обновление POLIOM HR Assistant"
    
    # Проверка новых образов
    $updateImages = Read-Host "Обновить Docker образы? (y/n)"
    if ($updateImages -eq "y" -or $updateImages -eq "Y") {
        Write-Info "Сборка новых образов..."
        docker build -t poliom-backend:latest -f backend/Dockerfile .
        docker build -t poliom-frontend:latest -f frontend/Dockerfile .
        
        # Обновление deployments
        kubectl set image deployment/poliom-backend backend=poliom-backend:latest -n poliom-hr
        kubectl set image deployment/poliom-frontend frontend=poliom-frontend:latest -n poliom-hr
        
        # Ожидание завершения rollout
        kubectl rollout status deployment/poliom-backend -n poliom-hr
        kubectl rollout status deployment/poliom-frontend -n poliom-hr
        
        Write-Success "Обновление завершено"
    }
    
    # Обновление конфигурации
    $updateConfig = Read-Host "Обновить конфигурацию? (y/n)"
    if ($updateConfig -eq "y" -or $updateConfig -eq "Y") {
        $configFiles = @("k8s/backend-deployment.yaml", "k8s/frontend-deployment.yaml", "k8s/ingress.yaml")
        foreach ($file in $configFiles) {
            if (Test-Path $file) {
                kubectl apply -f $file
                Write-Success "Обновлен: $file"
            }
        }
    }
}

# Главная функция
function Main {
    switch ($Action) {
        "status" { Get-DeploymentStatus }
        "logs" { Get-Logs -ComponentFilter $Component }
        "scale" { 
            if ($Component -eq "all") {
                @("poliom-backend", "poliom-frontend") | ForEach-Object {
                    Set-Scale -ComponentName $_ -ReplicaCount $Replicas
                }
            } else {
                Set-Scale -ComponentName "poliom-$Component" -ReplicaCount $Replicas
            }
        }
        "restart" { Restart-Components -ComponentFilter $Component }
        "backup" { New-Backup -Name $BackupName }
        "restore" { Restore-Backup -Name $BackupName }
        "cleanup" { Remove-Deployment }
        "monitor" { Start-Monitoring }
        "update" { Update-Application }
        default { 
            Write-ErrorMsg "Неизвестное действие: $Action"
            Write-Info "Доступные действия: status, logs, scale, restart, backup, restore, cleanup, monitor, update"
        }
    }
}

# Проверка kubectl
if (!(Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-ErrorMsg "kubectl не найден. Установите kubectl и повторите попытку."
    exit 1
}

# Запуск
try {
    Main
} catch {
    Write-ErrorMsg "Ошибка выполнения: $_"
    exit 1
} 