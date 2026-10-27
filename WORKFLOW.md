# Un post al día, con revisión

## Lo que entregas a la IA
La combinación (tipo de cuerpo, color de cabello, estatura y tono/subtono de piel), el texto y una carpeta de fotos. Puedes usar:

> Crea un post para esta combinación: [cuerpo], [cabello], [estatura], [piel]. Usa el texto y las imágenes de [carpeta]. Sigue AGENTS.md y WORKFLOW.md. Prepara un borrador con la plantilla del blog, convierte las imágenes a WebP, actualiza catálogo y relacionados, verifica similitud y enlaces y muéstrame la vista previa. No publiques.

## Organización
```
content/posts/<slug>/
  post.json       # título, descripción, perfil, estado, fecha y portada
  body.html       # contenido flexible del artículo
  source.txt      # material recibido, privado
  editorial.md    # observaciones y fuentes, privado
  img/*.webp      # solo imágenes del post
templates/        # estructura común y banner MOSA
public/assets/    # CSS original y cuatro imágenes compartidas del banner
scripts/          # generación y verificaciones
dist-preview/     # sitio de revisión, incluye borradores, noindex
dist/             # solo publicación aprobada
reports/          # compresión y verificación (no se despliegan)
```

Cada carpeta genera `/blog/<slug>/`. Se evita `/closet-capsula/` porque el sitio ya redirige esa familia. Los originales JPG no se suben; guárdalos en tu carpeta de trabajo. Los seis WebP del ejemplo están junto a su contenido. El banner compartido no se duplica en cada carpeta.

`source.txt` y `editorial.md` se conservan localmente y están excluidos de Git porque este repositorio es público. Una copia nueva del repositorio contiene lo necesario para generar el sitio; el material editorial privado se comparte por separado cuando haga falta revisar o ampliar el post.

## Preparación y comandos
Python 3.10 o posterior. La generación y la verificación usan la biblioteca estándar; solo convertir imágenes requiere Pillow (`python -m pip install -r requirements.txt`). Ejecutar desde la raíz del repositorio:

```
python scripts/site.py images RUTA_ORIGINALES content/posts/SLUG/img
python scripts/site.py build --preview
python scripts/verificar.py dist-preview --preview --report reports/preview.json
python -m http.server 4174 --bind 127.0.0.1 --directory dist-preview
```

Abrir `http://127.0.0.1:4174/blog/`. La plantilla tiene contenido HTML estático: no depende de JavaScript para leer el artículo ni ver sus fotos. Cada foto se limita a 1200 × 1500 píxeles, WebP calidad 82, con orientación corregida y sin copiar EXIF. La compresión no es un límite duro de peso: el verificador avisa por encima de 220 KB. Inspeccionar color y detalle de la ropa antes de aceptar.

`post.json` requiere slug, title, description, h1, intro, status, date, profile (body/hair/height/skin), cover y cover_alt. `category` es opcional. La fecha debe ser la de revisión real; no actualizarla por regenerar archivos. Usar slugs minúsculos sin acentos y perfiles normalizados como `rectangular`, `negro-azabache`, `media`, `morena-calida`. Los apartados pueden variar según los datos. No se exige inventar un número de palabras ni apartados vacíos.

## Qué verifica
- Un H1, canonical propio y títulos, descripciones y H1 no repetidos.
- Enlaces, archivos y anclas internas existentes; JSON-LD parseable y breadcrumbs válidos.
- Sitemap por sección, URLs existentes e indexables, sin duplicados ni páginas públicas omitidas.
- Ausencia de marcas sin completar; WebP, alt y dimensiones en posts nuevos.
- Similitud Jaccard de secuencias de cinco palabras del artículo; ignora nav/aside/footer/form/script/style y bloques data-shared. Compara contra todas las páginas existentes. Desde 50 %: fallo. El reporte lista todas las parejas, no solo las que fallan.
- Títulos de 45–62 caracteres y descripciones de 120–160 generan avisos orientativos, no una supuesta obligación de Google.
- No se publican fuentes editoriales ni scripts dentro de dist.

La revisión editorial comprueba que la combinación aporta diferencias reales. No basta con que cambie el perfil o que un algoritmo dé una cifra baja. Esta primera guía utiliza el material proporcionado; no se han inventado referencias para los nombres de publicaciones que venían sin enlaces.

## Cuando apruebes publicar
```
python scripts/site.py status SLUG published
python scripts/site.py build
python scripts/verificar.py dist --report reports/production.json
```
Después, revisar cambios y subir a GitHub/desplegar solo con autorización. La guía coquette tiene publicación autorizada y su estado es `published`; la presencia en el dominio se verifica después del despliegue.

Cloudflare Workers Assets: el Worker conectado es `mosa-es` y `wrangler.jsonc` sirve exclusivamente `dist`. El comando de compilación es `python scripts/site.py build && python scripts/verificar.py dist`; también debe configurarse en Workers Builds. El despliegue utiliza `npx wrangler deploy`. Cloudflare Pages: carpeta de salida `dist`, comando de compilación `python3 scripts/site.py build && python3 scripts/verificar.py dist`. No requiere Pillow en Cloudflare si los WebP ya están versionados.

## Actualizar o quitar
Editar body.html/post.json/imágenes y reconstruir. Para retirar sin borrar las fuentes:
```
python scripts/site.py status SLUG archived
```
Si hay sustituto pertinente, añadir `--redirect-to /blog/SLUG-SUSTITUTO/`. La reconstrucción retira el post del catálogo, de los relacionados y del sitemap, elimina sus archivos generados anteriores y genera las redirecciones aprobadas. Sin sustituto, devuelve 404. No decide qué retirar basándose solo en similitud.

## Pruebas
`python -m unittest discover -s tests -v`

## Avisos del sitio heredado
El repositorio original refiere 14 WebP que no contiene. Se reportan como avisos heredados, no se sustituyen con fotos ajenas. En los posts nuevos una imagen ausente es un fallo. Los HTML heredados no se rediseñan: la generación actualiza sus rails y añade acceso al catálogo.
