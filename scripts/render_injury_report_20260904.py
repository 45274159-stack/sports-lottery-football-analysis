import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

root=Path('/workspace/scratch/25a8eae0469b')
data=json.loads(Path('reports/model_run_20260904_injuries.json').read_text())
snap=json.loads(Path('data/prematch/2026-09-04-injuries.json').read_text())
font='/workspace/scratch/e2199d158bd5/tmp/pdfs/fontpkg/NotoSansSC-700.ttf'
im=Image.new('RGB',(1600,2520),'#0c1626'); d=ImageDraw.Draw(im)
def text(x,y,s,size=26,color='#e7edf7'):
    d.text((x,y),s,font=ImageFont.truetype(font,size),fill=color)
def box(y,h): d.rounded_rectangle((40,y,1560,y+h),18,fill='#17283e')
text(55,35,'竞彩足球｜模型实跑 + 伤停观察',49,'#f3d08b')
stamp=datetime.fromisoformat(data['created_at']).astimezone(timezone(timedelta(hours=8))).strftime('%m-%d %H:%M')
text(55,110,f'2026年9月4日 · 周五   /   北京时间 {stamp} 计算',28)
text(55,160,'sports-lottery-football-analysis · 17,937条历史赛果 · 不使用赔率生成概率',25,'#93cdd7')
box(210,150)
text(65,225,'重要边界：14场中仅6场有对应历史模型，8场不硬填预测。',30,'#f3d08b')
text(65,277,'2026/27数据尚未补齐，原始概率未校准；伤停已挂接资料，但未数值加权。',26)
text(65,317,'以下比分均为90分钟主队在前；“最大概率”不等于高把握。',25)
text(55,388,'01 / 完整赛程与处理意见',32)
text(55,433,'全部开赛时间为北京时间9月5日；编号来自当日第三方列表，受注以体彩终端为准。',24,'#aabbd0')
headers=[(65,'编号'),(220,'开赛'),(385,'主队 — 客队'),(1140,'分析状态')]
d.rectangle((40,485,1560,530),fill='#28465e')
for x,s in headers:text(x,490,s,25)
choices={'002':'偏主胜，防平','008':'偏主胜，伤停风险','009':'偏客胜，防平','010':'模型冲突，回避','011':'模型冲突，回避','012':'偏主胜，谨慎'}
for i,m in enumerate(snap['fixtures']):
    y=531+i*44
    d.rectangle((40,y,1560,y+43),fill='#17283e' if i%2==0 else '#111f32')
    num=m['number'][-3:]
    label=' — '.join(t['name_zh'] for t in m['teams'])
    for x,s in [(65,m['number']),(220,m['kickoff'][11:16]),(385,label),(1140,choices.get(num,'模型未覆盖'))]:
        text(x,y+5,s,24)
text(55,1180,'02 / 原始概率对照与比分分布',32)
text(55,1227,'A＝历史主客场模型；B＝拟合攻防模型。胜 / 平 / 负均相对主队。',25,'#aabbd0')
d.rectangle((40,1280,1560,1330),fill='#28465e')
for x,s in [(65,'编号'),(205,'A：胜 / 平 / 负 %'),(600,'B：胜 / 平 / 负 %'),(1020,'B：概率最高的两个比分')]:text(x,1288,s,24)
for i,r in enumerate(data['results']):
    out=r['comparison']['outputs'];a=out['venue-form-v1']['prediction'];b=out['fitted-attack-defence-v1']['prediction']
    vals=[' / '.join(f'{p["result"][k]*100:.1f}' for k in 'HDA') for p in [a,b]]
    scores='、'.join(f'{s} ({p*100:.1f}%)' for s,p in b['scores'][:2])
    y=1331+i*61;d.rectangle((40,y,1560,y+60),fill='#17283e' if i%2==0 else '#111f32')
    for x,s in [(65,r['number']),(205,vals[0]),(600,vals[1]),(1020,scores)]:text(x,y+14,s,25)
box(1730,365)
text(65,1747,'03 / 结合伤停后的人工风险判断（不改模型数值）',30,'#f3d08b')
notes=[
'002 里昂：双模型偏胜，但主勝仅47%—55%；伤停报道有分歧，防平。',
'008 斯图加特：双模型偏胜；官方列多名缺阵，不能按完整阵容看待。',
'009 科莫：客胜44%—51%，优势有限；比分集中小比分，平局仍要防。',
'010 利物浦：客胜37.5%与69.3%分歧显著，且官方有多名伤缺；回避当胆。',
'011 皇马：A偏主胜、B偏客胜，缺少新赛季完整解释；不强行选边。',
'012 巴黎：双模型偏胜；摩纳哥复训与伤缺报道不同，正式名单仍需核对。']
for i,s in enumerate(notes):text(65,1805+i*43,s,25)
box(2120,235)
text(65,2135,'本次结论：有观察方向，没有“最稳比分串”',32,'#f2ab97')
text(65,2194,'比分单项概率多在一成左右；两场都猜对更难，不把比分当作稳健玩法。',26)
text(65,2238,'伤停覆盖24/28队；汉诺威、卡尔斯鲁厄、格勒诺布尔、福伦丹仍缺名单。',25)
text(65,2282,'只作小额娱乐；不因日上限500元而花满，不追损、不加倍。',26)
text(55,2390,'赛程：足彩网实时列表；伤停：仓库2026-09-04快照（逐条保留来源）。',23,'#aabbd0')
text(55,2434,'预测：本次实际运行结果；无伤停权重 / 无校准 / 不承诺命中。',23,'#aabbd0')
path=root/'football_model_injuries_20260904.png';im.save(path);print(path)
