from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
W,H=1080,1920
im=Image.new('RGB',(W,H)); pix=im.load()
for y in range(H):
 for x in range(W):
  t=(x/W*.32+y/H*.68); pix[x,y]=(int(255-30*t),int(205-74*t),int(159+64*t))
d=ImageDraw.Draw(im)
font='graphics/templates/_base/fonts/Anton.ttf';inter='graphics/templates/_base/fonts/Inter.ttf'
def text(x,y,s,size,fill):d.text((x,y),s,font=ImageFont.truetype(font,size),fill=fill,stroke_width=0)
d.text((75,355),'GTA 6 CLIPPER',font=ImageFont.truetype(inter,36),fill='#492851',stroke_width=0)
text(68,415,'TURN STREAMS',119,'#252343'); text(68,562,'INTO SHORTS',119,'#432754')
# Tool-specific illustration: long horizontal stream, cut to vertical phone format.
d.rounded_rectangle((78,810,706,1198),38,fill='#fff7ee',outline='#513858',width=7)
d.rounded_rectangle((99,832,686,1114),22,fill='#393b62')
d.polygon([(324,885),(324,1044),(458,965)],fill='#ffd252')
d.rectangle((110,1142,654,1162),fill='#dbbed3');d.rounded_rectangle((274,1128,465,1178),12,outline='#e45c87',width=7)
d.rounded_rectangle((737,816,987,1314),40,fill='#292841',outline='#fff7ee',width=8)
d.rounded_rectangle((755,842,969,1272),20,fill='#f9e5d8')
d.rounded_rectangle((770,860,954,1007),14,fill='#775f8a');d.ellipse((833,890,895,952),fill='#ffd252')
d.rounded_rectangle((770,1020,954,1197),14,fill='#a97b99');d.rectangle((788,1218,935,1232),fill='#4b3a60');d.rectangle((808,1242,916,1255),fill='#e45c87')
d.line([(545,1260),(637,1307),(690,1307)],fill='#503553',width=12);d.polygon([(690,1275),(744,1307),(690,1339)],fill='#503553')
d.text((83,1430),'LONG STREAM',font=ImageFont.truetype(inter,30),fill='#493050'); d.text((747,1430),'9:16 CLIP',font=ImageFont.truetype(inter,30),fill='#493050')
d.text((75,1550),'@HYPELESS',font=ImageFont.truetype(inter,28),fill='#503553')
im.save('covers/repo-gta6-clipper-01/custom-cover-proposal.png')
