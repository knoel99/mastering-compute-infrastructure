/* false_sharing.c -- per-thread histograms, with and without false sharing.
 *
 * usage: false_sharing LAYOUT N REPEAT
 *   LAYOUT: packed  -> each thread owns 7 counters (56 bytes) stored back to back
 *           padded  -> each thread owns 7 counters but its slot starts on its own 64-byte line
 *           private -> each thread counts in a private local array and merges once at the end
 *
 * The data are pseudo-random bytes folded into 7 bins (deterministic: fixed
 * multiplicative hash, no rand()). Every layout must give the same histogram.
 * "shared_lines" is a deterministic structural measure: the number of 64-byte
 * cache lines that contain counters of more than one thread.
 */
#include <omp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BINS 7
#define LINE 64
#define MAX_THREADS 256

static int cmp(const void *x, const void *y)
{
    double a = *(const double *)x, b = *(const double *)y;
    return (a > b) - (a < b);
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s packed|padded|private N REPEAT\n", argv[0]);
        return 2;
    }
    const char *layout = argv[1];
    long n = atol(argv[2]);
    int repeat = atoi(argv[3]);
    int nth = omp_get_max_threads();
    size_t slot = strcmp(layout, "padded") == 0 ? LINE / sizeof(long) : BINS; /* in longs */

    uint8_t *a = malloc((size_t)n);
    long ref[BINS] = {0};
    for (long i = 0; i < n; i++) {
        a[i] = (uint8_t)(((uint32_t)i * 2654435761u >> 7) % BINS);
        ref[a[i]]++;
    }
    long *h = aligned_alloc(LINE, MAX_THREADS * LINE);
    double *t = malloc((size_t)repeat * sizeof(double));
    long total[BINS];
    for (int r = 0; r < repeat; r++) {
        memset(h, 0, MAX_THREADS * LINE);
        double t0 = omp_get_wtime();
        if (strcmp(layout, "private") == 0) {
#pragma omp parallel num_threads(nth)
            {
                long mine[BINS] = {0};
#pragma omp for nowait
                for (long i = 0; i < n; i++) mine[a[i]]++;
#pragma omp critical
                for (int b = 0; b < BINS; b++) h[b] += mine[b];
            }
        } else {
#pragma omp parallel num_threads(nth)
            {
                long *m = &h[(size_t)omp_get_thread_num() * slot];
#pragma omp for
                for (long i = 0; i < n; i++) m[a[i]]++;
            }
        }
        t[r] = omp_get_wtime() - t0;
        memset(total, 0, sizeof total);
        if (strcmp(layout, "private") == 0) {
            for (int b = 0; b < BINS; b++) total[b] = h[b];
        } else {
            for (int th = 0; th < nth; th++)
                for (int b = 0; b < BINS; b++) total[b] += h[(size_t)th * slot + b];
        }
    }
    int ok = memcmp(total, ref, sizeof ref) == 0;

    /* Structural measure: which cache lines hold counters of two or more threads? */
    int shared_lines = 0;
    if (strcmp(layout, "private") != 0) {
        for (size_t line = 0; line < MAX_THREADS; line++) {
            int owners = 0;
            for (int th = 0; th < nth; th++) {
                size_t first = (size_t)th * slot * sizeof(long);
                size_t last = first + BINS * sizeof(long) - 1;
                if (first / LINE <= line && line <= last / LINE) owners++;
            }
            if (owners > 1) shared_lines++;
        }
    }
    qsort(t, (size_t)repeat, sizeof(double), cmp);
    printf("layout=%s threads=%d n=%ld repeat=%d histogram_ok=%d shared_lines=%d slot_bytes=%zu min_ms=%.3f median_ms=%.3f\n",
           layout, nth, n, repeat, ok, shared_lines, slot * sizeof(long), 1e3 * t[0], 1e3 * t[repeat / 2]);
    free(a);
    free(h);
    free(t);
    return ok ? 0 : 1;
}
