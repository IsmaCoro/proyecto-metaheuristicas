# Proyecto Final — Algoritmos Metaheurísticos

Sistema interactivo de **Asignación de Recursos en la Nube** usando metaheurísticas: Algoritmo Genético (GA), Colonia de Hormigas (ACO) e Híbrido GA-ACO.

## Qué hace

- Múltiples usuarios agregan tareas a servidores desde su celular en tiempo real
- Los algoritmos optimizan la distribución automáticamente
- El admin controla el flujo: pausar entradas, quitar/poner cooldown, reiniciar
- Gráficas de convergencia, análisis Wilcoxon y sensibilidad de parámetros

## Estructura

```
├── main.py                      # Servidor Flask + API REST
├── requirements.txt             # Dependencias
├── explicacion_conceptos.txt    # Referencia de conceptos (fitness, Wilcoxon, etc.)
├── README.md
├── algoritmos/
│   ├── problema_nube.py         # Modelo del problema (servidores, tareas, fitness)
│   ├── genetico.py              # Algoritmo Genético
│   ├── colonia_hormigas.py      # Colonia de Hormigas (ACO)
│   └── hibrido.py               # Híbrido GA-ACO + búsqueda local
├── templates/
│   ├── votar.html               # Interfaz de votación (compañeros)
│   └── panel.html               # Panel de control (admin)
└── static/
    └── estilos.css              # Tema oscuro
```

## Instalación

```bash
pip install flask numpy scipy
```

## Ejecución

```bash
python main.py
```

## URLs

| Quién | URL |
|-------|-----|
| Compañeros | `http://TU_IP:5000` |
| Admin | `http://TU_IP:5000/panel?clave=admin` |

Para acceso fuera de la red local, usar [ngrok](https://ngrok.com):
```bash
pip install pyngrok
ngrok http 5000
```

## Controles del admin

| Botón | Función |
|-------|---------|
| Pausar | Bloquea todas las entradas de tareas |
| Timer ON/OFF | Activa/desactiva cooldown de 10s entre clicks |
| Reiniciar | Borra todas las tareas |
| Optimizar | Ejecuta los 3 algoritmos manualmente |

## Pestañas de análisis

| Pestaña | Contenido |
|---------|-----------|
| Carga | Barras comparativas antes vs después por servidor |
| Convergencia | Fitness vs iteraciones (GA, ACO, Híbrido) |
| Wilcoxon | 10 corridas + prueba estadística entre pares |
| Sensibilidad | Fitness vs población y Fitness vs iteraciones |

## Características técnicas

- 3 algoritmos metaheurísticos (GA, ACO, Híbrido GA-ACO)
- Fitness multiobjetivo: balance + energía + tiempo de respuesta
- Restricciones con penalización (CPU/RAM)
- Baseline determinístico (Greedy)
- Validación estadística Wilcoxon / Mann-Whitney U
- Análisis de sensibilidad de parámetros
- Soporte para 20+ usuarios simultáneos (threading.Lock)
- Polling cada 2-3 segundos

## Tecnologías

- **Backend:** Python 3 + Flask
- **Algoritmos:** NumPy, SciPy
- **Frontend:** HTML5 + CSS3 + JavaScript + Chart.js
- **Túnel:** ngrok (opcional, para acceso remoto)

## Autores

- [Tu nombre aquí]

## Licencia

Proyecto académico — Universidad de Guadalajara, 2026
