# 🎤 Guión de Presentación — Optimización Inteligente de Recursos en la Nube

> [!TIP]
> Este guión está diseñado para que lo leas antes de tu defensa y lo uses como referencia. No lo leas textualmente — úsalo para internalizar las ideas y luego habla con naturalidad.

---

## 📋 Estructura General (11 slides, ~15-20 minutos)

| Slide | Tema | Tiempo sugerido |
|-------|------|-----------------|
| 1 | Portada | 30 seg |
| 2 | El Problema | 2 min |
| 3 | Función de Fitness | 2 min |
| 4 | Algoritmo Genético | 2-3 min |
| 5 | Colonia de Hormigas | 2-3 min |
| 6 | Híbrido GA-ACO | 2-3 min |
| 7 | Resultados | 2 min |
| 8 | Wilcoxon | 2 min |
| 9 | Sensibilidad | 1.5 min |
| 10 | Conclusiones | 1 min |
| 11 | Demo en vivo / QR | 1-2 min |

---

## 🎬 SLIDE 1 — Portada

### Qué decir:
> "Buenos días/tardes. Mi nombre es Jonathan Ismael Corona Mendez, y mi proyecto final se titula **Optimización Inteligente de Recursos en la Nube**. En este proyecto implementé tres metaheurísticas: un Algoritmo Genético, una Colonia de Hormigas, y un Híbrido que combina ambos. Además, realicé validación estadística con la prueba de Wilcoxon y análisis de sensibilidad de parámetros."

### Consejo:
- Sé breve, es solo la presentación. No te extiendas.
- Habla con confianza desde el inicio.

---

## 🎬 SLIDE 2 — ¿Cuál es el Problema?

### Qué decir:
> "El problema que ataco es la **asignación de recursos en un datacenter en la nube**. Imaginen un centro de datos con 6 servidores de diferente capacidad — unos tienen 4 CPUs, otros 8, 16 o 32. Llegan tareas con distintos requerimientos de CPU y RAM, y la pregunta es: **¿a qué servidor asigno cada tarea para que todo funcione de la mejor manera posible?**"

> "Esto es un problema **NP-duro**, similar al problema del empaquetamiento (bin packing). Con 60 tareas y 6 servidores, hay 6 elevado a la 60 combinaciones posibles — eso es un número de 46 dígitos. Es imposible evaluar todas las combinaciones. Por eso necesitamos **metaheurísticas**: algoritmos inteligentes que encuentran buenas soluciones sin revisar todo el espacio de búsqueda."

---

## 🎬 SLIDE 3 — Función de Fitness

### Qué decir:
> "Para que los algoritmos puedan comparar soluciones, necesitamos una **función de fitness** que le asigne un número a cada asignación. En este proyecto el fitness es una **combinación ponderada de tres métricas**, más una penalización."

> "El **Balance** representa la desviación estándar del porcentaje de uso de CPU entre servidores — si un servidor está al 100% y otro al 0%, el balance es malo. Pesa un **40%** porque es el objetivo principal: distribuir la carga equitativamente."

> "La **Energía** es el consumo en watts del datacenter — servidores pequeños consumen más watts por CPU que los grandes, así que conviene usar los servidores grandes eficientemente. Pesa **30%**."

> "El **Tiempo de respuesta** se mide por el servidor más saturado — ese es el cuello de botella del sistema. También pesa **30%**."

> "Finalmente, si una solución **viola restricciones** (asigna más CPU o RAM de la que tiene un servidor), recibe una **penalización fuerte** que la hace no competitiva. Esto fuerza a los algoritmos a respetar las capacidades físicas."

> "El fitness es de **minimización**: menor valor = mejor solución."

### Si te preguntan "¿Por qué esos pesos (0.4, 0.3, 0.3)?":
> "El balance tiene más peso porque es el objetivo primario del problema — un datacenter desbalanceado causa cuellos de botella y degradación de servicio. Energía y tiempo son importantes pero secundarios. Los pesos se podrían ajustar según las prioridades del negocio."

---

## 🎬 SLIDE 4 — Algoritmo Genético (GA)

### Qué decir:
> "El primer algoritmo es el **Algoritmo Genético**, inspirado en la **evolución natural de Darwin**. La idea es que tenemos una *población* de 60 soluciones posibles, y las hacemos *evolucionar* durante 150 generaciones."

> "Cada solución, o *individuo*, es un **arreglo de enteros** donde la posición i indica a qué servidor se asigna la tarea i. Por ejemplo, `[2, 0, 5, 1, 3, ...]` significa que la tarea 0 va al servidor 2, la tarea 1 al servidor 0, etc."

> "El proceso funciona así en cada generación:
> 1. **Evaluamos** el fitness de todos los individuos
> 2. **Selección por torneo**: tomamos 5 individuos al azar y el mejor gana — esto simula la supervivencia del más apto
> 3. **Cruce uniforme**: dos padres crean un hijo tomando genes al azar de cada uno, con probabilidad 0.85
> 4. **Mutación**: cada gen tiene 15% de probabilidad de cambiar a un servidor aleatorio — esto introduce variedad
> 5. **Elitismo**: los 3 mejores individuos pasan directamente a la siguiente generación sin modificarse"

### ¿Por qué se escogió el GA?
> "El Algoritmo Genético es el pilar de las metaheurísticas poblacionales. Lo escogí porque tiene una **excelente capacidad de exploración global** — la combinación de cruce y mutación le permite recorrer amplias regiones del espacio de búsqueda. Sin embargo, su debilidad es que puede **estancarse en óptimos locales** porque la mutación es completamente aleatoria y no tiene 'memoria' de qué funcionó antes."

### Si te preguntan "¿Qué es la selección por torneo?":
> "Es una técnica donde se eligen k individuos al azar de la población (en mi caso k=5) y el que tenga mejor fitness gana y se selecciona como padre. Es mejor que la selección proporcional porque no depende de la escala del fitness y mantiene buena presión selectiva sin ser demasiado agresiva."

### Si te preguntan "¿Por qué cruce uniforme y no de un punto?":
> "El cruce de un punto tiende a preservar bloques contiguos de genes, lo cual tiene sentido en problemas donde la posición importa (como el TSP). Pero en asignación de recursos, cada tarea es independiente — no importa si las tareas 3 y 4 van al mismo servidor. El cruce uniforme mezcla mejor los genes y da más diversidad."

---

## 🎬 SLIDE 5 — Colonia de Hormigas (ACO)

### Qué decir:
> "El segundo algoritmo es la **Colonia de Hormigas**, inspirado en cómo las hormigas reales encuentran el camino más corto a la comida. En la naturaleza, las hormigas depositan **feromonas** en los caminos que recorren. Los caminos más cortos acumulan más feromona porque las hormigas los recorren más rápido, y las hormigas siguientes prefieren los caminos con más feromona. Así, la colonia converge al mejor camino sin que ninguna hormiga individual conozca el panorama completo."

> "En mi implementación, tengo una **matriz de feromonas** de tamaño `tareas × servidores`. Cada hormiga construye una solución completa asignando una tarea a la vez. La probabilidad de asignar la tarea i al servidor j depende de:
> - **Feromona** τ (tau): qué tan bueno fue asignar esa tarea a ese servidor en el pasado
> - **Heurística** η (eta): capacidad libre del servidor — favorece servidores con más espacio"

> "La fórmula es: **Probabilidad ∝ τ^α × η^β**"

> "Después de cada iteración:
> 1. Las feromonas se **evaporan** un 30% — esto evita convergencia prematura y permite olvidar caminos malos
> 2. Las hormigas **depositan** feromona inversamente proporcional a su fitness: mejor fitness = más feromona"

### ¿Por qué se escogió ACO?
> "Lo escogí porque es un paradigma completamente diferente al GA. Mientras el GA trabaja con **poblaciones que se mezclan**, ACO trabaja con **construcción secuencial guiada por memoria colectiva** (feromonas). Su fortaleza es la **intensificación**: una vez que encuentra buenas regiones, la feromona las refuerza y concentra la búsqueda ahí. Su debilidad es que al inicio la convergencia es **lenta** porque las feromonas están uniformes y no guían nada."

### Si te preguntan "¿Qué es alfa y beta?":
> "Alfa (α=1.0) controla qué tanto influye la feromona, y Beta (β=2.0) controla qué tanto influye la heurística de capacidad libre. Con β > α, le damos más peso a la información local (cuánto espacio tiene el servidor) que a la memoria histórica. Esto ayuda a encontrar soluciones factibles rápido."

### Si te preguntan "¿Qué es la evaporación y por qué 30%?":
> "La evaporación reduce las feromonas cada iteración para que el algoritmo no se quede atrapado en una sola solución. Si no se evapora, las primeras buenas soluciones dominarían para siempre. Un 30% es un balance: suficiente para olvidar caminos malos, pero no tanto como para perder la memoria útil."

---

## 🎬 SLIDE 6 — Híbrido GA-ACO

### Qué decir:
> "El tercer algoritmo es la estrella del proyecto: el **Híbrido GA-ACO**. La idea es simple pero poderosa: **¿por qué elegir entre GA y ACO si podemos combinar lo mejor de ambos?**"

> "El Híbrido funciona así:
> 1. Tiene una población de **80 individuos** y una **matriz de feromonas**
> 2. En cada generación, el **70% de la nueva población** se genera con operadores genéticos (selección, cruce) pero la **mutación NO es aleatoria** — en vez de cambiar un gen a un servidor al azar, consulta la matriz de feromonas para elegir servidores que históricamente han funcionado bien
> 3. El **30% restante** se genera con construcción tipo ACO (como las hormigas)
> 4. Las feromonas se actualizan con **elitismo**: solo los 5 mejores individuos depositan feromona
> 5. Cada **20 generaciones** se aplica una **búsqueda local** al mejor individuo
> 6. Al final, se hace un **refinamiento final** del mejor resultado global"

> "La búsqueda local es un procedimiento simple: toma tareas del servidor más cargado y las mueve al menos cargado, aceptando solo mejoras."

### ¿Por qué se escogió el Híbrido?
> "La razón principal del Híbrido es atacar las **debilidades de cada algoritmo por separado**:
> - El GA **explora bien** pero **se estanca** porque la mutación es ciega
> - El ACO **intensifica bien** pero **empieza lento** porque las feromonas no guían al inicio
> - El Híbrido usa la exploración del GA para encontrar buenas regiones rápidamente, y las feromonas del ACO para que la mutación sea inteligente en lugar de ciega. La búsqueda local actúa como un tercer componente que **refina** las mejores soluciones."

### Los 3 componentes en acción:
> "Piénsenlo así: **GA = exploración** (recorre muchas regiones), **ACO = intensificación** (profundiza en las buenas regiones), **Búsqueda local = refinamiento** (pule el resultado final). Es como buscar oro: primero exploras un territorio amplio (GA), luego excavas donde encontraste indicios (ACO), y finalmente tamizas con cuidado (búsqueda local)."

---

## 🎬 SLIDE 7 — Resultados de Optimización

### Qué decir:
> "Aquí vemos los resultados de una corrida típica. La asignación sin optimizar — la que haría una persona manualmente — tiene un fitness de aproximadamente **8800**. Esto es porque los usuarios tienden a sobrecargar unos servidores y dejar otros vacíos."

> "Los tres algoritmos logran mejorar significativamente:
> - **GA**: ~6722
> - **ACO**: ~6740
> - **Híbrido**: ~6714 — el mejor de los tres"

> "Si vemos la distribución antes y después, se nota el impacto: antes teníamos un servidor al **120% de su capacidad** (saturado) mientras otros estaban al 0%. Después de la optimización del Híbrido, todos los servidores están entre **17% y 30%** — carga perfectamente balanceada, sin ningún servidor saturado."

> "Los valores exactos se generan en tiempo real en la demo."

---

## 🎬 SLIDE 8 — Wilcoxon

### Qué decir:
> "Para demostrar que el Híbrido realmente es mejor y no fue suerte, ejecuté cada algoritmo **10 veces con semillas diferentes** y comparé los resultados estadísticamente."

> "La tabla superior muestra las estadísticas descriptivas: media, mejor, peor y desviación estándar de cada algoritmo. El Híbrido tiene la mejor media (**7196**), el mejor mínimo (**5911**) y la menor desviación."

> "La tabla inferior muestra la **prueba de Wilcoxon** para cada par de algoritmos. Los tres p-valores son menores a 0.05, lo que significa que las diferencias **no son producto del azar** — son estadísticamente significativas. El Híbrido supera a ambos individuales de forma consistente."

### Si te preguntan "¿Por qué Wilcoxon y no t-test?":
> "Wilcoxon es una prueba **no paramétrica**. No asume que los datos siguen una distribución normal, lo cual es correcto para nuestro caso porque los valores de fitness de metaheurísticas no necesariamente son normales. Además, con solo 10 muestras, no se puede verificar normalidad de forma confiable."

### Si te preguntan "¿Qué es el p-valor?":
> "El p-valor es la probabilidad de observar una diferencia tan grande o mayor **si los algoritmos fueran realmente iguales**. Un p-valor de 0.001953 significa que hay solo un 0.19% de probabilidad de que la diferencia sea por azar. Como es menor a 0.05, rechazamos la hipótesis nula de que son iguales y concluimos que la diferencia es significativa."

### Si te preguntan "¿Usaste Wilcoxon de rangos con signo o Mann-Whitney?":
> "Usé Wilcoxon de rangos con signo (signed-rank) porque son **muestras pareadas**: cada corrida usa la misma semilla para ambos algoritmos, así que la comparación es par a par. Si por alguna razón Wilcoxon falla (por ejemplo, si todas las diferencias son cero), el código cae a Mann-Whitney U como respaldo."

### Si te preguntan "¿Por qué 10 corridas?":
> "10 corridas es el mínimo recomendado en la literatura para pruebas estadísticas con metaheurísticas. Con menos de 10, la prueba de Wilcoxon pierde poder estadístico. Se podrían hacer 30 o más, pero 10 es suficiente para demostrar significancia y mantener el tiempo de ejecución razonable."

---

## 🎬 SLIDE 9 — Análisis de Sensibilidad

### Qué decir:
> "Para calibrar los parámetros, hice un **análisis de sensibilidad** variando dos factores clave: tamaño de población y número de iteraciones."

> "Con la **población**, probé 20, 40, 60, 80 y 100 individuos con iteraciones fijas en 80. Con 20 individuos el fitness es alto porque no hay suficiente diversidad genética. **60 es el punto de equilibrio**: después de eso, agregar más individuos no mejora proporcionalmente el resultado pero sí aumenta el costo computacional."

> "Con las **iteraciones**, probé 30, 60, 100, 150 y 200 con población fija en 60. Con 30 iteraciones el algoritmo no ha convergido. Se estabiliza alrededor de 100 y **150 es el valor óptimo**. Con 200 la mejora es insignificante."

> "El punto óptimo es **60 individuos × 150 iteraciones**: equilibrio entre calidad de solución y costo computacional."

### Si te preguntan "¿Qué pasaría con más iteraciones/población?":
> "Habría rendimientos decrecientes. Cada iteración extra aporta menos mejora porque el algoritmo ya convergió. En la práctica, duplicar las iteraciones podría mejorar el fitness un 0.1% pero duplicaría el tiempo de cómputo."

---

## 🎬 SLIDE 10 — Conclusiones

### Qué decir:
> "En conclusión:
> 1. Los tres algoritmos **superan significativamente** tanto la asignación manual como un greedy determinista
> 2. El **Híbrido GA-ACO es consistentemente el mejor** porque combina exploración, intensificación y refinamiento
> 3. La prueba de **Wilcoxon confirma** que las diferencias son estadísticamente significativas con p < 0.05
> 4. El análisis de sensibilidad nos permitió **calibrar los parámetros óptimos** a 60 individuos y 150 iteraciones"

---

## 🎬 SLIDE 11 — Demo / QR

### Qué decir:
> "El proyecto está desplegado en línea. Si escanean el QR o entran a la URL pueden probarlo ustedes mismos: asignar tareas a servidores, ejecutar los tres algoritmos, ver las gráficas de convergencia, la prueba de Wilcoxon y el análisis de sensibilidad en tiempo real."

> "¿Alguna pregunta?"

---

# ❓ PREGUNTAS FRECUENTES — Respuestas Preparadas

## Sobre el problema

### "¿Por qué no usaste el TSP?"
> "El TSP es un excelente benchmark pero decidí abordar un problema **más realista y multi-objetivo**. La asignación de recursos en la nube involucra 3 métricas simultáneas (balance, energía, tiempo) y restricciones duras (capacidad de CPU y RAM), lo cual lo hace más interesante como caso de estudio. Además, las empresas de cloud computing enfrentan este problema diariamente."

### "¿Esto se podría aplicar en la vida real?"
> "Sí, con adaptaciones. En la vida real habría que considerar: latencia de red, afinidad de tareas, migración en vivo de VMs, predicción de demanda, y más tipos de recursos (GPU, disco, ancho de banda). Pero el framework de optimización sería el mismo."

### "¿Qué es un problema NP-duro?"
> "Es un problema para el cual no se conoce un algoritmo que lo resuelva de forma óptima en tiempo polinomial. A medida que crece el tamaño del problema, el tiempo para encontrar la solución óptima crece exponencialmente. Por eso usamos metaheurísticas: no garantizan la solución óptima, pero encuentran soluciones *muy buenas* en tiempo razonable."

## Sobre los algoritmos

### "¿Qué es una metaheurística?"
> "Es una estrategia de alto nivel para explorar el espacio de búsqueda de un problema de optimización. A diferencia de los algoritmos exactos (que prueban todas las opciones), las metaheurísticas usan reglas inspiradas en la naturaleza para guiar la búsqueda de forma inteligente. No garantizan el óptimo global, pero en problemas NP-duros son la herramienta más práctica."

### "¿Qué diferencia hay entre exploración e intensificación?"
> "La **exploración** es buscar en regiones nuevas y lejanas del espacio de búsqueda — evita quedarse atrapado en óptimos locales. La **intensificación** es profundizar en regiones prometedoras para encontrar el mejor punto local. Un buen algoritmo balancea ambas. El GA es bueno explorando (cruce y mutación aleatoria), el ACO es bueno intensificando (las feromonas concentran la búsqueda), y el Híbrido hace ambas cosas."

### "¿Por qué la mutación guiada por feromonas es mejor que la aleatoria?"
> "La mutación aleatoria del GA cambia un gen a *cualquier* servidor con la misma probabilidad. Es como explorar a ciegas. La mutación guiada del Híbrido consulta la **matriz de feromonas**, que contiene la 'memoria colectiva' de qué asignaciones funcionaron bien. Entonces cuando muta, no elige al azar — elige servidores que históricamente dieron buenos resultados. Es mutación con *conocimiento*."

### "¿Qué es el elitismo?"
> "Es la estrategia de preservar los mejores individuos de una generación a la siguiente sin modificarlos. Sin elitismo, el mejor individuo podría perderse por cruce o mutación. Con elitismo (top 3 en GA, top 5 en Híbrido) garantizamos que la calidad nunca retrocede."

### "¿Qué es la búsqueda local del Híbrido?"
> "Es un procedimiento simple que toma la mejor solución y hace mejoras incrementales: identifica el servidor más cargado y el menos cargado, mueve una tarea del más cargado al menos cargado, y acepta el cambio solo si mejora el fitness. Se repite hasta 50 veces o hasta que no haya mejora. Es como 'pulir' la solución después de la búsqueda global."

### "¿Por qué el Híbrido usa 70% GA y 30% ACO?"
> "Porque el GA es más efectivo para la exploración amplia (necesita más individuos para cubrir el espacio de búsqueda) mientras que ACO es más eficiente para intensificar (con menos individuos construidos secuencialmente logra buen refinamiento). 70/30 es un balance empírico que dio buenos resultados en las pruebas."

## Sobre la implementación

### "¿Qué tecnologías usaste?"
> "Python para los algoritmos, Flask como servidor web, NumPy y SciPy para cálculos numéricos y la prueba de Wilcoxon. El frontend usa HTML/CSS/JavaScript vanilla con Chart.js para las gráficas. Está desplegado en Render."

### "¿Cómo funciona la demo interactiva?"
> "La página web simula un datacenter. Los usuarios pueden asignar tareas a servidores manualmente (como si fueran 'clientes' enviando peticiones). Luego el administrador puede ejecutar los algoritmos de optimización y ver en tiempo real cómo se redistribuirían las tareas, con gráficas de convergencia y comparativas."

### "¿Cómo se genera la población inicial?"
> "En los tres algoritmos, el primer individuo siempre es la **solución greedy** (asignar cada tarea al servidor con más capacidad libre) y el resto son soluciones **aleatorias**. La solución greedy da un buen punto de partida, y las aleatorias dan diversidad."

## Sobre la validación

### "¿Qué hipótesis prueba Wilcoxon?"
> "La **hipótesis nula** (H₀) es que no hay diferencia significativa entre los dos algoritmos comparados — es decir, que son equivalentes. La **hipótesis alternativa** (H₁) es que sí hay diferencia. Si el p-valor es menor a 0.05, rechazamos H₀ y concluimos que la diferencia es real, no producto del azar."

### "¿Qué pasa si el p-valor fuera mayor a 0.05?"
> "Significaría que **no podemos asegurar** que un algoritmo sea mejor que otro — la diferencia observada podría ser simplemente variación aleatoria. No significaría que son iguales, solo que no tenemos evidencia suficiente para afirmar que son diferentes."

### "¿El greedy no sería suficiente?"
> "El greedy es determinista y rápido, pero solo considera la siguiente tarea de forma **miope** — no ve el panorama global. Las metaheurísticas superan al greedy porque consideran la interacción entre *todas* las asignaciones simultáneamente. En mis resultados, las tres metaheurísticas superan al greedy de forma significativa."

---

# 🧠 Concepto Clave: Cómo Trabajan los 3 Algoritmos en Conjunto

> [!IMPORTANT]
> Esta es la pregunta más probable y más importante. Asegúrate de poder explicarla con fluidez.

Los tres algoritmos **no trabajan juntos en una sola ejecución** — son **tres enfoques independientes** que resuelven el mismo problema de forma diferente, y luego se **comparan** para determinar cuál es el mejor.

### La analogía perfecta:
Imagina que quieres encontrar el restaurante más barato de la ciudad:

1. **GA (Genético)**: Envías a 60 personas a buscar al azar. Las que encuentren buenos precios se "cruzan" (comparten información) y van mejorando. Pero como buscan al azar, a veces se quedan en el mismo barrio.

2. **ACO (Hormigas)**: Envías 30 hormigas que dejan rastro de feromona. Las primeras van al azar, pero cada una marca con feromona los restaurantes baratos. Las siguientes hormigas siguen las feromonas y encuentran cada vez mejores precios. Pero al inicio, sin feromonas, van a ciegas.

3. **Híbrido**: Combinas ambas estrategias. El 70% de los buscadores usan la estrategia genética pero cuando "mutan" (cambian de restaurante), no eligen al azar — siguen las feromonas. El 30% restante son hormigas puras. Además, cada cierto tiempo, tomas al mejor resultado y lo "pules" visitando restaurantes cercanos. **Resultado: encontrar más rápido y con más consistencia el mejor precio.**

### En términos técnicos:

```
GA     → Exploración global (cruce + mutación aleatoria)
       → Debilidad: se estanca

ACO    → Intensificación con memoria (feromonas)
       → Debilidad: arranque lento

Híbrido → Exploración (GA) + Intensificación (feromonas guían la mutación)
        + Construcción probabilística (30% ACO puro)
        + Refinamiento periódico (búsqueda local cada 20 gen)
        + Pulido final (búsqueda local al resultado)
```

El proyecto demuestra que al **combinar paradigmas complementarios** se obtienen resultados **superiores y más consistentes** que cualquier paradigma por sí solo.

---

# 💡 Tips para la Presentación

> [!TIP]
> - **No leas las slides** — las slides son apoyo visual, tú eres el que explica
> - **Usa las analogías** — "evolución de Darwin", "hormigas dejando feromonas", "buscar oro"
> - **Si no sabes una respuesta**, di: "Eso no lo exploré en este proyecto, pero sería interesante investigarlo como trabajo futuro"
> - **Menciona las limitaciones** honestamente: "Los datos son simulados, no de un datacenter real", "Se podrían probar más de 10 corridas", etc.
> - **La demo es tu as bajo la manga** — si el profesor quiere ver algo en acción, abre la URL en vivo
> - **Habla de los números** con confianza: "fitness de 6714 vs 8800 = una mejora del 24%"
