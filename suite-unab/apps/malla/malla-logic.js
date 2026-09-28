/**
 * Malla Curricular - Lógica de Grafos y Estados (Motor Puro)
 * Suite UNAB
 */

/**
 * Construye las estructuras de adyacencia directa e inversa para el grafo de prerrequisitos.
 * @param {Array<{codigo: string, requisitos: string[], semestre: number, creditos: number}>} cursos 
 */
function createPrereqGraph(cursos) {
  const byCode = Object.fromEntries(cursos.map(c => [c.codigo, c]));
  const PRE = Object.fromEntries(cursos.map(c => [c.codigo, (c.requisitos || []).filter(p => byCode[p])]));
  const DEP = Object.fromEntries(cursos.map(c => [c.codigo, []]));
  cursos.forEach(c => PRE[c.codigo].forEach(p => DEP[p].push(c.codigo)));
  return { byCode, PRE, DEP };
}

/**
 * Retorna todos los ancestros (prerrequisitos directos e indirectos) de un ramo.
 */
function getAncestors(code, PRE) {
  const seen = new Set();
  const st = [...(PRE[code] || [])];
  while (st.length) {
    const x = st.pop();
    if (seen.has(x)) continue;
    seen.add(x);
    (PRE[x] || []).forEach(y => st.push(y));
  }
  return seen;
}

/**
 * Retorna todos los descendientes (ramos que dependen directa o indirectamente) de un ramo.
 */
function getDescendants(code, DEP) {
  const seen = new Set();
  const st = [...(DEP[code] || [])];
  while (st.length) {
    const x = st.pop();
    if (seen.has(x)) continue;
    seen.add(x);
    (DEP[x] || []).forEach(y => st.push(y));
  }
  return seen;
}

/**
 * Determina si una asignatura está disponible/cursable según el conjunto de ramos aprobados.
 */
function isAvailable(code, aprobadas, PRE) {
  if (aprobadas.has(code)) return false;
  return (PRE[code] || []).every(p => aprobadas.has(p));
}

/**
 * Determina si un ramo se dicta en el periodo académico consultado.
 * - Plan Común (semestre 1 a 4): Siempre dictado.
 * - Semestres 5+: '1' para impares (Mar - Jul), '2' para pares (Ago - Dic), 'todos' para anual.
 */
function isOffered(curso, period) {
  if (period === 'todos') return true;
  if (curso.semestre <= 4) return true;
  if (period === '1') {
    return curso.semestre % 2 !== 0;
  } else {
    return curso.semestre % 2 === 0;
  }
}

/**
 * Detecta si existe algún ciclo en el grafo de cursos (debe ser un DAG).
 * Retorna array con el ciclo encontrado o null si es acíclico.
 */
function detectCycle(cursos) {
  const { PRE } = createPrereqGraph(cursos);
  const visited = {}; // 0 = unvisited, 1 = visiting, 2 = visited
  for (const c of cursos) visited[c.codigo] = 0;

  function dfs(node, path) {
    visited[node] = 1;
    for (const neighbor of PRE[node] || []) {
      if (visited[neighbor] === 1) {
        return [...path, neighbor];
      }
      if (visited[neighbor] === 0) {
        const cycle = dfs(neighbor, [...path, neighbor]);
        if (cycle) return cycle;
      }
    }
    visited[node] = 2;
    return null;
  }

  for (const c of cursos) {
    if (visited[c.codigo] === 0) {
      const cycle = dfs(c.codigo, [c.codigo]);
      if (cycle) return cycle;
    }
  }
  return null;
}

/**
 * Simula el toggle de aprobación con cascada inteligente.
 */
function simulateApprovalCascade(code, aprobadasSet, PRE, DEP) {
  const next = new Set(aprobadasSet);
  if (next.has(code)) {
    next.delete(code);
    getDescendants(code, DEP).forEach(d => next.delete(d));
  } else {
    next.add(code);
    getAncestors(code, PRE).forEach(p => next.add(p));
  }
  return next;
}

/**
 * Simula la aprobación/desaprobación en bloque de un semestre.
 */
function simulateSemesterToggle(semestre, cursos, aprobadasSet, PRE, DEP) {
  const coursesInSem = cursos.filter(c => c.semestre === semestre);
  const allApproved = coursesInSem.every(c => aprobadasSet.has(c.codigo));
  const next = new Set(aprobadasSet);

  if (allApproved) {
    coursesInSem.forEach(c => {
      next.delete(c.codigo);
      getDescendants(c.codigo, DEP).forEach(d => next.delete(d));
    });
  } else {
    coursesInSem.forEach(c => {
      next.add(c.codigo);
      getAncestors(c.codigo, PRE).forEach(p => next.add(p));
    });
  }
  return next;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    createPrereqGraph,
    getAncestors,
    getDescendants,
    isAvailable,
    isOffered,
    detectCycle,
    simulateApprovalCascade,
    simulateSemesterToggle
  };
}
