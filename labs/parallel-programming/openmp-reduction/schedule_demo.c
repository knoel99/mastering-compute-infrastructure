/* schedule_demo.c -- who runs which iteration, and what does it cost?
 *
 * usage: OMP_SCHEDULE=static,1 OMP_NUM_THREADS=4 ./schedule_demo N COST K
 *   COST: uniform    iteration i costs 1 unit
 *         triangular iteration i costs i+1 units
 *         spiky      iteration i costs 40 units when i % 40 == 0, else 1
 *   K   : number of dependent floating-point operations per unit (calibration knob)
 *
 * The loop uses schedule(runtime): the kind and chunk size come from OMP_SCHEDULE,
 * so one binary shows every schedule. The program records which thread ran each
 * iteration (owner[i]) and derives, from that record only:
 *   - assigned[t]   work units executed by thread t (the model of the load),
 *   - imbalance     max(assigned) / mean(assigned)  (1.0 = perfectly balanced),
 *   - runs          maximal groups of consecutive iterations with the same owner,
 *   - predicted_ms  max(assigned) * (serial time per unit),
 * and compares predicted_ms with the measured wall time of the parallel loop.
 */
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static long cost_of(const char *kind, long i)
{
    if (strcmp(kind, "uniform") == 0) return 1;
    if (strcmp(kind, "triangular") == 0) return i + 1;
    if (strcmp(kind, "spiky") == 0) return (i % 40 == 0) ? 40 : 1;
    fprintf(stderr, "unknown cost %s\n", kind);
    exit(2);
}

/* A chain of dependent operations the compiler cannot vectorise or remove. */
static double burn(long ops)
{
    double x = 1.0;
    for (long k = 0; k < ops; k++) x = x * 1.0000001 + 1e-9;
    return x;
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s N uniform|triangular|spiky K\n", argv[0]);
        return 2;
    }
    long n = atol(argv[1]);
    const char *kind = argv[2];
    long k = atol(argv[3]);
    int nth = omp_get_max_threads();

    long *cost = malloc((size_t)n * sizeof(long));
    int *owner = malloc((size_t)n * sizeof(int));
    long total = 0;
    for (long i = 0; i < n; i++) {
        cost[i] = cost_of(kind, i);
        total += cost[i];
    }

    volatile double sink = 0.0;
    double t0 = omp_get_wtime();
    for (long i = 0; i < n; i++) sink += burn(cost[i] * k);
    double t_serial = omp_get_wtime() - t0;
    double t_unit = t_serial / (double)total;

    omp_sched_t sk;
    int chunk;
    omp_get_schedule(&sk, &chunk);

    double *part = calloc((size_t)nth, sizeof(double));
    t0 = omp_get_wtime();
#pragma omp parallel num_threads(nth)
    {
        int me = omp_get_thread_num();
        double local = 0.0;
#pragma omp for schedule(runtime)
        for (long i = 0; i < n; i++) {
            owner[i] = me;
            local += burn(cost[i] * k);
        }
        part[me] = local;
    }
    double t_par = omp_get_wtime() - t0;
    for (int t = 0; t < nth; t++) sink += part[t];

    long *assigned = calloc((size_t)nth, sizeof(long));
    long runs = 1, covered = 0;
    for (long i = 0; i < n; i++) {
        assigned[owner[i]] += cost[i];
        if (i > 0 && owner[i] != owner[i - 1]) runs++;
    }
    long maxa = 0;
    for (int t = 0; t < nth; t++) {
        covered += assigned[t];
        if (assigned[t] > maxa) maxa = assigned[t];
    }
    double imbalance = (double)maxa / ((double)total / nth);

    int base = (int)sk & 0x7fffffff; /* drop the "monotonic" modifier bit that OpenMP 5.0 may add */
    const char *kname = base == omp_sched_static ? "static" : base == omp_sched_dynamic ? "dynamic"
                      : base == omp_sched_guided ? "guided" : "auto";
    printf("schedule=%s chunk=%d threads=%d n=%ld cost=%s total_units=%ld covered_units=%ld runs=%ld imbalance=%.3f "
           "serial_ms=%.1f parallel_ms=%.1f predicted_ms=%.1f speedup=%.2f\n",
           kname, chunk, nth, n, kind, total, covered, runs, imbalance, 1e3 * t_serial, 1e3 * t_par,
           1e3 * (double)maxa * t_unit, t_serial / t_par);
    if (n <= 64) {
        printf("owner=");
        for (long i = 0; i < n; i++) printf("%d", owner[i]);
        printf("\n");
    }
    free(cost);
    free(owner);
    free(part);
    free(assigned);
    return covered == total ? 0 : 1;
}
