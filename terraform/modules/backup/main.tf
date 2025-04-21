resource "azurerm_data_protection_backup_vault" "mysql_backup_vault" {
  name                = "mysqlBackupVault"
  location            = var.location
  resource_group_name = var.resource_group_name
  datastore_type      = "VaultStore"
  redundancy          = "LocallyRedundant"
}

resource "azurerm_data_protection_backup_policy_disk" "daily_policy" {
  name                = "dailyMySQLBackupPolicy"
  vault_name          = azurerm_data_protection_backup_vault.mysql_backup_vault.name
  resource_group_name = var.resource_group_name

  default_retention_rule {
    name     = "Default"
    duration = "P15D"
    priority = 1
    criteria {
      absolute_criteria = ["FirstOfDay"]
    }
  }

  backup_repeating_time_intervals = ["R/2024-01-01T02:00:00Z/PT24H"]
}
