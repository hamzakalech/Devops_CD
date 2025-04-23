# Velero Terraform Setup for AKS + Azure Blob

provider "azurerm" {
  features {}
}

provider "helm" {
  kubernetes {
    host                   = var.kube_host
    client_certificate     = base64decode(var.kube_client_certificate)
    client_key             = base64decode(var.kube_client_key)
    cluster_ca_certificate = base64decode(var.kube_cluster_ca_certificate)
  }
}

provider "kubernetes" {
  host                   = var.kube_host
  client_certificate     = base64decode(var.kube_client_certificate)
  client_key             = base64decode(var.kube_client_key)
  cluster_ca_certificate = base64decode(var.kube_cluster_ca_certificate)
}

resource "random_integer" "suffix" {
  min = 10000
  max = 99999
}

resource "azurerm_storage_account" "velero" {
  name                     = "velerobackup${random_integer.suffix.result}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  kind                     = "StorageV2"
}

resource "azurerm_storage_container" "velero" {
  name                  = "velero"
  storage_account_name  = azurerm_storage_account.velero.name
  container_access_type = "private"
}

resource "azurerm_ad_application" "velero" {
  display_name = "velero-app"
}

resource "azurerm_ad_service_principal" "velero" {
  application_id = azurerm_ad_application.velero.application_id
}

resource "azurerm_ad_service_principal_password" "velero" {
  service_principal_id = azurerm_ad_service_principal.velero.id
  value                = random_password.velero.result
  end_date             = "2099-12-31T23:59:59Z"
}

resource "random_password" "velero" {
  length  = 32
  special = true
}

resource "azurerm_role_assignment" "velero" {
  scope                = azurerm_storage_account.velero.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_ad_service_principal.velero.id
}

resource "helm_release" "velero" {
  name       = "velero"
  repository = "https://vmware-tanzu.github.io/helm-charts"
  chart      = "velero"
  namespace  = "velero"
  create_namespace = true

  set {
    name  = "credentials.secretContents.cloud"
    value = <<EOT
{"clientId":"${azurerm_ad_application.velero.application_id}","clientSecret":"${azurerm_ad_service_principal_password.velero.value}","tenantId":"${data.azurerm_client_config.current.tenant_id}","subscriptionId":"${data.azurerm_client_config.current.subscription_id}"}
EOT
  }

  set {
    name  = "configuration.provider"
    value = "azure"
  }

  set {
    name  = "configuration.backupStorageLocation.bucket"
    value = azurerm_storage_container.velero.name
  }

  set {
    name  = "configuration.backupStorageLocation.config.resourceGroup"
    value = var.resource_group_name
  }

  set {
    name  = "configuration.backupStorageLocation.config.storageAccount"
    value = azurerm_storage_account.velero.name
  }

  set {
    name  = "initContainers[0].name"
    value = "velero-plugin-for-microsoft-azure"
  }

  set {
    name  = "initContainers[0].image"
    value = "velero/velero-plugin-for-microsoft-azure:v1.7.0"
  }

  depends_on = [
    azurerm_role_assignment.velero, 
    null_resource.update_kubeconfig
  ]
}

# Data block to get tenant and subscription IDs
data "azurerm_client_config" "current" {}
