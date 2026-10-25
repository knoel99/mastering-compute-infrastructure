variable "output_dir" {
  type = string
}

module "fleet" {
  source       = "../../modules/fleet"
  cluster_name = "dev"
  output_dir   = var.output_dir
  nodes        = var.nodes
}

variable "nodes" {
  type = map(object({
    rack      = string
    gpu_model = string
    gpus      = number
    mac       = string
    ip        = string
    bmc_ip    = string
  }))
}

output "summary" {
  value = {
    nodes = module.fleet.node_count
    gpus  = module.fleet.total_gpus
    racks = module.fleet.nodes_per_rack
  }
}
