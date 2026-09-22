// Extrae el array CURSOS embebido en cada malla_*.html a un JSON limpio.
const fs = require("fs");
const path = require("path");

const MALLA_DIR = "E:/Proyecto seminario/suite-unab/apps/malla";
const OUT_DIR = "E:/Proyecto seminario/suite-unab/shared/mallas";
fs.mkdirSync(OUT_DIR, { recursive: true });

// carrera metadata copiada de index.html (CAREERS), para no reinventar nombres/badges
const CARRERAS = [
  { slug: "automatizacion-robotica", file: "malla_automatizacion_robotica.html", nombre: "Ingeniería en Automatización y Robótica", badge: "DUN 14-2022" },
  { slug: "civil-electrica", file: "malla_ingenieria_civil_electrica.html", nombre: "Ingeniería Civil Eléctrica", badge: "DUN 84-2022" },
  { slug: "civil-informatica", file: "malla_ingenieria_civil_informatica.html", nombre: "Ingeniería Civil Informática", badge: "Plan 12210" },
  { slug: "computacion-informatica", file: "malla_ingenieria_en_computacion_e_informatica.html", nombre: "Ingeniería en Computación e Informática", badge: "Res. 2719-2020" },
  { slug: "industrial", file: "malla_ingenieria_industrial.html", nombre: "Ingeniería Industrial", badge: "DUN 71-2022" },
  { slug: "civil", file: "malla_ingenieria_civil.html", nombre: "Ingeniería Civil", badge: "Plan 11300" },
  { slug: "civil-minas", file: "malla_ingenieria_civil_en_minas.html", nombre: "Ingeniería Civil en Minas", badge: "Plan 11303" },
  { slug: "construccion", file: "malla_ingenieria_en_construccion.html", nombre: "Ingeniería en Construcción", badge: "Plan 11400" },
  { slug: "civil-industrial", file: "malla_ingenieria_civil_industrial.html", nombre: "Ingeniería Civil Industrial", badge: "Plan 12100" },
  { slug: "civil-industrial-2-0", file: "malla_ingenieria_civil_industrial_2_0.html", nombre: "Ingeniería Civil Industrial 2.0", badge: "UNAB37044" },
];

const indice = [];

for (const c of CARRERAS) {
  const fp = path.join(MALLA_DIR, c.file);
  const html = fs.readFileSync(fp, "utf-8");
  const m = html.match(/<script>const CURSOS = (\[.*?\]);<\/script>/s);
  if (!m) { console.error("NO MATCH:", c.file); continue; }
  // eval seguro: es nuestro propio archivo local, JS ya validado por node --check antes
  const CURSOS = eval(m[1]);

  const semestres = [...new Set(CURSOS.map(x => x.semestre))];
  const totalCreditos = CURSOS.reduce((a, x) => a + (x.creditos || 0), 0);

  const data = {
    slug: c.slug,
    nombre: c.nombre,
    badge: c.badge,
    href: c.file,
    nCursos: CURSOS.length,
    nSemestres: semestres.length,
    totalCreditos,
    cursos: CURSOS.map(x => ({
      codigo: x.codigo,
      nombre: x.nombre,
      semestre: x.semestre,
      creditos: x.creditos,
      area: x.area || "",
      lane: x.lane,
      requisitos: x.requisitos || [],
    })),
  };
  fs.writeFileSync(path.join(OUT_DIR, c.slug + ".json"), JSON.stringify(data), "utf-8");
  indice.push({ slug: c.slug, nombre: c.nombre, badge: c.badge, nCursos: CURSOS.length, nSemestres: semestres.length, totalCreditos });
  console.log("OK:", c.slug, "-", CURSOS.length, "cursos,", semestres.length, "semestres");
}

fs.writeFileSync(path.join(OUT_DIR, "index.json"), JSON.stringify(indice), "utf-8");
console.log("\nCatálogo escrito en", OUT_DIR);
