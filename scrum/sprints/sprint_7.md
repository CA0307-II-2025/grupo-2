# 📆 Planificación – Sprint (2025-14-11)

## 🎯 Objetivo del Sprint
Tener datos completamente limpios, un análisis exploratorio sólido, un dashboard funcional con primeras visualizaciones y avances técnicos en cópulas y teoría de valores extremos para comenzar la fase final del proyecto.

---

## 😃 Historias para este sprint
- Limpieza completa de la base de datos.  
- Análisis exploratorio y no paramétrico inicial.  
- Actualización del dashboard con datos limpios y visualizaciones descriptivas.  
- Implementación inicial del análisis de cópulas.  
- Implementación inicial del análisis de valores extremos.  
- Avance del reporte escrito en metodología y descripción de datos.

---

## 🔜 Plan de alto nivel

### Semana 1
- Limpieza completa de datos.  
- EDA inicial (tablas y visualizaciones).  
- Integración de datos limpios al dashboard.  
- Comienzo de cópulas marginales y selección de familias.  
- Selección de umbral EVT.

### Semana 2
- Ajustes EVT (cola/cuerpo).  
- Comparación preliminar de cópulas.  
- Integración de resultados al dashboard.  
- Redacción de metodología y descripción del proceso.

---

## 🥇 Criterios de aceptación del Sprint
- [ ] Todas las tareas completadas y revisadas por el profesor.  
- [ ] Limpieza automática de la base sin procesos manuales.  
- [ ] Dashboard funcional con datos limpios.  
- [ ] Análisis preliminar de colas y dependencias (EVT y cópulas).  

---

## 📌 Asignación de tareas inicial

### Holmar  
- Análisis de cópulas (marginales, contrastes, correlación de colas).  
- Apoyo en algunas gráficas del EDA.

### Andrey Prado  
- Limpieza y validación completa de datos.  
- Análisis exploratorio y no paramétrico.  
- Selección de umbral y modelos EVT.

### Joseph Romero  
- Actualización del dashboard (tablas, visualizaciones).  
- Redacción de la metodología general y estructura del reporte.

### Dixon Montero  
- Diseño y mejoras en el dashboard.  
- Redacción del reporte (contexto, descripción de datos).

---

## 🚫 Posibles bloqueos

- **Bloqueo:** Dependencia directa entre limpieza de datos y ajustes de cópulas/EVT.  
  **Solución:** Priorizar limpieza y validación antes de análisis.  

- **Bloqueo:** Reglas estrictas de GitHub (PR obligatorio, no merge commits).  
  **Solución:** Mantener flujo estricto de ramas → PR → revisión.

---

# ⏳ Daily – Fecha: 2025-09-XX

### Holmar
- **¿Qué hice ayer?**  
  Implementé las primeras cópulas marginales para las variables principales y comparé distribuciones empíricas con las ajustadas. También generé gráficos preliminares de dependencia.
- **¿Qué haré hoy?**  
  Probaré distintas familias de cópulas (Clayton, Gumbel, Frank) y comenzaré a evaluar criterios de selección como AIC y lambda-tails.
- **¿Hay algo que me está bloqueando?**  
  No, pero necesito la versión final de los datos limpios para recalibrar los modelos.

### Andrey Prado
- **¿Qué hice ayer?**  
  Limpié la base de datos completa, corregí inconsistencias en variables, eliminé outliers extremos y realicé un EDA inicial con histogramas y boxplots. También implementé la selección del umbral EVT.
- **¿Qué haré hoy?**  
  Ajustar modelos GPD y distribuciones para el cuerpo y cola, comparar modelos y generar gráficos para el dashboard.
- **¿Hay algo que me está bloqueando?**  
  No, excepto definir si usamos categorías o provincias para EVT según tamaño de muestra.

### Joseph Romero
- **¿Qué hice ayer?**  
  Actualicé el dashboard incorporando los datos limpios, agregué tablas descriptivas y comencé a integrar visualizaciones interactivas.
- **¿Qué haré hoy?**  
  Integrar los gráficos de EVT y dependencia que Andrey y Holmar produzcan. Además, comenzar la sección metodológica del reporte.
- **¿Hay algo que me está bloqueando?**  
  Falta recibir algunos gráficos y descripciones técnicas para el dashboard.

### Dixon Montero
- **¿Qué hice ayer?**  
  Mejoré la estética general del dashboard, ajusté tipografías y colores, y preparé plantillas para gráficos adicionales.
- **¿Qué haré hoy?**  
  Integrar nuevas visualizaciones, revisar consistencia visual del dashboard y avanzar en la redacción del contexto del informe.
- **¿Hay algo que me está bloqueando?**  
  No, solo dependo del avance de los análisis para integrar gráficos.

---

# 🔍 Revisión en clase – Fecha: 2025-09-XX

## 📈 Resultado mostrado
- Primera versión funcional del dashboard con datos limpios.  
- Gráficos descriptivos y análisis exploratorio completo.  
- Ejecución preliminar de modelos EVT y ajuste de cópulas marginales.  

## 🔄 Retroalimentación

- **Profesor:**  
  Sugirió validar la estabilidad del umbral EVT y revisar sensibilidad del modelo. Recomendó más claridad en el reporte respecto a motivación estadística.  

- **Compañeros:**  
  Comentaron positivamente la claridad del dashboard, pero sugirieron agregar filtros adicionales.

## ✔ Criterios de aceptación cumplidos
- [x] Datos limpios y validados.  
- [x] Dashboard funcional.  
- [x] Análisis exploratorio completo.  
- [ ] Modelos EVT y cópulas en progreso (requieren refinamiento).  

---

# 🔙 Retrospective – Fecha: 2025-14-11

## ✔ Qué salió bien
1. Excelente colaboración entre roles técnicos (EVT + cópulas).  
2. Dashboard completamente funcional y actualizado.  
3. Documentación al día evitó confusiones.

## ❌ Qué podría mejorar
- Falta de sincronización entre análisis y dashboard generó tiempos muertos.  
- Criterios de aceptación incompletos para métodos estadísticos avanzados.  
- Distribución de carga aún desigual (EVT y cópulas muy pesados).

## 📝 Acciones para el próximo Sprint
1. Reunión técnica semanal entre Holmar y Andrey para alinear EVT-cópulas.  
2. Implementar tests automáticos básicos en limpieza de datos.  
3. Balancear mejor la cantidad de tareas técnicas por miembro.  
