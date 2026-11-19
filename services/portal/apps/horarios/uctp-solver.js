/**
 * Motor cliente de optimización combinatoria UCTP (Suite UNAB).
 *
 * Espejo fiel de ``services/core/horarios/motor.py``: evalúa restricciones
 * blandas (ventanas horarias, días activos, preferencia de jornada y sobrecarga),
 * audita conflictos duros de sala (H2) y docente (H3) sobre la oferta cargada,
 * y optimiza combinaciones de horario sin topes (H1 = 0) mediante Branch-and-Bound
 * con ordenamiento MRV y cota inferior matemáticamente admisible.
 */
(function (global) {
  "use strict";

  const SALAS_NO_FISICAS = new Set([
    "", "TBA", "S/I", "SIN SALA", "ONLINE", "VIRTUAL", "REMOTO", "POR DEFINIR"
  ]);

  const JORNADA_RANGO = {
    manana: [1, 6],
    tarde: [7, 14],
    vespertino: [15, 20]
  };

  /**
   * Calcula los módulos libres intermedios (ventanas) en un día académico.
   * @param {number[]} modulos
   * @returns {number}
   */
  function ventanasDia(modulos) {
    const diurnos = modulos.filter(m => m <= 14).sort((a, b) => a - b);
    const vespertinos = modulos.filter(m => m >= 15).sort((a, b) => a - b);
    let v = 0;
    if (diurnos.length >= 2) {
      v += (diurnos[diurnos.length - 1] - diurnos[0] + 1) - diurnos.length;
    }
    if (vespertinos.length >= 2) {
      v += (vespertinos[vespertinos.length - 1] - vespertinos[0] + 1) - vespertinos.length;
    }
    return v;
  }

  /**
   * Evalúa la función objetivo f(x) sobre un conjunto de slots "Dia|Modulo".
   * @param {Set<string>} slotsSet
   * @param {Object} [prefs]
   * @returns {{ventanas:number, diasActivos:number, fueraJornada:number, excesoCarga:number, penalizacion:number}}
   */
  function evaluarSlots(slotsSet, prefs) {
    const p = Object.assign({
      jornada: "cualquiera",
      pesoVentanas: 3.0,
      pesoDias: 2.0,
      pesoJornada: 1.5,
      pesoSobrecarga: 1.0,
      maxModulosDia: 6
    }, prefs || {});

    const porDia = {};
    let fueraJornada = 0;
    const rango = JORNADA_RANGO[p.jornada] || null;

    for (const s of slotsSet) {
      const idx = s.indexOf("|");
      const dia = s.slice(0, idx);
      const mod = Number(s.slice(idx + 1));
      if (!porDia[dia]) porDia[dia] = [];
      porDia[dia].push(mod);
      if (rango && (mod < rango[0] || mod > rango[1])) {
        fueraJornada += 1;
      }
    }

    const dias = Object.keys(porDia);
    let ventanas = 0;
    let excesoCarga = 0;
    for (const d of dias) {
      const mods = porDia[d];
      ventanas += ventanasDia(mods);
      if (mods.length > p.maxModulosDia) {
        excesoCarga += mods.length - p.maxModulosDia;
      }
    }

    const diasActivos = dias.length;
    const penalizacion = Number((
      p.pesoVentanas * ventanas +
      p.pesoDias * diasActivos +
      p.pesoJornada * fueraJornada +
      p.pesoSobrecarga * excesoCarga
    ).toFixed(4));

    return { ventanas, diasActivos, fueraJornada, excesoCarga, penalizacion };
  }

  /**
   * Cota inferior admisible para poda Branch-and-Bound sin descartar óptimos globales.
   * @param {Set<string>} slotsParciales
   * @param {number} slotsRestantesMax
   * @param {Object} prefs
   * @returns {number}
   */
  function cotaInferiorAdmisible(slotsParciales, slotsRestantesMax, prefs) {
    const m = evaluarSlots(slotsParciales, prefs);
    const ventanasMin = Math.max(0, m.ventanas - slotsRestantesMax);
    return (
      prefs.pesoVentanas * ventanasMin +
      prefs.pesoDias * m.diasActivos +
      prefs.pesoJornada * m.fueraJornada +
      prefs.pesoSobrecarga * m.excesoCarga
    );
  }

  function seSolapan(a, b) {
    for (const x of a) if (b.has(x)) return true;
    return false;
  }

  function firmaAsignacion(cursos, sel) {
    return cursos
      .slice()
      .sort()
      .map(c => c + ":" + sel[c].secs.map(s => s.nrc).sort().join(","))
      .join(";");
  }

  /**
   * Audita restricciones duras H2 (salas) y H3 (docentes) sobre filas normalizadas.
   * @param {Array<Object>} filas
   * @param {function(Object): Array<{slots:Set<string>, sala:string, edif:string}>} segmentosFn
   * @returns {{salas:Array<Object>, docentes:Array<Object>}}
   */
  function auditarConflictosOferta(filas, segmentosFn) {
    const porSala = new Map();
    const porDocente = new Map();

    for (const row of filas) {
      const nrc = String(row.NRC || "").trim();
      if (!nrc) continue;
      const rut = String(row.RUT_PROF || "").replace(/[^0-9kK]/g, "").toUpperCase();
      for (const seg of segmentosFn(row)) {
        const salaRaw = String(seg.sala || "").trim().toUpperCase();
        const edifRaw = String(seg.edif || "").trim().toUpperCase();
        const salaKey = SALAS_NO_FISICAS.has(salaRaw) ? "" : (edifRaw ? `${edifRaw}-${salaRaw}` : salaRaw);

        for (const sl of seg.slots) {
          if (salaKey) {
            const k = `${salaKey}|${sl}`;
            if (!porSala.has(k)) porSala.set(k, new Set());
            porSala.get(k).add(nrc);
          }
          if (rut.length >= 7) {
            const k = `${rut}|${sl}`;
            if (!porDocente.has(k)) porDocente.set(k, new Set());
            porDocente.get(k).add(nrc);
          }
        }
      }
    }

    const toList = (mapa, tipo) => {
      const out = [];
      for (const [k, nrcs] of mapa.entries()) {
        if (nrcs.size > 1) {
          const [recurso, dia, mod] = k.split("|");
          out.push({ tipo, recurso, dia, modulo: Number(mod), nrcs: [...nrcs].sort() });
        }
      }
      return out.sort((a, b) => a.recurso.localeCompare(b.recurso) || a.dia.localeCompare(b.dia) || a.modulo - b.modulo);
    };

    return {
      salas: toList(porSala, "sala"),
      docentes: toList(porDocente, "docente")
    };
  }

  /**
   * Optimiza horarios libres de topes (H1 = 0) minimizando f(x) vía Branch-and-Bound MRV.
   * @param {string[]} cursos
   * @param {Object<string, Array<{secs:Array<Object>, slots:Set<string>}>>} opciones
   * @param {Object} [opts]
   * @returns {{soluciones:Array<{sel:Object, metricas:Object}>, nodosExplorados:number, nodosPodados:number}}
   */
  function optimizarBranchAndBound(cursos, opciones, opts) {
    const cfg = Object.assign({
      jornada: "cualquiera",
      pesoVentanas: 3.0,
      pesoDias: 2.0,
      pesoJornada: 1.5,
      pesoSobrecarga: 1.0,
      maxModulosDia: 6,
      maxHorarios: 8,
      disjuntos: false,
      maxNodos: 60000
    }, opts || {});

    let nodosExplorados = 0;
    let nodosPodados = 0;

    function buscarTopK(disp, limiteSol, presupuesto) {
      const orden = cursos.slice().sort((a, b) => (disp[a].length - disp[b].length) || a.localeCompare(b));
      const sufijoSlots = new Array(orden.length + 1).fill(0);
      for (let i = orden.length - 1; i >= 0; i--) {
        const maxC = disp[orden[i]].reduce((mx, op) => Math.max(mx, op.slots.size), 0);
        sufijoSlots[i] = sufijoSlots[i + 1] + maxC;
      }

      const mejores = [];
      const vistas = new Set();
      const sel = {};
      let locales = 0;

      function bt(idx, usados) {
        if (locales >= presupuesto) return;
        nodosExplorados += 1;
        locales += 1;

        if (idx === orden.length) {
          const metricas = evaluarSlots(usados, cfg);
          const firma = firmaAsignacion(orden, sel);
          if (!vistas.has(firma)) {
            vistas.add(firma);
            mejores.push({ sel: Object.assign({}, sel), metricas, firma });
            mejores.sort((a, b) =>
              (a.metricas.penalizacion - b.metricas.penalizacion) ||
              (a.metricas.ventanas - b.metricas.ventanas) ||
              (a.metricas.diasActivos - b.metricas.diasActivos) ||
              a.firma.localeCompare(b.firma)
            );
            if (mejores.length > limiteSol) {
              const desc = mejores.pop();
              vistas.delete(desc.firma);
            }
          }
          return;
        }

        const cotaCorte = mejores.length < limiteSol ? Infinity : mejores[mejores.length - 1].metricas.penalizacion;
        if (cotaCorte < Infinity) {
          const lb = cotaInferiorAdmisible(usados, sufijoSlots[idx], cfg);
          if (lb > cotaCorte + 1e-9) {
            nodosPodados += 1;
            return;
          }
        }

        const curso = orden[idx];
        const factibles = [];
        for (const op of disp[curso]) {
          if (seSolapan(op.slots, usados)) continue;
          const union = new Set(usados);
          for (const x of op.slots) union.add(x);
          factibles.push({ op, union, pen: evaluarSlots(union, cfg).penalizacion });
        }
        factibles.sort((a, b) => a.pen - b.pen);

        for (const item of factibles) {
          if (locales >= presupuesto) return;
          sel[curso] = item.op;
          bt(idx + 1, item.union);
          delete sel[curso];
        }
      }

      bt(0, new Set());
      return mejores;
    }

    let soluciones = [];
    if (!cfg.disjuntos) {
      soluciones = buscarTopK(opciones, cfg.maxHorarios, cfg.maxNodos);
    } else {
      const usadosNRC = new Set();
      const presupuestoRonda = Math.max(Math.floor(cfg.maxNodos / Math.max(cfg.maxHorarios, 1)), 2500);
      for (let h = 0; h < cfg.maxHorarios; h++) {
        const disp = {};
        let viable = true;
        for (const c of cursos) {
          disp[c] = opciones[c].filter(op => !op.secs.some(s => usadosNRC.has(s.nrc)));
          if (!disp[c].length) { viable = false; break; }
        }
        if (!viable) break;
        const ronda = buscarTopK(disp, 1, presupuestoRonda);
        if (!ronda.length) break;
        soluciones.push(ronda[0]);
        for (const c of cursos) {
          ronda[0].sel[c].secs.forEach(s => s.nrc && usadosNRC.add(s.nrc));
        }
      }
    }

    return { soluciones, nodosExplorados, nodosPodados };
  }

  global.SuiteUCTP = {
    evaluarSlots,
    cotaInferiorAdmisible,
    auditarConflictosOferta,
    optimizarBranchAndBound
  };
})(window);
