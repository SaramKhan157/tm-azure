variable "prefix" {
  description = "Short prefix used for all resource names"
  type        = string
  default     = "tm"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "UK South"
}

variable "image_name" {
  description = "Container image name (without tag)"
  type        = string
  default     = "task-manager"
}

variable "image_tag" {
  description = "Container image tag to deploy"
  type        = string
  default     = "latest"
}

variable "custom_domain" {
  description = "Custom hostname to bind to the Container App with a free Azure-managed TLS cert. Leave empty to serve only on *.azurecontainerapps.io."
  type        = string
  default     = "tm.saram-khan.site"
}

variable "tags" {
  description = "Tags applied to every resource"
  type        = map(string)
  default = {
    project     = "coderco-assignment-1"
    managed_by  = "terraform"
    environment = "production"
  }
}
