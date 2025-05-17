import numpy as np
from terminaltables import AsciiTable
import copy
import time
import re

class SimplexTableau:
    def __init__(self, objetivo, restricoes, sinais, b, variaveis_restritas=None, maximizar=True):
        self.objetivo_original = copy.deepcopy(objetivo)
        self.restricoes_original = copy.deepcopy(restricoes)
        self.sinais_original = copy.deepcopy(sinais)
        self.b_original = copy.deepcopy(b)
        self.variaveis_restritas = variaveis_restritas if variaveis_restritas else {}
        self.maximizar = maximizar
        self.limites_inferiores = {}  # Novo: rastrear substituições x = x' + L
        self.constante_objetivo = 0   # Novo: termo constante da função objetivo
        
        # Etapa 1: Processar restrições específicas e limites inferiores
        self.aplicar_restricoes_especificas()
        self.aplicar_limites_inferiores()  # Novo: substituição de variáveis
        
        # Converter para forma padrão (<=) após substituições
        if not maximizar:
            objetivo = [-x for x in self.objetivo_original]  # Objetivo já ajustado
        else:
            objetivo = copy.deepcopy(self.objetivo_original)
            
        self.converter_restricoes_forma_padrao(objetivo, self.restricoes_original, self.sinais_original, self.b_original)
    
    def aplicar_restricoes_especificas(self):
        """Processa restrições do tipo x_i >= L ou x_i <= U"""
        num_vars = len(self.objetivo_original)
        
        for var_idx, (sinal, valor) in list(self.variaveis_restritas.items()):
            if sinal == ">=":
                if valor != 0:
                    self.limites_inferiores[var_idx] = valor  # Marca para substituição
                # Remove a restrição >= para evitar duplicação
                del self.variaveis_restritas[var_idx]
    
    def aplicar_limites_inferiores(self):
        """Substitui x_i por x_i' + L e ajusta objetivo/restrições"""
        if not self.limites_inferiores:
            return
        
        # Ajustar função objetivo com termo constante
        self.constante_objetivo = sum(
            self.objetivo_original[var] * L 
            for var, L in self.limites_inferiores.items()
        )
        
        # Ajustar restrições originais
        for i in range(len(self.restricoes_original)):
            soma_L = sum(
                self.restricoes_original[i][var] * L 
                for var, L in self.limites_inferiores.items()
            )
            self.b_original[i] -= soma_L
    
    def converter_restricoes_forma_padrao(self, objetivo, restricoes, sinais, b):
        """Converte restrições para <= e adiciona variáveis de folga/excesso"""
        self.restricoes = []
        self.b = []
        
        for restricao, sinal, valor_b in zip(restricoes, sinais, b):
            if sinal == "<=":
                self.restricoes.append(restricao)
                self.b.append(valor_b)
            elif sinal == ">=":
                self.restricoes.append([-x for x in restricao])
                self.b.append(-valor_b)
            elif sinal == "=":
                self.restricoes.append(restricao)
                self.b.append(valor_b)
                self.restricoes.append([-x for x in restricao])
                self.b.append(-valor_b)
        
        self.objetivo = objetivo
        
    def montar_tableau_inicial(self):
        """Configura o tableau inicial com variáveis de folga"""
        num_restricoes = len(self.restricoes)
        num_var_originais = len(self.objetivo)
        num_var_totais = num_var_originais + num_restricoes
        
        self.tableau = np.zeros((num_restricoes + 1, num_var_totais + 1))
        
        # Preencher restrições
        for i in range(num_restricoes):
            self.tableau[i, :num_var_originais] = self.restricoes[i]
            self.tableau[i, num_var_originais + i] = 1  # Variável de folga
            self.tableau[i, -1] = self.b[i]
        
        # Preencher função objetivo
        self.tableau[-1, :num_var_originais] = [-x for x in self.objetivo]
        
        # Variáveis básicas (folgas) e não básicas (originais)
        self.var_basicas = list(range(num_var_originais, num_var_totais))
        self.var_nao_basicas = list(range(num_var_originais))
    
    def encontrar_variavel_entrada(self):
        """Encontra a coluna pivô (mais negativo na última linha)"""
        ultima_linha = self.tableau[-1, :-1]
        min_valor = np.min(ultima_linha)
        return None if min_valor >= 0 else np.argmin(ultima_linha)
    
    def encontrar_variavel_saida(self, coluna_entrada):
        """Encontra a linha pivô usando a regra da razão mínima"""
        razoes = []
        for i in range(len(self.tableau) - 1):
            if self.tableau[i, coluna_entrada] <= 0:
                razoes.append(np.inf)
            else:
                razoes.append(self.tableau[i, -1] / self.tableau[i, coluna_entrada])
        
        if all(r == np.inf for r in razoes):
            return None  # Ilimitado
        
        return np.argmin(razoes)
    
    def atualizar_tableau(self, linha_pivo, coluna_pivo):
        """Realiza o pivoteamento em torno do elemento selecionado"""
        pivo = self.tableau[linha_pivo, coluna_pivo]
        self.tableau[linha_pivo] = self.tableau[linha_pivo] / pivo
        
        for i in range(len(self.tableau)):
            if i != linha_pivo:
                fator = self.tableau[i, coluna_pivo]
                self.tableau[i] -= fator * self.tableau[linha_pivo]
        
        # Atualizar variáveis básicas/não básicas
        var_saida = self.var_basicas[linha_pivo]
        self.var_basicas[linha_pivo] = coluna_pivo
        self.var_nao_basicas.remove(coluna_pivo)
        self.var_nao_basicas.append(var_saida)
        self.var_nao_basicas.sort()
    
    def formato_tableau_terminal(self, iteracao):
        """Formata o tableau para exibição no terminal"""
        num_var_originais = len(self.objetivo_original)
        headers = [''] + [f"x{j+1}" for j in range(num_var_originais)] + \
                  [f"s{j+1}" for j in range(len(self.restricoes))] + ["b"]
        
        row_headers = []
        for var in self.var_basicas:
            if var < num_var_originais:
                row_headers.append(f"x{var+1}")
            else:
                row_headers.append(f"s{var - num_var_originais + 1}")
        row_headers.append("z")
        
        table_data = [headers]
        for i, row in enumerate(self.tableau):
            formatted = [f"{val:.4f}" if abs(val) >= 1e-10 else "0" for val in row]
            table_data.append([row_headers[i]] + formatted)
        
        table = AsciiTable(table_data)
        table.inner_heading_row_border = True
        table.inner_row_border = True
        return f"Iteração {iteracao}", table.table
    
    def obter_solucao(self):
        """Extrai a solução final considerando substituições"""
        num_var_originais = len(self.objetivo_original)
        solucao = [0.0] * num_var_originais
        
        # Valores das variáveis originais (x_i = x_i' + L)
        for i, var in enumerate(self.var_basicas):
            if var < num_var_originais:
                solucao[var] = self.tableau[i, -1]
        
        # Adicionar limites inferiores
        for var, L in self.limites_inferiores.items():
            solucao[var] += L
        
        # Calcular valor objetivo (incluindo constante)
        valor_objetivo = self.tableau[-1, -1] + self.constante_objetivo
        if not self.maximizar:
            valor_objetivo = -valor_objetivo
        
        return solucao, valor_objetivo
    
    def resolver(self):
        """Executa o algoritmo Simplex completo"""
        self.montar_tableau_inicial()
        iteracao = 0
        max_iter = 100
        
        print("\n" + "="*50)
        print(" TABELAUS SIMPLEX ".center(50))
        print("="*50)
        titulo, tabela = self.formato_tableau_terminal(0)
        print(f"\n{titulo} (Inicial)")
        print(tabela)
        
        while iteracao < max_iter:
            col_entrada = self.encontrar_variavel_entrada()
            if col_entrada is None:
                print("\nÓtimo encontrado!")
                break
            
            lin_pivo = self.encontrar_variavel_saida(col_entrada)
            if lin_pivo is None:
                print("\nProblema ilimitado!")
                return None, None
            
            print(f"\nPivô: Linha {lin_pivo+1}, Coluna {col_entrada+1}")
            self.atualizar_tableau(lin_pivo, col_entrada)
            
            titulo, tabela = self.formato_tableau_terminal(iteracao+1)
            print(f"\n{titulo}")
            print(tabela)
            
            iteracao += 1
            time.sleep(0.5)
        
        solucao, valor = self.obter_solucao()
        
        print("\n" + "="*50)
        print(" SOLUÇÃO FINAL ".center(50))
        print("="*50)
        for i, x in enumerate(solucao):
            print(f"x{i+1} = {x:.4f}")
        print(f"\nValor da função objetivo: {valor:.4f}")
        return solucao, valor

# Funções de parsing 
def parser_funcao_objetivo(entrada):
    entrada = entrada.lower()
    maximizar = "max" in entrada
    padrao = r'(?:max|min)\s*(\w+)\s*=\s*(.+)'
    match = re.search(padrao, entrada, re.IGNORECASE)
    
    if not match:
        raise ValueError("Formato da função objetivo inválido")
    
    lado_dir = match.group(2)
    termos = re.findall(r'([+-]?\s*\d*\.?\d*)\s*x(\d+)', lado_dir)
    
    coefs = {}
    for termo in termos:
        coef_str, var = termo
        var_idx = int(var) - 1
        
        if coef_str.strip() in ["", "+"]:
            coef = 1.0
        elif coef_str.strip() == "-":
            coef = -1.0
        else:
            coef = float(coef_str.replace(" ", ""))
        
        coefs[var_idx] = coef
    
    num_vars = max(coefs.keys()) + 1 if coefs else 0
    objetivo = [0.0] * num_vars
    for var, coef in coefs.items():
        objetivo[var] = coef
    
    return objetivo, maximizar

def parser_restricao(entrada, num_variaveis):
    sinais_validos = ["<=", ">=", "="]
    sinal = None
    for s in sinais_validos:
        if s in entrada:
            sinal = s
            partes = entrada.split(s)
            break
    
    if not sinal:
        raise ValueError(f"Sinal inválido na restrição: {entrada}")
    
    lado_esq = partes[0].strip()
    lado_dir = float(partes[1].strip())
    
    termos = re.findall(r'([+-]?\s*\d*\.?\d*)\s*x(\d+)', lado_esq)
    coefs = {}
    
    for termo in termos:
        coef_str, var = termo
        var_idx = int(var) - 1
        
        if coef_str.strip() in ["", "+"]:
            coef = 1.0
        elif coef_str.strip() == "-":
            coef = -1.0
        else:
            coef = float(coef_str.replace(" ", ""))
        
        coefs[var_idx] = coef
    
    restricao = [0.0] * num_variaveis
    for var, coef in coefs.items():
        if var >= num_variaveis:
            raise ValueError(f"Variável x{var+1} não existe na função objetivo")
        restricao[var] = coef
    
    return restricao, sinal, lado_dir

def parser_restricoes_variaveis(entrada):
    restricoes = {}
    partes = entrada.split(',')
    for parte in partes:
        parte = parte.strip()
        match = re.search(r'x(\d+)\s*([<>=]+)\s*([+-]?\d+\.?\d*)', parte)
        if match:
            var = int(match.group(1)) - 1
            sinal = match.group(2)
            valor = float(match.group(3))
            restricoes[var] = (sinal, valor)
    return restricoes

def solicitar_entrada_usuario():
    print("\n" + "="*50)
    print(" ENTRADA DO PROBLEMA ".center(50))
    print("="*50)
    
    while True:
        try:
            # Função objetivo
            print("\nDigite a função objetivo (ex: 'Max Z = 3x1 + 2x2')")
            entrada_objetivo = input("> ")
            objetivo, maximizar = parser_funcao_objetivo(entrada_objetivo)
            num_vars = len(objetivo)
            
            # Restrições
            print("\nDigite as restrições (uma por linha, 'fim' para terminar):")
            restricoes = []
            sinais = []
            b = []
            var_restricoes = {}
            
            while True:
                entrada = input("Restrição> ").strip()
                if entrada.lower() in ["fim", ""]:
                    break
                
                # Verificar se é restrição de variável
                if re.match(r'x\d+\s*[<>=]', entrada):
                    novas = parser_restricoes_variaveis(entrada)
                    var_restricoes.update(novas)
                else:
                    restricao, sinal, valor = parser_restricao(entrada, num_vars)
                    restricoes.append(restricao)
                    sinais.append(sinal)
                    b.append(valor)
            
            # Confirmação
            print("\n" + "="*50)
            print(" PROBLEMA CONFIGURADO ".center(50))
            print("="*50)
            print("Função objetivo:")
            print(f"{'Max' if maximizar else 'Min'} Z = " + 
                  " + ".join([f"{c}x{i+1}" for i, c in enumerate(objetivo) if c != 0]))
            
            print("\nRestrições:")
            for i, (r, s, v) in enumerate(zip(restricoes, sinais, b)):
                termos = [f"{c}x{j+1}" for j, c in enumerate(r) if c != 0]
                print(f"{' + '.join(termos)} {s} {v}")
            
            if var_restricoes:
                print("\nRestrições de variáveis:")
                for var, (s, v) in var_restricoes.items():
                    print(f"x{var+1} {s} {v}")
            
            confirmar = input("\nConfirmar (s/n)? ").lower()
            if confirmar == "s":
                return objetivo, restricoes, sinais, b, var_restricoes, maximizar
            
        except Exception as e:
            print(f"Erro: {e}\nTente novamente.")

def main():
    while True:
        try:
            objetivo, restricoes, sinais, b, var_restricoes, maximizar = solicitar_entrada_usuario()
            simplex = SimplexTableau(objetivo, restricoes, sinais, b, var_restricoes, maximizar)
            simplex.resolver()
            
            continuar = input("\nNovo problema (s/n)? ").lower()
            if continuar != "s":
                break
        except Exception as e:
            print(f"Erro: {e}")
            print("Reiniciando...\n")

if __name__ == "__main__":
    main()