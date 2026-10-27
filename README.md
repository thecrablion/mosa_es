# Flujo actual: posts diarios revisados

La documentación vigente está en [WORKFLOW.md](WORKFLOW.md) y las instrucciones para la IA en [AGENTS.md](AGENTS.md). Los scripts están en `scripts/`. Construye `dist` antes de desplegar; la vista previa con borradores está en `dist-preview`.

El contenido siguiente se conserva como historial del sitio original; sus referencias a scripts y CSV que no estaban en el repositorio no describen el flujo nuevo. La publicación diaria solicitada sustituye la antigua regla de publicar solo por lotes.

---

# miestilopropio.com

Sitio estático. No hay build ni dependencias para subirlo: los archivos HTML ya están hechos.

## Qué es este sitio hoy: un solo lote

**Lote 1 · Colores.** Ocho páginas de colorimetría de la piel, más la portada y «Sobre el sitio».
Las otras cuatro familias (cuerpo, altura, clóset cápsula, edad) y la celda heredada de
Guadalajara × lluvias **se retiraron**: el sitio se quedó solo con la sección que la evidencia de
búsquedas sostenía. Las rutas viejas responden **301 a `/colores/`** (ver más abajo).

| Página | URL | Consulta principal (autocompletado real) |
|---|---|---|
| Hub de la sección | `/colores/` | qué colores me favorecen |
| Test en casa (4 pruebas) | `/colores/test/` | test de colorimetría con foto gratis |
| Subtono | `/colores/subtono-calido-o-frio/` | cómo saber mi subtono de piel |
| Piel morena | `/colores/piel-morena/` | colores que favorecen a la piel morena |
| Piel morena clara | `/colores/piel-morena-clara/` | colores que me favorecen si soy morena clara |
| Piel trigueña u oliva | `/colores/piel-triguena/` | colores para piel oliva |
| Piel clara o blanca | `/colores/piel-clara/` | colores para piel blanca |
| Piel oscura o negra | `/colores/piel-oscura/` | colores para piel negra |
| Portada (hub del lote) | `/` | colores que me favorecen según mi piel |
| Sobre el sitio | `/sobre/` | — (confianza, no SEO) |

Total: **10 páginas**. Un solo sitemap de contenido: `sitemap-colores.xml` (8 URLs) más
`sitemap-inicio.xml` y `sitemap-sitio.xml`, indexados en `sitemap.xml`.

El sitio en inglés (`myownstyleapp.com`) conserva su propio reparto (ocasión, Houston, petite):
**los dos sitios no comparten páginas ni textos**, y así se mantiene.

## Lotes (unidad de publicación y medición)

| Lote | Dimensión | Páginas | Sitemap |
|---|---|---|---|
| `L1-colores` | tono de piel y subtono | 8 | `sitemap-colores.xml` |
| `L0-sitio` | — (portada, sobre) | 2 | `sitemap-inicio.xml`, `sitemap-sitio.xml` |

- El estado del lote (borrador / publicado, fecha, nota) se edita en `lotes.csv`.
- `python3 build.py` regenera `reporte-lotes.md` (páginas, dimensión, sitemap y regla de decisión).
- Mapa de consultas del lote: `plan-lote1.md` y `keywords/lote1-colores.csv` (415 consultas del
  autocompletado de Google y Bing, es-MX). Respuestas crudas: `keywords/raw-autocomplete.json`.
- Guía del modelo de trabajo: `como-trabajar-por-lotes.md` (fuera del repo).

## Rutas retiradas (301)

`REDIRECCIONES` en `build.py` es la lista fuente de verdad; `python3 build.py` escribe los tres
formatos de despliegue con ella:

| Ruta vieja | Destino |
|---|---|
| `/guadalajara/lluvias/**` | `/colores/` |
| `/cuerpo/**`, `/altura/**`, `/edad/**` | `/colores/` |
| `/closet-capsula/**` | `/colores/` |
| `/closet-capsula/piel-morena/` | `/colores/piel-morena/` (misma piel) |

Archivos generados: `.htaccess` (Apache), `vercel.json` (Vercel) y `_redirects` (Cloudflare Pages /
Netlify). Si decides volver a publicar una de esas familias, quita su línea de `REDIRECCIONES`
antes de subir: una 301 no se puede deshacer sin perder el enlace heredado.

## Cómo regenerar

1. Edita los CSV en `datos/` (una fila = una página).
2. `python3 build.py`
3. Listo: reescribe las páginas, los sitemaps, `robots.txt`, `reporte-lotes.md`,
   `404.html`, el manifiesto de imágenes y los tres archivos de redirecciones.
4. `python3 build.py --dist` arma `dist/` con **solo lo público** (16 archivos: HTML, sitemaps,
   `robots.txt`). Despliega esa carpeta: así `build.py`, `datos/` y las notas internas no quedan
   descargables desde el dominio. En Vercel: Output Directory = `dist`; en Cloudflare Pages:
   Framework preset = None y Build output = `dist` (o sube el repo y deja que `.assetsignore` haga
   la mitad del trabajo).

Campos del CSV: `slug, title, desc, h1, sub, intro, datos_box, ref, fotos, fichas, paleta_si, paleta_no, paleta_nota, tabla, tabla_titulo, tabla_nota, si, no, faq, cierre, metodo, cross, tipo, hijos`.
Las listas se separan con `|` o con salto de línea. Las parejas usan `@` (título@texto, archivo@alt@pie de foto).
La familia se deduce del primer segmento del slug: no hay que escribirla. `lote` agrupa las filas por
cohorte de publicación; `consulta` guarda la frase textual que se le encontró en el buscador.

## Qué se corrigió

- **Canonical propio** en las 10 páginas: `https://miestilopropio.com/...` (antes apuntaban a `mosa.mx`,
  que es otra empresa). También `og:url`, `og:image` y el JSON-LD.
- **Sitemaps en el dominio propio**: `sitemap.xml` es un índice con un archivo por familia; hoy quedan
  `sitemap-colores.xml`, `sitemap-inicio.xml` y `sitemap-sitio.xml`. `robots.txt` declara el índice.
- **404 propio** generado por `build.py`: enlaza solo las rutas que existen.
- **`.htaccess`, `vercel.json` y `_redirects`** generados desde `REDIRECCIONES`: https forzado, sin www,
  barra final y las 301 de las familias retiradas. La portada ya no redirige a ninguna carpeta.
- **Títulos y H1 escritos con la consulta real** del autocompletado (`piel oliva`, `piel blanca`,
  `piel negra` entraron en los títulos; `colorimetría` a secas se evitó porque el término lo tiene el tinte de pelo).

## Pendiente (por orden)

1. **Imágenes**: 14 archivos WebP por producir. `IMAGENES.txt` es el manifiesto y cada carpeta `img/`
   tiene su `LEEME.txt` (nombre, alt y pie de foto). La página reserva el hueco aunque falte el archivo.
2. **Publicar el lote 1 completo el mismo día** y anotar la fecha en `lotes.csv`. Medir a los 14-28 días
   en Search Console sobre `sitemap-colores.xml` (una pantalla, una cohorte).
3. **Confirmar volúmenes** en Google Keyword Planner con `keywords/lote1-colores.csv` (415 consultas);
   el autocompletado da popularidad relativa, no números.
4. **El siguiente lote no existe todavía**: se abre cuando el lote 1 tenga señal. Candidatos con demanda
   capturada: estaciones (48 consultas), combinaciones de color (11) y el público masculino (13).

## Reglas del proyecto

- Una página = una decisión de la lectora, no un tema abstracto.
- Ninguna cifra sin fuente ni fecha. Si no hay dato, el bloque desaparece.
- Sin enlaces de afiliado y sin cobrar por recomendaciones: se dice en cada página.
- `python3 similitud.py . 0.45` comprueba que no hay páginas clonadas (hoy: 10 páginas, máximo 10 %, media 8 %).
- No se publica una página suelta: se publica un lote con fecha. Sin fecha no hay cohorte que medir.
