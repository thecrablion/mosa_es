"""Verifica HTML, recursos, SEO, sitemaps y similitud del contenido principal."""
import argparse
import itertools
import json
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
import xml.etree.ElementTree as ET

DOMAIN = 'https://miestilopropio.com'
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.stack=[]; self.links=[]; self.images=[]; self.ids=set(); self.duplicate_ids=[]
        self.meta={}; self.canonicals=[]; self.h1=[]; self.title=[]; self.content=[]; self.ld=[]; self.ld_current=None
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag not in ('meta','link','img','input','hr','br','source','wbr','area','base','embed','param','track','col'):
            self.stack.append((tag, a))
        if a.get('id'):
            if a['id'] in self.ids: self.duplicate_ids.append(a['id'])
            self.ids.add(a['id'])
        if tag in ('a','link','script'):
            u=a.get('href') or a.get('src')
            if u: self.links.append(u)
        if tag=='img': self.images.append(a)
        if tag=='link' and a.get('rel')=='canonical': self.canonicals.append(a.get('href',''))
        if tag=='meta': self.meta[a.get('name',a.get('property',''))]=a.get('content','')
        if tag=='h1': self.h1.append('')
        if tag=='script' and a.get('type')=='application/ld+json': self.ld_current=''
    def handle_endtag(self, tag):
        if tag=='script' and self.ld_current is not None:
            self.ld.append(self.ld_current); self.ld_current=None
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                self.stack=self.stack[:i]; break
    def handle_data(self, data):
        tags=[t for t,a in self.stack]
        if 'title' in tags: self.title.append(data)
        if 'h1' in tags and self.h1: self.h1[-1]+=data
        if self.ld_current is not None: self.ld_current+=data
        excluded=('script','style','nav','aside','footer','form')
        if 'main' in tags and not any(t in excluded for t in tags) and not any('data-shared' in a or set(a.get('class','').split()) & {'crumb','post-date','bloque-probador','botonera','cta'} for t,a in self.stack):
            self.content.append(data)

def shingles(text):
    words=re.findall(r'\w+',text.casefold())
    return {' '.join(words[i:i+5]) for i in range(max(0,len(words)-4))}

def verify(root, threshold=.5, preview=False):
    root=Path(root).resolve(); errors=[]; warnings=[]; pairs=[]
    files=sorted(root.rglob('*.html'))
    if not files: return {'errors':['No hay HTML para verificar'], 'warnings':[], 'pairs':[], 'pages':0}
    pages={p:Page(p.read_text(encoding='utf-8-sig')) for p in files}
    def local(url):
        path=unquote(urlsplit(url).path)
        target=(root/path.lstrip('/')).resolve()
        if not target.is_relative_to(root): return root/'__invalid__'
        if path.endswith('/') or not target.suffix: target=target/'index.html'
        return target
    duplicate=defaultdict(list)
    for path,page in pages.items():
        rel=path.relative_to(root).as_posix(); route='/'+rel.removesuffix('index.html')
        base=DOMAIN+route; fresh=rel.startswith('blog/'); title=''.join(page.title).strip()
        for label,value in [('title',title),('description',page.meta.get('description','')),('h1',' '.join(page.h1))]:
            if not value: errors.append(f'{rel}: falta {label}')
            elif path.name!='404.html': duplicate[(label,value.casefold())].append(rel)
        if len(page.h1)!=1: errors.append(f'{rel}: requiere exactamente un H1')
        if page.canonicals!=[base] and path.name!='404.html': errors.append(f'{rel}: canonical incorrecto {page.canonicals}')
        if page.duplicate_ids: errors.append(f'{rel}: IDs duplicados {page.duplicate_ids}')
        if not 45<=len(title)<=62: warnings.append(f'{rel}: title de {len(title)} caracteres (orientativo)')
        if not 120<=len(page.meta.get('description',''))<=160: warnings.append(f'{rel}: description fuera de 120–160 caracteres (orientativo)')
        raw=path.read_text(encoding='utf-8-sig')
        if '@@' in raw or 'TUDOMINIO' in raw or '<!-- PROBADOR -->' in raw: errors.append(f'{rel}: plantilla sin resolver')
        if fresh and re.search(r'\bVERIFICAR\b', ' '.join(page.content)): errors.append(f'{rel}: dato pendiente de verificar')
        for u in page.links+[i.get('src','') for i in page.images]:
            absolute=urljoin(base,u); parsed=urlsplit(absolute)
            if parsed.scheme not in ('http','https') or parsed.netloc!=urlsplit(DOMAIN).netloc: continue
            target=local(absolute)
            if not target.is_file():
                message=f'{rel}: recurso inexistente {u}'
                (warnings if not fresh and target.suffix.lower() in ('.webp','.jpg','.png') else errors).append(message)
            elif parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:
                errors.append(f'{rel}: ancla inexistente {u}')
        for img in page.images:
            if 'alt' not in img: errors.append(f'{rel}: imagen sin alt')
            if fresh:
                if not img.get('src','').endswith('.webp'): errors.append(f'{rel}: imagen no WebP')
                if not img.get('width') or not img.get('height'): errors.append(f'{rel}: imagen sin dimensiones')
                target=local(urljoin(base,img.get('src','')))
                if target.is_file() and target.stat().st_size>220_000: warnings.append(f'{rel}: imagen supera 220 KB: {img["src"]}')
        if fresh and not page.ld: errors.append(f'{rel}: falta JSON-LD')
        for block in page.ld:
            try:
                data=json.loads(block)
                def visit(o):
                    if isinstance(o,dict):
                        if o.get('@type')=='BreadcrumbList':
                            for item in o.get('itemListElement',[]):
                                u=item.get('item',''); u=u.get('@id','') if isinstance(u,dict) else u
                                if not local(u).is_file(): errors.append(f'{rel}: breadcrumb roto {u}')
                        for v in o.values(): visit(v)
                    elif isinstance(o,list):
                        for v in o: visit(v)
                visit(data)
            except (ValueError,TypeError): errors.append(f'{rel}: JSON-LD inválido')
        if preview and 'noindex' not in page.meta.get('robots',''): errors.append(f'{rel}: preview indexable')
    for (label,value), locations in duplicate.items():
        if len(locations)>1: errors.append(f'{label} duplicado: {locations}')
    seen=set(); seen_xml=set()
    def sitemap(path):
        if path in seen_xml: errors.append(f'Sitemap circular o repetido: {path.name}'); return
        seen_xml.add(path)
        try: tree=ET.parse(path).getroot()
        except (OSError,ET.ParseError) as e: errors.append(f'Sitemap inválido {path.name}: {e}'); return
        isindex=tree.tag.endswith('sitemapindex')
        for loc in tree.findall('.//{*}loc'):
            u=loc.text or ''
            if not u.startswith(DOMAIN+'/'): errors.append(f'Sitemap fuera de dominio: {u}'); continue
            target=local(u)
            if isindex: sitemap(target); continue
            if u in seen: errors.append(f'URL duplicada en sitemap: {u}')
            seen.add(u)
            if target not in pages: errors.append(f'Sitemap sin página: {u}')
            elif 'noindex' in pages[target].meta.get('robots',''): errors.append(f'Sitemap contiene noindex: {u}')
    sitemap(root/'sitemap.xml')
    for path,page in pages.items():
        url=DOMAIN+'/'+path.relative_to(root).as_posix().removesuffix('index.html')
        if path.name!='404.html' and 'noindex' not in page.meta.get('robots','') and url not in seen:
            errors.append(f'Página indexable fuera de sitemap: {url}')
    robot=root/'robots.txt'
    if not robot.exists(): errors.append('Falta robots.txt')
    elif not preview and DOMAIN+'/sitemap.xml' not in robot.read_text(): errors.append('robots.txt no señala el sitemap correcto')
    content={p:shingles(' '.join(v.content)) for p,v in pages.items() if p.name!='404.html'}
    for (a,sa),(b,sb) in itertools.combinations(content.items(),2):
        similarity=len(sa&sb)/len(sa|sb) if sa and sb else 0
        pairs.append({'a':a.relative_to(root).as_posix(),'b':b.relative_to(root).as_posix(),'similarity':round(similarity,4)})
        if similarity>=threshold: errors.append(f'Similitud {similarity:.1%}: {a.relative_to(root)} ↔ {b.relative_to(root)}')
    for path in root.rglob('*'):
        if path.is_file() and path.suffix in ('.py','.json','.md','.pdf','.csv') and path.name!='.generated-files.json': errors.append(f'Archivo editorial en salida pública: {path.relative_to(root)}')
    return {'pages':len(pages),'errors':sorted(set(errors)),'warnings':sorted(set(warnings)),'pairs':sorted(pairs,key=lambda p:p['similarity'],reverse=True),'threshold':threshold}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('folder'); parser.add_argument('--preview',action='store_true'); parser.add_argument('--threshold',type=float,default=.5); parser.add_argument('--report',default='reports/verification.json'); args=parser.parse_args()
    if not 0<args.threshold<=1: parser.error('threshold debe estar entre 0 y 1')
    result=verify(args.folder,args.threshold,args.preview)
    output=Path(args.report); output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    for message in result['errors']: print('FALLO:',message)
    for message in result['warnings']: print('AVISO:',message)
    print(f'{result["pages"]} páginas · {len(result["errors"])} fallos · {len(result["warnings"])} avisos')
    if result['pairs']: print('Máxima similitud:',f'{result["pairs"][0]["similarity"]:.1%}')
    sys.exit(bool(result['errors']))
