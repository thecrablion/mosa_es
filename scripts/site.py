"""Generador local: python scripts/site.py build --preview | build | images | status."""
import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from datetime import date
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://miestilopropio.com'
POSTS = ROOT / 'content' / 'posts'
NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

def read(path):
    return path.read_text(encoding='utf-8-sig')

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8')

def esc(value):
    return html.escape(str(value), quote=True)

def posts():
    result = []
    keys = set()
    for path in sorted(POSTS.glob('*/post.json')):
        p = json.loads(read(path))
        for field in ('slug', 'title', 'description', 'h1', 'intro', 'status', 'date', 'profile', 'cover', 'cover_alt'):
            if not p.get(field):
                raise ValueError(f'{path}: falta {field}')
        if not SLUG.fullmatch(p['slug']) or p['slug'] != path.parent.name:
            raise ValueError(f'{path}: slug inválido o distinto de su carpeta')
        if p['status'] not in ('draft', 'published', 'archived'):
            raise ValueError(f'{path}: estado inválido')
        date.fromisoformat(p['date'])
        for field in ('body', 'hair', 'height', 'skin'):
            if not p['profile'].get(field):
                raise ValueError(f'{path}: falta profile.{field}')
        key = tuple(p['profile'][f].strip().casefold() for f in ('body', 'hair', 'height', 'skin'))
        if key in keys and p['status'] != 'archived':
            raise ValueError(f'Combinación repetida: {key}')
        if p['status'] != 'archived':
            keys.add(key)
        cover = Path(p['cover'])
        if cover.is_absolute() or '..' in cover.parts or cover.suffix != '.webp' or not (path.parent / cover).is_file():
            raise ValueError(f'{path}: portada WebP inválida o ausente')
        p['folder'] = path.parent
        p['url'] = '/blog/' + p['slug'] + '/'
        result.append(p)
    return sorted(result, key=lambda p: (p['date'], p['slug']), reverse=True)

def legacy_pages():
    files = [ROOT / 'index.html', ROOT / '404.html']
    for folder in ('colores', 'sobre'):
        files.extend(sorted((ROOT / folder).rglob('*.html')))
    return files

def legacy_catalog():
    items = []
    for path in legacy_pages():
        if path.name == '404.html':
            continue
        text = read(path)
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.S).group(1)
        canonical = re.search(r'<link rel="canonical" href="([^"]+)"', text).group(1)
        items.append({'url': canonical.removeprefix(DOMAIN), 'h1': re.sub('<[^>]+>', '', h1), 'category': 'Guías de color', 'legacy': True})
    return items

def rail(items, current):
    # Nuevos posts primero; la coincidencia de perfil ordena los posts relacionados.
    current_post = next((p for p in items if p['url'] == current), {})
    def score(p):
        return sum(v == p.get('profile', {}).get(k) for k, v in current_post.get('profile', {}).items())
    candidates = [p for p in items if p['url'] not in (current, '/', '/sobre/')]
    candidates.sort(key=lambda p: (not p.get('legacy', False), score(p), p.get('date', '')), reverse=True)
    links = []
    for p in candidates[:5]:
        thumb = f'<img src="{esc(p["url"] + p["cover"])}" alt="" width="74" height="74" loading="lazy">' if p.get('cover') else ''
        links.append(f'<a class="rail-item" href="{esc(p["url"])}"><span class="rail-thumb pat-a">{thumb}</span><span class="rail-txt"><span class="rail-cat">{esc(p.get("category", "Armario personalizado"))}</span><span class="rail-h">{esc(p["h1"])}</span></span></a>')
    return '<aside class="rail" aria-label="Más artículos"><h2 class="rail-tit">Más artículos</h2>' + ''.join(links) + '<p><a href="/blog/">Ver todos los posts →</a></p></aside>'

def shell(title, description, url, content, sidebar, preview=False, image=None, modified=None):
    template = read(ROOT / 'templates' / 'post.html')
    css_version = hashlib.sha256((ROOT / 'public/assets/blog.css').read_bytes()).hexdigest()[:12]
    template = template.replace('/assets/blog.css"', f'/assets/blog.css?v={css_version}"')
    canonical = DOMAIN + url
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Article' if image else 'CollectionPage', 'headline': title, 'description': description,
         'url': canonical, 'inLanguage': 'es-MX', **({'image': DOMAIN + image, 'datePublished': modified, 'dateModified': modified} if image else {})},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Mi Estilo Propio', 'item': DOMAIN + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Blog', 'item': DOMAIN + '/blog/'},
            *([{'@type': 'ListItem', 'position': 3, 'name': title, 'item': canonical}] if url != '/blog/' else [])]}]}
    values = {'TITLE': esc(title), 'DESCRIPTION': esc(description), 'URL': esc(canonical),
              'ROBOTS': 'noindex,follow' if preview else 'index,follow,max-image-preview:large',
              'SCHEMA': json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c'),
              'OG_IMAGE': f'<meta property="og:image" content="{esc(DOMAIN + image)}">' if image else '',
              'CONTENT': content, 'RAIL': sidebar}
    for key, value in values.items():
        template = template.replace('@@' + key + '@@', value)
    return template

def xml_file(path, urls, index=False):
    ET.register_namespace('', NS)
    root = ET.Element(f'{{{NS}}}' + ('sitemapindex' if index else 'urlset'))
    for url in urls:
        node = ET.SubElement(root, f'{{{NS}}}' + ('sitemap' if index else 'url'))
        ET.SubElement(node, f'{{{NS}}}loc').text = DOMAIN + url
    write(path, '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode'))

def build(preview=False):
    all_posts = posts()
    active = [p for p in all_posts if p['status'] == 'published' or (preview and p['status'] == 'draft')]
    output = ROOT / ('dist-preview' if preview else 'dist')
    # Solo se eliminan archivos enumerados por la compilación anterior, dentro de su salida.
    manifest = output / '.generated-files.json'
    if manifest.exists():
        for relative in json.loads(read(manifest)):
            target = (output / relative).resolve()
            if not target.is_relative_to(output.resolve()):
                raise ValueError('Ruta fuera de salida en manifiesto')
            if target.is_file():
                target.unlink()
                parent = target.parent
                while parent != output.resolve() and parent.is_relative_to(output.resolve()):
                    try:
                        parent.rmdir()
                    except OSError:
                        break
                    parent = parent.parent
    output.mkdir(exist_ok=True)
    items = active + legacy_catalog()
    catalog_link = '<p data-blog-catalog><a href="/blog/">Armarios personalizados: explora todos los posts →</a></p>'
    for path in legacy_pages():
        text = read(path)
        url = '/' + path.relative_to(ROOT).as_posix().removesuffix('index.html')
        text = re.sub(r'<aside class="rail".*?</aside>', rail(items, url), text, flags=re.S)
        text = text.replace('</main>', catalog_link + '</main>')
        if preview:
            text = re.sub(r'(<meta name="robots" content=")[^"]+', r'\g<1>noindex,follow', text)
        write(output / path.relative_to(ROOT), text)
    # Copiar únicamente recursos públicos ya existentes; no notas ni fuentes editoriales.
    for parent in ('colores', 'sobre'):
        for path in (ROOT / parent).rglob('*'):
            if path.is_file() and path.suffix.lower() in ('.webp', '.jpg', '.png', '.svg', '.css', '.js', '.woff2'):
                target = output / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    shutil.copytree(ROOT / 'public', output, dirs_exist_ok=True)
    banner = read(ROOT / 'templates' / 'probador.html')
    for p in active:
        body = read(p['folder'] / 'body.html').replace('<!-- PROBADOR -->', banner)
        warning = '<p class="draft-note" data-shared>Borrador para revisión · No publicado</p>' if p['status'] == 'draft' else ''
        content = warning + f'<article data-post><p class="crumb"><a href="/">Mi Estilo Propio</a> · <a href="/blog/">Blog</a> · Armario personalizado</p><h1>{esc(p["h1"])}</h1><p class="sub">{esc(p["intro"])}</p><p class="post-date">Revisión: {esc(p["date"])} · Guía de estilo</p>{body}</article>'
        dest = output / 'blog' / p['slug']
        write(dest / 'index.html', shell(p['title'], p['description'], p['url'], content, rail(items, p['url']), preview, p['url'] + p['cover'], p['date']))
        for path in (p['folder'] / 'img').glob('*.webp'):
            target = dest / 'img' / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    cards = ''.join(f'<a href="{esc(p["url"])}"><b>{esc(p["h1"])}</b><small>{esc(p["intro"])}</small></a>' for p in active)
    content = '<p class="crumb"><a href="/">Mi Estilo Propio</a> · Blog</p><h1>Armarios personalizados: guías para tu estilo</h1><p class="sub">Combinaciones de cuerpo, cabello, estatura y piel. Una guía con prendas, colores y ejemplos para cada perfil.</p><div class="cuerpos">' + cards + '</div>'
    if not active:
        content += '<p>Estamos preparando las primeras guías. Mientras tanto, <a href="/colores/">explora tus colores</a>.</p>'
    write(output / 'blog' / 'index.html', shell('Armarios personalizados y guías de estilo | Mi Estilo Propio', 'Explora guías de armario según tu cuerpo, cabello, estatura y tono de piel, con paletas, combinaciones y ejemplos de looks para cada perfil.', '/blog/', content, rail(items, '/blog/'), preview))
    redirects = read(ROOT / '_redirects').rstrip() + '\n'
    known = {p['url'] for p in items} | {'/blog/'}
    for p in all_posts:
        if p['status'] == 'archived' and p.get('redirect_to'):
            if p['redirect_to'] not in known or p['redirect_to'] == p['url']:
                raise ValueError(f'Destino de redirección inexistente: {p["slug"]}')
            redirects += f'{p["url"]} {p["redirect_to"]} 301\n'
            redirects += f'{p["url"].rstrip("/")} {p["redirect_to"]} 301\n'
    write(output / '_redirects', redirects)
    shutil.copy2(ROOT / '_headers', output / '_headers')
    for name in ('sitemap-colores.xml', 'sitemap-inicio.xml', 'sitemap-sitio.xml'):
        shutil.copy2(ROOT / name, output / name)
    xml_file(output / 'sitemap-blog.xml', [] if preview else ['/blog/'] + [p['url'] for p in active])
    names = ['sitemap-colores.xml', 'sitemap-inicio.xml', 'sitemap-sitio.xml', 'sitemap-blog.xml']
    xml_file(output / 'sitemap.xml', [] if preview else ['/' + n for n in names], index=True)
    if preview:
        for name in names:
            xml_file(output / name, [])
    write(output / 'robots.txt', 'User-agent: *\n' + ('Disallow: /\n' if preview else 'Allow: /\nSitemap: ' + DOMAIN + '/sitemap.xml\n'))
    write(output / '.assetsignore', '.generated-files.json\n.assetsignore\n')
    generated = [p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file() and p != manifest]
    write(manifest, json.dumps(generated, indent=2))
    print(f'{output}: {len(active)} posts; ' + ('VISTA PREVIA, noindex' if preview else 'solo posts publicados'))
    return output

def images(source, destination):
    from PIL import Image, ImageOps
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not destination.is_relative_to(POSTS.resolve()) and not destination.is_relative_to((ROOT / 'public').resolve()):
        raise ValueError('La salida de imágenes debe estar dentro de content/posts o public')
    destination.mkdir(parents=True, exist_ok=True)
    report = []
    for file in sorted(source.iterdir()):
        if file.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp'):
            continue
        target = destination / (file.stem + '.webp')
        with Image.open(file) as original:
            image = ImageOps.exif_transpose(original).convert('RGB')
            image.thumbnail((1200, 1500))
            image.save(target, 'WEBP', quality=82, method=6)
            report.append({'file': target.name, 'width': image.width, 'height': image.height,
                           'before': file.stat().st_size, 'after': target.stat().st_size,
                           'source_sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    if not report:
        raise ValueError('No hay imágenes compatibles en la carpeta de entrada')
    write(ROOT / 'reports' / ('images-' + destination.parent.name + '.json'), json.dumps(report, indent=2))
    print(f'{len(report)} imágenes: {sum(p["before"] for p in report):,} → {sum(p["after"] for p in report):,} bytes')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    b = sub.add_parser('build'); b.add_argument('--preview', action='store_true')
    i = sub.add_parser('images'); i.add_argument('source'); i.add_argument('destination')
    s = sub.add_parser('status'); s.add_argument('slug'); s.add_argument('state', choices=['draft', 'published', 'archived']); s.add_argument('--redirect-to')
    args = parser.parse_args()
    if args.command == 'build':
        build(args.preview)
    elif args.command == 'images':
        images(args.source, args.destination)
    else:
        if not SLUG.fullmatch(args.slug):
            parser.error('Slug inválido')
        path = POSTS / args.slug / 'post.json'
        data = json.loads(read(path))
        data['status'] = args.state
        if args.redirect_to:
            if args.state != 'archived' or args.redirect_to not in {p['url'] for p in posts() if p['status'] == 'published'} | {p['url'] for p in legacy_catalog()} | {'/blog/'}:
                parser.error('La redirección requiere archived y un destino público existente')
            data['redirect_to'] = args.redirect_to
        else:
            data.pop('redirect_to', None)
        write(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(f'{args.slug}: {args.state}. Reconstruye y verifica; no se ha publicado nada.')

if __name__ == '__main__':
    main()
