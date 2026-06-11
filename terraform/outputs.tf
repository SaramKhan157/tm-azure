output "acr_login_server" {
  description = "ACR login server URL"
  value       = module.acr.login_server
}

output "container_app_fqdn" {
  description = "Container App FQDN"
  value       = module.container_app.app_fqdn
}

output "app_url" {
  description = "Public HTTPS URL of the deployed app (custom domain if set, else the Azure-managed FQDN)"
  value       = "https://${var.custom_domain != "" ? var.custom_domain : module.container_app.app_fqdn}"
}

# Re-enable when Front Door module is uncommented (requires non-free-tier subscription)
# output "frontdoor_endpoint" {
#   description = "Azure Front Door endpoint hostname"
#   value       = module.frontdoor.endpoint_hostname
# }
