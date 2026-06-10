html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Guía de Estudio — Caso MELI Media Milla</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: #F5F7FA; color: #1A1A2E; }
  .header { background: linear-gradient(135deg, #1A1A2E, #16213E); color: #FFE600; padding: 32px 40px; }
  .header h1 { font-size: 24px; font-weight: 800; }
  .header p { color: #9E9E9E; margin-top: 6px; font-size: 14px; }
  .nav { display: flex; gap: 4px; background: #fff; padding: 12px 40px; border-bottom: 2px solid #E0E0E0; flex-wrap: wrap; position: sticky; top: 0; z-index: 10; }
  .nav button { background: transparent; border: 1px solid #E0E0E0; color: #555; padding: 7px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; }
  .nav button.active, .nav button:hover { background: #3483FA; color: #fff; border-color: #3483FA; }
  .section { display: none; padding: 32px 40px; max-width: 1100px; margin: 0 auto; }
  .section.active { display: block; }
  h2 { font-size: 20px; color: #1A1A2E; margin-bottom: 20px; padding-bottom: 8px; border-bottom: 3px solid #FFE600; }
  h3 { font-size: 15px; font-weight: 700; color: #3483FA; margin: 20px 0 10px; }
  .card { background: #fff; border-radius: 10px; padding: 20px 24px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.07); }
  .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 24px; }
  .kpi { background: #fff; border-radius: 10px; padding: 16px 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,.07); border-top: 4px solid #3483FA; }
  .kpi .val { font-size: 26px; font-weight: 800; color: #1A1A2E; font-family: monospace; }
  .kpi .lbl { font-size: 12px; color: #777; margin-top: 4px; }
  .kpi .sub { font-size: 11px; color: #AAA; margin-top: 2px; }
  .kpi.green { border-top-color: #2ED573; }
  .kpi.red { border-top-color: #FF4757; }
  .kpi.yellow { border-top-color: #FFE600; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: #1A1A2E; color: #FFE600; padding: 10px 14px; text-align: left; }
  td { padding: 9px 14px; border-bottom: 1px solid #F0F0F0; }
  tr:nth-child(even) td { background: #F9F9F9; }
  .tag { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
  .tag-green { background: #E8F8F0; color: #27AE60; }
  .tag-orange { background: #FFF4E0; color: #F39C12; }
  .tag-red { background: #FFEAEA; color: #E74C3C; }
  .tag-blue { background: #E8F0FE; color: #3483FA; }
  .qa { border-left: 4px solid #3483FA; padding: 14px 18px; background: #F0F4FF; border-radius: 0 8px 8px 0; margin-bottom: 12px; }
  .qa .q { font-weight: 700; color: #1A1A2E; margin-bottom: 8px; font-size: 14px; }
  .qa .a { color: #444; font-size: 13px; line-height: 1.7; }
  .qa .a strong { color: #3483FA; }
  .warn { background: #FFF8E1; border-left: 4px solid #FFE600; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 12px 0; font-size: 13px; }
  .insight { background: #E8F8F0; border-left: 4px solid #2ED573; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 12px 0; font-size: 13px; }
  .danger { background: #FFEAEA; border-left: 4px solid #E74C3C; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 12px 0; font-size: 13px; }
  .thread { background: linear-gradient(135deg, #1A1A2E, #0F3460); color: #FFE600; padding: 20px 24px; border-radius: 10px; font-size: 16px; font-style: italic; line-height: 1.6; margin-bottom: 20px; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media(max-width: 768px) { .two-col { grid-template-columns: 1fr; } .section { padding: 20px; } .nav { padding: 10px 20px; } }
</style>
</head>
<body>
<div class="header">
  <h1>Guía de Estudio · Caso MELI — Media Milla</h1>
  <p>Demand Planner · Logística de linehaul FC → Estaciones · Semana 18–24 Jun 2023</p>
</div>

<nav class="nav">
  <button class="active" onclick="show('numeros')">📊 Números clave</button>
  <button onclick="show('conceptos')">🧠 Conceptos</button>
  <button onclick="show('narrativa')">🧵 Narrativa</button>
  <button onclick="show('quiz')">❓ Quiz</button>
  <button onclick="show('trampas')">⚠️ Trampas</button>
</nav>

<!-- ══════════════ NÚMEROS CLAVE ══════════════ -->
<div id="sec-numeros" class="section active">
  <h2>Números que debes dominar de memoria</h2>

  <div class="kpi-grid">
    <div class="kpi"><div class="val">200,304</div><div class="lbl">Envíos / semana</div><div class="sub">18–24 Jun 2023</div></div>
    <div class="kpi yellow"><div class="val">$53.71</div><div class="lbl">Costo / paquete (as-is)</div><div class="sub">con km reales</div></div>
    <div class="kpi green"><div class="val">$43.27</div><div class="lbl">Costo / paquete (co-load)</div><div class="sub">−19% optimizado</div></div>
    <div class="kpi"><div class="val">43</div><div class="lbl">Vehículos / día</div><div class="sub">17 trailers + 26 tortons</div></div>
    <div class="kpi red"><div class="val">$10.76M</div><div class="lbl">Costo total / semana</div><div class="sub">MXN</div></div>
    <div class="kpi red"><div class="val">0.34%</div><div class="lbl">Volumen en micro-rutas</div><div class="sub">682 paqutes</div></div>
    <div class="kpi red"><div class="val">19.4%</div><div class="lbl">Costo de micro-rutas</div><div class="sub">$2.09M/sem</div></div>
    <div class="kpi"><div class="val">60%</div><div class="lbl">Ocupación global</div><div class="sub">3,500 pal / 5,838 cap</div></div>
  </div>

  <h3>Estructura de la red</h3>
  <div class="card">
    <table>
      <tr><th>Origen</th><th>Envíos/sem</th><th>% Volumen</th><th>% Costo</th><th>$/pqt</th><th>Rol</th></tr>
      <tr><td>Tepotzotlán</td><td>168,948</td><td>84.3%</td><td>72.6%</td><td>$46.22</td><td><span class="tag tag-blue">FC Principal</span></td></tr>
      <tr><td>Mérida</td><td>30,733</td><td>15.3%</td><td>8.1%</td><td>$28.32</td><td><span class="tag tag-green">Hub Sureste</span></td></tr>
      <tr><td>Otros nodos</td><td>623</td><td>0.4%</td><td>19.3%</td><td>$3,000+</td><td><span class="tag tag-red">Micro-rutas</span></td></tr>
    </table>
  </div>

  <h3>Horarios críticos (P1)</h3>
  <div class="card">
    <table>
      <tr><th>Destino</th><th>Origen</th><th>Sale</th><th>Llega</th><th>Veh/día</th><th>Nota</th></tr>
      <tr><td>Villahermosa</td><td>Tepotzotlán</td><td>22:30</td><td>13:11 D+1</td><td>5.9</td><td></td></tr>
      <tr><td>Tuxtla Gutierrez</td><td>Tepotzotlán</td><td>20:30</td><td>11:19 D+1</td><td>4.3</td><td></td></tr>
      <tr><td>Mérida</td><td>Tepotzotlán</td><td>20:30</td><td>21:21 D+1</td><td>2.0</td><td></td></tr>
      <tr><td>Cancún</td><td>Tepotzotlán</td><td>20:30</td><td>23:30 D+1</td><td>1.9</td><td></td></tr>
      <tr><td><strong>Playa del Carmen</strong></td><td>Tepotzotlán</td><td>20:30</td><td><strong>00:30 D+2</strong></td><td>1.4</td><td>⚠️ D+2</td></tr>
    </table>
  </div>

  <h3>Supuestos clave (debes poder justificar cada uno)</h3>
  <div class="card">
    <table>
      <tr><th>Supuesto</th><th>Valor</th><th>Por qué</th></tr>
      <tr><td>Paquetes por pallet</td><td>60</td><td>Dato del caso</td></tr>
      <tr><td>Trailer 53'</td><td>28 tarimas · $60/km</td><td>Estándar caja seca MX</td></tr>
      <tr><td>Torton</td><td>14 tarimas · $40/km</td><td>Estándar MX</td></tr>
      <tr><td>Asignación flota</td><td>Llenar trailers; rem ≤14→torton, >14→trailer</td><td>2 tortons ($80/km) > 1 trailer ($60/km)</td></tr>
      <tr><td>Km</td><td>Reales de Sheet3 (40/45 rutas)</td><td>Más preciso que velocidad asumida</td></tr>
      <tr><td>Consolidación</td><td>Todos los procesos viajan juntos por ruta-día</td><td>Pestaña 3 da una sola salida por origen</td></tr>
    </table>
  </div>

  <h3>Estacionalidad semanal</h3>
  <div class="card">
    <table>
      <tr><th>Día</th><th>Índice</th><th>Interpretación</th></tr>
      <tr><td>Martes</td><td><strong>1.24x</strong></td><td>Pico — 24% sobre el promedio</td></tr>
      <tr><td>Miércoles</td><td>1.16x</td><td></td></tr>
      <tr><td>Jueves</td><td>1.09x</td><td></td></tr>
      <tr><td>Viernes</td><td>1.01x</td><td></td></tr>
      <tr><td>Sábado</td><td>0.81x</td><td></td></tr>
      <tr><td>Lunes</td><td>1.05x</td><td></td></tr>
      <tr><td>Domingo</td><td><strong>0.63x</strong></td><td>Valle — 37% bajo el promedio</td></tr>
    </table>
  </div>
</div>

<!-- ══════════════ CONCEPTOS ══════════════ -->
<div id="sec-conceptos" class="section">
  <h2>Conceptos que debes dominar</h2>

  <div class="card">
    <h3>Coeficiente de Variación (CV)</h3>
    <p style="font-size:13px;line-height:1.8"><strong>Qué es:</strong> CV = (desviación estándar / media) × 100. Mide qué tan irregular es el volumen diario de una ruta.</p>
    <p style="font-size:13px;line-height:1.8;margin-top:8px"><strong>Por qué importa:</strong> te dice con cuánta confianza puedes comprometer flota por adelantado.</p>
    <table style="margin-top:12px">
      <tr><th>CV</th><th>Significado</th><th>Tu acción</th></tr>
      <tr><td>&lt;20%</td><td>Estable — casi siempre cerca del promedio</td><td>Flota fija T-48h, tarifa preferencial</td></tr>
      <tr><td>20–50%</td><td>Moderado — varía pero hay patrón</td><td>Base fija + 20% buffer spot pre-negociado</td></tr>
      <tr><td>&gt;50%</td><td>Caótico — no hay patrón predecible</td><td>Solo co-load, cero flota dedicada</td></tr>
    </table>
    <div class="insight" style="margin-top:12px">En tus datos: rutas CV alto = exactamente las mismas micro-rutas con 7.1% de ocupación. CV es el diagnóstico, co-load es el tratamiento.</div>
  </div>

  <div class="card">
    <h3>Co-load</h3>
    <p style="font-size:13px;line-height:1.8"><strong>Qué es:</strong> subir paquetes de una ruta micro a un vehículo que ya va al mismo corredor. El paquete viaja HOY — mismo SLA, cero vehículos extra.</p>
    <p style="font-size:13px;line-height:1.8;margin-top:8px"><strong>No confundir con:</strong> acumular (retener paquetes un día para llenar el camión = romper SLA).</p>
    <div class="warn"><strong>3 condiciones antes de aprobar un co-load:</strong><br>
    1. <strong>Dirección:</strong> el flujo micro va en el mismo corredor que la troncal<br>
    2. <strong>Espacio:</strong> la troncal receptora tiene holgura disponible<br>
    3. <strong>Cutoff:</strong> el paquete llega al hub antes de que salga la troncal</div>
    <p style="font-size:13px;margin-top:8px"><strong>Ejemplo real:</strong> Campeche → Cancún (12 pqts/sem, $6,355/pqt) → co-load vía Mérida: Campeche→Mérida torton corto (178.8 km), transbordo, Mérida→Cancún trailer existente al 79% → mismo día de entrega, ahorro del 98% en costo/pqt.</p>
  </div>

  <div class="card">
    <h3>Dwell Time</h3>
    <p style="font-size:13px;line-height:1.8">Tiempo que un paquete (o camión) permanece en una instalación sin moverse. En Media Milla importa en dos puntos:</p>
    <ul style="font-size:13px;line-height:1.8;margin:8px 0 0 20px">
      <li>En el hub destino: si el sortation está saturado, el camión espera → el SLA se consume antes de descargar</li>
      <li>En hub secundario sin flujo de retorno: el inventario se acumula, satura el hub, bloquea la recepción de trailers troncales</li>
    </ul>
  </div>

  <div class="card">
    <h3>NOM-087-SCT2-2017</h3>
    <p style="font-size:13px;line-height:1.8">Norma mexicana de autotransporte: el operador no puede manejar más de 11h continuas ni más de 15h en servicio en 24h.</p>
    <p style="font-size:13px;line-height:1.8;margin-top:8px"><strong>Impacto en la red:</strong> rutas con tiempo de tránsito &gt;21h (Tep→Cancún 27h, Tep→Playa 28h) requieren <em>doble operador</em> (team driving) para no detener el camión. Sobrecosto: +15-30%.</p>
    <div class="danger"><strong>Lo que dice tu modelo:</strong> usa Tiempo Tránsito de pestaña 2 (incluye paradas operativas). <strong>Lo que NO modela:</strong> el sobrecosto de doble operador. Para la entrevista: "lo agregaría en producción pidiendo la tarifa diferenciada al carrier."</div>
  </div>

  <div class="card">
    <h3>Inventario posicionado vs. flujo lineal</h3>
    <p style="font-size:13px;line-height:1.8"><strong>Flujo lineal:</strong> el paquete viaja desde el FC (Tepotzotlán) hasta el cliente cuando se genera el pedido. Tepotzotlán→Playa tarda 28h → imposible D+1.</p>
    <p style="font-size:13px;line-height:1.8;margin-top:8px"><strong>Inventario posicionado:</strong> el artículo ya está físicamente en el hub de Mérida antes de que se genere el pedido. Mérida→Playa tarda 7h → D+1 posible.</p>
    <div class="insight"><strong>Implicación para tu rol:</strong> el Demand Planner no solo planea cuántos camiones salen de Tepotzotlán — anticipa qué SKUs deben estar en Mérida antes de que se genere la demanda en Playa del Carmen.</div>
  </div>

  <div class="card">
    <h3>Asimetría del error de forecast</h3>
    <table>
      <tr><th>Error</th><th>Consecuencia</th><th>Costo</th></tr>
      <tr><td>Sub-forecast (te quedaste corto)</td><td>Paquetes en piso, rompes SLA, cliente no recompra</td><td>Spot +30-50% + NPS + churn — <strong>caro y visible</strong></td></tr>
      <tr><td>Sobre-forecast (pediste de más)</td><td>Camión va medio vacío</td><td>~$35K del vehículo extra — <strong>barato y silencioso</strong></td></tr>
    </table>
    <div class="insight" style="margin-top:12px"><strong>Conclusión:</strong> en troncales con CV bajo planifico con percentil 85-90 de la demanda, no con la media. El colchón cuesta menos que romper la promesa.</div>
  </div>
</div>

<!-- ══════════════ NARRATIVA ══════════════ -->
<div id="sec-narrativa" class="section">
  <h2>La narrativa: hilo conductor y slide por slide</h2>

  <div class="thread">
    "La red tiene dos regímenes de demanda. La cola caótica es justo la que destruye el costo. Pero no puedo matarla porque el SLA depende de ella — así que la consolido sin romper la promesa."
  </div>

  <div class="two-col">
    <div>
      <div class="card">
        <h3>Slide 1 — Resumen ejecutivo</h3>
        <p style="font-size:13px;line-height:1.8">200K pqts/sem a <strong>$53.71</strong>. 84% sale eficiente de Tepotzotlán. Pero 0.34% del volumen consume 19% del costo → co-load lo baja −19%.</p>
        <p style="font-size:13px;color:#777;margin-top:6px"><em>Activa los 3 mensajes en una frase.</em></p>
      </div>
      <div class="card">
        <h3>Slide 2 — Datos y método</h3>
        <p style="font-size:13px;line-height:1.8">Supuestos declarados. Gaps honestos. Genera credibilidad antes de mostrar resultados.</p>
      </div>
      <div class="card">
        <h3>Slide 3 — P1: Vehículos y horarios</h3>
        <p style="font-size:13px;line-height:1.8">~43 veh/día. Tabla de llegadas. <strong>Siembras aquí: Playa llega D+2.</strong> El panel ya tiene el dato cuando llegues a la slide 6.</p>
      </div>
      <div class="card">
        <h3>Slide 4 — P2: Dos regímenes</h3>
        <p style="font-size:13px;line-height:1.8">Troncales 67–94% (CV bajo) vs. cola 7.1% (CV alto). <strong>Esta slide prepara el clímax.</strong> Primero muestras que hay dos mundos.</p>
      </div>
    </div>
    <div>
      <div class="card">
        <h3>Slide 5 — P3: El hallazgo (clímax)</h3>
        <p style="font-size:13px;line-height:1.8">Esa cola de CV alto de la slide anterior = 0.34% del volumen pero 19% del costo. <strong>La misma cola, el mismo problema.</strong></p>
      </div>
      <div class="card">
        <h3>Slide 6 — La tensión</h3>
        <p style="font-size:13px;line-height:1.8">¿Por qué no cancelar? Devoluciones, saturación de hubs, inventario distribuido. <strong>Playa D+2 paga aquí</strong> (la sembraste en slide 3). Solución: co-load.</p>
      </div>
      <div class="card">
        <h3>Slide 7 — Recomendaciones</h3>
        <p style="font-size:13px;line-height:1.8">1) Co-load −19% inmediato · 2) Multi-stop Mérida ~$50K/sem · 3) Planeación por CV · 4) Tarifas reales con NOM-087.</p>
      </div>
      <div class="card">
        <h3>Slide 8 — Para producción</h3>
        <p style="font-size:13px;line-height:1.8">Tarifario real · 8-12 sem con Hot Sale · Promesa a nivel paquete · Ventanas de recibo · Calendario comercial.</p>
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:8px">
    <h3>La conexión entre slides que el panel nota</h3>
    <table>
      <tr><th>Siembras en</th><th>Pagas en</th><th>El link</th></tr>
      <tr><td>Slide 3: Playa llega D+2</td><td>Slide 6: tensión</td><td>No puedes cancelar micro-rutas sin perder la promesa en Riviera Maya</td></tr>
      <tr><td>Slide 4: dos regímenes (CV)</td><td>Slide 5: hallazgo</td><td>La cola caótica = la que destruye el costo</td></tr>
      <tr><td>Slide 5: co-load −19%</td><td>Slide 8: producción</td><td>El ahorro solo sobrevive si el tarifario real y los picos lo sostienen</td></tr>
    </table>
  </div>
</div>

<!-- ══════════════ QUIZ ══════════════ -->
<div id="sec-quiz" class="section">
  <h2>Quiz — Preguntas que el panel hará</h2>

  <div class="qa">
    <div class="q">¿Por qué solo tienes una semana de datos y cuál es el problema principal?</div>
    <div class="a">Con 7 días tengo una sola observación por día de semana — estadísticamente insuficiente. No puedo separar tendencia de ruido, ni capturar estacionalidad mensual ni el impacto de eventos comerciales. El pico del martes (1.24x) podría ser un martes atípico, no el patrón real. Pediría 8-12 semanas con un Hot Sale incluido para validar que el co-load sobrevive al pico (cuando las troncales van al 100% no hay holgura para absorber la cola).</div>
  </div>

  <div class="qa">
    <div class="q">¿Por qué llegaste a $53.71/pqt y otro candidato llegó a $43.30?</div>
    <div class="a"><strong>Los dos son correctos — difieren en supuesto, no en error.</strong> $53.71 es el costo as-is: cada ruta-día despacha su propio vehículo, incluyendo tortons casi vacíos. $43.27 es el escenario optimizado con co-load: elimino los 33 vehículos dedicados de micro-rutas y los absorbo en salidas troncales existentes. Siempre declaro el supuesto antes de dar el número.</div>
  </div>

  <div class="qa">
    <div class="q">¿Por qué no simplemente cancelas las micro-rutas y te quedas con el ahorro?</div>
    <div class="a">Porque son el flujo de retorno que mantiene los hubs operativos. Sin transporte de salida, los hubs secundarios se saturan (dwell time sube), bloquean la recepción de trailers troncales, y las devoluciones no proceadas bloquean reembolsos. La solución es co-load: el paquete viaja hoy en la salida existente del corredor, sin despachar vehículo dedicado. Mismo SLA, cero vehículos extra.</div>
  </div>

  <div class="qa">
    <div class="q">El lunes 19 tuviste Tep→Tuxtla al 99.1%. ¿Qué pasa si el volumen supera el forecast un 10%?</div>
    <div class="a">Un +10% son ~660 envíos extra = 11 pallets. Tenía 112 de capacidad y usé 111 — no me cabe ni el 1%. Plan en orden de costo: (1) torton spot pre-negociado para el remanente (+$35.5K vs. romper SLA), (2) priorizar por SLA: D+1 sube primero, D+2 espera la salida del día siguiente. Por eso en troncales con alta ocupación planifico con percentil 85-90, no con la media.</div>
  </div>

  <div class="qa">
    <div class="q">Tu modelo asume tarifas lineales de $60/km y $40/km. ¿Por qué es un problema?</div>
    <div class="a">En la realidad las tarifas tienen componente fijo + variable y mínimos por viaje. Si el torton de Villahermosa→Campeche está en un contrato mensual dedicado, cancelarlo no ahorra nada a corto plazo. Además, rutas largas como Tep→Cancún (27h) pueden requerir doble operador bajo NOM-087 (+15-30%). El $53.71, el −19% de co-load, todo fluye por esa asunción. El primer dato que pediría al carrier es el tarifario real.</div>
  </div>

  <div class="qa">
    <div class="q">¿Qué es el CV y por qué lo usas para priorizar rutas?</div>
    <div class="a">CV = desv_std / media × 100. Mide la irregularidad del volumen diario. Con CV alto no puedo comprometer flota con anticipación — si reservo un torton y no llegan paquetes, quemé el costo; si no reservo y sí llegan, rompo el SLA. El error es asimétrico: fallarle al cliente cuesta más. Por eso rutas con CV &gt;50% no reciben flota dedicada — se co-loadean en la troncal estable vecina. CV es el diagnóstico, co-load es el tratamiento.</div>
  </div>

  <div class="qa">
    <div class="q">¿Por qué Playa del Carmen no puede tener promesa D+1 desde CDMX?</div>
    <div class="a">El camión Tepotzotlán→Playa sale a las 20:30 y tarda 28 horas — llega a las 00:30 del D+2. Cualquier pedido generado hoy llega pasado mañana viniendo lineal desde el FC. Para cumplir D+1, el artículo debe estar posicionado en el hub de Mérida antes de que se genere el pedido: Mérida→Playa son 7 horas, salida 22:30, llegada 05:30 D+1. Eso requiere que yo como Demand Planner anticipe la demanda por SKU en destino final, no solo por FC de origen.</div>
  </div>
</div>

<!-- ══════════════ TRAMPAS ══════════════ -->
<div id="sec-trampas" class="section">
  <h2>Trampas y errores comunes — lo que el panel busca cazar</h2>

  <div class="danger">
    <strong>❌ Decir "acumular envíos" para mejorar la ocupación</strong><br>
    Acumular = retener paquetes un día = romper SLA. En MELI la velocidad ES el producto. La palabra correcta es <strong>co-load</strong>: el paquete viaja hoy, en un vehículo que ya existe.
  </div>

  <div class="danger">
    <strong>❌ Dar un solo número de costo sin declarar el supuesto</strong><br>
    $53.71 (as-is) y $43.27 (co-load) no son el mismo número. Si dices uno, el panel pregunta qué supuso. Siempre di: "bajo el supuesto de [X], el costo es [Y]."
  </div>

  <div class="danger">
    <strong>❌ Confundir "Tiempo a recorrer" (Sheet3) con "Tiempo Tránsito" (Pestaña 2)</strong><br>
    Sheet3 = manejo puro (~75 km/h implícito). Pestaña 2 = tiempo operativo (~58 km/h, +3.8h promedio por paradas y NOM-087). El modelo usa Pestaña 2 para horarios de llegada — son los correctos.
  </div>

  <div class="danger">
    <strong>❌ Decir que "Playa del Carmen" en tránsito causó que se perdieran 12,836 envíos</strong><br>
    Ese nombre solo aparece como <em>origen</em> en pestaña 2 (→Cancún 2.5h, →Mérida 12h). No hay tránsito hacia Playa en ninguna pestaña. Lo que le falta a esas rutas es la <strong>hora de llegada</strong> — el costo no se afecta porque usa km de Sheet3.
  </div>

  <div class="danger">
    <strong>❌ "La ocupación global es 60%, está bien"</strong><br>
    El 60% esconde la bimodalidad: troncales al 67-94% y micro-rutas al 7.1%. Promediar es engañoso. Di siempre: "60% global que esconde dos realidades muy distintas."
  </div>

  <div class="danger">
    <strong>❌ Priorizar "planeación por CV" como primera recomendación</strong><br>
    El CV es el diagnóstico — ya lo tienes calculado. Como primera recomendación el panel quiere escuchar acción inmediata con dinero. Co-load primero (−19%, sin inversión), CV como modelo operativo permanente en #3.
  </div>

  <div class="warn">
    <strong>⚠️ Semana del 18-24 junio: contexto que debes mencionar</strong><br>
    • Día del Padre fue el 18 de junio (tercer domingo) → posible cola de volumen<br>
    • Hot Sale 2023: 29 mayo–6 junio → a 2 semanas del cierre, posibles devoluciones elevadas<br>
    • Antesala de vacaciones de verano → demanda atípica<br>
    Conclusión: esta semana puede no representar la línea base. Por eso pediría 8-12 semanas con calendario comercial.
  </div>

  <div class="warn">
    <strong>⚠️ Campeche no tiene hora de salida en pestaña 3</strong><br>
    316 envíos (0.16%) quedan sin hora de llegada. No es un error del modelo — es un gap del dataset. Mencionarlo suma puntos porque demuestra que auditaste los datos.
  </div>
</div>

<script>
function show(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('sec-' + name).classList.add('active');
  event.target.classList.add('active');
}
</script>
</body>
</html>"""

with open("/home/user/r-basic/meli_case/guia_estudio.html", "w", encoding="utf-8") as f:
    f.write(html)

import os
print(f"✅ guia_estudio.html — {os.path.getsize('/home/user/r-basic/meli_case/guia_estudio.html')//1024} KB")
