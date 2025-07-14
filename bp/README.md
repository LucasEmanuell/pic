# Bin Packing Problem - First Fit com Segment Tree

Este projeto é um trabalho da dsiciplina de Programação Inteira e Combinatória / Tópicos em Otimização, ministrada pelo professor **Gerardo Valdísio Rodrigues Viana** o algoritmo **First Fit** para o problema de empacotamento de bins (BPP), utilizando uma **Segment Tree** para otimizar a busca do primeiro bin adequado, reduzindo a complexidade.

## Como o código funciona

- Para cada instância:
  - Lê o número de itens (n), capacidade dos bins (C) e os pesos.
  - Executa 5 rodadas independentes.
  - Em cada rodada:
    - Gera 1 milhão de permutações dos itens:
      - Ordem decrescente
      - Ordem crescente
      - 999.998 permutações aleatórias
    - Para cada permutação:
      - Executa o algoritmo **First Fit**.
      - Registra o mínimo, máximo e média de bins utilizados na rodada.
- Ao final:
  - Exibe no terminal:
    - Bins mínimos, máximos e médios.
    - Percentual de perda.
    - Tempo médio de execução.
  - Gera tabela em LaTeX com os resultados consolidados.

## Principais características

- Segment Tree para busca rápida do primeiro bin que comporta o item.
- Algoritmo First Fit.
- Processamento paralelo para acelerar as permutações.
- Exporta os resultados em LaTeX pronto para inclusão em documentos acadêmicos.

## Como rodar

Execute o seguinte comando no terminal:

```bash
python bin_packing.py _BP-1_n50C1000.txt _BP-2_n100C1000.txt _BP-3_n120C150.txt _BP-4_n200C1000.txt _BP-5_n250C150.txt _BP-6_n500C150.txt _BP-7_n1000C150.txt
