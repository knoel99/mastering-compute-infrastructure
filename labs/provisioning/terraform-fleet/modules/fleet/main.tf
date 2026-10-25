locals {
  # Deterministic order: a map is sorted by key, so the generated files never reorder by accident.
  names = sort(keys(var.nodes))

  racks = {
    for rack in distinct([for n in values(var.nodes) : n.rack]) :
    rack => sort([for name, n in var.nodes : name if n.rack == rack])
  }

  gpu_models = distinct([for n in values(var.nodes) : n.gpu_model if n.gpus > 0])
}

# One record per node. terraform_data lives in the built-in provider: no download, and every node
# becomes a separate object in the state, so "remove a node from the map" is a visible destroy.
resource "terraform_data" "node" {
  for_each = var.nodes
  input = {
    name      = each.key
    rack      = each.value.rack
    gpu_model = each.value.gpu_model
    gpus      = each.value.gpus
    mac       = each.value.mac
  }
}

resource "local_file" "ansible_inventory" {
  filename        = "${var.output_dir}/${var.cluster_name}-inventory.yml"
  file_permission = "0644"
  content = templatefile("${path.module}/templates/ansible_inventory.yml.tftpl", {
    cluster = var.cluster_name
    racks   = local.racks
    nodes   = var.nodes
  })
}

resource "local_file" "dhcp_hosts" {
  filename        = "${var.output_dir}/${var.cluster_name}-dhcp-hosts.conf"
  file_permission = "0644"
  content = templatefile("${path.module}/templates/dhcp_hosts.conf.tftpl", {
    names = local.names
    nodes = var.nodes
  })
}

resource "local_file" "slurm_nodes" {
  filename        = "${var.output_dir}/${var.cluster_name}-slurm-nodes.conf"
  file_permission = "0644"
  content = templatefile("${path.module}/templates/slurm_nodes.conf.tftpl", {
    names = local.names
    nodes = var.nodes
  })
}

resource "local_file" "dnsmasq" {
  filename        = "${var.output_dir}/${var.cluster_name}-dnsmasq.conf"
  file_permission = "0644"
  content = templatefile("${path.module}/templates/dnsmasq.conf.tftpl", {
    cluster     = var.cluster_name
    server_ip   = var.boot_server_ip
    interface   = var.boot_interface
    hosts_file  = "${var.output_dir}/${var.cluster_name}-dhcp-hosts.conf"
    output_dir  = var.output_dir
    ipxe_script = "${var.cluster_name}-boot.ipxe"
  })
}

resource "local_file" "boot_ipxe" {
  filename        = "${var.output_dir}/${var.cluster_name}-boot.ipxe"
  file_permission = "0644"
  content = templatefile("${path.module}/templates/boot.ipxe.tftpl", {
    names     = local.names
    nodes     = var.nodes
    server_ip = var.boot_server_ip
  })
}
