/* tasks_fib.c -- OpenMP tasks and the price of a task.
 *
 * usage: OMP_NUM_THREADS=4 ./tasks_fib N CUTOFF
 * fib(N) is computed recursively. Calls at depth < CUTOFF spawn their first
 * recursive call as an OpenMP task; deeper calls run sequentially. The number of
 * tasks created is counted and compared with the number a sequential walk of
 * the same recursion predicts (a deterministic structural check).
 */
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

static long fib_seq(int n) { return n < 2 ? n : fib_seq(n - 1) + fib_seq(n - 2); }

/* How many tasks does the recursion create? (sequential walk, no OpenMP) */
static long tasks_expected(int n, int depth, int cutoff)
{
    if (n < 2 || depth >= cutoff) return 0;
    return 1 + tasks_expected(n - 1, depth + 1, cutoff) + tasks_expected(n - 2, depth + 1, cutoff);
}

static long created = 0;

static long fib_task(int n, int depth, int cutoff)
{
    if (n < 2) return n;
    if (depth >= cutoff) return fib_seq(n);
    long x, y;
#pragma omp atomic
    created++;
#pragma omp task shared(x)
    x = fib_task(n - 1, depth + 1, cutoff);
    y = fib_task(n - 2, depth + 1, cutoff);
#pragma omp taskwait
    return x + y;
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s N CUTOFF\n", argv[0]);
        return 2;
    }
    int n = atoi(argv[1]), cutoff = atoi(argv[2]);
    long result = 0;
    double t0 = omp_get_wtime();
#pragma omp parallel
#pragma omp single
    result = fib_task(n, 0, cutoff);
    double t = omp_get_wtime() - t0;
    long expected_tasks = tasks_expected(n, 0, cutoff);
    printf("n=%d cutoff=%d threads=%d result=%ld reference=%ld tasks=%ld expected_tasks=%ld ms=%.1f\n", n, cutoff,
           omp_get_max_threads(), result, fib_seq(n), created, expected_tasks, 1e3 * t);
    return (result == fib_seq(n) && created == expected_tasks) ? 0 : 1;
}
