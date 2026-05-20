# 📚 Guía de Estudio — Proyecto Final: Optimización de Recursos en la Nube

---

## 1. EL PROBLEMA

### ¿Qué resuelve tu proyecto?
Asignar **tareas** (procesos, peticiones) a **servidores** de un datacenter de la forma más eficiente posible. Cada tarea necesita CPU y RAM, cada servidor tiene capacidad limitada.

### ¿Por qué es difícil?
Es un problema **NP-duro** (similar a bin packing). Con 60 tareas y 6 servidores hay **6⁶⁰ = 4.8 × 10⁴⁶** combinaciones. No se pueden probar todas.

### ¿Qué es NP-duro?
Un problema para el cual **no se conoce** un algoritmo que lo resuelva óptimamente en tiempo polinomial. A medida que crece el tamaño, el tiempo crece **exponencialmente**. Las metaheurísticas no garantizan la solución óptima, pero encuentran soluciones *muy buenas* en tiempo razonable.

### ¿Qué datos tiene cada servidor?
```python
# 4 tipos de servidor que se repiten cíclicamente
tipos = [(4 CPUs, 16 GB RAM, 12 W/CPU),    # Pequeño
         (8 CPUs, 32 GB RAM, 9 W/CPU),     # Mediano
         (16 CPUs, 64 GB RAM, 7 W/CPU),    # Grande
         (32 CPUs, 128 GB RAM, 5 W/CPU)]   # Monstruo
```
- Servidores pequeños gastan más watts por CPU (ineficientes)
- Servidores grandes gastan menos watts por CPU (eficientes)
- Con 6 servidores: S0=Pequeño, S1=Mediano, S2=Grande, S3=Monstruo, S4=Pequeño, S5=Mediano

### ¿Qué datos tiene cada tarea?
```python
tarea = {
    "cpu": 1-4,           # CPUs que necesita (aleatorio)
    "ram": cpu × (2 o 4), # RAM proporcional al CPU
    "prioridad": 0.5-2.0  # (no se usa en fitness, reservado)
}
```

---

## 2. FUNCIÓN DE FITNESS

### ¿Qué es el fitness?
Un **número** que mide qué tan buena es una asignación. **Menor = mejor**.

### ¿Cuál es la fórmula?
```
fitness = 0.4 × Balance + 0.3 × (Energía/100) + 0.3 × (Tiempo×10) + Penalización
```

### ¿Qué mide cada componente?

| Componente | Peso | Qué mide | Cómo se calcula |
|---|---|---|---|
| **Balance** | 40% | Distribución equitativa de carga | Desviación estándar del % de uso de CPU entre servidores |
| **Energía** | 30% | Consumo eléctrico total | Suma de watts_base + (CPU usados × watts_por_cpu) por servidor activo |
| **Tiempo** | 30% | Cuello de botella | El servidor más saturado (carga_cpu / capacidad × 10) |
| **Penalización** | Variable | Violación de restricciones | 50 × exceso_CPU + 25 × exceso_RAM por cada servidor saturado |

### ¿Por qué esos pesos?
- **Balance (40%)** es el más importante: un datacenter desbalanceado causa cuellos de botella
- **Energía y Tiempo (30% cada uno)** son secundarios pero relevantes
- Los pesos se podrían ajustar según prioridades del negocio

### ¿Qué es la penalización?
Si una solución asigna **más CPU o RAM** de la que tiene un servidor, recibe un castigo enorme. Esto **fuerza** a los algoritmos a respetar las capacidades físicas. Una solución penalizada nunca gana contra una factible.

### ¿Por qué se divide energía entre 100 y se multiplica tiempo por 10?
Para **normalizar** las escalas. La energía puede ser ~500 watts y el tiempo ~2.5 — sin normalización, la energía dominaría completamente. La normalización pone los tres componentes en rangos comparables.

---

## 3. REPRESENTACIÓN DE SOLUCIONES

### ¿Cómo se representa una solución?
Un **arreglo de enteros** de longitud = número de tareas.

```python
individuo = [2, 0, 5, 1, 3, 0, 4, 2, ...]
#            ↑  ↑  ↑  ↑
#            │  │  │  └─ Tarea 3 → Servidor 1
#            │  │  └──── Tarea 2 → Servidor 5
#            │  └─────── Tarea 1 → Servidor 0
#            └────────── Tarea 0 → Servidor 2
```

Cada posición `i` indica **a qué servidor** se asigna la tarea `i`.

---

## 4. ALGORITMO GENÉTICO (GA)

### ¿En qué se inspira?
En la **evolución natural de Darwin**: selección natural, reproducción, mutación, supervivencia del más apto.

### ¿Cuáles son sus parámetros?
| Parámetro | Valor | Significado |
|---|---|---|
| Población | 60 individuos | Cuántas soluciones se evalúan por generación |
| Generaciones | 150 | Cuántas veces se repite el ciclo evolutivo |
| Prob. cruce | 0.85 (85%) | Probabilidad de que dos padres creen un hijo |
| Prob. mutación | 0.15 (15%) | Probabilidad de cambiar un gen al azar |
| Elitismo | Top 3 | Los 3 mejores pasan directo sin modificarse |
| Torneo | k=5 | Se eligen 5 al azar, gana el mejor |

### ¿Cómo funciona paso a paso?

```
1. CREAR POBLACIÓN INICIAL
   → 1 solución greedy + 59 aleatorias

2. REPETIR por 150 generaciones:
   a. EVALUAR fitness de todos los individuos
   b. ELITISMO: copiar los 3 mejores a la nueva generación
   c. RELLENAR la nueva generación:
      - SELECCIONAR 2 padres por torneo (k=5)
      - CRUCE UNIFORME con 85% de probabilidad
      - MUTAR cada gen con 15% de probabilidad
   d. Reemplazar la población

3. RETORNAR el mejor individuo encontrado
```

### ¿Qué es la selección por torneo?
Se eligen **5 individuos al azar** de la población. El de **menor fitness** (mejor) gana y se selecciona como padre. Es mejor que la selección proporcional porque:
- No depende de la escala del fitness
- Mantiene buena presión selectiva sin ser demasiado agresiva

### ¿Qué es el cruce uniforme?
Dados dos padres, cada gen del hijo se toma del padre A o padre B con **50/50 de probabilidad**:
```
Padre A:  [2, 0, 5, 1, 3, 0]
Padre B:  [4, 3, 1, 5, 0, 2]
Hijo:     [2, 3, 5, 5, 3, 2]  ← cada gen viene de A o B al azar
```

### ¿Por qué cruce uniforme y no de un punto?
En asignación de recursos, **cada tarea es independiente**. No hay relación entre tareas contiguas (a diferencia del TSP donde el orden importa). El cruce uniforme mezcla mejor y da más diversidad.

### ¿Qué es el elitismo?
Guardar los **mejores N individuos** directo a la siguiente generación sin modificarlos. Sin elitismo, el mejor podría perderse por cruce o mutación. Garantiza que **la calidad nunca retrocede**.

### ¿Qué es la mutación?
Cambiar un gen a un **servidor aleatorio**:
```
Antes:  [2, 0, 5, 1, 3, 0]
                 ↓ (mutación en posición 2)
Después: [2, 0, 3, 1, 3, 0]  ← la tarea 2 ahora va al servidor 3
```

### Fortalezas y debilidades del GA
- ✅ **Buena exploración global** — cruce y mutación recorren muchas regiones
- ❌ **Se estanca en óptimos locales** — la mutación es ciega (aleatoria), no tiene memoria

---

## 5. COLONIA DE HORMIGAS (ACO)

### ¿En qué se inspira?
En cómo las **hormigas reales** encuentran el camino más corto a la comida usando **feromonas**.

### ¿Cómo funciona en la naturaleza?
1. Las hormigas exploran al azar
2. Depositan feromona en los caminos que recorren
3. Los caminos más cortos acumulan más feromona (las hormigas los recorren más rápido → más pasadas → más feromona)
4. Las siguientes hormigas **prefieren caminos con más feromona**
5. La colonia **converge** al mejor camino sin que ninguna hormiga conozca el panorama completo

### ¿Cuáles son sus parámetros?
| Parámetro | Valor | Significado |
|---|---|---|
| Hormigas | 30 | Cuántas soluciones construye por iteración |
| Iteraciones | 150 | Cuántas veces se repite el ciclo |
| α (alfa) | 1.0 | Peso de la feromona en la decisión |
| β (beta) | 2.0 | Peso de la heurística (capacidad libre) |
| Evaporación | 0.3 (30%) | Cuánta feromona se pierde por iteración |
| Q | 100 | Constante de depósito de feromona |

### ¿Qué es la matriz de feromonas?
Una tabla de tamaño `tareas × servidores`. La celda `[i][j]` indica **qué tan bueno fue** asignar la tarea `i` al servidor `j` en el pasado.

```
         S0    S1    S2    S3    S4    S5
Tarea 0: 0.17  0.32  0.08  0.25  0.12  0.06
Tarea 1: 0.05  0.10  0.40  0.15  0.20  0.10
...
```

### ¿Cómo construye una hormiga su solución?
Para cada tarea (una por una), calcula la probabilidad de asignarla a cada servidor:

```
Probabilidad(tarea i → servidor j) ∝ τ[i][j]^α × η[i][j]^β
```

Donde:
- **τ (tau)** = feromona → qué tan bueno fue esa asignación antes
- **η (eta)** = heurística → capacidad libre del servidor (más libre = mejor)

### ¿Qué es la heurística η?
```python
η = capacidad_libre / capacidad_total
```
Favorece servidores con **más espacio disponible**. Si un servidor ya está casi lleno, η ≈ 0 y la hormiga casi nunca lo elige.

### ¿Por qué β > α?
Con `β=2.0 > α=1.0`, la **heurística** (espacio libre) tiene **más peso** que la feromona. Esto ayuda a encontrar **soluciones factibles** rápido desde el inicio.

### ¿Cómo se actualizan las feromonas?
```
1. EVAPORACIÓN: τ = τ × (1 - 0.3)     → todas las feromonas se reducen 30%
2. DEPÓSITO: τ[i][j] += Q / fitness    → las buenas soluciones depositan más
```

### ¿Por qué se evaporan las feromonas?
Para **evitar convergencia prematura**. Sin evaporación, las primeras buenas soluciones dominarían para siempre. La evaporación permite "olvidar" caminos malos y explorar nuevos.

### Fortalezas y debilidades del ACO
- ✅ **Buena intensificación** — las feromonas concentran la búsqueda en regiones prometedoras
- ✅ **Memoria colectiva** — aprende de soluciones pasadas
- ❌ **Convergencia lenta al inicio** — las feromonas empiezan uniformes, no guían nada

---

## 6. HÍBRIDO GA-ACO

### ¿Por qué combinar GA y ACO?
Porque sus fortalezas y debilidades son **complementarias**:

| | GA | ACO |
|---|---|---|
| **Fortaleza** | Exploración global | Intensificación |
| **Debilidad** | Mutación ciega | Arranque lento |

El Híbrido toma lo mejor de cada uno.

### ¿Cuáles son sus parámetros?
| Parámetro | Valor |
|---|---|
| Población | 80 individuos |
| Iteraciones | 150 |
| Elitismo | Top 5 |
| Peso ACO | 30% |
| Búsqueda local | Cada 20 generaciones |

### ¿Cómo funciona?
```
1. CREAR POBLACIÓN (1 greedy + 79 aleatorias) + MATRIZ DE FEROMONAS

2. REPETIR 150 veces:
   a. EVALUAR fitness de todos
   b. ACTUALIZAR FEROMONAS (solo top 5 depositan → elitismo)
   c. ELITISMO: copiar top 5

   d. 70% de nuevos individuos → OPERADORES GENÉTICOS:
      - Selección por torneo
      - Cruce uniforme
      - MUTACIÓN GUIADA POR FEROMONAS  ← DIFERENCIA CLAVE

   e. 30% de nuevos individuos → CONSTRUCCIÓN ACO PURA

   f. Cada 20 generaciones: BÚSQUEDA LOCAL al mejor

3. REFINAMIENTO FINAL del mejor global con búsqueda local
4. RETORNAR mejor
```

### ¿Qué es la mutación guiada por feromonas? (DIFERENCIA CLAVE)
En el GA normal, cuando un gen muta, cambia a un **servidor aleatorio** (cualquiera con la misma probabilidad). En el Híbrido, la mutación **consulta la matriz de feromonas** para elegir el servidor:

```python
# GA normal (mutación ciega):
ind[i] = random.randint(0, 5)  # cualquier servidor al azar

# Híbrido (mutación guiada):
probs = feromonas[i] ** alfa   # probabilidad según historial
ind[i] = np.random.choice(servidores, p=probs)  # elige con conocimiento
```

Es mutación con **conocimiento** en vez de mutación ciega.

### ¿Qué es la búsqueda local?
Un procedimiento de **refinamiento** que mejora incrementalmente la mejor solución:
```
REPETIR hasta 50 veces:
  1. Encontrar el servidor MÁS cargado
  2. Encontrar el servidor MENOS cargado
  3. Mover una tarea del más cargado al menos cargado
  4. Si mejora el fitness → aceptar
  5. Si no mejora → parar
```

### ¿Por qué 70% GA y 30% ACO?
- GA necesita **más individuos** para explorar el espacio de búsqueda
- ACO es más **eficiente con menos** individuos (construcción secuencial)
- 70/30 es un balance empírico que dio buenos resultados

### Los 3 componentes del Híbrido
```
EXPLORACIÓN  → GA (cruce + mutación) → buscar regiones nuevas
INTENSIFICACIÓN → Feromonas (guían la mutación + 30% ACO) → profundizar en buenas regiones
REFINAMIENTO → Búsqueda local (cada 20 gen + final) → pulir el resultado
```

### Analogía: buscar oro
1. **GA** = explorar un territorio amplio buscando indicios
2. **ACO** = excavar donde encontraste indicios
3. **Búsqueda local** = tamizar con cuidado para separar el oro

---

## 7. VALIDACIÓN ESTADÍSTICA — WILCOXON

### ¿Por qué se necesita validación estadística?
Las metaheurísticas son **estocásticas** (aleatorias). Cada ejecución da un resultado diferente. Si el Híbrido da mejor fitness en UNA corrida, podría ser **suerte**. Con 10 corridas + prueba estadística, demostramos que la diferencia es **real**.

### ¿Qué es la prueba de Wilcoxon?
Una prueba **no paramétrica** que compara dos grupos de datos **pareados** para determinar si hay diferencia significativa.

### ¿Por qué Wilcoxon y no t-test?
- Wilcoxon **no asume distribución normal** (el t-test sí)
- Los valores de fitness de metaheurísticas **no necesariamente son normales**
- Con solo 10 muestras, **no se puede verificar normalidad** confiablemente

### ¿Qué son las hipótesis?
- **H₀ (nula)**: "No hay diferencia significativa entre los dos algoritmos" (son equivalentes)
- **H₁ (alternativa)**: "Sí hay diferencia significativa"

### ¿Qué es el p-valor?
La probabilidad de observar una diferencia tan grande **si los algoritmos fueran realmente iguales**.
- **p < 0.05** → rechazamos H₀ → la diferencia es significativa → ¡uno es mejor!
- **p ≥ 0.05** → no podemos rechazar H₀ → no hay evidencia suficiente

### ¿Qué significa p = 0.001953?
Hay solo un **0.19% de probabilidad** de que la diferencia sea por azar. Como es menor a 5%, concluimos que la diferencia es **real y significativa**.

### ¿Por qué muestras pareadas?
Porque cada corrida usa la **misma semilla** para ambos algoritmos. La corrida 1 del GA y la corrida 1 del ACO usan los mismos datos. Eso permite comparación **justa** par a par.

### ¿Por qué 10 corridas?
Es el **mínimo recomendado** en la literatura para pruebas estadísticas con metaheurísticas. Con menos de 10, Wilcoxon pierde poder estadístico.

### ¿Qué pasa si p ≥ 0.05?
**No podemos asegurar** que un algoritmo sea mejor. No significa que sean iguales, solo que no tenemos **evidencia suficiente**.

### Resultados de Wilcoxon en tu proyecto
| Par | p-valor | ¿Significativo? | Ganador |
|---|---|---|---|
| GA vs ACO | 0.001953 | ✅ Sí | GA |
| GA vs Híbrido | 0.003906 | ✅ Sí | **Híbrido** |
| ACO vs Híbrido | 0.001953 | ✅ Sí | **Híbrido** |

**Conclusión**: El Híbrido es **estadísticamente mejor** que ambos algoritmos individuales.

---

## 8. ANÁLISIS DE SENSIBILIDAD

### ¿Qué es?
Variar un parámetro a la vez para ver **cómo afecta** al resultado. Sirve para encontrar los **valores óptimos**.

### ¿Qué se varió?
1. **Tamaño de población**: 20, 40, 60, 80, 100 (con iteraciones fijas = 80)
2. **Número de iteraciones**: 30, 60, 100, 150, 200 (con población fija = 60)

### Resultados
- **Población 20** → fitness alto (poca diversidad genética)
- **Población 60** → punto de equilibrio ✅
- **Población 100** → mejora insignificante, más costo computacional

- **30 iteraciones** → no ha convergido
- **100 iteraciones** → se estabiliza
- **150 iteraciones** → valor óptimo ✅
- **200 iteraciones** → mejora despreciable

### ¿Qué son los rendimientos decrecientes?
Después del punto óptimo, cada unidad extra de recurso (población o iteraciones) aporta **cada vez menos mejora**. Duplicar las iteraciones de 150 a 300 podría mejorar el fitness un 0.1% pero **duplicaría el tiempo**.

### Parámetros óptimos
**60 individuos × 150 iteraciones** → equilibrio entre calidad y costo computacional.

---

## 9. BASELINES (COMPARACIONES)

### ¿Contra qué se comparan los algoritmos?

**1. Asignación del usuario (manual)**
Los usuarios asignan tareas sin criterio → desbalance extremo → fitness ~8800

**2. Greedy determinista**
Asigna cada tarea al servidor con **más capacidad libre** en ese momento.
- Es **miope**: solo ve la siguiente tarea, no el panorama global
- Es **determinista**: siempre da el mismo resultado
- Los algoritmos lo superan porque consideran **todas las asignaciones** simultáneamente

### ¿Por qué las metaheurísticas superan al greedy?
El greedy toma decisiones **localmente óptimas** que pueden ser **globalmente malas**. Las metaheurísticas consideran la **interacción** entre todas las asignaciones.

---

## 10. EXPLORACIÓN vs INTENSIFICACIÓN

### ¿Qué es la exploración?
Buscar en **regiones nuevas y lejanas** del espacio de búsqueda. Evita quedarse atrapado en **óptimos locales**.

### ¿Qué es la intensificación?
**Profundizar** en regiones prometedoras para encontrar el mejor punto dentro de esa región.

### ¿Qué es un óptimo local?
Una solución que es **mejor que sus vecinos** pero **no la mejor global**. Imagina estar en la cima de una colina baja — necesitas bajar antes de subir a la montaña más alta.

### ¿Cómo balancea cada algoritmo?

| Algoritmo | Exploración | Intensificación | Refinamiento |
|---|---|---|---|
| GA | ✅ Alta (cruce + mutación aleatoria) | ❌ Baja | ❌ No tiene |
| ACO | ❌ Baja al inicio | ✅ Alta (feromonas) | ❌ No tiene |
| Híbrido | ✅ Alta (GA) | ✅ Alta (feromonas guían mutación) | ✅ Búsqueda local |

---

## 11. IMPLEMENTACIÓN TÉCNICA

### ¿Qué tecnologías usaste?
- **Python** → algoritmos
- **Flask** → servidor web
- **NumPy** → cálculos numéricos
- **SciPy** → prueba de Wilcoxon
- **Gunicorn** → servidor de producción
- **HTML/CSS/JS + Chart.js** → frontend con gráficas
- **Render** → hosting en la nube

### ¿Cómo funciona la demo?
1. Los usuarios entran a `/votar` y asignan tareas a servidores (simulan "clientes")
2. El admin entra a `/panel` con contraseña
3. El admin ejecuta optimización → se ejecutan GA, ACO e Híbrido
4. Se muestran gráficas de convergencia, comparativas, distribución antes/después
5. El admin puede ejecutar análisis de Wilcoxon y sensibilidad

### ¿Por qué Flask y no Streamlit?
Flask da **control total** sobre la interfaz y permite la interacción en tiempo real con múltiples usuarios (votación). Streamlit es más simple pero menos flexible.

### ¿Por qué se escala dinámicamente?
En Render free tier, gunicorn tiene recursos limitados. Con muchas tareas, los algoritmos tardan más. El escalado dinámico **reduce iteraciones y población** cuando hay muchas tareas para evitar timeouts.

---

## 12. CONCEPTOS CLAVE (FLASHCARDS)

| Pregunta | Respuesta |
|---|---|
| ¿Qué es una metaheurística? | Estrategia de alto nivel para explorar espacios de búsqueda. No garantiza el óptimo pero encuentra buenas soluciones rápido. |
| ¿Qué es fitness? | Número que mide la calidad de una solución. Menor = mejor. |
| ¿Qué es una población? | Conjunto de soluciones candidatas que se evalúan en paralelo. |
| ¿Qué es una generación? | Una iteración del ciclo evolutivo del GA. |
| ¿Qué es la feromona? | Valor numérico que indica qué tan buena fue una asignación en el pasado. |
| ¿Qué es la evaporación? | Reducción gradual de feromonas para evitar convergencia prematura. |
| ¿Qué es convergencia? | Cuando el algoritmo deja de mejorar significativamente. |
| ¿Qué es convergencia prematura? | Cuando el algoritmo converge demasiado rápido a un óptimo local malo. |
| ¿Qué es el espacio de búsqueda? | Todas las posibles soluciones al problema (6⁶⁰ en tu caso). |
| ¿Qué es una solución factible? | Una que no viola restricciones (CPU y RAM dentro de los límites). |
| ¿Qué es una restricción? | Límite que debe respetarse (ej: no asignar más CPU de la disponible). |
| ¿Qué es un baseline? | Punto de referencia para comparar (greedy, asignación manual). |
| ¿Estocástico vs determinista? | Estocástico = usa aleatoriedad (metaheurísticas). Determinista = siempre da el mismo resultado (greedy). |
| ¿Qué es bin packing? | Problema de empaquetar objetos en contenedores minimizando desperdicio. Tu problema es similar. |

---

## 13. POSIBLES PREGUNTAS TRAMPA

### "¿Tu Híbrido siempre es mejor?"
> "En mis 10 corridas, sí fue consistentemente mejor y Wilcoxon lo confirma. Pero en teoría, con un problema diferente o parámetros muy distintos, podría no ser así. El No Free Lunch Theorem dice que ningún algoritmo es universalmente mejor para todos los problemas."

### "¿Por qué no usaste otro algoritmo como PSO o Simulated Annealing?"
> "Elegí GA y ACO porque son complementarios: uno es poblacional evolutivo y el otro es basado en inteligencia de enjambre con memoria (feromonas). Eso los hace ideales para hibridar. PSO o SA serían alternativas válidas para futuros trabajos."

### "¿Cómo sabes que no hay un bug en tu código?"
> "Verifico con el baseline: si las metaheurísticas dan fitness PEOR que el greedy, hay un error. Además, la prueba de Wilcoxon con 10 corridas confirma que los resultados son consistentes y no aleatorios."

### "¿Tu función de fitness es la correcta?"
> "Es una elección de diseño, no hay una función 'correcta' universal. Los pesos (0.4, 0.3, 0.3) reflejan la prioridad del balance sobre energía y tiempo. En producción, estos pesos se ajustarían según las necesidades del negocio."

### "¿Por qué no probaste con más servidores o tareas?"
> "El proyecto es un proof of concept con 6 servidores y tareas variables. La arquitectura escala — solo habría que ajustar los parámetros de los algoritmos para manejar instancias más grandes."