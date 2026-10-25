/* sum_variants.c -- sum of n numbers with OpenMP, in several ways.
 *
 * usage: sum_variants VARIANT N REPEAT
 *   VARIANT: serial | simd | race | critical | atomic | reduction | reduction_simd | local
 *
 * The data are small integers stored as doubles (a[i] = i % 7 + 1), so every
 * partial sum is exactly representable and a correct variant returns EXACTLY
 * the expected value, whatever the order of the additions. Rounding is studied
 * separately (chapter 6 of the course, lab mpi-ring).
 *
 * Output: one "key=value" line, easy to parse. Timings use omp_get_wtime().
 */
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


static double run_variant(const char *v, const double *a, long n, int nth)
{
    double sum = 0.0;
    if (strcmp(v, "serial") == 0) {
        for (long i = 0; i < n; i++) sum += a[i];
    } else if (strcmp(v, "race") == 0) {
        /* DATA RACE (undefined behaviour): shared accumulator, no protection. */
#pragma omp parallel for num_threads(nth)
        for (long i = 0; i < n; i++) sum += a[i];
    } else if (strcmp(v, "critical") == 0) {
#pragma omp parallel for num_threads(nth)
        for (long i = 0; i < n; i++) {
#pragma omp critical
            sum += a[i];
        }
    } else if (strcmp(v, "atomic") == 0) {
#pragma omp parallel for num_threads(nth)
        for (long i = 0; i < n; i++) {
#pragma omp atomic
            sum += a[i];
        }
    } else if (strcmp(v, "reduction") == 0) {
#pragma omp parallel for num_threads(nth) reduction(+ : sum)
        for (long i = 0; i < n; i++) sum += a[i];
    } else if (strcmp(v, "simd") == 0) {
        /* One thread, vectorised: the compiler may reorder the additions. */
#pragma omp simd reduction(+ : sum)
        for (long i = 0; i < n; i++) sum += a[i];
    } else if (strcmp(v, "reduction_simd") == 0) {
#pragma omp parallel for simd num_threads(nth) reduction(+ : sum)
        for (long i = 0; i < n; i++) sum += a[i];
    } else if (strcmp(v, "local") == 0) {
        /* The reduction clause written by hand: private variable, one
         * combination per thread at the end. */
#pragma omp parallel num_threads(nth)
        {
            double mine = 0.0;
#pragma omp for nowait
            for (long i = 0; i < n; i++) mine += a[i];
#pragma omp atomic
            sum += mine;
        }
    } else {
        fprintf(stderr, "unknown variant %s\n", v);
        exit(2);
    }
    return sum;
}

static int cmp(const void *x, const void *y)
{
    double a = *(const double *)x, b = *(const double *)y;
    return (a > b) - (a < b);
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s VARIANT N REPEAT\n", argv[0]);
        return 2;
    }
    const char *variant = argv[1];
    long n = atol(argv[2]);
    int repeat = atoi(argv[3]);
    int nth = omp_get_max_threads();
    double *a = aligned_alloc(64, (size_t)n * sizeof(double));
    double expected = 0.0;
    for (long i = 0; i < n; i++) {
        a[i] = (double)(i % 7 + 1);
        expected += a[i];
    }
    double *t = malloc((size_t)repeat * sizeof(double));
    double result = 0.0;
    int wrong = 0;
    for (int r = 0; r < repeat; r++) {
        double t0 = omp_get_wtime();
        result = run_variant(variant, a, n, nth);
        t[r] = omp_get_wtime() - t0;
        if (result != expected) wrong++;
    }
    qsort(t, (size_t)repeat, sizeof(double), cmp);
    printf("variant=%s threads=%d n=%ld repeat=%d wrong=%d result=%.0f expected=%.0f min_ms=%.3f median_ms=%.3f\n",
           variant, nth, n, repeat, wrong, result, expected, 1e3 * t[0], 1e3 * t[repeat / 2]);
    free(t);
    free(a);
    return 0;
}
