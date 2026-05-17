"""
Modelo del problema de asignación de recursos en la nube.
Tres objetivos: balance de carga, consumo energético y tiempo de respuesta.
"""

import numpy as np
import random


class ProblemaCloud:

    def __init__(self, n_servidores=6, n_tareas=20, semilla=42):
        self.n_servidores = n_servidores
        self.n_tareas = n_tareas
        self.semilla = semilla
        random.seed(semilla)
        np.random.seed(semilla)
        self.servidores = self._generar_servidores()
        self.tareas = self._generar_tareas()

    def _generar_servidores(self):
        # Tipos: (cpus, ram_gb, watts_por_cpu)
        tipos = [(4, 16, 12), (8, 32, 9), (16, 64, 7), (32, 128, 5)]
        servidores = []
        for i in range(self.n_servidores):
            t = tipos[i % len(tipos)]
            servidores.append({
                "id": f"S{i}", "cpu_total": t[0], "ram_total": t[1],
                "watts_por_cpu": t[2], "watts_base": t[0] * 2,
            })
        return servidores

    def _generar_tareas(self):
        tareas = []
        for i in range(self.n_tareas):
            cpu = random.randint(1, 4)
            tareas.append({
                "id": f"T{i}", "cpu": cpu,
                "ram": cpu * random.choice([2, 4]),
                "prioridad": random.uniform(0.5, 2.0),
            })
        return tareas

    def evaluar(self, asignacion, w_balance=0.4, w_energia=0.3, w_tiempo=0.3):
        """Evalúa una asignación y retorna fitness + métricas."""
        n = self.n_servidores
        carga_cpu = [0] * n
        carga_ram = [0] * n

        for i, sid in enumerate(asignacion):
            if 0 <= sid < n:
                carga_cpu[sid] += self.tareas[i]["cpu"]
                carga_ram[sid] += self.tareas[i]["ram"]

        # Balance: desviación estándar de porcentajes de uso
        porcentajes = []
        for j in range(n):
            cap = self.servidores[j]["cpu_total"]
            porcentajes.append((carga_cpu[j] / cap * 100) if cap > 0 else 0)
        balance = float(np.std(porcentajes))

        # Energía total del datacenter
        energia = 0.0
        for j in range(n):
            srv = self.servidores[j]
            if carga_cpu[j] > 0:
                energia += srv["watts_base"] + (carga_cpu[j] * srv["watts_por_cpu"])

        # Tiempo de respuesta: el servidor más saturado
        tiempos = []
        for j in range(n):
            cap = self.servidores[j]["cpu_total"]
            if carga_cpu[j] > 0:
                tiempos.append((carga_cpu[j] / cap) * 10)
            else:
                tiempos.append(0)
        tiempo_max = max(tiempos) if tiempos else 0

        # Penalización por violar restricciones de CPU/RAM
        penalizacion = 0
        saturados = 0
        for j in range(n):
            exceso_cpu = max(0, carga_cpu[j] - self.servidores[j]["cpu_total"])
            exceso_ram = max(0, carga_ram[j] - self.servidores[j]["ram_total"])
            if exceso_cpu > 0 or exceso_ram > 0:
                penalizacion += (exceso_cpu * 50) + (exceso_ram * 25)
                saturados += 1

        # Fitness combinado (menor = mejor)
        fitness = (w_balance * balance) + (w_energia * energia / 100) + \
                  (w_tiempo * tiempo_max * 10) + penalizacion

        return {
            "fitness": round(fitness, 4), "balance": round(balance, 4),
            "energia": round(energia, 2), "tiempo_max": round(tiempo_max, 2),
            "penalizacion": round(penalizacion, 2), "servidores_saturados": saturados,
            "carga_cpu": carga_cpu, "carga_ram": carga_ram, "porcentajes": porcentajes,
        }

    def asignacion_aleatoria(self):
        return [random.randint(0, self.n_servidores - 1) for _ in range(self.n_tareas)]

    def asignacion_greedy(self):
        """Asigna cada tarea al servidor con más capacidad libre (baseline)."""
        carga = [0] * self.n_servidores
        asignacion = []
        for i in range(self.n_tareas):
            mejor = max(range(self.n_servidores),
                        key=lambda j: self.servidores[j]["cpu_total"] - carga[j])
            asignacion.append(mejor)
            carga[mejor] += self.tareas[i]["cpu"]
        return asignacion

    def asignacion_desbalanceada(self):
        """Concentra todo en 2 servidores (para demo)."""
        return [i % 2 for i in range(self.n_tareas)]
