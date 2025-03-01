provider "azurerm" {
  features {}
}

# 1. Create a Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "hamza-resources"
  location = "East US"
}

# 2. Create the AKS Cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "hamzaDevOps"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "hamzaDevOps"

  kubernetes_version  = "1.28" # Change to the latest available if needed

  default_node_pool {
    name                = "systempool"
    node_count          = 1
    enable_auto_scaling = false
    vm_size             = "Standard_B2als_v2" # Will be updated dynamically
    os_disk_size_gb     = 16
    os_sku              = "Ubuntu"
    vnet_subnet_id      = azurerm_subnet.aks_subnet.id
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

  api_server_access_profile {
    enable_private_cluster = false
  }
}

# 3. Create Virtual Network (if needed)
resource "azurerm_virtual_network" "vnet" {
  name                = "aks-vnet"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "aks_subnet" {
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}
