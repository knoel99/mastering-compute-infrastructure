/* fs_counters.c -- one counter per thread, incremented N/threads times, counters packed or padded.
 *
 * usage: fs_counters KIND LAYOUT N REPEAT
 *   KIND   : volatile  plain read-add-write through a volatile pointer
 *            atomic    relaxed atomic increment (a locked instruction)
 *   LAYOUT : packed    counters 8 bytes apart (same cache line)
 *            padded    counters 64 bytes apart (one line each)
 * Course chapter 2 uses it to show that false sharing is hardware dependent: on the test VM the
 * volatile version showed no measurable gap between packed and padded, the atomic version did.
 */
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_THREADS 64

static int cmp(const void *x, const void *y)
{
    double a = *(const double *)x, b = *(const double *)y;
    return (a > b) - (a < b);
}

int main(int argc, char **argv)
{
    if (argc != 5) {
        fprintf(stderr, "usage: %s volatile|atomic packed|padded N REPEAT\n", argv[0]);
        return 2;
    }
    int is_atomic = strcmp(argv[1], "atomic") == 0;
    size_t stride = strcmp(argv[2], "padded") == 0 ? 8 : 1; /* in longs */
    long n = atol(argv[3]);
    int repeat = atoi(argv[4]);
    int nth = omp_get_max_threads();
    long *c = aligned_alloc(64, MAX_THREADS * 64);
    double *t = malloc((size_t)repeat * sizeof(double));
    long total = 0;
    for (int r = 0; r < repeat; r++) {
        memset(c, 0, MAX_THREADS * 64);
        double t0 = omp_get_wtime();
#pragma omp parallel num_threads(nth)
        {
            long *mine = &c[(size_t)omp_get_thread_num() * stride];
            long share = n / nth;
            if (is_atomic) {
                for (long i = 0; i < share; i++) __atomic_fetch_add(mine, 1, __ATOMIC_RELAXED);
            } else {
                volatile long *v = mine;
                for (long i = 0; i < share; i++) *v = *v + 1;
            }
        }
        t[r] = omp_get_wtime() - t0;
        total = 0;
        for (int k = 0; k < nth; k++) total += c[(size_t)k * stride];
    }
    qsort(t, (size_t)repeat, sizeof(double), cmp);
    printf("kind=%s layout=%s threads=%d n=%ld total=%ld expected=%ld min_ms=%.2f median_ms=%.2f\n", argv[1], argv[2], nth, n,
           total, (n / nth) * nth, 1e3 * t[0], 1e3 * t[repeat / 2]);
    free(c);
    free(t);
    return total == (n / nth) * nth ? 0 : 1;
}
