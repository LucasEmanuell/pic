import random
import time
import os
import sys
import math
from multiprocessing import Pool, Manager

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
            self.tree[i] = max(self.tree[2*i], self.tree[2*i+1])
            i //= 2
    
    def query_index(self, item):
        node = 1
        seg_l = 0
        seg_r = self.size - 1
        
        while seg_l != seg_r:
            if self.tree[2*node] >= item:
                node = 2*node
                seg_r = (seg_l + seg_r) // 2
            else:
                node = 2*node + 1
                seg_l = (seg_l + seg_r) // 2 + 1
        
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

def read_instance(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    n = int(lines[0].strip())
    C = int(lines[1].strip())
    weights = [int(line.strip()) for line in lines[2:2+n]]
    
    return n, C, weights

def worker_process(args):
    items, bin_capacity, num_perms, seed = args
    random.seed(seed)
    best_bins = float('inf')
    best_packing = None
    
    for _ in range(num_perms):
        perm = random.sample(items, len(items))
        bins, bin_count = first_fit_fast(perm, bin_capacity)
        if bin_count < best_bins:
            best_bins = bin_count
            best_packing = bins
    
    return best_bins, best_packing

def main(instance_files):
    results = []
    num_workers = os.cpu_count() or 4
    
    for file_path in instance_files:
        n, C, weights = read_instance(file_path)
        total_weight = sum(weights)
        instance_name = os.path.basename(file_path)
        
        exec_times = []
        bin_counts = []
        all_packings = []
        
        print(f"\nProcessing {instance_name} (n={n}, C={C})...")
        print("=" * 60)
        
        for run in range(5):
            start_time = time.time()
            best_bins = float('inf')
            best_packing = None
            
            # Permutação 1: Não-crescente
            perm = sorted(weights, reverse=True)
            bins, bin_count = first_fit_fast(perm, C)
            if bin_count < best_bins:
                best_bins = bin_count
                best_packing = bins
            
            # Permutação 2: Não-decrescente
            perm = sorted(weights)
            bins, bin_count = first_fit_fast(perm, C)
            if bin_count < best_bins:
                best_bins = bin_count
                best_packing = bins
            
            # Permutações aleatórias paralelizadas
            total_perms = 1000000 - 2
            perms_per_worker = total_perms // num_workers
            remainder = total_perms % num_workers
            seeds = [random.randint(1, 1000000) for _ in range(num_workers)]
            
            args_list = []
            for i in range(num_workers):
                perms = perms_per_worker + (1 if i < remainder else 0)
                if perms > 0:
                    args_list.append((weights, C, perms, seeds[i]))
            
            with Pool(processes=num_workers) as pool:
                worker_results = pool.map(worker_process, args_list)
            
            for bins_count, packing in worker_results:
                if bins_count < best_bins:
                    best_bins = bins_count
                    best_packing = packing
            
            exec_time = time.time() - start_time
            exec_times.append(exec_time)
            bin_counts.append(best_bins)
            all_packings.append(best_packing)
            
            print(f"  Run {run+1}: bins = {best_bins}, time = {exec_time:.2f}s")
        
        # Encontrar melhor solução global
        min_bins = min(bin_counts)
        best_run_index = bin_counts.index(min_bins)
        best_packing_global = all_packings[best_run_index]
        
        # Calcular métricas
        max_bins = max(bin_counts)
        avg_bins = sum(bin_counts) / len(bin_counts)
        avg_time = sum(exec_times) / len(exec_times)
        loss_percent = (1 - total_weight / (min_bins * C)) * 100
        
        # Armazenar resultados
        results.append({
            'instance': instance_name,
            'n': n,
            'C': C,
            'min_bins': min_bins,
            'max_bins': max_bins,
            'avg_bins': avg_bins,
            'loss': loss_percent,
            'avg_time': avg_time,
            'packing': best_packing_global,
            'total_weight': total_weight
        })
    
    generate_report(results)

def generate_report(results):
    latex_output = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{multirow}

\title{Resultados do Problema de Empacotamento de Bins}
\author{Equipe First Fit}
\date{}

\begin{document}

\maketitle

\section*{Resultados Gerais}

\begin{longtable}{c c c c c c c c}
\toprule
\textbf{Instância} & \textbf{n} & \textbf{C} & \textbf{b\_min} & \textbf{b\_max} & \textbf{b\_avg} & \textbf{\% Perda} & \textbf{Tempo Médio (s)} \\
\midrule
"""
    
    for res in results:
        latex_output += (
            f"{res['instance']} & {res['n']} & {res['C']} & {res['min_bins']} & "
            f"{res['max_bins']} & {res['avg_bins']:.2f} & {res['loss']:.4f}\% & "
            f"{res['avg_time']:.2f} \\\\\n"
        )
    
    latex_output += r"""\bottomrule
\end{longtable}

\newpage
"""
    
    for res in results:
        packing_str = " \\\\\n".join(
            [f"Bin {i+1}: {bin_items} (Total: {sum(bin_items)}/{res['C']})" 
             for i, bin_items in enumerate(res['packing'])]
        )
        latex_output += f"""
\\section*{{Instância {res['instance']}}}

\\begin{{itemize}}
    \\item Total de itens: {res['n']}
    \\item Capacidade do bin: {res['C']}
    \\item Peso total: {res['total_weight']}
    \\item Número de bins: {res['min_bins']}
    \\item Percentual de perda: {res['loss']:.4f}\%
\\end{{itemize}}

Distribuição dos itens:

\\begin{{verbatim}}
{packing_str}
\\end{{verbatim}}

\\vspace{{1cm}}
"""
    
    latex_output += r"\end{document}"
    
    with open("relatorio.tex", "w") as f:
        f.write(latex_output)
    
    print("\nRelatório LaTeX gerado em 'relatorio.tex'")
    print("Compile com: pdflatex relatorio.tex")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python bin_packing.py <arquivo1> <arquivo2> ...")
        sys.exit(1)
    
    main(sys.argv[1:])