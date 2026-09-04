"""Exact-data black/gold football poster; no synthetic probabilities."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json, random, math
ROOT=Path('/workspace/scratch/25a8eae0469b')
report=json.loads(Path('reports/model_run_20260904_injuries.json').read_text())
fixtures=json.loads(Path('data/prematch/2026-09-04-injuries.json').read_text())['fixtures']
results={r['number']:r['comparison']['outputs'] for r in report['results']}
W,H=2000,2190
im=Image.new('RGB',(W,H),'#08131f');d=ImageDraw.Draw(im)
FONT='/workspace/scratch/e2199d158bd5/tmp/pdfs/fontpkg/NotoSansSC-700.ttf'
def tx(x,y,s,size=28,color='#eef3f4'):
    d.text((x,y),s,font=ImageFont.truetype(FONT,size),fill=color)
def center(x,y,w,s,size=28,color='#eef3f4'):
    f=ImageFont.truetype(FONT,size);d.text((x+(w-d.textlength(s,font=f))/2,y),s,font=f,fill=color)
def panel(x,y,w,h,title,color):
    d.rounded_rectangle((x,y,x+w,y+h),18,fill='#0b1a27',outline=color,width=2)
    d.rounded_rectangle((x+4,y+65,x+w-4,y+h-4),12,fill='#ecf1f3')
    tx(x+20,y+9,title,37,color)
def tag(x,y,w,s,color):
    d.rounded_rectangle((x,y,x+w,y+39),6,fill=color);center(x,y+1,w,s,25)
random.seed(9)
for _ in range(1600):
    x=random.randrange(W);y=random.randrange(H);v=random.randrange(20,42)
    d.point((x,y),fill=(v,v+10,v+16))
for a in range(6):d.line((0,160+a*14,2000,20+a*14),fill='#182c3b',width=2)
tx(45,30,'用数据说话',30,'#b9cbd5');tx(45,75,'让热爱更理性',27,'#b9cbd5')
center(310,20,1330,'每日竞彩足球分析',76,'#f0ce83')
center(310,112,1330,'双模型实跑 · 伤停观察 · 理性参考 · 仅供娱乐',29,'#95d3e6')
d.rounded_rectangle((1685,22,1960,145),12,outline='#b69758',width=2)
center(1685,35,275,'2026 / 09 / 04',32);center(1685,83,275,'星期五',30,'#eed298')
tx(42,170,'全部开赛时间：北京时间9月5日｜概率取拟合攻防模型B，尚未校准；主队在前。',27,'#bacbd5')
cols=[40,135,240,690,790,1080,1225,1370,1810,1960]
head=['场次','联赛','对阵','时间','B概率 胜/平/负','B方向','模型对照','分析要点','处理']
top=220;rh=57
d.rounded_rectangle((40,top,1960,top+62),12,fill='#082b50',outline='#7299ae',width=2)
for i,s in enumerate(head):center(cols[i],top+16,cols[i+1]-cols[i],s,24)
leagues=['德乙','法甲','挪超','沙特联','法乙','荷甲','荷乙','德甲','意甲','英超','西甲','法甲','葡超','美职联']
notes={'002':'主胜优势有限，需防平局','008':'主队多人伤缺，优势需降温','009':'客胜略占优，平局不可忽视','010':'两模型方向不同，差距较大','011':'一偏主胜一偏客胜，回避','012':'客队复训消息需临场核对'}
short={'001':'汉诺威96 vs 卡尔斯鲁厄','002':'里昂 vs 欧塞尔','003':'腓特烈斯塔 vs 博德闪耀','004':'利雅得青年 vs 利雅得新月','005':'格勒诺布尔 vs 阿讷西','006':'鹿特丹斯巴达 vs 兹沃勒','007':'埃门 vs 福伦丹','008':'斯图加特 vs 科隆','009':'热那亚 vs 科莫','010':'伊普斯维奇 vs 利物浦','011':'皇家贝蒂斯 vs 皇家马德里','012':'巴黎圣日耳曼 vs 摩纳哥','013':'波尔图 vs 莫雷伦斯','014':'纽约城 vs 纳什维尔'}
for i,m in enumerate(fixtures):
    n=m['number'][-3:];y=top+62+i*rh
    d.rectangle((40,y,1960,y+rh),fill='#f1f5f5' if i%2==0 else '#deeaee')
    vals=[n,leagues[i],short[n],m['kickoff'][11:16]]
    for j,s in enumerate(vals):center(cols[j],y+15,cols[j+1]-cols[j],s,24,'#142434')
    if n in results:
        p=results[n]['fitted-attack-defence-v1']['prediction']['result']
        a=results[n]['venue-form-v1']['prediction']['result'];key=max(p,key=p.get)
        label={'H':'主胜','D':'平局','A':'客胜'}[key];same=max(a,key=a.get)==key
        center(cols[4],y+15,290,' / '.join(f'{p[k]*100:.1f}' for k in 'HDA'),26,'#142434')
        tag(cols[5]+14,y+9,115,label,'#d52e36' if key=='H' else '#078bc0')
        tag(cols[6]+14,y+9,115,'同向' if same else '冲突','#927126' if same else '#7c687b')
        center(cols[7],y+16,440,notes[n],23,'#142434')
        tag(cols[8]+12,y+9,126,'观察' if same else '回避','#334e64' if same else '#76646c')
    else:
        center(cols[4],y+15,290,'— / — / —',26,'#697985')
        center(cols[5],y+15,145,'未覆盖',24,'#697985');center(cols[6],y+15,145,'—',24,'#697985')
        center(cols[7],y+16,440,'缺少对应联赛模型，不填预测',23,'#536778')
        tag(cols[8]+12,y+9,126,'暂缓','#7f8d95')
    for x in cols:d.line((x,y,x,y+rh),fill='#c2d0d6',width=1)

panel(40,1110,620,315,'重点观察｜不是胜率排名','#edc77b')
for i,(n,name,di) in enumerate([('002','里昂','主胜'),('008','斯图加特','主胜'),('009','科莫','客胜'),('012','巴黎圣日耳曼','主胜')]):
    y=1187+i*55;tx(58,y,n,29,'#1c3b52');tx(142,y,name,28,'#172d3c');tag(360,y,95,di,'#d52e36' if di=='主胜' else '#078bc0');tx(485,y,'需防冷',26,'#70613c')
panel(680,1110,620,315,'组合处理｜不强行凑串','#89d4af')
for j,s in enumerate(['本期不提供“稳健二串”','比分单项最高也仅约一成','010 / 011 模型方向冲突','先补新赛季，再校准概率']):tx(703,1188+j*55,s,29,'#253b44')
panel(1320,1110,640,315,'风险提示','#f1a4a0')
for j,s in enumerate(['1. 17,937条历史赛果，非完整新赛季','2. 伤停已附证据，尚未数值加权','3. 24队有报告，4队名单仍缺失','4. 小额娱乐，不追损、不翻倍']):tx(1340,1187+j*55,s,25,'#34414a')

tx(45,1460,'比分推演',51,'#efd18b');tx(330,1480,'攻防模型B前两位比分与概率｜不是确定赛果',29,'#c1d5df')
for block in range(2):
    x=40+block*765;w=735;y=1545
    d.rounded_rectangle((x,y,x+w,y+476),12,fill='#102b40',outline='#8eabba',width=2)
    xs=[x,x+85,x+315,x+545,x+w]
    for j,s in enumerate(['场次','第一比分','第二比分','进球众数']):center(xs[j],y+13,xs[j+1]-xs[j],s,25)
    for idx in range(7):
        n=f'{block*7+idx+1:03d}';yy=y+53+idx*59
        d.rectangle((x+2,yy,x+w-2,yy+58),fill='#e7eff1' if idx%2==0 else '#d1e1e7')
        if n in results:
            b=results[n]['fitted-attack-defence-v1']['prediction'];ss=[f'{s} ({p*100:.1f}%)' for s,p in b['scores'][:2]]
            total=b['total_goals'];g=max(total,key=total.get);vs=[n,*ss,g+'球']
        else:vs=[n,'—','—','—']
        for j,s in enumerate(vs):center(xs[j],yy+15,xs[j+1]-xs[j],s,25,'#193144')
tx(1590,1550,'热爱',45,'#efd18b');tx(1630,1608,'更需理性',39,'#dde9ec')
# Original code-drawn jersey ornament, not a real player or club.
d.polygon([(1660,1715),(1750,1685),(1790,1710),(1830,1685),(1920,1715),(1970,1800),(1910,1830),(1885,1795),(1900,2000),(1680,2000),(1695,1795),(1670,1830),(1610,1800)],fill='#476174',outline='#96b2c2',width=3)
center(1690,1770,200,'DATA',38,'#dbe5e9');center(1690,1825,200,'90',90,'#0a2235')
tx(1585,2040,'FOOTBALL / RESEARCH',21,'#a1c3d2')
tx(45,2050,'进球众数仅指概率最高的一项，不是推荐区间。概率未校准；不承诺命中。',27,'#c0d5df')
tx(45,2098,'数据：本次仓库实跑｜赛程：足彩网｜伤停：9月4日快照｜未覆盖项保持空缺。',24,'#99b3c4')
center(0,2143,2000,'用数据减少盲猜，用克制保护热爱',29,'#e8c983')
out=ROOT/'football_blackgold_20260904.png';im.save(out);print(out)
