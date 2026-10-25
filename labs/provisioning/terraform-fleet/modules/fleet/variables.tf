variable "cluster_name" {
  description = "Short name of the cluster, used in file names and as the Slurm ClusterName."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,30}$", var.cluster_name))
    error_message = "cluster_name must be 2-31 characters: lowercase letters, digits and dashes, starting with a letter."
  }
}

variable "output_dir" {
  description = "Directory that receives the generated files (inventory, DHCP hosts, Slurm node lines)."
  type        = string
}

variable "nodes" {
  description = "The desired fleet: one entry per node, keyed by hostname."
  type = map(object({
    rack      = string
    gpu_model = string
    gpus      = number
    mac       = string
    ip        = string
    bmc_ip    = string
  }))

  validation {
    condition     = alltrue([for n in values(var.nodes) : can(regex("^([0-9a-f]{2}:){5}[0-9a-f]{2}$", n.mac))])
    error_message = "Every mac must be six lowercase hexadecimal pairs separated by colons."
  }

  validation {
    condition     = length(distinct([for n in values(var.nodes) : n.mac])) == length(var.nodes)
    error_message = "Two nodes share the same MAC address: the DHCP server could not tell them apart."
  }

  validation {
    condition = length(distinct(concat(
      [for n in values(var.nodes) : n.ip],
      [for n in values(var.nodes) : n.bmc_ip]
    ))) == 2 * length(var.nodes)
    error_message = "Every ip and bmc_ip must be unique across the fleet."
  }

  validation {
    condition = alltrue([
      for n in values(var.nodes) :
      can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}$", n.ip)) && can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}$", n.bmc_ip))
    ])
    error_message = "ip and bmc_ip must be dotted IPv4 addresses."
  }

  validation {
    condition     = alltrue([for n in values(var.nodes) : contains([0, 4, 8], n.gpus)])
    error_message = "gpus must be 0 (CPU node), 4 or 8: other counts are not a supported node shape in this course."
  }
}

variable "boot_server_ip" {
  description = "Address of the provisioning server (DHCP, TFTP and HTTP) on the boot network."
  type        = string
  default     = "192.0.2.2"
}

variable "boot_interface" {
  description = "Network interface of the provisioning server that faces the nodes."
  type        = string
  default     = "eth1"
}
