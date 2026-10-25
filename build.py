"""Build the serial reader from maintained Markdown; no network access required."""
from pathlib import Path
import html, json, re, shutil, subprocess
import markdown
from pygments.formatters import HtmlFormatter

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'docs'
OUT.mkdir(exist_ok=True)
BOOK=json.loads((ROOT/'book.json').read_text(encoding='utf-8'))
NAMES=[c['title'] for c in BOOK['chapters']]
TOPICS=[c['topics'] for c in BOOK['chapters']]
COUNT=len(NAMES)
OPTIONAL=BOOK['next'].get('optional',False)
STATUS=f'现有 {COUNT} 章 · 可选进阶篇' if OPTIONAL else f'现有 {COUNT} 章 · 第 {COUNT+1} 章待续'
assert len(list((ROOT/'chapters').glob('[0-9][0-9].md')))==COUNT, 'Update book.json together with chapters/'

def page(title,body,chapter=0):
    menu=''.join(f'<a href="/{slug}/"'+(' aria-current="true"' if slug=='data-empire-reader' else '')+f'>{name}</a>' for slug,name in [('pytorch-apprentice','PyTorch：炼金术士的学徒'),('ai-era-reader','AI 纪元'),('data-empire-reader','数据帝国'),('rag-empire-reader','RAG 帝国'),('system-design-reader','系统设计')])
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="数据帝国：以 Java 后端工程师的视角，在小说和交互实验中理解高并发与大数据。{STATUS}。"><title>{html.escape(title)} · 数据帝国</title><script>try{{document.documentElement.dataset.theme=localStorage.getItem('de-theme')||'light';document.documentElement.style.setProperty('--reader-size',Math.max(14,Math.min(26,Number(localStorage.getItem('de-size'))||18))+'px')}}catch(e){{}}</script><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="shelf-nav.css"><link rel="stylesheet" href="labs.css"><script src="app.js" defer></script><script src="labs.js" defer></script><script src="quizzes.js" defer></script><script src="white-theme.js" defer></script></head>
<body data-chapter="{chapter}" data-count="{COUNT}"><a class="skip" href="#main">跳到正文</a><div id="progress" aria-hidden="true"></div><header class="topbar"><a class="brand" href="index.html"><span class="emblem" aria-hidden="true">D<span>↗</span></span><span>数据帝国<small>THE DATA EMPIRE</small></span></a><nav class="shelf-nav" aria-label="学习项目导航"><a class="shelf-home" href="/">← 学习书架</a><details class="shelf-switch"><summary>切换项目 ▾</summary><div class="shelf-menu">{menu}</div></details></nav><div class="controls"><button id="search-open" aria-label="搜索全书">搜索 <kbd>/</kbd></button><button id="smaller" aria-label="缩小字号">A−</button><button id="larger" aria-label="增大字号">A＋</button><button id="theme" aria-label="切换深浅色主题">◐</button></div></header>
{body}<footer><a href="index.html">数据帝国</a><p>在故事中理解系统，在实验中观察原理。<span>{STATUS}</span></p><a href="https://github.com/wupzl/data-empire-reader">项目源码 ↗</a></footer>
<dialog id="search-dialog" aria-labelledby="search-title"><div class="search-top"><h2 id="search-title">在帝国里寻找答案</h2><button id="search-close" aria-label="关闭搜索">关闭 ×</button></div><label for="query">关键词或代码，例如 Redis、背压、Checkpoint</label><input id="query" type="search" autocomplete="off" placeholder="搜索全书正文…"><p id="search-status" role="status">输入关键词，搜索 {COUNT} 章内容</p><div id="search-results"></div></dialog></body></html>'''

def render(source,toc=False):
    formulas=[]
    def stash(m):
        formulas.append({'tex':m[1] if m[1] is not None else m[2],'display':m[1] is not None})
        return f'MATHTOKEN{len(formulas)-1}END'
    chunks=re.split(r'(```.*?```|`[^`\n]+`)',source,flags=re.S)
    for i in range(0,len(chunks),2):
        chunks[i]=re.sub(r'\\\[(.*?)\\\]|\\\((.*?)\\\)',stash,chunks[i],flags=re.S)
    md=markdown.Markdown(extensions=['fenced_code','tables','toc','sane_lists','codehilite'],extension_configs={'toc':{'toc_depth':'2-2'},'codehilite':{'guess_lang':False}})
    rendered=md.convert(''.join(chunks))
    if formulas:
        run=subprocess.run(['node',str(ROOT/'render-math.cjs')],input=json.dumps(formulas),text=True,encoding='utf-8',capture_output=True,check=True)
        for i,value in enumerate(json.loads(run.stdout)): rendered=rendered.replace(f'MATHTOKEN{i}END',value)
    return rendered,md.toc

metadata=[]; search=[]
for i,path in enumerate(sorted((ROOT/'chapters').glob('[0-9][0-9].md'))):
    source=path.read_text(encoding='utf-8'); rendered,toc=render(source,True)
    title=NAMES[i]; minutes=max(5,round(len(source)/450))
    metadata.append({'number':i+1,'title':title,'topics':TOPICS[i],'minutes':minutes})
    booknav=''.join(f'<a class="{"current" if k==i else ""}" href="chapter-{k+1:02}.html"'+(' aria-current="page"' if k==i else '')+f'><span>{k+1:02}</span>{name}</a>' for k,name in enumerate(NAMES))
    nav=f'<a href="chapter-{i:02}.html">← 上一章<span>{NAMES[i-1]}</span></a>' if i else '<a href="index.html">← 全书目录<span>回到故事起点</span></a>'
    nav+=f'<a href="chapter-{i+2:02}.html">下一章 →<span>{NAMES[i+1]}</span></a>' if i<COUNT-1 else (f'<a href="index.html#coming">本阶段读毕 →<span>第 {COUNT+1} 章为可选进阶设想 · 返回目录</span></a>' if OPTIONAL else f'<a href="index.html#coming">待续 →<span>第 {COUNT+1} 章尚未发布 · 返回目录</span></a>')
    body=f'''<div class="reader-layout"><aside class="sidebar"><p class="eyebrow">THE EMPIRE’S JOURNEY</p><nav aria-label="全书章节">{booknav}</nav><details class="local-toc" open><summary>本章线索</summary>{toc}</details></aside><main id="main" class="chapter-main"><div class="chapter-heading"><p class="eyebrow">CHAPTER {i+1:02} <span>/ {COUNT:02} · 约 {minutes} 分钟</span></p><h1>{title}</h1><p class="topics">{TOPICS[i]}</p><div class="bridge">先遇见系统的问题，再理解技术为什么出现。</div></div><details class="mobile-toc"><summary>章节与本章目录</summary><nav aria-label="移动端章节">{booknav}</nav>{toc}</details><article>{rendered}</article><section class="practice"><h2>把原理放进实验</h2><p>调整参数，观察系统如何变化。所有实验均在当前浏览器中运行。</p><a href="practice.html">查看全部交互实验 →</a> · <a href="editorial.html">内容整理与技术校正 →</a></section><nav class="chapter-nav" aria-label="上下章">{nav}</nav></main></div>'''
    (OUT/f'chapter-{i+1:02}.html').write_text(page(title,body,i+1),encoding='utf-8')
    # Use actual rendered headings, including Unicode-safe anchors, as search boundaries.
    sections=re.split(r'(<h2 id="[^"]+">.*?</h2>)',rendered,flags=re.S)
    heading='故事开始'; anchor=''
    for section in sections:
        match=re.fullmatch(r'<h2 id="([^"]+)">(.*?)</h2>',section,flags=re.S)
        if match: anchor=match[1]; heading=html.unescape(re.sub('<[^>]+>','',match[2])); continue
        text=html.unescape(re.sub('<[^>]+>',' ',section))
        search.append({'chapter':i+1,'title':title,'section':heading,'url':f'chapter-{i+1:02}.html'+('#'+anchor if anchor else ''),'text':re.sub(r'\s+',' ',text)})

cards=''
for i,item in enumerate(metadata):
    stages={0:'01 / 守住交易城',2:'02 / 海量存储',3:'03 / 分布式计算',5:'04 / 实时数据流',7:'05 / 系统设计',8:'06 / 可信数据与分析',10:'07 / 资源与工程验证',12:'08 / 持续演化与可靠性'}
    if i in stages: cards+=f'<div class="stage"><span>{stages[i]}</span><i></i></div>'
    cards+=f'<a class="chapter-card" href="chapter-{i+1:02}.html"><span class="chapter-number">{i+1:02}</span><div><h3>{item["title"]}</h3><p>{item["topics"]}</p></div><span class="card-meta">约 {item["minutes"]} 分钟 <b>↗</b></span></a>'
home=f'''<main id="main" class="home"><section class="hero"><div class="hero-copy"><p class="eyebrow">一部高并发与大数据技术小说</p><h1>每一座帝国，<br>都经历过<span>拥堵。</span></h1><p class="hero-subtitle">数据帝国 · 千万并发的战争</p><p class="intro">一万人，同时敲响交易城的城门。<br>从最后一张优惠券，到永不停歇的数据之河。<br>跟随 Java 国王与架构师，理解系统背后的取舍。</p><div class="hero-actions"><a class="primary" href="chapter-01.html">翻开第一章 <span>→</span></a><a id="resume" class="resume" href="chapter-01.html" hidden>继续上次阅读 →</a></div><p class="hero-note">{COUNT} 个章节 <span>·</span> {"可选进阶篇" if OPTIONAL else f"第 {COUNT+1} 章待续"} <span>·</span> 无需登录</p></div><div class="book-art" aria-hidden="true"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><div class="book"><p>THE DATA<br>EMPIRE</p><div class="book-title">数据帝国<span>千万并发的战争</span></div><div class="book-symbol">∞<span>从一条请求，到千万并发</span></div><div class="book-bottom">CONCURRENCY → BIG DATA<span>VOL. 01</span></div></div><span class="art-note">技术的答案，藏在问题里。</span></div></section><section class="journey"><p class="eyebrow">FOLLOW THE PROBLEM</p><h2>先遇见问题，再认识答案。</h2><p>缓存为什么出现？消息为什么排队？数据为什么分片？让系统遇到的每一次困境，成为下一步理解的起点。</p><div class="path"><span>高并发</span><b>→</b><span>海量存储</span><b>→</b><span>分布式计算</span><b>→</b><span>实时系统</span></div></section><section class="catalog"><div class="catalog-heading"><div><p class="eyebrow">A CONNECTED LEARNING JOURNEY</p><h2>帝国的技术战争</h2></div><a href="practice.html">进入交互实验室 ↗</a></div><div class="chapter-list">{cards}</div><div class="coming" id="coming"><span>{COUNT+1:02}</span><div><h3>{BOOK["next"]["title"]}</h3><p>{BOOK["next"]["subtitle"]} · {"可选进阶" if OPTIONAL else "待续"}</p><a href="chapter-08.html#PREVIEW">{"查看进阶设想" if OPTIONAL else "阅读预告"}</a></div><span class="tag">{"可选 · 无正文" if OPTIONAL else "尚未发布"}</span></div></section><section class="reading-note"><h2>怎样读这本书</h2><p>建议顺序阅读。了解基础 Java 与数据库会更容易进入故事；网页实验无需安装中间件。已有 {COUNT} 章正文。{"当前阶段的学习主线已齐备，第十四章仅保留可选进阶设想。" if OPTIONAL else f"第 {COUNT+1} 章只保留预告，后续持续更新。"}</p><p>阅读进度、主题和字号只保存在当前浏览器。<a href="editorial.html">查看内容整理与技术校正 →</a></p></section></main>'''
# Resolve preview anchor from rendered Markdown instead of hardcoding a generated slug.
last=(OUT/f'chapter-{COUNT:02}.html').read_text(encoding='utf-8')
preview=re.search(r'<h2 id="([^"]+)">(?:待续|可选进阶)',last)
home=home.replace('chapter-08.html#PREVIEW',f'chapter-{COUNT:02}.html'+('#'+preview[1] if preview else ''))
(OUT/'index.html').write_text(page('全书目录',home),encoding='utf-8')
labs=[('little','并发实验室'),('atomic','库存原子性'),('queue','消息积压'),('bucket','令牌桶'),('pagination','深分页'),('shard','分片路由'),('wordcount','MapReduce WordCount'),('skew','数据倾斜'),('watermark','事件时间与 Watermark'),('lag','Kafka Lag'),('capacity','API 容量规划')]
labs += [('reconcile','数据口径与重复事件'),('granules','Granule 裁剪'),('querycost','分析查询资源模型'),('unitcost','单位请求成本'),('stocksql','数据库并发库存更新')]
labs += [('canary','金丝雀流量阶段'),('faultlab','故障演练检查'),('errorbudget','SLO 错误预算与 Burn Rate')]
practice='# 帝国交互实验室\n\n在浏览器中修改参数、逐步执行并重置实验。结果为教学模型，适用条件见各实验说明。\n\n'+''.join(f'## {name}\n\n<div class="lab" data-lab="{key}"></div>\n\n' for key,name in labs)
for name,title,source in [('practice','交互实验室',practice),('editorial','内容整理与技术校正',(ROOT/'EDITORIAL.md').read_text(encoding='utf-8'))]:
    body,_=render(source)
    (OUT/f'{name}.html').write_text(page(title,f'<main id="main" class="standalone"><a href="index.html">← 返回全书目录</a><article>{body}</article></main>'),encoding='utf-8')
(OUT/'search.json').write_text(json.dumps(search,ensure_ascii=False),encoding='utf-8')
(OUT/'chapters.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'syntax.css').write_text(HtmlFormatter().get_style_defs('.codehilite'),encoding='utf-8')
for path in (ROOT/'assets').iterdir():
    if path.is_file(): shutil.copyfile(path,OUT/path.name)
(OUT/'.nojekyll').touch()
print(f'Built {len(metadata)} chapters, {len(labs)} interactive labs and 3 supporting pages.')
