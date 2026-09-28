const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {
  createPrereqGraph,
  getAncestors,
  getDescendants,
  isAvailable,
  isOffered,
  detectCycle,
  simulateApprovalCascade,
  simulateSemesterToggle
} = require('../suite-unab/apps/malla/malla-logic.js');

describe('Malla Curricular - Algoritmos de Grafos y Lógica Pura', () => {

  // Grafo de prueba simple:
  // A -> B -> C -> D
  // E -> C
  const mockCursos = [
    { codigo: 'A', nombre: 'Curso A', semestre: 1, creditos: 4, requisitos: [] },
    { codigo: 'B', nombre: 'Curso B', semestre: 2, creditos: 4, requisitos: ['A'] },
    { codigo: 'E', nombre: 'Curso E', semestre: 2, creditos: 4, requisitos: [] },
    { codigo: 'C', nombre: 'Curso C', semestre: 3, creditos: 4, requisitos: ['B', 'E'] },
    { codigo: 'D', nombre: 'Curso D', semestre: 5, creditos: 4, requisitos: ['C'] },
    { codigo: 'F', nombre: 'Curso F', semestre: 6, creditos: 4, requisitos: [] },
  ];

  const { PRE, DEP } = createPrereqGraph(mockCursos);

  test('Construcción de grafo PRE y DEP correcta', () => {
    assert.deepEqual(PRE['A'], []);
    assert.deepEqual(PRE['B'], ['A']);
    assert.deepEqual(PRE['C'], ['B', 'E']);
    assert.deepEqual(DEP['A'], ['B']);
    assert.deepEqual(DEP['B'], ['C']);
    assert.deepEqual(DEP['E'], ['C']);
    assert.deepEqual(DEP['C'], ['D']);
  });

  test('getAncestors retorna todos los prerrequisitos transitivos recursivamente', () => {
    const ancA = getAncestors('A', PRE);
    assert.equal(ancA.size, 0);

    const ancB = getAncestors('B', PRE);
    assert.deepEqual([...ancB].sort(), ['A']);

    const ancC = getAncestors('C', PRE);
    assert.deepEqual([...ancC].sort(), ['A', 'B', 'E']);

    const ancD = getAncestors('D', PRE);
    assert.deepEqual([...ancD].sort(), ['A', 'B', 'C', 'E']);
  });

  test('getDescendants retorna todas las dependencias futuras recursivamente', () => {
    const depD = getDescendants('D', DEP);
    assert.equal(depD.size, 0);

    const depC = getDescendants('C', DEP);
    assert.deepEqual([...depC].sort(), ['D']);

    const depA = getDescendants('A', DEP);
    assert.deepEqual([...depA].sort(), ['B', 'C', 'D']);
  });

  test('isAvailable valida correctamente si una materia puede ser cursada', () => {
    const aprobadas = new Set(['A', 'E']);
    // B requiere A -> disponible
    assert.equal(isAvailable('B', aprobadas, PRE), true);
    // C requiere B y E, pero B no está aprobada -> no disponible
    assert.equal(isAvailable('C', aprobadas, PRE), false);
    // A ya está aprobada -> no disponible para cursar de nuevo
    assert.equal(isAvailable('A', aprobadas, PRE), false);
  });

  test('isOffered respeta la política de Plan Común y paridad de semestres', () => {
    const sem1 = { semestre: 1 };
    const sem4 = { semestre: 4 };
    const sem5 = { semestre: 5 }; // Impar
    const sem6 = { semestre: 6 }; // Par

    // Plan común (semestres 1 a 4) siempre se ofrece
    assert.equal(isOffered(sem1, '1'), true);
    assert.equal(isOffered(sem1, '2'), true);
    assert.equal(isOffered(sem4, '1'), true);
    assert.equal(isOffered(sem4, '2'), true);

    // Semestres superiores
    // En periodo 'todos', todo se ofrece
    assert.equal(isOffered(sem5, 'todos'), true);
    assert.equal(isOffered(sem6, 'todos'), true);

    // Periodo 1: impares sí, pares no
    assert.equal(isOffered(sem5, '1'), true);
    assert.equal(isOffered(sem6, '1'), false);

    // Periodo 2: impares no, pares sí
    assert.equal(isOffered(sem5, '2'), false);
    assert.equal(isOffered(sem6, '2'), true);
  });

  test('simulateApprovalCascade aprueba en cascada hacia atrás y desaprueba hacia adelante', () => {
    let aprobadas = new Set();

    // Aprobar D debe aprobar automáticamente C, B, E, A
    aprobadas = simulateApprovalCascade('D', aprobadas, PRE, DEP);
    assert.ok(aprobadas.has('D'));
    assert.ok(aprobadas.has('C'));
    assert.ok(aprobadas.has('B'));
    assert.ok(aprobadas.has('E'));
    assert.ok(aprobadas.has('A'));

    // Desaprobar B debe desaprobar C y D, pero mantener A y E
    aprobadas = simulateApprovalCascade('B', aprobadas, PRE, DEP);
    assert.equal(aprobadas.has('B'), false);
    assert.equal(aprobadas.has('C'), false);
    assert.equal(aprobadas.has('D'), false);
    assert.equal(aprobadas.has('A'), true);
    assert.equal(aprobadas.has('E'), true);
  });

  test('simulateSemesterToggle aprueba y desaprueba semestres completos', () => {
    let aprobadas = new Set();

    // Toggle semestre 1 (Curso A)
    aprobadas = simulateSemesterToggle(1, mockCursos, aprobadas, PRE, DEP);
    assert.ok(aprobadas.has('A'));

    // Toggle semestre 2 (B y E) -> B requiere A (ya está), aprueba B y E
    aprobadas = simulateSemesterToggle(2, mockCursos, aprobadas, PRE, DEP);
    assert.ok(aprobadas.has('B'));
    assert.ok(aprobadas.has('E'));

    // Si desmarcamos semestre 1 (A), debe desmarcar A, y en cascada a B, C, D
    aprobadas = simulateSemesterToggle(1, mockCursos, aprobadas, PRE, DEP);
    assert.equal(aprobadas.has('A'), false);
    assert.equal(aprobadas.has('B'), false);
    assert.equal(aprobadas.has('E'), true); // E no dependía de A
  });

  test('detectCycle detecta ciclos y valida grafos acíclicos', () => {
    // Grafo acíclico válido
    assert.equal(detectCycle(mockCursos), null);

    // Grafo con ciclo circular: X -> Y -> Z -> X
    const cyclicCursos = [
      { codigo: 'X', requisitos: ['Z'], semestre: 1 },
      { codigo: 'Y', requisitos: ['X'], semestre: 2 },
      { codigo: 'Z', requisitos: ['Y'], semestre: 3 }
    ];
    const cycle = detectCycle(cyclicCursos);
    assert.ok(cycle !== null);
    assert.ok(cycle.length >= 3);
  });
});

describe('Malla Curricular - Validación de las 10 Carreras Reales de Suite UNAB', () => {
  const mallasDir = path.join(__dirname, '..', 'suite-unab', 'apps', 'malla');
  const files = fs.readdirSync(mallasDir).filter(f => f.startsWith('malla_') && f.endsWith('.html'));

  test('Existen exactamente las 10 mallas de la Suite', () => {
    assert.equal(files.length, 10);
  });

  for (const filename of files) {
    describe(`Carrera: ${filename}`, () => {
      const filePath = path.join(mallasDir, filename);
      const content = fs.readFileSync(filePath, 'utf-8');

      // Extraer cursos
      const match = content.match(/const CURSOS\s*=\s*(\[.*?\]);/s);
      assert.ok(match, `${filename} debe contener el arreglo const CURSOS`);
      const cursos = JSON.parse(match[1]);

      test('Tiene cantidad representativa de asignaturas (> 30 cursos)', () => {
        assert.ok(cursos.length >= 30, `Cantidad de cursos: ${cursos.length}`);
      });

      test('El plan de estudios es un Grafo Dirigido Acíclico (DAG) sin ciclos', () => {
        const cycle = detectCycle(cursos);
        assert.equal(cycle, null, `Se encontró ciclo en ${filename}: ${JSON.stringify(cycle)}`);
      });

      test('Lógica de cascada funcional en asignaturas avanzadas', () => {
        const { PRE, DEP } = createPrereqGraph(cursos);
        // Buscar un ramo de último año que tenga prerrequisitos
        const ultimoSem = Math.max(...cursos.map(c => c.semestre));
        const ramoFinal = cursos.find(c => c.semestre >= ultimoSem - 1 && (c.requisitos || []).length > 0);
        
        if (ramoFinal) {
          const ancestors = getAncestors(ramoFinal.codigo, PRE);
          assert.ok(ancestors.size > 0, `Ramo final ${ramoFinal.codigo} debe tener prerrequisitos`);
          
          let estado = new Set();
          estado = simulateApprovalCascade(ramoFinal.codigo, estado, PRE, DEP);
          assert.ok(estado.has(ramoFinal.codigo));
          for (const anc of ancestors) {
            assert.ok(estado.has(anc), `Debe haberse aprobado el prerrequisito ${anc}`);
          }
        }
      });

      test('Contiene componentes UI requeridos (suite-bar, periodo-select, sem-chk)', () => {
        assert.ok(content.includes('suite-bar.js'), 'Debe incluir suite-bar.js');
        assert.ok(content.includes('tokens.css'), 'Debe incluir tokens.css');
        assert.ok(content.includes('periodo-select'), 'Debe incluir selector de periodos');
        assert.ok(content.includes('sem-chk'), 'Debe incluir botón check de semestre');
        assert.ok(content.includes('SuiteAuth.getUser'), 'Debe separar persistencia por usuario');
      });
    });
  }
});
