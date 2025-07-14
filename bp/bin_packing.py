import os
import random
import time
import multiprocessing as mp

class SegmentTree:
    def __init__(self, size):
        self.n = size
        self.size = 1
        while self.size < size:
            self.size *= 2
        self.tree = [-10**9] * (2 * self.size)

    def update(self, index, value):
        i = self.size + index
        self.tree[i] = value
        i //= 2
        while i:
            self.tree[i] = max(self.tree[2 * i], self.tree[2 * i + 1])
            i //= 2

    def query_index(self, item):
        node = 1
        seg_l = 0
        seg_r = self.size - 1
        while seg_l != seg_r:
            mid = (seg_l + seg_r) // 2
            if self.tree[2 * node] >= item:
                node = 2 * node
                seg_r = mid
            else:
                node = 2 * node + 1
                seg_l = mid + 1
        return seg_l if self.tree[node] >= item else -1

def first_fit_fast(items, bin_capacity):
    n = len(items)
    tree = SegmentTree(n)
    bins = []
    remaining = [-10**9] * n
    count = 0
    for item in items:
        idx = tree.query_index(item)
        if idx == -1 or idx >= count:
            bins.append([item])
            remaining[count] = bin_capacity - item
            tree.update(count, remaining[count])
            count += 1
        else:
            bins[idx].append(item)
            remaining[idx] -= item
            tree.update(idx, remaining[idx])
    return bins, count

def generate_permutations(items, total_permutations=1000000):
    permutations = []
    permutations.append(sorted(items, reverse=True))  # não-crescente
    permutations.append(sorted(items))                # não-decrescente
    for _ in range(total_permutations - 2):
        permutations.append(random.sample(items, len(items)))
    return permutations

def process_permutation(args):
    perm, capacity = args
    bins, bin_count = first_fit_fast(perm, capacity)
    return bin_count

def read_instance(filepath):
    with open(filepath) as f:
        n = int(f.readline())
        C = int(f.readline())
        weights = [int(f.readline()) for _ in range(n)]
    return n, C, weights

def save_latex(results, filename="results.tex"):
    with open(filename, "w") as f:
        f.write("\\begin{tabular}{|l|c|c|c|c|c|}\n")
        f.write("\\hline\n")
        f.write("Instância & n & C & Bins Mín & Bins Máx & Bins Médio \\\\\n")
        f.write("\\hline\n")
        for res in results:
            f.write(f"{res['instance']} & {res['n']} & {res['C']} & {res['min_bins']} & {res['max_bins']} & {res['avg_bins']:.2f} \\\\\n")
            f.write("\\hline\n")
        f.write("\\end{tabular}\n")

def main():
    import sys

    instances = [file for file in sys.argv[1:] if file.endswith(".txt")]
    final_results = []

    for instance_file in instances:
        n, C, weights = read_instance(instance_file)
        total_weight = sum(weights)

        min_bins_runs = []
        max_bins_runs = []
        avg_bins_runs = []
        times_runs = []

        print(f"\nProcessing {instance_file} (n={n}, C={C})...")
        print("="*60)

        for run in range(5):
            start = time.time()

            permutations = generate_permutations(weights, total_permutations=1000000)

            # Processa permutações em paralelo
            pool = mp.Pool(processes=mp.cpu_count())
            results = pool.map(process_permutation, [(perm, C) for perm in permutations])
            pool.close()
            pool.join()

            min_bins = min(results)
            max_bins = max(results)
            avg_bins = sum(results) / len(results)

            end = time.time()

            min_bins_runs.append(min_bins)
            max_bins_runs.append(max_bins)
            avg_bins_runs.append(avg_bins)
            times_runs.append(end - start)

            print(f"  Run {run+1}: min_bins = {min_bins}, max_bins = {max_bins}, avg_bins = {avg_bins:.2f}, time = {end-start:.2f}s")

        overall_min_bins = min(min_bins_runs)
        overall_max_bins = max(max_bins_runs)
        overall_avg_bins = sum(avg_bins_runs) / len(avg_bins_runs)
        avg_time = sum(times_runs) / len(times_runs)
        avg_loss = (1 - total_weight / (overall_min_bins * C)) * 100

        # Exibir resumo
        print(f"\nSummary for {instance_file}:")
        print(f"  Bins Min = {overall_min_bins}")
        print(f"  Bins Max = {overall_max_bins}")
        print(f"  Bins Avg = {overall_avg_bins:.2f}")
        print(f"  Average Loss (%) = {avg_loss:.4f}")
        print(f"  Average Time = {avg_time:.2f}s")

        # Guardar resultado para LaTeX
        final_results.append({
            "instance": instance_file,
            "n": n,
            "C": C,
            "min_bins": overall_min_bins,
            "max_bins": overall_max_bins,
            "avg_bins": overall_avg_bins,
            "avg_loss": avg_loss,
            "avg_time": avg_time,
        })

    save_latex(final_results, filename="results.tex")

if __name__ == "__main__":
    main()
