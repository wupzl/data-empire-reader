"""Local browser and link verification. Requires playwright and Chromium."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse
import json, mimetypes, re, subprocess, hashlib, ast
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parent
RESULTS=ROOT/'test-results'
RESULTS.mkdir(exist_ok=True)
BOOK=json.loads((ROOT/'book.json').read_text(encoding='utf-8'))
COUNT=len(BOOK['chapters'])
class Page(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.ids=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs: self.ids.append(attrs['id'])
        if tag in ('a','link','script'):
            value=attrs.get('href',attrs.get('src',''))
            if value: self.links.append(value)

pages={}
for file in (ROOT/'docs').glob('*.html'):
    parser=Page(); parser.feed(file.read_text(encoding='utf-8')); pages[file.name]=parser
    # TOCs repeat links but content IDs must be unique.
    assert len(parser.ids)==len(set(parser.ids)),file
assert len(pages)==COUNT+3,len(pages)
for name,parser in pages.items():
    for link in parser.links:
        if link.startswith(('https:','http:','/')): continue
        file,_,anchor=link.partition('#'); file=file or name
        assert (ROOT/'docs'/unquote(file)).is_file(),(name,link)
        if anchor: assert unquote(anchor) in pages[file].ids,(name,link)
for entry in json.loads((ROOT/'docs/search.json').read_text(encoding='utf-8')):
    file,_,anchor=entry['url'].partition('#')
    assert not anchor or anchor in pages[file].ids,entry
assert hashlib.sha256((ROOT/'source/data-empire-original.md').read_bytes()).hexdigest()==json.loads((ROOT/'book.json').read_text(encoding='utf-8'))['source_sha256']
assert hashlib.sha256((ROOT/'source/data-empire-continuation-original.md').read_bytes()).hexdigest()==BOOK['continuation_source_sha256']
for file in (ROOT/'chapters').glob('*.md'):
    assert file.read_text(encoding='utf-8').count('```')%2==0,file
    for code in re.findall(r'```python\n(.*?)```',file.read_text(encoding='utf-8'),re.S):
        ast.parse(code,filename=str(file))
for name in ('app.js','labs.js','quizzes.js'):
    subprocess.run(['node','--check',str(ROOT/'assets'/name)],check=True)
subprocess.run(['node',str(ROOT/'tests/models.cjs')],check=True)

with sync_playwright() as pw:
    browser=pw.chromium.launch()
    errors=[]
    for width in (390,768,1440):
        context=browser.new_context(viewport={'width':width,'height':950},permissions=['clipboard-read','clipboard-write'])
        page=context.new_page(); page.on('pageerror',lambda e: errors.append(str(e)))
        def serve(route):
            path=unquote(urlparse(route.request.url).path)
            if path.startswith('/data-empire-reader/'):
                file=ROOT/'docs'/(path[len('/data-empire-reader/'):] or 'index.html')
            elif path.startswith('/pytorch-apprentice/'):
                file=ROOT.parent/'pytorch-apprentice/docs'/(path[len('/pytorch-apprentice/'):] or 'index.html')
            elif path.startswith('/ai-era-reader/'):
                file=ROOT.parent/'ai-era-reader/docs'/(path[len('/ai-era-reader/'):] or 'index.html')
            else: file=ROOT.parent/'bookshelf'/(path.lstrip('/') or 'index.html')
            if file.is_file(): route.fulfill(path=str(file),content_type=mimetypes.guess_type(file)[0] or 'application/octet-stream')
            else: route.fulfill(status=404,body='Missing file')
        page.route('https://reader.test/**',serve)
        page.route('https://images.openai.com/**',lambda r:r.abort())
        base='https://reader.test/data-empire-reader/'
        for name in pages:
            response=page.goto(base+name); assert response.status==200
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,name)
            assert page.locator('[data-lab] .lab-output').count()==page.locator('[data-lab]').count(),name
            assert page.locator('.shelf-nav').count()==1
        assert not errors,errors
        page.goto(base+'index.html'); page.locator('#theme').click(); page.locator('#theme').click(); page.locator('#larger').click(); page.reload()
        assert page.locator('html').get_attribute('data-theme')=='dark'
        assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--reader-size')").strip()=='19px'
        page.locator('#theme').click()
        page.screenshot(path=str(RESULTS/f'home-{width}.png'),full_page=True)
        page.locator('#search-open').click(); page.locator('#query').fill('Checkpoint')
        expect(page.locator('.search-result').first).to_be_visible(); assert page.locator('mark').count()>0
        page.keyboard.press('Escape'); expect(page.locator('#search-dialog')).not_to_be_visible()
        page.goto(base+'chapter-02.html'); copy=page.locator('.copy-code').first; copy.click(); expect(copy).to_have_text('已复制')
        assert page.evaluate('navigator.clipboard.readText()')
        quiz=page.locator('[data-quiz="2"]'); quiz.get_by_role('button',name='查看参考答案').click(); expect(quiz.locator('#quiz-answer-2')).to_be_visible()
        quiz.get_by_role('button',name='下一题',exact=True).click(); expect(quiz.locator('#quiz-answer-2')).not_to_be_visible()
        page.evaluate("scrollTo({top:(document.documentElement.scrollHeight-innerHeight)*0.5,behavior:'instant'})"); page.wait_for_timeout(300)
        page.reload(); page.wait_for_timeout(300)
        assert .42<page.evaluate('scrollY/(document.documentElement.scrollHeight-innerHeight)')<.58
        page.goto(base+'index.html'); expect(page.locator('#resume')).to_be_visible()
        page.goto(base+'practice.html')
        lab=lambda kind:page.locator(f'[data-lab="{kind}"]')
        expect(lab('little').locator('.lab-output')).to_contain_text('200 个')
        lab('little').locator('input').first.fill('2000'); expect(lab('little').locator('.lab-output')).to_contain_text('400 个')
        lab('little').locator('input').first.fill('-1'); expect(lab('little').locator('.lab-output')).to_contain_text('请检查输入')
        lab('little').get_by_role('button',name='重置实验').click(); expect(lab('little').locator('.lab-output')).to_contain_text('200 个')
        for _ in range(4): lab('atomic').get_by_role('button',name='下一步').click()
        expect(lab('atomic').locator('.lab-output')).to_contain_text('超卖')
        lab('atomic').locator('select').select_option('lua')
        for _ in range(2): lab('atomic').get_by_role('button',name='下一步').click()
        expect(lab('atomic').locator('.lab-output')).to_contain_text('拒绝领取')
        for _ in range(6): lab('bucket').get_by_role('button',name='发送请求').click()
        expect(lab('bucket').locator('.lab-output')).to_contain_text('已放行 5 · 已拒绝 1')
        lab('bucket').get_by_role('button',name='补充令牌').click(); expect(lab('bucket').locator('.lab-output')).to_contain_text('剩余令牌 1')
        expect(lab('pagination').locator('.lab-output')).to_contain_text('100,020')
        lab('shard').locator('input').fill('9007199254740993'); expect(lab('shard').locator('.lab-output')).to_contain_text('orders_01')
        for _ in range(3): lab('wordcount').get_by_role('button',name='下一步').click()
        expect(lab('wordcount').locator('.lab-output')).to_contain_text('Reduce 汇总')
        expect(lab('skew').locator('.lab-output')).to_contain_text('82%')
        for _ in range(6): lab('watermark').get_by_role('button',name='接收下一条事件').click()
        expect(lab('watermark').locator('.lab-output')).to_contain_text('窗口金额 ¥350')
        expect(lab('watermark').locator('.lab-output')).to_contain_text('丢弃 1 条')
        expect(lab('lag').locator('.lab-output')).to_contain_text('150 秒')
        lab('lag').locator('input').nth(1).fill('80000'); expect(lab('lag').locator('.lab-output')).to_contain_text('无法清空')
        expect(lab('capacity').locator('.lab-output')).to_contain_text('72 台')
        for kind in ('queue','pagination','shard','wordcount','skew','watermark','lag','capacity'):
            lab(kind).get_by_role('button',name='重置实验').click()
        lab('watermark').scroll_into_view_if_needed(); page.screenshot(path=str(RESULTS/f'lab-{width}.png'))
        # New continuation interactions, including invalid input and transaction alternatives.
        expect(lab('reconcile').locator('.lab-output')).to_contain_text('¥400')
        lab('reconcile').locator('input').first.check(); expect(lab('reconcile').locator('.lab-output')).to_contain_text('¥300')
        lab('reconcile').locator('input').nth(1).check(); expect(lab('reconcile').locator('.lab-output')).to_contain_text('¥270')
        expect(lab('granules').locator('.lab-output')).to_contain_text('跳过 29')
        lab('granules').locator('input').fill('32'); expect(lab('granules').locator('.active')).to_have_count(32)
        lab('granules').locator('input').fill('33'); expect(lab('granules').locator('.lab-output')).to_contain_text('请检查输入')
        lab('granules').get_by_role('button',name='重置实验').click()
        lab('querycost').locator('select').select_option('3'); expect(lab('querycost').locator('.lab-output')).to_contain_text('物化预聚合结果')
        expect(lab('unitcost').locator('.lab-output')).to_contain_text('¥20.00')
        expect(lab('unitcost').locator('.lab-output')).to_contain_text('¥16.00')
        lab('unitcost').locator('input').nth(1).fill('0'); expect(lab('unitcost').locator('.lab-output')).to_contain_text('请检查输入')
        lab('unitcost').get_by_role('button',name='重置实验').click()
        lab('stocksql').locator('select').select_option('lua')
        for _ in range(2): lab('stocksql').get_by_role('button',name='下一步').click()
        expect(lab('stocksql').locator('.lab-output')).to_contain_text('拒绝领取')
        for number in range(9,13):
            page.goto(base+f'chapter-{number:02}.html')
            quiz=page.locator(f'[data-quiz="{number}"]')
            expect(quiz.locator('.eyebrow')).to_contain_text('1 / 10')
            quiz.get_by_role('button',name='查看参考答案').click(); expect(quiz.locator(f'#quiz-answer-{number}')).to_be_visible()
            for _ in range(9): quiz.get_by_role('button',name='下一题',exact=True).click()
            expect(quiz.get_by_role('button',name='下一题',exact=True)).to_be_disabled()
            target=page.locator('.concept').first if page.locator('.concept').count() else page.locator('.table-wrap').first
            target.screenshot(path=str(RESULTS/f'continuation-{number}-{width}.png'))
        page.goto(base+f'chapter-{COUNT:02}.html'); expect(page.locator('.chapter-nav')).to_contain_text(f'第 {COUNT+1} 章尚未发布')
        page.goto(base+'chapter-11.html')
        assert page.locator('math').count()>0
        page.screenshot(path=str(RESULTS/f'chapter-{width}.png'))
        context.close()
    assert not errors,errors
    browser.close()
print(f'PASS: {len(pages)} pages at 390/768/1440 px, links/anchors, both source archives, Python syntax, JS, labs, quizzes, themes, copy, search and progress restore.')
