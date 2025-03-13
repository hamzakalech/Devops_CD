###############################################################################
# Terraform Core & Provider Version Pinning
###############################################################################
terraform {
  required_version = ">= 1.0.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0.0, < 4.0.0" # ✅ Using AzureRM v3.x instead of v4.x
    }
  }
}

###############################################################################
# Variables
###############################################################################
variable "resource_group_name" {
  description = "Name of the Azure resource group."
  default     = "hamza-resources"
}

variable "location" {
  description = "Azure region for resources."
  default     = "East US"
}

variable "cluster_name" {
  description = "Name of the AKS cluster."
  default     = "hamzaDevOps"
}

variable "kubernetes_version" {
  description = "Kubernetes version to run on AKS."
  default     = "1.28.0"
}

###############################################################################
# Provider Configuration
###############################################################################
provider "azurerm" {
  features {}
}

###############################################################################
# Resource Group
###############################################################################
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

###############################################################################
# Virtual Network
###############################################################################
resource "azurerm_virtual_network" "vnet" {
  name                = "aks-vnet"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = ["10.0.0.0/16"]
}

###############################################################################
# Subnet for AKS
###############################################################################
resource "azurerm_subnet" "aks_subnet" {
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

###############################################################################
# AKS Cluster (System Node Pool - Auto-scaling Enabled)
###############################################################################
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.cluster_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = var.cluster_name
  kubernetes_version  = var.kubernetes_version

  # ✅ System Node Pool with Auto-scaling
  default_node_pool {
    name                = "agentpool"
    vm_size             = "Standard_B2als_v2"
    os_disk_size_gb     = 30
    os_sku              = "Ubuntu"
    vnet_subnet_id      = azurerm_subnet.aks_subnet.id

    enable_auto_scaling = true  # ✅ Auto-scaling is enabled
    min_count           = 1      # ✅ Minimum 1 node
    max_count           = 2      # ✅ Maximum 3 nodes
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    network_policy    = "calico"
    load_balancer_sku = "standard"
  }

  role_based_access_control_enabled = true
}

###############################################################################
# Additional User Node Pool (Worker, Auto-scaling Enabled)
###############################################################################
resource "azurerm_kubernetes_cluster_node_pool" "worker" {
  name                  = "worker"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = "Standard_B2als_v2"
  os_disk_size_gb       = 30
  os_type               = "Linux"
  os_sku                = "Ubuntu"
  vnet_subnet_id        = azurerm_subnet.aks_subnet.id
  mode                  = "User"

  # ✅ Auto-scaling Enabled (Only in User Pools)
  enable_auto_scaling = true
  min_count           = 1
  max_count           = 2
}

###############################################################################
# Outputs
###############################################################################
output "kube_config" {
  description = "Raw Kubeconfig for the AKS cluster."
  value       = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive   = true
}

output "host" {
  description = "The Kubernetes server URL for remote access."
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].host
  sensitive   = true
}

output "fqdn" {
  description = "The FQDN of the AKS cluster's API server."
  value       = azurerm_kubernetes_cluster.aks.fqdn
}

output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}
