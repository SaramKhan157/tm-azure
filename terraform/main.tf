terraform {
  required_version = ">= 1.7"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }

  backend "azurerm" {
    resource_group_name  = "tm-tfstate-rg"
    storage_account_name = "tmtfstate12421"
    container_name       = "tfstate"
    key                  = "tm-azure.tfstate"
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "${var.prefix}-rg"
  location = var.location

  tags = var.tags
}

module "acr" {
  source              = "./modules/acr"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  prefix              = var.prefix
  tags                = var.tags
}

module "networking" {
  source              = "./modules/networking"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  prefix              = var.prefix
  tags                = var.tags
}

module "container_app" {
  source                   = "./modules/container-app"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = var.location
  prefix                   = var.prefix
  tags                     = var.tags
  acr_login_server         = module.acr.login_server
  acr_admin_username       = module.acr.admin_username
  acr_admin_password       = module.acr.admin_password
  container_image          = "${module.acr.login_server}/${var.image_name}:${var.image_tag}"
  infrastructure_subnet_id = module.networking.container_app_subnet_id
  custom_domain            = var.custom_domain
}

# Azure Front Door is not available on Free Trial subscriptions.
# Uncomment this module after upgrading to pay-as-you-go.
# The Container App ingress already provides public HTTPS with a managed certificate.
#
# module "frontdoor" {
#   source              = "./modules/frontdoor"
#   resource_group_name = azurerm_resource_group.main.name
#   prefix              = var.prefix
#   tags                = var.tags
#   origin_hostname     = module.container_app.app_fqdn
#   custom_domain       = var.custom_domain
# }
