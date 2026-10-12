# miestilopropio.com

Sitio estático. No hay build ni dependencias para subirlo: los archivos HTML ya están hechos.

## Qué es ahora este sitio (reparto de estrategia)

Este dominio lleva el eje **«quién eres»**: color, cuerpo, altura, clóset y edad.
El eje **«dónde vas»** (ocasión, clima de ciudad, petite) vive en `myownstyleapp.com`.

| Familia | URL raíz | Páginas |
|---|---|---|
| Colores (colorimetría por piel) | `/colores/` | 6 |
| Cuerpo (proporciones) | `/cuerpo/` | 5 |
| Altura | `/altura/bajita/` | 1 |
| Clóset cápsula | `/closet-capsula/` | 4 |
| Edad | `/edad/40/` | 1 |
| Portada y «Sobre el sitio» | `/` y `/sobre/` | 2 |
| Celda heredada (Guadalajara × lluvias) | `/guadalajara/lluvias/` | 7 |

Total: 19 páginas generadas + 7 heredadas.

## Cómo regenerar

1. Edita los CSV en `datos/` (una fila = una página).
2. `python3 build.py`
3. Listo: reescribe las páginas, los sitemaps y `robots.txt`.

Campos del CSV: `slug, title, desc, h1, sub, intro, datos_box, ref, fotos, fichas, paleta_si, paleta_no, paleta_nota, tabla, tabla_titulo, tabla_nota, si, no, faq, cierre, metodo, cross, tipo, hijos`.
Las listas se separan con `|` o con salto de línea. Las parejas usan `@` (título@texto, archivo@alt@pie de foto).
La familia se deduce del primer segmento del slug: no hay que escribirla.

## Qué se arregló en esta pasada

- **Canonical propio**: todas las páginas apuntan a `https://miestilopropio.com/...` (antes apuntaban a `mosa.mx`, que es otra empresa). También `og:url`, `og:image` y el JSON-LD.
- **Sitemaps en el dominio correcto**: `sitemap.xml` es un índice y hay uno por familia (`sitemap-colores.xml`, `sitemap-cuerpo.xml`, `sitemap-capsula.xml`, `sitemap-altura.xml`, `sitemap-edad.xml`, `sitemap-inicio.xml`, `sitemap-lluvias.xml`). Así Search Console te dice qué familia entra y cuál no.
- **robots.txt** declara `https://miestilopropio.com/sitemap.xml`.
- **Cabecera y pie nuevos** con la navegación por familias, también en las 7 páginas heredadas (`python3 arreglar_heredadas.py`, idempotente).
- **404 propio** que enlaza a las familias.
- **`.htaccess` / `vercel.json`**: fuera la redirección de `/` a la carpeta de lluvias (la portada ya es una página), dominio propio y HTTPS forzado.
- Las páginas heredadas ganaron un bloque de enlaces hacia las familias nuevas: dejan de estar huérfanas.

## Pendiente (por orden)

1. **Imágenes**: `IMAGENES.txt` lista cada WebP con su ruta, su texto alternativo y su contenido. Cada carpeta `img/` trae su `LEEME.txt`. La página reserva el hueco aunque falte el archivo.
2. **Search Console**: dar de alta la propiedad, enviar `sitemap.xml` y mirar el informe de páginas a las 4 semanas.
3. **Contenido del probador**: cada página termina con el CTA a la app. El `?ref=` de cada URL identifica la página de origen.
4. **Ampliar familias**: los CSV son la tabla de datos. Añadir una piel, un cuerpo o una cápsula más es una fila y un `python3 build.py`.

## Reglas del proyecto

- Una página = una decisión de la lectora, no un tema abstracto.
- Ninguna cifra sin fuente ni fecha. Si no hay dato, el bloque desaparece.
- Sin enlaces de afiliado y sin cobrar por recomendaciones: se dice en cada página.
- `python3 similitud.py . 0.45` comprueba que no hay páginas clonadas (hoy: máximo 13 %, media 4 %).
