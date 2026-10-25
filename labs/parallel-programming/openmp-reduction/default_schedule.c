/* default_schedule.c -- which thread runs which iteration when the loop has NO schedule clause?
 * The OpenMP 6.0 specification leaves the choice to the implementation; this prints what yours does.
 * usage: OMP_NUM_THREADS=4 ./default_schedule
 */
#include <omp.h>
#include <stdio.h>

int main(void)
{
    int owner[16];
#pragma omp parallel for
    for (int i = 0; i < 16; i++) owner[i] = omp_get_thread_num();
    printf("threads=%d owner=", omp_get_max_threads());
    for (int i = 0; i < 16; i++) printf("%d", owner[i]);
    printf("\n");
    return 0;
}
