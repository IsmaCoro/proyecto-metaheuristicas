from flask import Flask, render_template, jsonify, request, redirect, session
from algoritmos.problema_nube import ProblemaCloud
from algoritmos.genetico import AlgoritmoGenetico
from algoritmos.colonia_hormigas import ColoniaHormigas
from algoritmos.hibrido import HibridoGAACO
import numpy as np
from scipy.stats import wilcoxon, mannwhitneyu
from itertools import combinations
import threading

app = Flask(__name__)
app.secret_key = 'clave_secreta_proyecto_final_2026'

# Configuracion del datacenter simulado
CLAVE_ADMIN = "25052023"
TIPOS_CPU = [4, 8, 16, 32]
N_SERVIDORES = 6

# Estado compartido entre hilos (protegido por lock)
estado = {
    "tareas": [0] * N_SERVIDORES,
    "capacidades": [TIPOS_CPU[i % len(TIPOS_CPU)] for i in range(N_SERVIDORES)],
    "pausado": False,
    "cooldown": True,
}
lock = threading.Lock()

# Datos de hardware por tipo de servidor
TIPOS_NOMBRE = ["Pequeno", "Mediano", "Grande", "Monstruo"]
WATTS_POR_CPU = [12, 9, 7, 5]
WATTS_BASE = [8, 16, 32, 64]
RAM_GB = [16, 32, 64, 128]


# ── Paginas ──

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/votar')
def votar():
    return render_template('votar.html')

@app.route('/verificar', methods=['POST'])
def verificar():
    """Valida la clave y guarda sesion si es correcta."""
    datos = request.get_json()
    clave = datos.get('clave', '') if datos else ''
    if clave == CLAVE_ADMIN:
        session['admin'] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route('/panel')
def panel():
    if not session.get('admin'):
        return redirect('/')
    return render_template('panel.html')


# ── API: lectura de estado ──

@app.route('/estado')
def get_estado():
    """Retorna tareas, capacidades y specs de hardware (polling cada 2-3s)."""
    servidores_info = []
    for i in range(N_SERVIDORES):
        idx = i % len(TIPOS_CPU)
        servidores_info.append({
            "id": f"S{i}",
            "tipo": TIPOS_NOMBRE[idx],
            "cpu": TIPOS_CPU[idx],
            "ram_gb": RAM_GB[idx],
            "watts_base": WATTS_BASE[idx],
            "watts_por_cpu": WATTS_POR_CPU[idx],
            "watts_max": WATTS_BASE[idx] + (TIPOS_CPU[idx] * WATTS_POR_CPU[idx]),
        })

    with lock:
        return jsonify({
            "tareas": estado["tareas"][:],
            "capacidades": estado["capacidades"][:],
            "total": sum(estado["tareas"]),
            "pausado": estado["pausado"],
            "cooldown": estado["cooldown"],
            "servidores": servidores_info,
        })


# ── API: control de tareas ──

@app.route('/agregar/<int:sid>', methods=['POST'])
def agregar(sid):
    """Agrega 1 tarea al servidor indicado. Rechaza si esta pausado."""
    with lock:
        if estado["pausado"]:
            return jsonify({"ok": False, "pausado": True})
        if 0 <= sid < N_SERVIDORES:
            estado["tareas"][sid] += 1
    return jsonify({"ok": True})

@app.route('/pausar', methods=['POST'])
def pausar():
    """Alterna pausado/activo para bloquear entradas."""
    with lock:
        estado["pausado"] = not estado["pausado"]
    return jsonify({"pausado": estado["pausado"]})

@app.route('/cooldown', methods=['POST'])
def toggle_cooldown():
    """Activa/desactiva el timer de 10s entre clicks."""
    with lock:
        estado["cooldown"] = not estado["cooldown"]
    return jsonify({"cooldown": estado["cooldown"]})

@app.route('/reiniciar', methods=['POST'])
def reiniciar():
    """Borra todas las tareas."""
    with lock:
        estado["tareas"] = [0] * N_SERVIDORES
    return jsonify({"ok": True})


# ── API: optimizacion ──

def crear_problema(caps, total):
    """Crea una instancia del problema con las capacidades actuales."""
    n = len(caps)
    problema = ProblemaCloud(n_servidores=n, n_tareas=total, semilla=42)
    for j in range(n):
        problema.servidores[j]["cpu_total"] = caps[j]
        problema.servidores[j]["ram_total"] = caps[j] * 4
    return problema

@app.route('/optimizar', methods=['POST'])
def optimizar():
    """Ejecuta GA, ACO e Hibrido sobre la distribucion actual."""
    with lock:
        tareas = estado["tareas"][:]
        caps = estado["capacidades"][:]

    total = sum(tareas)
    if total == 0:
        return jsonify({"error": "Sin tareas"}), 400

    n = len(caps)
    problema = crear_problema(caps, total)

    # Asignacion del usuario (baseline)
    asig_usr = []
    for j in range(n):
        asig_usr.extend([j] * tareas[j])
    met_antes = problema.evaluar(asig_usr)

    # Greedy determinista
    met_greedy = problema.evaluar(problema.asignacion_greedy())

    # Tres metaheuristicas
    res = {}
    res['GA'] = AlgoritmoGenetico(problema, tam_poblacion=60, generaciones=150).ejecutar()
    res['ACO'] = ColoniaHormigas(problema, n_hormigas=20, n_iteraciones=150).ejecutar()
    res['Híbrido'] = HibridoGAACO(problema, tam_poblacion=80, n_iteraciones=150).ejecutar()

    mejor_k = min(res, key=lambda k: res[k]['fitness'])
    mejor = res[mejor_k]

    # Contar tareas por servidor en la solucion optima
    tareas_opt = [0] * n
    for sid in mejor['asignacion']:
        if 0 <= sid < n:
            tareas_opt[sid] += 1

    # Respuesta JSON
    resp = {
        "mejor_algoritmo": mejor_k,
        "tareas_optimizadas": tareas_opt,
        "antes": {
            "balance": round(met_antes['balance'], 2),
            "energia": round(met_antes['energia'], 1),
            "tiempo_max": round(met_antes['tiempo_max'], 2),
            "saturados": met_antes['servidores_saturados'],
            "fitness": round(met_antes['fitness'], 2),
        },
        "greedy": {"fitness": round(met_greedy['fitness'], 2)},
        "despues": {
            "balance": round(mejor['metricas']['balance'], 2),
            "energia": round(mejor['metricas']['energia'], 1),
            "tiempo_max": round(mejor['metricas']['tiempo_max'], 2),
            "saturados": mejor['metricas']['servidores_saturados'],
            "fitness": round(mejor['metricas']['fitness'], 2),
        },
        "algoritmos": {},
    }

    for k in ['GA', 'ACO', 'Híbrido']:
        r = res[k]
        conv = r['convergencia']
        paso = max(1, len(conv) // 50)
        t_algo = [0] * n
        for sid in r['asignacion']:
            if 0 <= sid < n:
                t_algo[sid] += 1
        resp["algoritmos"][k] = {
            "fitness": round(r['fitness'], 2),
            "tiempo": round(r['tiempo'], 3),
            "convergencia": [round(v, 2) for v in conv[::paso]],
            "tareas_por_servidor": t_algo,
        }

    return jsonify(resp)


# ── API: analisis estadistico (10 corridas + Wilcoxon) ──

@app.route('/analisis', methods=['POST'])
def analisis():
    """Compara algoritmos con multiples corridas y prueba de Wilcoxon."""
    with lock:
        caps = estado["capacidades"][:]
        total = sum(estado["tareas"])

    if total == 0:
        return jsonify({"error": "Sin tareas"}), 400

    n = len(caps)
    n_corridas = 10

    # Ejecutar cada algoritmo n_corridas veces con semillas distintas
    todas = {'GA': [], 'ACO': [], 'Híbrido': []}
    for c in range(n_corridas):
        p = crear_problema(caps, total)
        p.semilla = 42 + c + 1
        todas['GA'].append(AlgoritmoGenetico(p, generaciones=100).ejecutar()['fitness'])
        todas['ACO'].append(ColoniaHormigas(p, n_iteraciones=100).ejecutar()['fitness'])
        todas['Híbrido'].append(HibridoGAACO(p, n_iteraciones=100).ejecutar()['fitness'])

    # Estadisticas descriptivas
    stats = {}
    for k in todas:
        a = np.array(todas[k])
        stats[k] = {
            'media': round(float(a.mean()), 2),
            'mejor': round(float(a.min()), 2),
            'peor': round(float(a.max()), 2),
            'desv_std': round(float(a.std()), 2),
            'valores': [round(float(v), 2) for v in todas[k]],
        }

    # Prueba de Wilcoxon / Mann-Whitney entre pares
    wilcoxon_res = []
    for a, b in combinations(['GA', 'ACO', 'Híbrido'], 2):
        da, db = np.array(todas[a]), np.array(todas[b])
        try:
            stat, pv = wilcoxon(da, db)
            prueba = 'Wilcoxon'
        except ValueError:
            stat, pv = mannwhitneyu(da, db, alternative='two-sided')
            prueba = 'Mann-Whitney'
        ganador = a if np.mean(da) < np.mean(db) else b
        wilcoxon_res.append({
            'par': f'{a} vs {b}',
            'prueba': prueba,
            'p_valor': round(float(pv), 6),
            'significativo': pv < 0.05,
            'mejor': ganador if pv < 0.05 else None,
        })

    return jsonify({"estadisticas": stats, "wilcoxon": wilcoxon_res})


# ── API: sensibilidad de parametros ──

@app.route('/sensibilidad', methods=['POST'])
def sensibilidad():
    """Varia poblacion e iteraciones para medir impacto en fitness."""
    with lock:
        caps = estado["capacidades"][:]
        total = sum(estado["tareas"])

    if total == 0:
        return jsonify({"error": "Sin tareas"}), 400

    n = len(caps)

    # Variacion de poblacion (iteraciones fijas a 80)
    poblaciones = [20, 40, 60, 80, 100]
    res_pob = {'GA': [], 'ACO': [], 'Híbrido': []}
    for tam in poblaciones:
        p = crear_problema(caps, total)
        res_pob['GA'].append(round(
            AlgoritmoGenetico(p, tam_poblacion=tam, generaciones=80).ejecutar()['fitness'], 2))
        res_pob['ACO'].append(round(
            ColoniaHormigas(p, n_hormigas=max(5, tam // 3), n_iteraciones=80).ejecutar()['fitness'], 2))
        res_pob['Híbrido'].append(round(
            HibridoGAACO(p, tam_poblacion=tam, n_iteraciones=80).ejecutar()['fitness'], 2))

    # Variacion de iteraciones (poblacion fija a 60)
    iteraciones = [30, 60, 100, 150, 200]
    res_iter = {'GA': [], 'ACO': [], 'Híbrido': []}
    for it in iteraciones:
        p = crear_problema(caps, total)
        res_iter['GA'].append(round(
            AlgoritmoGenetico(p, tam_poblacion=60, generaciones=it).ejecutar()['fitness'], 2))
        res_iter['ACO'].append(round(
            ColoniaHormigas(p, n_hormigas=20, n_iteraciones=it).ejecutar()['fitness'], 2))
        res_iter['Híbrido'].append(round(
            HibridoGAACO(p, tam_poblacion=60, n_iteraciones=it).ejecutar()['fitness'], 2))

    return jsonify({
        "poblacion": {"valores": poblaciones, "resultados": res_pob},
        "iteraciones": {"valores": iteraciones, "resultados": res_iter},
    })


if __name__ == '__main__':
    print("\n  Proyecto Final corriendo en http://0.0.0.0:5000")
    print("  Companeros: http://TU_IP:5000")
    print("  Admin:      http://TU_IP:5000 -> contrasena\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
