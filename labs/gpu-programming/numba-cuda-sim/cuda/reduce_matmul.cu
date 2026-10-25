// reduce_matmul.cu - the CUDA C++ twins of the Numba kernels in ../kernels.py.
//
// Build: nvcc -O2 -arch=sm_80 reduce_matmul.cu -o reduce_matmul
// Run  : ./reduce_matmul          (needs an NVIDIA GPU; compile-checked only in the course sandbox)
//
// block_sum   : tree reduction in shared memory, one partial sum per block (chapter 3).
// matmul_tiled: 16 x 16 tiles staged in shared memory (chapter 3).
// vec_add     : the guard `i < n` is mandatory because the grid is rounded up (chapter 1).
#include <cstdio>
#include <cmath>
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

constexpr int TPB = 256;   // threads per block of the reduction (a power of two)
constexpr int TILE = 16;   // matmul tile

__global__ void vec_add(const float* a, const float* b, float* c, int n) {
  int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < n) c[i] = a[i] + b[i];
}

__global__ void block_sum(const float* x, float* partial, int n) {
  __shared__ float sm[TPB];
  int t = threadIdx.x;
  int i = blockIdx.x * blockDim.x + t;
  sm[t] = (i < n) ? x[i] : 0.f;
  __syncthreads();
  for (int s = TPB / 2; s > 0; s >>= 1) {
    if (t < s) sm[t] += sm[t + s];
    __syncthreads();  // all threads reach this barrier: it is outside the `if`
  }
  if (t == 0) partial[blockIdx.x] = sm[0];
}

__global__ void matmul_tiled(const float* A, const float* B, float* C, int M, int K, int N) {
  __shared__ float sA[TILE][TILE];
  __shared__ float sB[TILE][TILE];
  int tx = threadIdx.x, ty = threadIdx.y;
  int col = blockIdx.x * TILE + tx, row = blockIdx.y * TILE + ty;
  float acc = 0.f;
  for (int t0 = 0; t0 < K; t0 += TILE) {
    sA[ty][tx] = (row < M && t0 + tx < K) ? A[row * K + t0 + tx] : 0.f;
    sB[ty][tx] = (t0 + ty < K && col < N) ? B[(t0 + ty) * N + col] : 0.f;
    __syncthreads();
    for (int k = 0; k < TILE; ++k) acc += sA[ty][k] * sB[k][tx];
    __syncthreads();
  }
  if (row < M && col < N) C[row * N + col] = acc;
}

int main() {
  // reduction of 1 Mi ones: the exact sum is 1048576 (every partial sum is exact in float32)
  const int n = 1 << 20;
  const int blocks = (n + TPB - 1) / TPB;
  std::vector<float> ones(n, 1.f), partial(blocks);
  float *d_x = nullptr, *d_p = nullptr;
  CHECK(cudaMalloc(&d_x, n * sizeof(float)));
  CHECK(cudaMalloc(&d_p, blocks * sizeof(float)));
  CHECK(cudaMemcpy(d_x, ones.data(), n * sizeof(float), cudaMemcpyHostToDevice));
  block_sum<<<blocks, TPB>>>(d_x, d_p, n);
  CHECK(cudaGetLastError());
  CHECK(cudaMemcpy(partial.data(), d_p, blocks * sizeof(float), cudaMemcpyDeviceToHost));
  double total = 0;
  for (float p : partial) total += p;
  printf("reduction: %.0f (expected %d)\n", total, n);

  // matrix product 256 x 256, compared with a CPU triple loop
  const int m = 256;
  std::vector<float> A(m * m), B(m * m), C(m * m), ref(m * m, 0.f);
  for (int i = 0; i < m * m; ++i) { A[i] = float((i * 7) % 13) / 13.f; B[i] = float((i * 5) % 11) / 11.f; }
  for (int i = 0; i < m; ++i)
    for (int k = 0; k < m; ++k)
      for (int j = 0; j < m; ++j) ref[i * m + j] += A[i * m + k] * B[k * m + j];
  float *dA = nullptr, *dB = nullptr, *dC = nullptr;
  CHECK(cudaMalloc(&dA, m * m * sizeof(float)));
  CHECK(cudaMalloc(&dB, m * m * sizeof(float)));
  CHECK(cudaMalloc(&dC, m * m * sizeof(float)));
  CHECK(cudaMemcpy(dA, A.data(), m * m * sizeof(float), cudaMemcpyHostToDevice));
  CHECK(cudaMemcpy(dB, B.data(), m * m * sizeof(float), cudaMemcpyHostToDevice));
  dim3 block(TILE, TILE), grid(m / TILE, m / TILE);
  matmul_tiled<<<grid, block>>>(dA, dB, dC, m, m, m);
  CHECK(cudaGetLastError());
  CHECK(cudaMemcpy(C.data(), dC, m * m * sizeof(float), cudaMemcpyDeviceToHost));
  double worst = 0;
  for (int i = 0; i < m * m; ++i) worst = fmax(worst, fabs(C[i] - ref[i]));
  printf("matmul: max abs difference vs CPU = %.3g\n", worst);
  CHECK(cudaFree(d_x)); CHECK(cudaFree(d_p));
  CHECK(cudaFree(dA)); CHECK(cudaFree(dB)); CHECK(cudaFree(dC));
  return worst < 1e-3 && total == n ? 0 : 1;
}
