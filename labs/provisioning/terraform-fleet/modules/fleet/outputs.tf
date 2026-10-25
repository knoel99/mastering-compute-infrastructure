output "node_count" {
  description = "Number of nodes in the fleet."
  value       = length(var.nodes)
}

output "total_gpus" {
  description = "Sum of GPUs over all nodes."
  value       = sum([for n in values(var.nodes) : n.gpus])
}

output "nodes_per_rack" {
  description = "Rack name -> number of nodes."
  value       = { for rack, members in local.racks : rack => length(members) }
}

output "gpu_models" {
  description = "Distinct GPU models present in the fleet."
  value       = local.gpu_models
}

output "generated_files" {
  description = "Paths of the files rendered by the module."
  value = [
    local_file.ansible_inventory.filename,
    local_file.dhcp_hosts.filename,
    local_file.slurm_nodes.filename,
    local_file.dnsmasq.filename,
    local_file.boot_ipxe.filename,
  ]
}
