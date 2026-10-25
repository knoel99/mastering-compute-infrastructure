# Synthetic addresses from documentation ranges (RFC 5737 / locally administered MACs). Not a real network.
nodes = {
  "gpu-n01" = { rack = "r01", gpu_model = "h100", gpus = 8, mac = "02:00:00:00:02:01", ip = "192.0.2.21", bmc_ip = "198.51.100.21" }
  "gpu-n02" = { rack = "r01", gpu_model = "h100", gpus = 8, mac = "02:00:00:00:02:02", ip = "192.0.2.22", bmc_ip = "198.51.100.22" }
  "gpu-n03" = { rack = "r02", gpu_model = "h100", gpus = 8, mac = "02:00:00:00:02:03", ip = "192.0.2.23", bmc_ip = "198.51.100.23" }
  "gpu-n04" = { rack = "r02", gpu_model = "h100", gpus = 8, mac = "02:00:00:00:02:04", ip = "192.0.2.24", bmc_ip = "198.51.100.24" }
  "gpu-n05" = { rack = "r03", gpu_model = "a100", gpus = 4, mac = "02:00:00:00:02:05", ip = "192.0.2.25", bmc_ip = "198.51.100.25" }
  "cpu-n01" = { rack = "r03", gpu_model = "none", gpus = 0, mac = "02:00:00:00:02:06", ip = "192.0.2.26", bmc_ip = "198.51.100.26" }
}
