resource "azurerm_log_analytics_workspace" "this" {
  name                = "${var.prefix}-logs"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_container_app_environment" "this" {
  name                       = "${var.prefix}-cae"
  resource_group_name        = var.resource_group_name
  location                   = var.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
  infrastructure_subnet_id   = var.infrastructure_subnet_id
  tags                       = var.tags

  lifecycle {
    ignore_changes = [
      infrastructure_resource_group_name,
      workload_profile,
    ]
  }
}

resource "azurerm_container_app" "this" {
  name                         = "${var.prefix}-app"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  registry {
    server               = var.acr_login_server
    username             = var.acr_admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = var.acr_admin_password
  }

  template {
    # NOTE: pinned to 1 replica because the app stores tasks in memory.
    # For a real deployment, add an external store (Cosmos DB / Postgres) and raise max_replicas.
    min_replicas = 1
    max_replicas = 1

    container {
      name   = "task-manager"
      image  = var.container_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "PORT"
        value = "3000"
      }

      liveness_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 3000

        initial_delay           = 10
        interval_seconds        = 30
        failure_count_threshold = 3
      }

      readiness_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 3000
      }
    }

    http_scale_rule {
      name                = "http-scale"
      concurrent_requests = "50"
    }
  }

  ingress {
    external_enabled = true
    target_port      = 3000

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  lifecycle {
    ignore_changes = [
      workload_profile_name,
    ]
  }
}

# Custom domain + Azure-managed Let's Encrypt certificate.
# azurerm provider 3.x doesn't expose a first-class resource for free managed
# certs, so we use a null_resource wrapping the az CLI. The commands are
# idempotent — re-running terraform apply won't break anything.
resource "null_resource" "custom_domain" {
  count = var.custom_domain == "" ? 0 : 1

  triggers = {
    hostname = var.custom_domain
    app_id   = azurerm_container_app.this.id
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = <<-EOT
      set -e

      # Add hostname (no-op if it already exists)
      if ! az containerapp hostname list \
            --name ${azurerm_container_app.this.name} \
            --resource-group ${var.resource_group_name} \
            --query "[?name=='${var.custom_domain}']" -o tsv | grep -q .; then
        az containerapp hostname add \
          --hostname ${var.custom_domain} \
          --name ${azurerm_container_app.this.name} \
          --resource-group ${var.resource_group_name}
      fi

      # Bind with a free managed TLS cert (idempotent — re-runs return the existing cert)
      az containerapp hostname bind \
        --hostname ${var.custom_domain} \
        --name ${azurerm_container_app.this.name} \
        --resource-group ${var.resource_group_name} \
        --environment ${azurerm_container_app_environment.this.name} \
        --validation-method CNAME
    EOT
  }
}
