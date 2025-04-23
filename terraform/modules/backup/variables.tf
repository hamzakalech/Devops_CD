variable "resource_group_name" {
  type        = string
  description = "The resource group name"
}

variable "location" {
  type        = string
  description = "Azure location"
}

variable "mysql_disk_id" {
  description = "The Azure resource ID of the MySQL disk to back up"
  type        = string
}
