# Velero Terraform Setup for AKS + Azure Blob (Using Access Key Instead of Azure AD)

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


resource "azurerm_storage_account" "velero" {
  name                     = "velerobackupkalech"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
}

resource "azurerm_storage_container" "velero" {
  name                  = "velero"
  storage_account_name  = azurerm_storage_account.velero.name
  container_access_type = "private"
}

output "velero_storage_key" {
  description = "Primary access key for Velero backup storage"
  value       = azurerm_storage_account.velero.primary_access_key
  sensitive   = true
}

resource "helm_release" "velero" {
  name       = "velero"
  repository = "https://vmware-tanzu.github.io/helm-charts"
  chart      = "velero"
  namespace  = "velero"
  create_namespace = true
  values           = [file("${path.module}/velero-values.yaml")]


  set {
    name  = "snapshotsEnabled"
    value = "true"
  }

  set {
    name  = "initContainers[0].name"
    value = "velero-plugin-for-microsoft-azure"
  }

  set {
    name  = "initContainers[0].image"
    value = "velero/velero-plugin-for-microsoft-azure:v1.7.0"
  }
}

resource "kubernetes_secret" "velero_credentials" {
  metadata {
    name      = "cloud-credentials"
    namespace = "velero"
  }

  data = {
    cloud = file("${path.module}/credentials-velero")
  }

  type = "Opaque"
}


data "azurerm_client_config" "current" {}
