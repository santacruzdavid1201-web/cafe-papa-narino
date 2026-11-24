// Mapa coroplético dibujado con polígonos (no depende de mapas base externos).
function colorEscala(t, escala) {
  t = Math.max(0, Math.min(1, t));
  for (let i = 1; i < escala.length; i++) {
    if (t <= escala[i][0]) {
      const [t0, c0] = escala[i - 1], [t1, c1] = escala[i], u = (t - t0) / (t1 - t0 || 1);
      const h = (c) => [1, 3, 5].map(k => parseInt(c.slice(k, k + 2), 16));
      const a = h(c0), b = h(c1);
      return "rgb(" + a.map((x, j) => Math.round(x + u * (b[j] - x))).join(",") + ")";
    }
  }
  return escala[escala.length - 1][1];
}
function dibujarMapa(div, geo, prop, valores, nombres, titulo, escala, decimales) {
  escala = escala || [[0, "#f7f1e8"], [0.5, "#f0a473"], [1, "#9a3d0c"]];
  const vals = Object.values(valores).filter(v => v !== null && v !== undefined && !isNaN(v));
  const lo = vals.length ? Math.min(...vals) : 0, hi = vals.length ? Math.max(...vals) : 1;
  if (!vals.length) titulo += " · sin datos para este año";
  const trazas = [];
  for (const f of geo.features) {
    const id = f.properties[prop], v = valores[id];
    const color = (v === null || v === undefined || isNaN(v)) ? "#e6e4de" : colorEscala((v - lo) / (hi - lo || 1), escala);
    const polis = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
    const xs = [], ys = [];
    for (const poli of polis) { const anillo = poli[0]; for (const [x, y] of anillo) { xs.push(x); ys.push(y); } xs.push(null); ys.push(null); }
    const txt = (nombres[id] || id) + "<br>" + ((v === null || v === undefined || isNaN(v)) ? "sin dato" : Number(v).toLocaleString("es-CO", {maximumFractionDigits: decimales ?? 2}));
    trazas.push({x: xs, y: ys, fill: "toself", fillcolor: color, mode: "lines", line: {color: "#ffffff", width: 0.7}, hoverinfo: "text", text: txt, hoveron: "fills", showlegend: false});
  }
  trazas.push({x: [null], y: [null], mode: "markers", hoverinfo: "skip", showlegend: false,
    marker: {color: [lo, hi], cmin: lo, cmax: hi, colorscale: escala, showscale: true, colorbar: {thickness: 12, len: 0.7}}});
  Plotly.react(div, trazas, {title: {text: titulo, font: {size: 15}}, margin: {l: 0, r: 0, t: 40, b: 0}, paper_bgcolor: "#fff", plot_bgcolor: "#fff",
    xaxis: {visible: false}, yaxis: {visible: false, scaleanchor: "x", scaleratio: 1}, hovermode: "closest",
    font: {family: "Source Sans 3, Segoe UI, sans-serif", size: 13}}, {responsive: true, displaylogo: false});
}
