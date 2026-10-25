/* jacobi.c -- 2-D Jacobi iteration for Laplace's equation, MPI domain decomposition, optional OpenMP.
 *
 * build : mpicc -O2 -fopenmp -Wall -Wextra -o jacobi jacobi.c -lm
 * run   : mpirun -np P ./jacobi --nx 1024 --ny 1024 --iters 100 [--decomp 1d|2d] [--overlap] [--check-every K]
 *
 * Problem: interior (ny x nx) starts at 0; Dirichlet boundary 1.0 on the top edge, 0.0 elsewhere.
 * One sweep: v[i][j] = 0.25 * (((u[i-1][j] + u[i+1][j]) + u[i][j-1]) + u[i][j+1]).
 * The order of the four additions is fixed, so the field is BIT-IDENTICAL whatever the number
 * of ranks, the decomposition, the overlap mode or the number of threads. The checksum below
 * (a sum of 64-bit patterns, modulo 2^64) is order-independent and proves it.
 *
 * Decomposition: 1d = blocks of rows (px = 1, py = P); 2d = MPI_Dims_create process grid.
 * Halo exchange: Isend/Irecv to the four neighbours; columns use an MPI_Type_vector.
 *   --overlap : post the exchange, sweep the points that need no halo, wait, sweep the border.
 * Residual: max-norm (exact, independent of the decomposition) and 2-norm (a floating-point sum
 * reduced with MPI_Allreduce: its last digits depend on P). Computed every K sweeps and at the end.
 *
 * --skip-sweep removes the arithmetic and keeps the exchanges: it times the communication alone.
 *
 * Output: one key=value line on rank 0. Times are the MAX over ranks of the time spent in
 * (comp) sweeps (t_comp_min: the smallest over ranks, to expose load imbalance), (halo) posting + waiting for the exchange, (red) the residual all-reduces.
 */
#include <math.h>
#include <mpi.h>
#include <omp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int nx, ny, iters, check_every, overlap, twod, warmup, skip_sweep;
} opts_t;

static void die(const char *msg)
{
    fprintf(stderr, "jacobi: %s\n", msg);
    MPI_Abort(MPI_COMM_WORLD, 2);
}

static void parse(int argc, char **argv, opts_t *o)
{
    o->nx = 256; o->ny = 256; o->iters = 50; o->check_every = 0; o->overlap = 0; o->twod = 0; o->warmup = 2; o->skip_sweep = 0;
    for (int a = 1; a < argc; a++) {
        if (!strcmp(argv[a], "--nx") && a + 1 < argc) o->nx = atoi(argv[++a]);
        else if (!strcmp(argv[a], "--ny") && a + 1 < argc) o->ny = atoi(argv[++a]);
        else if (!strcmp(argv[a], "--iters") && a + 1 < argc) o->iters = atoi(argv[++a]);
        else if (!strcmp(argv[a], "--check-every") && a + 1 < argc) o->check_every = atoi(argv[++a]);
        else if (!strcmp(argv[a], "--decomp") && a + 1 < argc) o->twod = !strcmp(argv[++a], "2d");
        else if (!strcmp(argv[a], "--overlap")) o->overlap = 1;
        else if (!strcmp(argv[a], "--skip-sweep")) o->skip_sweep = 1; /* communication only: no arithmetic */
        else die("unknown option");
    }
}

/* One sweep over rows i0..i1, columns j0..j1 of the local (ly+2) x (lx+2) block. */
static int skip_sweep = 0;

static inline void sweep(const double *u, double *v, int w, int i0, int i1, int j0, int j1, int want_res,
                         double *maxd, double *l2)
{
    double md = 0.0, s2 = 0.0;
    if (skip_sweep) return;
#pragma omp parallel for reduction(max : md) reduction(+ : s2) schedule(static)
    for (int i = i0; i <= i1; i++) {
        for (int j = j0; j <= j1; j++) {
            double nv = 0.25 * (((u[(i - 1) * w + j] + u[(i + 1) * w + j]) + u[i * w + j - 1]) + u[i * w + j + 1]);
            v[i * w + j] = nv;
            if (want_res) {
                double d = nv - u[i * w + j];
                if (fabs(d) > md) md = fabs(d);
                s2 += d * d;
            }
        }
    }
    if (want_res) {
        if (md > *maxd) *maxd = md;
        *l2 += s2;
    }
}

int main(int argc, char **argv)
{
    int provided;
    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);
    int p, rank;
    MPI_Comm_size(MPI_COMM_WORLD, &p);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    opts_t o;
    parse(argc, argv, &o);
    skip_sweep = o.skip_sweep;

    int dims[2] = {0, 0}, periods[2] = {0, 0}, coords[2];
    if (o.twod) MPI_Dims_create(p, 2, dims);
    else { dims[0] = p; dims[1] = 1; }
    MPI_Comm cart;
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 0, &cart);
    MPI_Cart_coords(cart, rank, 2, coords);
    int up, down, left, right;
    MPI_Cart_shift(cart, 0, 1, &up, &down);
    MPI_Cart_shift(cart, 1, 1, &left, &right);
    int py = dims[0], px = dims[1];
    int ly = o.ny / py + (coords[0] < o.ny % py), lx = o.nx / px + (coords[1] < o.nx % px);
    if (ly < 3 || lx < 3) die("local block smaller than 3 x 3");
    int w = lx + 2;
    size_t cells = (size_t)(ly + 2) * (size_t)w;
    double *u = malloc(cells * sizeof(double)), *v = malloc(cells * sizeof(double));
    if (!u || !v) die("out of memory");
    memset(u, 0, cells * sizeof(double));
    memset(v, 0, cells * sizeof(double));
    if (up == MPI_PROC_NULL)
        for (int j = 0; j < w; j++) u[j] = v[j] = 1.0; /* physical top edge */

    MPI_Datatype column;
    MPI_Type_vector(ly, 1, w, MPI_DOUBLE, &column);
    MPI_Type_commit(&column);

    long msgs = 0, bytes = 0;
    double t_comp = 0, t_halo = 0, t_red = 0;
    MPI_Request rq[8];
    int nrq;

    /* post the exchange for block `a` (its interior borders go out, its halos come in) */
#define POST(a)                                                                                  \
    do {                                                                                         \
        nrq = 0;                                                                                 \
        MPI_Irecv(&(a)[(ly + 1) * w + 1], lx, MPI_DOUBLE, down, 0, cart, &rq[nrq++]);            \
        MPI_Irecv(&(a)[0 * w + 1], lx, MPI_DOUBLE, up, 1, cart, &rq[nrq++]);                     \
        MPI_Irecv(&(a)[1 * w + lx + 1], 1, column, right, 2, cart, &rq[nrq++]);                  \
        MPI_Irecv(&(a)[1 * w + 0], 1, column, left, 3, cart, &rq[nrq++]);                        \
        MPI_Isend(&(a)[1 * w + 1], lx, MPI_DOUBLE, up, 0, cart, &rq[nrq++]);                     \
        MPI_Isend(&(a)[ly * w + 1], lx, MPI_DOUBLE, down, 1, cart, &rq[nrq++]);                  \
        MPI_Isend(&(a)[1 * w + 1], 1, column, left, 2, cart, &rq[nrq++]);                        \
        MPI_Isend(&(a)[1 * w + lx], 1, column, right, 3, cart, &rq[nrq++]);                      \
        if (up != MPI_PROC_NULL) { msgs++; bytes += 8L * lx; }                                   \
        if (down != MPI_PROC_NULL) { msgs++; bytes += 8L * lx; }                                 \
        if (left != MPI_PROC_NULL) { msgs++; bytes += 8L * ly; }                                 \
        if (right != MPI_PROC_NULL) { msgs++; bytes += 8L * ly; }                                \
    } while (0)

    double loop_start = 0.0, t_loop = 0.0, res_max = 0.0, res_l2 = 0.0;
    for (int it = -o.warmup; it < o.iters; it++) {
        if (it == 0) { /* warm-up done: reset counters and start the clock */
            msgs = bytes = 0;
            t_comp = t_halo = t_red = 0;
            MPI_Barrier(cart);
            loop_start = MPI_Wtime();
        }
        int want_res = it >= 0 && (it == o.iters - 1 || (o.check_every > 0 && (it + 1) % o.check_every == 0));
        double maxd = 0.0, l2 = 0.0, t0;
        if (!o.overlap) {
            t0 = MPI_Wtime();
            POST(u);
            MPI_Waitall(nrq, rq, MPI_STATUSES_IGNORE);
            t_halo += MPI_Wtime() - t0;
            t0 = MPI_Wtime();
            sweep(u, v, w, 1, ly, 1, lx, want_res, &maxd, &l2);
            t_comp += MPI_Wtime() - t0;
        } else {
            t0 = MPI_Wtime();
            POST(u);
            t_halo += MPI_Wtime() - t0;
            t0 = MPI_Wtime();
            sweep(u, v, w, 2, ly - 1, 2, lx - 1, want_res, &maxd, &l2); /* needs no halo */
            t_comp += MPI_Wtime() - t0;
            t0 = MPI_Wtime();
            MPI_Waitall(nrq, rq, MPI_STATUSES_IGNORE);
            t_halo += MPI_Wtime() - t0;
            t0 = MPI_Wtime();
            sweep(u, v, w, 1, 1, 1, lx, want_res, &maxd, &l2);
            sweep(u, v, w, ly, ly, 1, lx, want_res, &maxd, &l2);
            sweep(u, v, w, 2, ly - 1, 1, 1, want_res, &maxd, &l2);
            sweep(u, v, w, 2, ly - 1, lx, lx, want_res, &maxd, &l2);
            t_comp += MPI_Wtime() - t0;
        }
        if (want_res) {
            t0 = MPI_Wtime();
            MPI_Allreduce(&maxd, &res_max, 1, MPI_DOUBLE, MPI_MAX, cart);
            MPI_Allreduce(&l2, &res_l2, 1, MPI_DOUBLE, MPI_SUM, cart);
            t_red += MPI_Wtime() - t0;
        }
        double *tmp = u; /* swap: the new field becomes the input of the next sweep */
        u = v;
        v = tmp;
    }
    t_loop = MPI_Wtime() - loop_start;

    /* order-independent fingerprint of the interior field: sum of the 64-bit patterns modulo 2^64 */
    uint64_t local_ck = 0, ck;
    double local_sum = 0.0, sum;
    for (int i = 1; i <= ly; i++)
        for (int j = 1; j <= lx; j++) {
            uint64_t bits;
            memcpy(&bits, &u[i * w + j], sizeof bits);
            local_ck += bits;
            local_sum += u[i * w + j];
        }
    MPI_Allreduce(&local_ck, &ck, 1, MPI_UINT64_T, MPI_SUM, cart);
    MPI_Allreduce(&local_sum, &sum, 1, MPI_DOUBLE, MPI_SUM, cart);
    double mine[4] = {t_loop, t_comp, t_halo, t_red}, worst[4], t_comp_min;
    MPI_Reduce(mine, worst, 4, MPI_DOUBLE, MPI_MAX, 0, cart);
    MPI_Reduce(&t_comp, &t_comp_min, 1, MPI_DOUBLE, MPI_MIN, 0, cart);
    long b_total = 0, b_max = 0, m_total = 0;
    MPI_Reduce(&bytes, &b_total, 1, MPI_LONG, MPI_SUM, 0, cart);
    MPI_Reduce(&bytes, &b_max, 1, MPI_LONG, MPI_MAX, 0, cart);
    MPI_Reduce(&msgs, &m_total, 1, MPI_LONG, MPI_SUM, 0, cart);
    if (rank == 0)
        printf("p=%d threads=%d decomp=%s py=%d px=%d nx=%d ny=%d iters=%d overlap=%d check_every=%d skip_sweep=%d "
               "t_total=%.6f t_comp=%.6f t_comp_min=%.6f t_halo=%.6f t_red=%.6f msgs_total=%ld bytes_total=%ld bytes_max=%ld "
               "checksum=%016llx field_sum=%.17g res_max=%.17g res_l2=%.17g\n",
               p, omp_get_max_threads(), o.twod ? "2d" : "1d", py, px, o.nx, o.ny, o.iters, o.overlap, o.check_every, o.skip_sweep,
               worst[0], worst[1], t_comp_min, worst[2], worst[3], m_total, b_total, b_max, (unsigned long long)ck, sum, res_max,
               res_l2);
    MPI_Type_free(&column);
    free(u);
    free(v);
    MPI_Finalize();
    return 0;
}
