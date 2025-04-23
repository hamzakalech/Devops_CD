resource "azurerm_data_protection_backup_vault" "mysql_backup_vault" {
  name                = "mysqlBackupVault"
  location            = var.location
  resource_group_name = var.resource_group_name
  datastore_type      = "VaultStore"
  redundancy          = "LocallyRedundant"
}

resource "azurerm_data_protection_backup_policy_disk" "daily_policy" {
  name                = "dailyMySQLBackupPolicy"
  vault_id            = azurerm_data_protection_backup_vault.mysql_backup_vault.id
  default_retention_duration = "P15D"
  backup_repeating_time_intervals = ["R/2024-01-01T03:00:00Z/PT24H"] # adjust as needed
}

resource "azurerm_data_protection_backup_instance_disk" "mysql_instance" {
  name                           = "mysql-disk-backup"
  location                       = var.location
  vault_id                       = azurerm_data_protection_backup_vault.mysql_backup_vault.id
  snapshot_resource_group_name   = "MC_HAMZA-RESOURCES_HAMZADEVOPS_EASTUS"  # The disk's resource group
  disk_id                        = var.mysql_disk_id
  backup_policy_id               = azurerm_data_protection_backup_policy_disk.daily_policy.id
}

