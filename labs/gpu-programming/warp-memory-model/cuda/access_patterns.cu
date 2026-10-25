// access_patterns.cu - strided copy: what a warp pays when its 32 loads are not adjacent.
//
// Build: nvcc -O2 -arch=sm_80 access_patterns.cu -o access_patterns
// Run  : ./access_patterns            (needs an NVIDIA GPU; compile-checked only in the course sandbox)
//
// Lane k of a warp reads in[(base + k) * stride]. The model in ../warpmodel.py predicts the number
// of 32-byte sectors per warp request: min(stride, 8) * 4 for float32. The program prints the
// measured effective bandwidth next to the model's traffic ratio so that you can falsify the model.
#include <cstdio>
#include <cuda_runtime.h>

#define CHECK(call)                                                                  \
  do {                                                                               \
    cudaError_t err__ = (call);                                                      \
    if (err__ != cudaSuccess) {                                                      \
      fprintf(stderr, "CUDA error '%s' at %s:%d\n", cudaGetErrorString(err__), __FILE__, __LINE__); \
      return 2;                                                                      \
    }                                                                                \
  } while (0)

__global__ void copy_strided(const float* __restrict__ in, float* __restrict__ out, size_t n, int stride) {
  size_t i = blockIdx.x * (size_t)blockDim.x + threadIdx.x;
  if (i < n) out[i] = in[i * stride];  // the write is coalesced, the read is not when stride > 1
}

int main() {
  const size_t n = size_t(1) << 22;  // 4 Mi floats = 16 MiB written per launch
  const int max_stride = 32;
  const int block = 256;
  const int reps = 20;

  float *in = nullptr, *out = nullptr;
  CHECK(cudaMalloc(&in, n * max_stride * sizeof(float)));
  CHECK(cudaMalloc(&out, n * sizeof(float)));
  CHECK(cudaMemset(in, 0, n * max_stride * sizeof(float)));
  cudaEvent_t t0, t1;
  CHECK(cudaEventCreate(&t0));
  CHECK(cudaEventCreate(&t1));

  printf("%7s %10s %14s %22s\n", "stride", "ms/launch", "useful GB/s", "model traffic ratio");
  for (int stride = 1; stride <= max_stride; stride *= 2) {
    unsigned grid = unsigned((n + block - 1) / block);
    copy_strided<<<grid, block>>>(in, out, n, stride);  // warm-up
    CHECK(cudaGetLastError());
    CHECK(cudaEventRecord(t0));
    for (int r = 0; r < reps; ++r) copy_strided<<<grid, block>>>(in, out, n, stride);
    CHECK(cudaEventRecord(t1));
    CHECK(cudaEventSynchronize(t1));
    float ms = 0.f;
    CHECK(cudaEventElapsedTime(&ms, t0, t1));
    ms /= reps;
    double useful = 2.0 * n * sizeof(float);  // one useful read and one write per element
    // model: the write moves 4 sectors per warp, the read min(stride, 8) * 4 sectors
    double sectors_read = (stride < 8 ? stride : 8) * 4.0;
    double ratio = (4.0 + sectors_read) / 8.0;
    printf("%7d %10.3f %14.1f %22.2f\n", stride, ms, useful / (ms * 1e6), ratio);
  }
  CHECK(cudaFree(in));
  CHECK(cudaFree(out));
  return 0;
}
