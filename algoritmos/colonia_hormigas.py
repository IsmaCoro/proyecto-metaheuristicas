"""
Colonia de Hormigas (ACO) — Feromonas + heurística de capacidad libre.
"""

import numpy as np
import random
import time


class ColoniaHormigas:

    def __init__(self, problema, n_hormigas=30, n_iteraciones=150,
                 alfa=1.0, beta=2.0, evaporacion=0.3, Q=100):
        self.problema = problema
        self.n_hormigas = n_hormigas
        self.n_iteraciones = n_iteraciones
        self.alfa = alfa
        self.beta = beta
        self.evaporacion = evaporacion
        self.Q = Q

    def _inicializar_feromonas(self):
        # Matriz [tareas x servidores], todas iguales al inicio
        return np.ones((self.problema.n_tareas, self.problema.n_servidores)) \
               / self.problema.n_servidores

    def _heuristica(self, tarea_idx, srv_idx, carga_actual):
        # Favorece servidores con más espacio libre
        srv = self.problema.servidores[srv_idx]
        tarea = self.problema.tareas[tarea_idx]
        libre = srv["cpu_total"] - carga_actual[srv_idx]  # espacio disponible
        if libre < tarea["cpu"]:
            return 0.01  # no cabe, penalizar
        return libre / srv["cpu_total"]  # fraccion de espacio libre (0 a 1)

    def _construir_solucion(self, feromonas):
        # Cada hormiga asigna tarea por tarea.
        asig = []
        carga = [0] * self.problema.n_servidores

        for i in range(self.problema.n_tareas):
            probs = []
            for j in range(self.problema.n_servidores):
                tau = feromonas[i][j] ** self.alfa  # feromona (memoria colectiva)
                eta = self._heuristica(i, j, carga) ** self.beta  # heuristica (espacio libre)
                probs.append(tau * eta)  # probabilidad sin normalizar

            total = sum(probs)
            if total == 0:
                elegido = random.randint(0, self.problema.n_servidores - 1)
            else:
                probs = [p / total for p in probs]  # normalizar para que sumen 1
                elegido = int(np.random.choice(range(self.problema.n_servidores), p=probs))  # ruleta

            asig.append(elegido)
            carga[elegido] += self.problema.tareas[i]["cpu"]
        return asig

    def _actualizar_feromonas(self, feromonas, soluciones, fitness_vals):
        feromonas *= (1 - self.evaporacion)  # evaporacion: se pierde 30%
        for asig, fit in zip(soluciones, fitness_vals):
            if fit > 0:
                deposito = self.Q / fit  # mejor fitness = mas deposito
                for i, srv in enumerate(asig):
                    feromonas[i][srv] += deposito  # reforzar buenas asignaciones
        return feromonas

    def ejecutar(self):
        inicio = time.time()
        feromonas = self._inicializar_feromonas()  # feromonas uniformes al inicio
        mejor_asig, mejor_fitness = None, float('inf')
        convergencia = []  # para la grafica de convergencia

        for it in range(self.n_iteraciones):
            soluciones, fitness_vals = [], []

            for _ in range(self.n_hormigas):
                asig = self._construir_solucion(feromonas)
                fit = self.problema.evaluar(asig)["fitness"]
                soluciones.append(asig)
                fitness_vals.append(fit)
                if fit < mejor_fitness:
                    mejor_fitness = fit
                    mejor_asig = asig[:]

            feromonas = self._actualizar_feromonas(feromonas, soluciones, fitness_vals)  # evaporar + depositar
            convergencia.append(mejor_fitness)  # guardar para grafica

        return {
            "asignacion": mejor_asig, "fitness": mejor_fitness,
            "convergencia": convergencia, "tiempo": time.time() - inicio,
            "metricas": self.problema.evaluar(mejor_asig),
            "algoritmo": "Colonia de Hormigas (ACO)",
        }
