#!/bin/bash

# POLIOM HR Assistant - VK Cloud Deployment Script
# Автоматизация развертывания на VK Cloud

set -e

echo "🚀 POLIOM HR Assistant - VK Cloud Deployment"
echo "============================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка зависимостей
check_dependencies() {
    print_info "Проверка зависимостей..."
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl не найден. Установите kubectl и повторите попытку."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker не найден. Установите Docker и повторите попытку."
        exit 1
    fi
    
    print_success "Все зависимости найдены"
}

# Настройка переменных окружения
setup_environment() {
    print_info "Настройка переменных окружения..."
    
    # Запрос основных параметров
    read -p "Введите название проекта VK Cloud: " VK_PROJECT_NAME
    read -p "Введите endpoint PostgreSQL: " POSTGRES_HOST
    read -p "Введите имя пользователя PostgreSQL: " POSTGRES_USER
    read -s -p "Введите пароль PostgreSQL: " POSTGRES_PASSWORD
    echo
    read -p "Введите название базы данных: " POSTGRES_DB
    read -p "Введите Access Key для Object Storage: " S3_ACCESS_KEY
    read -s -p "Введите Secret Key для Object Storage: " S3_SECRET_KEY
    echo
    read -p "Введите имя bucket: " S3_BUCKET_NAME
    read -p "Введите endpoint Object Storage: " S3_ENDPOINT
    
    # Экспорт переменных
    export VK_PROJECT_NAME
    export POSTGRES_HOST
    export POSTGRES_USER
    export POSTGRES_PASSWORD
    export POSTGRES_DB
    export S3_ACCESS_KEY
    export S3_SECRET_KEY
    export S3_BUCKET_NAME
    export S3_ENDPOINT
    
    print_success "Переменные окружения настроены"
}

# Создание namespace
create_namespace() {
    print_info "Создание namespace poliom-hr..."
    
    kubectl create namespace poliom-hr --dry-run=client -o yaml | kubectl apply -f -
    kubectl config set-context --current --namespace=poliom-hr
    
    print_success "Namespace создан и установлен как текущий"
}

# Создание ConfigMap
create_configmap() {
    print_info "Создание ConfigMap..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: poliom-config
  namespace: poliom-hr
data:
  POSTGRES_HOST: "${POSTGRES_HOST}"
  POSTGRES_DB: "${POSTGRES_DB}"
  POSTGRES_PORT: "5432"
  S3_ENDPOINT: "${S3_ENDPOINT}"
  S3_BUCKET_NAME: "${S3_BUCKET_NAME}"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
EOF

    print_success "ConfigMap создан"
}

# Создание Secret
create_secret() {
    print_info "Создание Secret..."
    
    kubectl create secret generic poliom-secrets \
        --from-literal=POSTGRES_USER="${POSTGRES_USER}" \
        --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
        --from-literal=S3_ACCESS_KEY="${S3_ACCESS_KEY}" \
        --from-literal=S3_SECRET_KEY="${S3_SECRET_KEY}" \
        --from-literal=JWT_SECRET="$(openssl rand -base64 32)" \
        --namespace=poliom-hr \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_success "Secret создан"
}

# Развертывание Redis
deploy_redis() {
    print_info "Развертывание Redis..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: poliom-hr
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
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
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
EOF

    print_success "Redis развернут"
}

# Проверка подключения к PostgreSQL
test_postgres() {
    print_info "Проверка подключения к PostgreSQL..."
    
    # Создание тестового pod для проверки
    kubectl run postgres-test --rm -i --restart=Never --image=postgres:16 -- \
        psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5432/${POSTGRES_DB}" \
        -c "SELECT version();" -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
    
    if [ $? -eq 0 ]; then
        print_success "Подключение к PostgreSQL успешно"
    else
        print_error "Ошибка подключения к PostgreSQL"
        exit 1
    fi
}

# Сборка и публикация образов
build_images() {
    print_info "Сборка Docker образов..."
    
    # Backend
    print_info "Сборка backend образа..."
    docker build -t poliom-backend:latest -f backend/Dockerfile .
    
    # Frontend
    print_info "Сборка frontend образа..."
    docker build -t poliom-frontend:latest -f frontend/Dockerfile .
    
    print_success "Образы собраны"
    
    # Если используется внешний registry
    read -p "Хотите загрузить образы в registry? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Введите URL registry: " REGISTRY_URL
        docker tag poliom-backend:latest ${REGISTRY_URL}/poliom-backend:latest
        docker tag poliom-frontend:latest ${REGISTRY_URL}/poliom-frontend:latest
        docker push ${REGISTRY_URL}/poliom-backend:latest
        docker push ${REGISTRY_URL}/poliom-frontend:latest
        print_success "Образы загружены в registry"
    fi
}

# Применение конфигурации Kubernetes
apply_k8s_configs() {
    print_info "Применение конфигураций Kubernetes..."
    
    # Проверяем наличие файлов конфигурации
    if [ -f "k8s/backend-deployment.yaml" ]; then
        kubectl apply -f k8s/backend-deployment.yaml
        print_success "Backend deployment применен"
    else
        print_warning "Файл k8s/backend-deployment.yaml не найден"
    fi
    
    if [ -f "k8s/frontend-deployment.yaml" ]; then
        kubectl apply -f k8s/frontend-deployment.yaml
        print_success "Frontend deployment применен"
    else
        print_warning "Файл k8s/frontend-deployment.yaml не найден"
    fi
    
    if [ -f "k8s/ingress.yaml" ]; then
        kubectl apply -f k8s/ingress.yaml
        print_success "Ingress применен"
    else
        print_warning "Файл k8s/ingress.yaml не найден"
    fi
}

# Проверка статуса развертывания
check_deployment_status() {
    print_info "Проверка статуса развертывания..."
    
    print_info "Pods:"
    kubectl get pods -n poliom-hr
    
    print_info "Services:"
    kubectl get services -n poliom-hr
    
    print_info "Ingress:"
    kubectl get ingress -n poliom-hr
    
    # Ожидание готовности подов
    print_info "Ожидание готовности подов..."
    kubectl wait --for=condition=ready pod --all -n poliom-hr --timeout=300s
    
    print_success "Развертывание завершено!"
}

# Вывод информации о доступе
show_access_info() {
    print_info "Информация о доступе:"
    
    INGRESS_IP=$(kubectl get ingress -n poliom-hr -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "не найден")
    
    echo "=================================="
    echo "🌐 IP адрес приложения: ${INGRESS_IP}"
    echo "📊 Мониторинг: http://${INGRESS_IP}/grafana"
    echo "🔍 Логи: kubectl logs -n poliom-hr -l app=poliom-backend"
    echo "⚙️  Статус: kubectl get all -n poliom-hr"
    echo "=================================="
}

# Основная функция
main() {
    echo "Начинаем развертывание POLIOM HR Assistant на VK Cloud..."
    
    check_dependencies
    setup_environment
    create_namespace
    create_configmap
    create_secret
    deploy_redis
    test_postgres
    
    read -p "Хотите собрать и загрузить Docker образы? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_images
    fi
    
    apply_k8s_configs
    check_deployment_status
    show_access_info
    
    print_success "🎉 Развертывание завершено успешно!"
    print_info "Используйте 'kubectl get all -n poliom-hr' для проверки статуса"
}

# Обработка сигналов
trap 'print_error "Развертывание прервано"; exit 1' INT TERM

# Запуск основной функции
main "$@" 