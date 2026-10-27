import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,BASE/'scripts'/f'{name}.py')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
site=module('site'); verifier=module('verificar')

class VerificationTests(unittest.TestCase):
    def test_shared_shell_ignored(self):
        a=verifier.Page('<header>menú</header><main><article>Una recomendación propia de este perfil.</article><aside>texto repetido</aside><div data-shared>banner común</div></main><footer>pie</footer>')
        self.assertEqual(' '.join(a.content),'Una recomendación propia de este perfil.')

    def test_duplicate_detection(self):
        text='Esta combinación permite usar prendas con cintura definida y un largo adecuado para el perfil.'
        self.assertEqual(verifier.shingles(text),verifier.shingles(text.upper()))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ('uno','dos'):
                p=root/name/'index.html'; p.parent.mkdir()
                p.write_text(f'<html><head><title>Título repetido</title><link rel="canonical" href="https://miestilopropio.com/{name}/"><meta name="description" content="Descripción repetida"></head><main><h1>El mismo título</h1><p>{text}</p><a href="/inexistente/">Enlace roto</a></main></html>',encoding='utf-8')
            result=verifier.verify(root)
            self.assertTrue(any('Similitud 100.0%' in e for e in result['errors']))
            self.assertTrue(any('title duplicado' in e for e in result['errors']))
            self.assertTrue(any('inexistente' in e for e in result['errors']))

    def test_post_lifecycle(self):
        import shutil
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ('index.html','404.html','_headers','_redirects','sitemap-colores.xml','sitemap-inicio.xml','sitemap-sitio.xml'):
                shutil.copy2(BASE/name,root/name)
            for name in ('content','public','templates','colores','sobre'):
                shutil.copytree(BASE/name,root/name)
            old_root,old_posts=site.ROOT,site.POSTS
            site.ROOT,site.POSTS=root,root/'content/posts'
            try:
                p=next(site.POSTS.glob('*/post.json')); data=json.loads(site.read(p)); slug=data['slug']
                data['status']='draft'; site.write(p,json.dumps(data))
                preview=site.build(True); production=site.build(False)
                self.assertTrue((preview/'blog'/slug/'index.html').exists())
                self.assertFalse((production/'blog'/slug/'index.html').exists())
                self.assertNotIn(slug,site.read(production/'sitemap-blog.xml'))
                data['status']='published'; site.write(p,json.dumps(data)); site.build(False)
                self.assertTrue((production/'blog'/slug/'index.html').exists())
                self.assertIn(slug,site.read(production/'sitemap-blog.xml'))
                self.assertIn(slug,site.read(production/'index.html'))
                data['status']='archived'; data['redirect_to']='/colores/'; site.write(p,json.dumps(data)); site.build(False)
                self.assertFalse((production/'blog'/slug/'index.html').exists())
                self.assertNotIn(slug,site.read(production/'sitemap-blog.xml'))
                self.assertNotIn(slug,site.read(production/'index.html'))
                self.assertIn(f'/blog/{slug}/ /colores/ 301',site.read(production/'_redirects'))
                self.assertTrue((p.parent/'body.html').exists())
                self.assertFalse((production/'content').exists())
                self.assertFalse((production/'scripts').exists())
            finally:
                site.ROOT,site.POSTS=old_root,old_posts

if __name__=='__main__': unittest.main()
