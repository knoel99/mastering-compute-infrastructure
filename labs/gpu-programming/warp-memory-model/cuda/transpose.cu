// transpose.cu - matrix transpose: naive, shared-memory tile, and tile with one column of padding.
//
// Build: nvcc -O2 -arch=sm_80 transpose.cu -o transpose
// Run  : ./transpose                  (needs an NVIDIA GPU; compile-checked only in the course sandbox)
//
// naive : reads are coalesced, writes are strided by n floats (32 sectors per warp store).
// tile  : both global accesses are coalesced, but lane k reads tile[k][c]: stride 32 words = 32-way bank conflict.
// padded: tile[32][33]: stride 33 words, conflict-free (../warpmodel.py: bank_conflict_degree).
#include <cstdio>
#include <vector>
#include <cuda_runtime.h>

#define CHECK(call)                                                                  \
  do {                                                                               \
    cudaError_t err__ = (call);                                                      \
    if (err__ != cudaSuccess) {                                                      \
      fprintf(stderr, "CUDA error '%s' at %s:%d\n", cudaGetErrorString(err__), __FILE__, __LINE__); \
      return 2;                                                                      \
    }                                                                                \
  } while (0)

constexpr int TILE = 32;
constexpr int ROWS = 8;  // block is 32 x 8 threads; each thread moves 4 elements

__global__ void transpose_naive(float* out, const float* in, int n) {
  int x = blockIdx.x * TILE + threadIdx.x;
  int y = blockIdx.y * TILE + threadIdx.y;
  for (int j = 0; j < TILE; j += ROWS) out[x * n + (y + j)] = in[(y + j) * n + x];
}

template <int PAD>
__global__ void transpose_tiled(float* out, const float* in, int n) {
  __shared__ float tile[TILE][TILE + PAD];
  int x = blockIdx.x * TILE + threadIdx.x;
  int y = blockIdx.y * TILE + threadIdx.y;
  for (int j = 0; j < TILE; j += ROWS) tile[threadIdx.y + j][threadIdx.x] = in[(y + j) * n + x];
  __syncthreads();  // every element of the tile must be written before any thread reads another's
  x = blockIdx.y * TILE + threadIdx.x;  // swap the block coordinates
  y = blockIdx.x * TILE + threadIdx.y;
  for (int j = 0; j < TILE; j += ROWS) out[(y + j) * n + x] = tile[threadIdx.x][threadIdx.y + j];
}

template <typename Kernel>
static int run(const char* name, Kernel kernel, const float* d_in, float* d_out, int n,
               const std::vector<float>& ref, std::vector<float>& host) {
  dim3 grid(n / TILE, n / TILE), block(TILE, ROWS);
  cudaEvent_t t0, t1;
  CHECK(cudaEventCreate(&t0));
  CHECK(cudaEventCreate(&t1));
  kernel<<<grid, block>>>(d_out, d_in, n);  // warm-up
  CHECK(cudaGetLastError());
  const int reps = 20;
  CHECK(cudaEventRecord(t0));
  for (int r = 0; r < reps; ++r) kernel<<<grid, block>>>(d_out, d_in, n);
  CHECK(cudaEventRecord(t1));
  CHECK(cudaEventSynchronize(t1));
  float ms = 0.f;
  CHECK(cudaEventElapsedTime(&ms, t0, t1));
  ms /= reps;
  CHECK(cudaMemcpy(host.data(), d_out, host.size() * sizeof(float), cudaMemcpyDeviceToHost));
  bool ok = (host == ref);
  printf("%-10s %8.3f ms  %8.1f GB/s  %s\n", name, ms, 2.0 * n * n * sizeof(float) / (ms * 1e6), ok ? "correct" : "WRONG");
  return ok ? 0 : 1;
}

int main() {
  const int n = 4096;
  std::vector<float> h_in(size_t(n) * n), ref(size_t(n) * n), host(size_t(n) * n);
  for (int i = 0; i < n; ++i)
    for (int j = 0; j < n; ++j) {
      h_in[size_t(i) * n + j] = float(i * 7 + j);
      ref[size_t(j) * n + i] = h_in[size_t(i) * n + j];
    }
  float *d_in = nullptr, *d_out = nullptr;
  CHECK(cudaMalloc(&d_in, h_in.size() * sizeof(float)));
  CHECK(cudaMalloc(&d_out, h_in.size() * sizeof(float)));
  CHECK(cudaMemcpy(d_in, h_in.data(), h_in.size() * sizeof(float), cudaMemcpyHostToDevice));
  int bad = 0;
  bad += run("naive", transpose_naive, d_in, d_out, n, ref, host);
  bad += run("tile", transpose_tiled<0>, d_in, d_out, n, ref, host);
  bad += run("padded", transpose_tiled<1>, d_in, d_out, n, ref, host);
  CHECK(cudaFree(d_in));
  CHECK(cudaFree(d_out));
  return bad ? 1 : 0;
}
