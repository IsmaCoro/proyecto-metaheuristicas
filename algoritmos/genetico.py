"""
Algoritmo Genético — Selección por torneo, cruce uniforme, mutación y elitismo.
"""

import random
import time


class AlgoritmoGenetico:

    def __init__(self, problema, tam_poblacion=60, generaciones=150,
                 prob_cruce=0.85, prob_mutacion=0.15, tam_elite=3, tam_torneo=5):
        self.problema = problema
        self.tam_poblacion = tam_poblacion
        self.generaciones = generaciones
        self.prob_cruce = prob_cruce
        self.prob_mutacion = prob_mutacion
        self.tam_elite = tam_elite
        self.tam_torneo = tam_torneo

    def _crear_poblacion(self):
        # 1 greedy (buena) + resto aleatorias
        pob = [self.problema.asignacion_greedy()]
        for _ in range(self.tam_poblacion - 1):
            pob.append(self.problema.asignacion_aleatoria())
        return pob

    def _seleccion_torneo(self, poblacion, fitness_vals):
        candidatos = random.sample(range(len(poblacion)), self.tam_torneo)
        ganador = min(candidatos, key=lambda i: fitness_vals[i])
        return poblacion[ganador][:]

    def _cruce_uniforme(self, p1, p2):
        return [a if random.random() < 0.5 else b for a, b in zip(p1, p2)]

    def _mutar(self, ind):
        for i in range(len(ind)):
            if random.random() < self.prob_mutacion:
                ind[i] = random.randint(0, self.problema.n_servidores - 1)
        return ind

    def ejecutar(self):
        inicio = time.time()
        poblacion = self._crear_poblacion()
        mejor_global, mejor_fitness = None, float('inf')
        convergencia = []

        for gen in range(self.generaciones):
            fitness_vals = [self.problema.evaluar(ind)["fitness"] for ind in poblacion]

            for i, fit in enumerate(fitness_vals):
                if fit < mejor_fitness:
                    mejor_fitness = fit
                    mejor_global = poblacion[i][:]
            convergencia.append(mejor_fitness)

            # Elitismo: los mejores pasan directo
            ranking = sorted(range(len(poblacion)), key=lambda i: fitness_vals[i])
            nueva = [poblacion[i][:] for i in ranking[:self.tam_elite]]

            while len(nueva) < self.tam_poblacion:
                p1 = self._seleccion_torneo(poblacion, fitness_vals)
                p2 = self._seleccion_torneo(poblacion, fitness_vals)
                hijo = self._cruce_uniforme(p1, p2) if random.random() < self.prob_cruce else p1[:]
                nueva.append(self._mutar(hijo))

            poblacion = nueva

        return {
            "asignacion": mejor_global, "fitness": mejor_fitness,
            "convergencia": convergencia, "tiempo": time.time() - inicio,
            "metricas": self.problema.evaluar(mejor_global),
            "algoritmo": "Algoritmo Genético (GA)",
        }
