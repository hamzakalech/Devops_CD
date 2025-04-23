variable "resource_group_name" {
  description = "Resource group name where storage will be created"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "kube_host" {
  type = string
}
variable "kube_client_certificate" {
  type = string
}
variable "kube_client_key" {
  type = string
}
variable "kube_cluster_ca_certificate" {
  type = string
}
