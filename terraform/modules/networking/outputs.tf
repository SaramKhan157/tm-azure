output "vnet_id" {
  value = azurerm_virtual_network.this.id
}

output "container_app_subnet_id" {
  value = azurerm_subnet.container_apps.id
}
