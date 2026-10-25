# Run with: terraform test   (from modules/fleet). Offline: plans only, no real resource is touched.
variables {
  cluster_name = "tt"
  output_dir   = "/tmp/never-written-by-plan"
  nodes = {
    a = { rack = "r1", gpu_model = "h100", gpus = 8, mac = "02:00:00:00:00:01", ip = "192.0.2.1", bmc_ip = "198.51.100.1" }
    b = { rack = "r1", gpu_model = "h100", gpus = 8, mac = "02:00:00:00:00:02", ip = "192.0.2.2", bmc_ip = "198.51.100.2" }
    c = { rack = "r2", gpu_model = "a100", gpus = 4, mac = "02:00:00:00:00:03", ip = "192.0.2.3", bmc_ip = "198.51.100.3" }
  }
}

run "totals_are_computed" {
  command = plan
  assert {
    condition     = output.total_gpus == 20
    error_message = "8 + 8 + 4 GPUs expected"
  }
  assert {
    condition     = output.nodes_per_rack["r1"] == 2 && output.nodes_per_rack["r2"] == 1
    error_message = "rack counts are wrong"
  }
}

run "duplicate_mac_is_rejected" {
  command = plan
  variables {
    nodes = {
      a = { rack = "r1", gpu_model = "h100", gpus = 8, mac = "02:00:00:00:00:01", ip = "192.0.2.1", bmc_ip = "198.51.100.1" }
      b = { rack = "r1", gpu_model = "h100", gpus = 8, mac = "02:00:00:00:00:01", ip = "192.0.2.2", bmc_ip = "198.51.100.2" }
    }
  }
  expect_failures = [var.nodes]
}

run "seven_gpus_is_rejected" {
  command = plan
  variables {
    nodes = {
      a = { rack = "r1", gpu_model = "h100", gpus = 7, mac = "02:00:00:00:00:01", ip = "192.0.2.1", bmc_ip = "198.51.100.1" }
    }
  }
  expect_failures = [var.nodes]
}
