// streams_overlap.cu - overlapping host-to-device copy, kernel and device-to-host copy with streams.
//
// Build: nvcc -O2 -arch=sm_80 streams_overlap.cu -o streams_overlap
// Run  : ./streams_overlap        (needs an NVIDIA GPU; compile-checked only in the course sandbox)
//
// The buffer is cut into CHUNKS pieces. Piece k goes through stream k % STREAMS: copy in, kernel,
// copy out. Copies of one piece overlap with the kernel of another one ONLY IF the host buffers are
// pinned (cudaMallocHost): from pageable memory cudaMemcpyAsync is synchronous and nothing overlaps
// (CUDA Programming Guide, section on asynchronous execution).
#include <cstdio>
#include <cstdlib>
#include <cuda_runtime.h>

#define CHECK(call)                                                                  \
  do {                                                                               \
    cudaError_t err__ = (call);                                                      \
    if (err__ != cudaSuccess) {                                                      \
      fprintf(stderr, "CUDA error '%s' at %s:%d\n", cudaGetErrorString(err__), __FILE__, __LINE__); \
      return 2;                                                                      \
    }                                                                                \
  } while (0)

__global__ void busy_scale(float* x, int n, int iters) {
  int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < n) {
    float v = x[i];
    for (int k = 0; k < iters; ++k) v = v * 1.0000001f + 0.5f;  // arithmetic to give the kernel a duration
    x[i] = v;
  }
}

static int run(bool pinned, int streams, size_t n, int chunks, float* ms_out) {
  float *h = nullptr, *d = nullptr;
  size_t bytes = n * sizeof(float);
  if (pinned) CHECK(cudaMallocHost(&h, bytes)); else h = static_cast<float*>(malloc(bytes));
  for (size_t i = 0; i < n; ++i) h[i] = 1.f;
  CHECK(cudaMalloc(&d, bytes));
  cudaStream_t s[8];
  for (int k = 0; k < streams; ++k) CHECK(cudaStreamCreate(&s[k]));
  cudaEvent_t t0, t1;
  CHECK(cudaEventCreate(&t0));
  CHECK(cudaEventCreate(&t1));
  size_t per = n / chunks;
  CHECK(cudaEventRecord(t0));
  for (int c = 0; c < chunks; ++c) {
    cudaStream_t st = s[c % streams];
    float* hp = h + c * per;
    float* dp = d + c * per;
    CHECK(cudaMemcpyAsync(dp, hp, per * sizeof(float), cudaMemcpyHostToDevice, st));
    busy_scale<<<(per + 255) / 256, 256, 0, st>>>(dp, int(per), 2000);
    CHECK(cudaMemcpyAsync(hp, dp, per * sizeof(float), cudaMemcpyDeviceToHost, st));
  }
  CHECK(cudaEventRecord(t1));
  CHECK(cudaEventSynchronize(t1));
  CHECK(cudaEventElapsedTime(ms_out, t0, t1));
  for (int k = 0; k < streams; ++k) CHECK(cudaStreamDestroy(s[k]));
  CHECK(cudaFree(d));
  if (pinned) CHECK(cudaFreeHost(h)); else free(h);
  return 0;
}

int main() {
  const size_t n = size_t(1) << 26;  // 64 Mi floats = 256 MiB
  const int chunks = 16;
  printf("%-28s %10s\n", "configuration", "total ms");
  struct Cfg { const char* name; bool pinned; int streams; } cfgs[] = {
      {"pageable, 1 stream", false, 1}, {"pinned, 1 stream", true, 1},
      {"pinned, 2 streams", true, 2},   {"pinned, 4 streams", true, 4}};
  for (const auto& c : cfgs) {
    float ms = 0.f;
    if (int rc = run(c.pinned, c.streams, n, chunks, &ms)) return rc;
    printf("%-28s %10.2f\n", c.name, ms);
  }
  return 0;
}
