# Synthetic addresses from documentation ranges (RFC 5737 / locally administered MACs). Not a real network.
nodes = {
  "dev-gpu01" = { rack = "r01", gpu_model = "h100", gpus = 8, mac = "02:00:00:00:01:01", ip = "192.0.2.11", bmc_ip = "198.51.100.11" }
  "dev-gpu02" = { rack = "r01", gpu_model = "h100", gpus = 8, mac = "02:00:00:00:01:02", ip = "192.0.2.12", bmc_ip = "198.51.100.12" }
}
