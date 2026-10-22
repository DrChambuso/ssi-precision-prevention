from pathlib import Path
from html.parser import HTMLParser
from html import unescape
import re,json,csv
root=Path('__SOURCE_ROOT__/Conference Bloodstreem Dataset/Sources/CDC_AR')
out=Path('work/ssi_inferential_microbiology')
class Tables(HTMLParser):
 def __init__(self): super().__init__();self.rows=[];self.cell=None;self.row=None;self.sup=0
 def handle_starttag(self,t,a):
  a=dict(a)
  if t=='tr':self.row=[]
  if t in ['td','th']: self.cell={'text':'','sup':'','rowspan':int(a.get('rowspan',1)),'colspan':int(a.get('colspan',1))}
  if t=='sup':self.sup+=1
  if t=='br' and self.cell is not None:self.cell['text']+=' '
 def handle_endtag(self,t):
  if t=='sup':self.sup=max(0,self.sup-1)
  if t in ['td','th'] and self.cell is not None:
   self.cell['text']=re.sub(r'\s+',' ',self.cell['text']).strip();self.row.append(self.cell);self.cell=None
  if t=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
 def handle_data(self,s):
  if self.cell is not None:self.cell['sup' if self.sup else 'text']+=s
for age in ['adult','pediatric']:
 html=(root/(age+'_2015_2017.html')).read_text()
 sections={}
 for m in re.finditer(r'<section class="tw xbox font-sm" id="([^"]+)">(.*?)</section>',html,re.S):
  id_,sec=m.groups();table=re.search(r'<table.*?</table>',sec,re.S)
  if table:
   p=Tables();p.feed(table[0]);sections[id_]={'raw_rows':p.rows,'html':sec}
   with open(out/f'{age}_{id_}_rows.txt','w') as f:
    for row in p.rows:f.write(' | '.join(c['text']+(' {sup='+c['sup']+'}' if c['sup'] else '') for c in row)+'\n')
   (out/f'{age}_{id_}_section.html').write_text(sec)
   # Span-expanded table
   grid={};ri=0
   for row in p.rows:
    ci=0
    for cell in row:
     while (ri,ci) in grid:ci+=1
     for rr in range(cell['rowspan']):
      for cc in range(cell['colspan']):grid[ri+rr,ci+cc]=cell['text']
     ci+=cell['colspan']
    ri+=1
   ncols=max(c for r,c in grid)+1
   with open(out/f'{age}_{id_}_expanded.csv','w') as f:
    w=csv.writer(f);w.writerows([[grid.get((r,c),'') for c in range(ncols)] for r in range(ri)])
 (out/f'{age}_tables.json').write_text(json.dumps({k:{'raw_rows':v['raw_rows']} for k,v in sections.items()},indent=2))
 print(age,list(sections))
