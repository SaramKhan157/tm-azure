variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "prefix" {
  type = string
}

variable "tags" {
  type = map(string)
}

variable "acr_login_server" {
  type = string
}

variable "acr_admin_username" {
  type = string
}

variable "acr_admin_password" {
  type      = string
  sensitive = true
}

variable "container_image" {
  type = string
}

variable "infrastructure_subnet_id" {
  type = string
}

variable "custom_domain" {
  description = "Optional custom hostname (e.g. tm.example.com) to bind with a free Azure-managed TLS certificate. Leave empty to skip."
  type        = string
  default     = ""
}
