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

# Configuración
CLAVE_ADMIN = "25052023"

TIPOS_CPU = [4, 8, 16, 32]
N_SERVIDORES = 6

estado = {
    "tareas": [0] * N_SERVIDORES,
    "capacidades": [TIPOS_CPU[i % len(TIPOS_CPU)] for i in range(N_SERVIDORES)],
    "pausado": False,
    "cooldown": True,
}
lock = threading.Lock()


# Rutas

@app.route('/')
def inicio():
    return render_template('inicio.html')


@app.route('/votar')
def votar():
    return render_template('votar.html')


@app.route('/verificar', methods=['POST'])
def verificar():
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


# ── API: estado actual ──

@app.route('/estado')
def get_estado():
    """Retorna el estado actual (polling)."""
    tipos_nombre = ["Pequeño", "Mediano", "Grande", "Monstruo"]
    watts_por_cpu = [12, 9, 7, 5]
    watts_base = [8, 16, 32, 64]
    ram = [16, 32, 64, 128]

    servidores_info = []
    for i in range(N_SERVIDORES):
        tipo_idx = i % len(TIPOS_CPU)
        servidores_info.append({
            "id": f"S{i}",
            "tipo": tipos_nombre[tipo_idx],
            "cpu": TIPOS_CPU[tipo_idx],
            "ram_gb": ram[tipo_idx],
            "watts_base": watts_base[tipo_idx],
            "watts_por_cpu": watts_por_cpu[tipo_idx],
            "watts_max": watts_base[tipo_idx] + (TIPOS_CPU[tipo_idx] * watts_por_cpu[tipo_idx]),
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


# ── API: agregar tarea ──

@app.route('/agregar/<int:sid>', methods=['POST'])
def agregar(sid):
    """Un compañero agrega 1 tarea al servidor sid."""
    with lock:
        if estado["pausado"]:
            return jsonify({"ok": False, "pausado": True})
        if 0 <= sid < N_SERVIDORES:
            estado["tareas"][sid] += 1
    return jsonify({"ok": True})


# ── API: pausar/reanudar ──

@app.route('/pausar', methods=['POST'])
def pausar():
    """Alterna el estado pausado/activo."""
    with lock:
        estado["pausado"] = not estado["pausado"]
    return jsonify({"pausado": estado["pausado"]})


@app.route('/cooldown', methods=['POST'])
def toggle_cooldown():
    """Alterna el cooldown de 10s para los votos."""
    with lock:
        estado["cooldown"] = not estado["cooldown"]
    return jsonify({"cooldown": estado["cooldown"]})


# ── API: reiniciar ──

@app.route('/reiniciar', methods=['POST'])
def reiniciar():
    """Resetea todas las tareas a 0."""
    with lock:
        estado["tareas"] = [0] * N_SERVIDORES
    return jsonify({"ok": True})


# ── API: optimizar ──

@app.route('/optimizar', methods=['POST'])
def optimizar():
    """Ejecuta los 3 algoritmos y retorna resultados."""
    with lock:
        tareas = estado["tareas"][:]
        caps = estado["capacidades"][:]

    total = sum(tareas)
    if total == 0:
        return jsonify({"error": "Sin tareas"}), 400

    n = len(caps)
    problema = ProblemaCloud(n_servidores=n, n_tareas=total, semilla=42)
    for j in range(n):
        problema.servidores[j]["cpu_total"] = caps[j]
        problema.servidores[j]["ram_total"] = caps[j] * 4

    # Asignación del usuario
    asig_usr = []
    for j in range(n):
        asig_usr.extend([j] * tareas[j])

    met_antes = problema.evaluar(asig_usr)

    # Baseline greedy
    asig_greedy = problema.asignacion_greedy()
    met_greedy = problema.evaluar(asig_greedy)

    # Ejecutar algoritmos
    res = {}
    res['GA'] = AlgoritmoGenetico(problema, tam_poblacion=60, generaciones=150).ejecutar()
    res['ACO'] = ColoniaHormigas(problema, n_hormigas=20, n_iteraciones=150).ejecutar()
    res['Híbrido'] = HibridoGAACO(problema, tam_poblacion=80, n_iteraciones=150).ejecutar()

    mejor_k = min(res, key=lambda k: res[k]['fitness'])
    mejor = res[mejor_k]

    tareas_opt = [0] * n
    for sid in mejor['asignacion']:
        if 0 <= sid < n:
            tareas_opt[sid] += 1

    # Armar respuesta
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
        "greedy": {
            "fitness": round(met_greedy['fitness'], 2),
        },
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


# ── API: análisis estadístico ──

@app.route('/analisis', methods=['POST'])
def analisis():
    """Múltiples corridas + prueba de Wilcoxon."""
    with lock:
        caps = estado["capacidades"][:]
        total = sum(estado["tareas"])

    if total == 0:
        return jsonify({"error": "Sin tareas"}), 400

    n = len(caps)
    n_corridas = 10

    todas = {'GA': [], 'ACO': [], 'Híbrido': []}
    for c in range(n_corridas):
        p = ProblemaCloud(n_servidores=n, n_tareas=total, semilla=42 + c + 1)
        for j in range(n):
            p.servidores[j]["cpu_total"] = caps[j]
            p.servidores[j]["ram_total"] = caps[j] * 4
        todas['GA'].append(AlgoritmoGenetico(p, generaciones=100).ejecutar()['fitness'])
        todas['ACO'].append(ColoniaHormigas(p, n_iteraciones=100).ejecutar()['fitness'])
        todas['Híbrido'].append(HibridoGAACO(p, n_iteraciones=100).ejecutar()['fitness'])

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


# ── API: análisis de sensibilidad ──

@app.route('/sensibilidad', methods=['POST'])
def sensibilidad():
    """
    Varía parámetros clave y mide el impacto en el fitness.
    Esto cumple el requisito de análisis de sensibilidad (nivel avanzado).
    """
    with lock:
        caps = estado["capacidades"][:]
        total = sum(estado["tareas"])

    if total == 0:
        return jsonify({"error": "Sin tareas"}), 400

    n = len(caps)

    # Variaciones de tamaño de población
    poblaciones = [20, 40, 60, 80, 100]
    res_poblacion = {'GA': [], 'ACO': [], 'Híbrido': []}
    for tam in poblaciones:
        p = ProblemaCloud(n_servidores=n, n_tareas=total, semilla=42)
        for j in range(n):
            p.servidores[j]["cpu_total"] = caps[j]
            p.servidores[j]["ram_total"] = caps[j] * 4
        res_poblacion['GA'].append(round(
            AlgoritmoGenetico(p, tam_poblacion=tam, generaciones=80).ejecutar()['fitness'], 2))
        res_poblacion['ACO'].append(round(
            ColoniaHormigas(p, n_hormigas=max(5, tam // 3), n_iteraciones=80).ejecutar()['fitness'], 2))
        res_poblacion['Híbrido'].append(round(
            HibridoGAACO(p, tam_poblacion=tam, n_iteraciones=80).ejecutar()['fitness'], 2))

    # Variaciones de iteraciones
    iteraciones = [30, 60, 100, 150, 200]
    res_iteraciones = {'GA': [], 'ACO': [], 'Híbrido': []}
    for it in iteraciones:
        p = ProblemaCloud(n_servidores=n, n_tareas=total, semilla=42)
        for j in range(n):
            p.servidores[j]["cpu_total"] = caps[j]
            p.servidores[j]["ram_total"] = caps[j] * 4
        res_iteraciones['GA'].append(round(
            AlgoritmoGenetico(p, tam_poblacion=60, generaciones=it).ejecutar()['fitness'], 2))
        res_iteraciones['ACO'].append(round(
            ColoniaHormigas(p, n_hormigas=20, n_iteraciones=it).ejecutar()['fitness'], 2))
        res_iteraciones['Híbrido'].append(round(
            HibridoGAACO(p, tam_poblacion=60, n_iteraciones=it).ejecutar()['fitness'], 2))

    return jsonify({
        "poblacion": {"valores": poblaciones, "resultados": res_poblacion},
        "iteraciones": {"valores": iteraciones, "resultados": res_iteraciones},
    })


if __name__ == '__main__':
    print("\n  ☁️  Proyecto Final corriendo en http://0.0.0.0:5000")
    print("  📱  Compañeros:  http://TU_IP:5000")
    print("  💻  Tu panel:    http://TU_IP:5000/panel?clave=admin\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
