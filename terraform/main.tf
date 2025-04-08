terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

provider "azurerm" {
  features {}
}

provider "kubernetes" {
  host                   = module.aks.kube_config_host
  client_certificate     = base64decode(module.aks.kube_config_client_certificate)
  client_key             = base64decode(module.aks.kube_config_client_key)
  cluster_ca_certificate = base64decode(module.aks.kube_config_cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = module.aks.kube_config_host
    client_certificate     = base64decode(module.aks.kube_config_client_certificate)
    client_key             = base64decode(module.aks.kube_config_client_key)
    cluster_ca_certificate = base64decode(module.aks.kube_config_cluster_ca_certificate)
  }
}

# Modules

module "resource_group" {
  source              = "./modules/resource_group"
  resource_group_name = var.resource_group_name
  location            = var.location
}

module "network" {
  source              = "./modules/network"
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
}

module "aks" {
  source              = "./modules/aks"
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  cluster_name        = var.cluster_name
  kubernetes_version  = var.kubernetes_version
  subnet_id           = module.network.subnet_id
}

resource "null_resource" "update_kubeconfig" {
  depends_on = [module.aks]

  provisioner "local-exec" {
    command = <<EOT
az aks get-credentials --resource-group ${module.resource_group.name} --name ${module.aks.cluster_name} --overwrite-existing
sleep 5
EOT
  }
}

module "monitoring" {
  source     = "./modules/monitoring"
  depends_on = [null_resource.update_kubeconfig]
  providers = {
    helm = helm
  }
}
