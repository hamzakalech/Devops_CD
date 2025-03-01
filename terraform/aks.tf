terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">=3.0"
    }
  }
  required_version = ">= 1.3.0"
}

provider "azurerm" {
  features {}
}

# Create Resource Group
resource "azurerm_resource_group" "hamza_rg" {
  name     = "hamza-resources"
  location = "East US"
}

# Select the best VM size among the given options
# Terraform will automatically choose the first available one
variable "vm_sizes" {
  default = ["Standard_B2pls_v2", "Standard_B2als_v2", "Standard_B2ls_v2"]
}

# Deploy AKS Cluster
resource "azurerm_kubernetes_cluster" "hamza_aks" {
  name                = "hamzaDevOps"
  location            = azurerm_resource_group.hamza_rg.location
  resource_group_name = azurerm_resource_group.hamza_rg.name
  dns_prefix          = "hamza-aks"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = element(var.vm_sizes, 0) # Picks the first available VM from the list
    os_disk_size_gb = 30
    enable_auto_scaling = false
    type = "VirtualMachineScaleSets"
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "none"
    load_balancer_sku = "standard"
  }

  role_based_access_control_enabled = true

  tags = {
    environment = "dev"
    owner       = "hamza"
  }
}

# Output the cluster details
output "kube_config" {
  value     = azurerm_kubernetes_cluster.hamza_aks.kube_config_raw
  sensitive = true
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.hamza_aks.name
}
