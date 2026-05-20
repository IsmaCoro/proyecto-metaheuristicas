"""
Híbrido GA-ACO — Combina operadores genéticos con feromonas + búsqueda local.
La mutación es guiada por feromonas en lugar de aleatoria.
"""

import numpy as np
import random
import time


class HibridoGAACO:

    def __init__(self, problema, tam_poblacion=80, n_iteraciones=150,
                 prob_cruce=0.85, prob_mutacion=0.15,
                 tam_elite=5, tam_torneo=5,
                 alfa=1.0, beta=2.0, evaporacion=0.3, Q=100, peso_aco=0.3):
        self.problema = problema
        self.tam_poblacion = tam_poblacion
        self.n_iteraciones = n_iteraciones
        self.prob_cruce = prob_cruce
        self.prob_mutacion = prob_mutacion
        self.tam_elite = tam_elite
        self.tam_torneo = tam_torneo
        self.alfa = alfa
        self.beta = beta
        self.evaporacion = evaporacion
        self.Q = Q
        self.peso_aco = peso_aco  # 30% de la poblacion se genera con ACO

    def _crear_poblacion(self):
        # 1 greedy + resto aleatorias
        pob = [self.problema.asignacion_greedy()]
        for _ in range(self.tam_poblacion - 1):
            pob.append(self.problema.asignacion_aleatoria())
        return pob

    def _crear_feromonas(self):
        # Matriz de feromonas [tareas x servidores], inicialmente uniforme
        return np.ones((self.problema.n_tareas, self.problema.n_servidores)) \
               / self.problema.n_servidores

    def _fitness(self, asig):
        return self.problema.evaluar(asig)["fitness"]

    def _seleccion_torneo(self, pob, fits):
        # Igual que en el GA: elige 5 al azar, gana el mejor
        cands = random.sample(range(len(pob)), self.tam_torneo)  # 5 indices al azar
        return pob[min(cands, key=lambda i: fits[i])][:]  # gana el de menor fitness

    def _cruce_uniforme(self, p1, p2):
        # Igual que en el GA: mezcla genes 50/50
        return [a if random.random() < 0.5 else b for a, b in zip(p1, p2)]

    def _mutacion_guiada(self, ind, feromonas):
        # DIFERENCIA CLAVE vs GA: en vez de mutar al azar, usa feromonas
        for i in range(len(ind)):
            if random.random() < self.prob_mutacion:
                probs = feromonas[i] ** self.alfa  # probabilidades segun feromona
                total = probs.sum()
                if total > 0:
                    probs = probs / total  # normalizar
                    ind[i] = int(np.random.choice(range(self.problema.n_servidores), p=probs))  # muta hacia servidor con mas feromona
                else:
                    ind[i] = random.randint(0, self.problema.n_servidores - 1)
        return ind

    def _construccion_aco(self, feromonas):
        # Construye una solucion tipo hormiga (igual que en ColoniaHormigas)
        asig = []
        carga = [0] * self.problema.n_servidores
        for i in range(self.problema.n_tareas):
            probs = []
            for j in range(self.problema.n_servidores):
                tau = feromonas[i][j] ** self.alfa  # feromona
                libre = max(0.01, self.problema.servidores[j]["cpu_total"] - carga[j])  # espacio libre
                eta = (libre / self.problema.servidores[j]["cpu_total"]) ** self.beta  # heuristica
                probs.append(tau * eta)
            total = sum(probs)
            if total == 0:
                elegido = random.randint(0, self.problema.n_servidores - 1)
            else:
                probs = [p / total for p in probs]
                elegido = int(np.random.choice(range(self.problema.n_servidores), p=probs))
            asig.append(elegido)
            carga[elegido] += self.problema.tareas[i]["cpu"]
        return asig

    def _actualizar_feromonas(self, feromonas, pob, fits):
        # Solo los top 5 depositan feromonas (elitismo en feromonas)
        feromonas *= (1 - self.evaporacion)  # evaporar 30%
        ranking = sorted(range(len(pob)), key=lambda i: fits[i])  # ordenar por fitness
        for idx in ranking[:self.tam_elite]:  # solo top 5 depositan
            if fits[idx] > 0:
                dep = self.Q / fits[idx]
                for i, srv in enumerate(pob[idx]):
                    feromonas[i][srv] += dep
        return feromonas

    def _busqueda_local(self, asig):
        # Mueve tareas del servidor mas cargado al menos cargado
        mejor = asig[:]
        mejor_fit = self._fitness(mejor)

        for _ in range(50):
            met = self.problema.evaluar(mejor)
            pcts = [met["carga_cpu"][j] / self.problema.servidores[j]["cpu_total"]
                    for j in range(self.problema.n_servidores)]
            mas = max(range(len(pcts)), key=lambda j: pcts[j])  # servidor mas cargado
            menos = min(range(len(pcts)), key=lambda j: pcts[j])  # servidor menos cargado
            if mas == menos:
                break

            tareas_en_mas = [i for i, s in enumerate(mejor) if s == mas]
            if not tareas_en_mas:
                break

            nuevo = mejor[:]
            nuevo[random.choice(tareas_en_mas)] = menos  # mover una tarea al menos cargado
            nuevo_fit = self._fitness(nuevo)
            if nuevo_fit < mejor_fit:
                mejor, mejor_fit = nuevo, nuevo_fit
            else:
                break
        return mejor

    def ejecutar(self):
        inicio = time.time()
        poblacion = self._crear_poblacion()
        feromonas = self._crear_feromonas()
        mejor_global, mejor_fitness = None, float('inf')
        convergencia = []

        for gen in range(self.n_iteraciones):
            fits = [self._fitness(ind) for ind in poblacion]  # evaluar los 80 individuos

            # Actualizar mejor global
            for i, fit in enumerate(fits):
                if fit < mejor_fitness:
                    mejor_fitness = fit
                    mejor_global = poblacion[i][:]
            convergencia.append(mejor_fitness)

            # Actualizar feromonas con elitismo
            feromonas = self._actualizar_feromonas(feromonas, poblacion, fits)

            # Elitismo: top 5 pasan directo
            ranking = sorted(range(len(poblacion)), key=lambda i: fits[i])
            nueva = [poblacion[i][:] for i in ranking[:self.tam_elite]]

            # 70% GA con mutacion guiada por feromonas
            n_ga = int((self.tam_poblacion - self.tam_elite) * (1 - self.peso_aco))
            for _ in range(n_ga):
                p1 = self._seleccion_torneo(poblacion, fits)
                p2 = self._seleccion_torneo(poblacion, fits)
                hijo = self._cruce_uniforme(p1, p2) if random.random() < self.prob_cruce else p1[:]
                nueva.append(self._mutacion_guiada(hijo, feromonas))  # mutacion inteligente (no al azar)

            # 30% construccion tipo ACO
            for _ in range(self.tam_poblacion - len(nueva)):
                nueva.append(self._construccion_aco(feromonas))

            # Busqueda local cada 20 generaciones
            if gen % 20 == 0 and gen > 0:
                idx = min(range(len(nueva)), key=lambda i: self._fitness(nueva[i]))
                nueva[idx] = self._busqueda_local(nueva[idx])

            poblacion = nueva  # reemplazar generacion

        # Refinamiento final del mejor resultado
        mejor_global = self._busqueda_local(mejor_global)
        mejor_fitness = self._fitness(mejor_global)

        return {
            "asignacion": mejor_global, "fitness": mejor_fitness,
            "convergencia": convergencia, "tiempo": time.time() - inicio,
            "metricas": self.problema.evaluar(mejor_global),
            "algoritmo": "Híbrido GA-ACO",
        }
