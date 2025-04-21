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
    duration = "P15D"  # 15-day retention
    priority = 1

    criteria {
      absolute_criteria = ["FirstOfDay"]
    }
  }

  trigger {
    schedule {
      hour      = 4
      minute    = 0
      time_zone = "UTC + 1"
    }

    criteria {
      absolute_criteria = ["FirstOfDay"]
    }
  }
}
