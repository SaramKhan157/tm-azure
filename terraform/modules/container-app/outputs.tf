output "app_fqdn" {
  value = azurerm_container_app.this.ingress[0].fqdn
}

output "app_url" {
  value = "https://${azurerm_container_app.this.ingress[0].fqdn}"
}
