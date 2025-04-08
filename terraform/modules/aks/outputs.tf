output "kube_config" {
  value     = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive = true
}

output "host" {
  value     = azurerm_kubernetes_cluster.aks.kube_config[0].host
  sensitive = true
}

output "fqdn" {
  value = azurerm_kubernetes_cluster.aks.fqdn
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}
