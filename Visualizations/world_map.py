import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageOps, ImageDraw
import numpy as np, os

COLORS = {'Christianity':'#CC0000','Judaism':'#0000CC','Islam':'#007700','Buddhism':'#7B3F00','Hinduism':'#CC6600'}

scholars = [
    # Christianity
    ('Rosemary\nRadford Ruether','Christianity', 0.17, 0.75, 'ruether.jpg',  0.35),
    ('Baruch Spinoza',           'Judaism',      0.47, 0.90, 'spinoza.jpg',  0.35),
    ('John Wesley',              'Christianity', 0.47, 0.78, 'wesley.jpg',   0.35),
    ('Hannah Arendt',            'Christianity', 0.56, 0.90, 'arendt.jpeg',  0.35),
    ('Martin Luther',            'Christianity', 0.56, 0.78, 'luther.jpg',   0.35),
    ('Thomas Aquinas',           'Christianity', 0.53, 0.66, 'aquinas.jpg',  0.35),

    # Judaism
    ('Martin Buber',             'Judaism',      0.60, 0.56, 'buber.jpg',    0.35),
    ('Moses Maimonides',         'Judaism',      0.60, 0.42, 'maimonides.jpeg',0.35),

    # Islam — Shariati moved right to 0.70 so no overlap with Nisargadatta at 0.63
    ('Fatema Mernissi',          'Islam',        0.46, 0.66, 'mernissi.jpeg',0.35),
    ('Ibn Taymiyya',             'Islam',        0.62, 0.66, 'taymiyya.jpeg',0.35),
    ('Al-Ghazali',               'Islam',        0.66, 0.80, 'ghazali.jpeg', 0.35),
    ('Ali Shariati',             'Islam',        0.66, 0.68, 'shariati.jpg', 0.35),

    # Buddhism
    ('Tsongkhapa',               'Buddhism',     0.79, 0.82, 'Tsongkhapa.jpg',0.35),
    ('14th Dalai Lama',          'Buddhism',     0.79, 0.70, 'lama.jpeg',    0.35),
    ('Ledi Sayadaw',             'Buddhism',     0.75, 0.58, 'sayadaw.jpg',  0.0),
    ('Yin Shun',                 'Buddhism',     0.84, 0.70, 'shun.jpg',     0.35),
    ('Dogen',                    'Buddhism',     0.84, 0.82, 'dogen.jpg',    0.35),
    ('Hakuin Ekaku',             'Buddhism',     0.84, 0.58, 'ekaku.jpeg',   0.35),

    # Hinduism — Nisargadatta moved to 0.63 (left column), well clear of Shariati at 0.70
    ('Swami\nVivekananda',       'Hinduism',     0.75, 0.58, 'swami.jpg',    0.35),
    ('Nisargadatta\nMaharaj',    'Hinduism',     0.65, 0.54, 'maharaj.jpeg', 0.35),
    ('Sri Aurobindo',            'Hinduism',     0.75, 0.46, 'aurobindo.jpg',0.35),
    ('Ramanuja',                 'Hinduism',     0.75, 0.34, 'ramanuja.jpeg',0.35),
    ('Adi Shankara',             'Hinduism',     0.65, 0.42, 'shankara.jpeg',0.35),
]

def recolor(p):
    img=Image.open(p).convert('RGB'); arr=np.array(img,dtype=np.float32); b=arr.mean(axis=2)
    out=np.zeros((*arr.shape[:2],4),dtype=np.uint8)
    out[b<30,:]=[20,20,20,255]; out[(b>=30)&(b<240),:]=[195,200,200,255]; out[b>=240,:]=[180,210,230,255]
    return out

def circ(path,size=80,v_offset=0.35):
    img=Image.open(path).convert('RGBA'); W,H=img.size; sq=min(W,H)
    left=(W-sq)//2; top=int((H-sq)*v_offset)
    img=img.crop((left,top,left+sq,top+sq)).resize((size*4,size*4),Image.LANCZOS)
    mask=Image.new('L',img.size,0); ImageDraw.Draw(mask).ellipse((0,0,*img.size),fill=255)
    img.putalpha(mask); return np.array(img.resize((size,size),Image.LANCZOS))

fig=plt.figure(figsize=(30,14),facecolor='white')
ax=fig.add_axes([0,0.08,1,0.89])
mp='mercator map.png' if os.path.exists('mercator map.png') else 'mercator_map.png'
m=recolor(mp); H,W=m.shape[:2]; m=m[int(H*0.08):int(H*0.72),:]
ax.imshow(m,aspect='auto',extent=[0,1,0,1],transform=ax.transAxes,zorder=0)
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')

for name,rel,x,y,f,voff in scholars:
    col=COLORS[rel]
    if os.path.exists(f):
        arr=circ(f,v_offset=voff); oi=OffsetImage(arr,zoom=1.0); oi.image.axes=ax
        ax.add_artist(AnnotationBbox(oi,(x,y),xycoords='axes fraction',frameon=True,
            bboxprops=dict(edgecolor=col,linewidth=2.5,boxstyle='round,pad=0.06',facecolor='white'),zorder=5))
        ax.text(x,y-0.055,name,ha='center',va='top',fontsize=10.5,fontweight='bold',color=col,
            transform=ax.transAxes,zorder=6,
            bbox=dict(facecolor='white',alpha=0.92,edgecolor=col,linewidth=0.4,pad=2))
    else:
        ax.plot(x,y,'o',color=col,ms=14,transform=ax.transAxes,zorder=5,
                markeredgecolor='white',markeredgewidth=2)
        ax.text(x,y+0.03,name,ha='center',va='bottom',fontsize=10.5,fontweight='bold',color=col,
            transform=ax.transAxes,zorder=6,
            bbox=dict(facecolor='white',alpha=0.92,edgecolor=col,linewidth=0.4,pad=2))

fig.text(0.5,0.995,'World Map of Religious Scholars',ha='center',va='top',fontsize=17,fontweight='bold')
leg=fig.add_axes([0.01,0.01,0.11,0.12]); leg.axis('off')
leg.add_patch(FancyBboxPatch((0,0),1,1,transform=leg.transAxes,facecolor='white',edgecolor='#aaaaaa',linewidth=0.8,boxstyle='round,pad=0.02'))
leg.text(0.08,0.93,'Religion',fontsize=10,fontweight='bold',transform=leg.transAxes,va='top')
for i,(r,c) in enumerate(COLORS.items()):
    leg.plot(0.10,0.75-i*0.155,'o',color=c,ms=8,transform=leg.transAxes)
    leg.text(0.22,0.75-i*0.155,r,fontsize=9,transform=leg.transAxes,va='center')

plt.savefig('world_map_scholars.pdf',dpi=200,bbox_inches='tight',facecolor='white')
plt.savefig('world_map_scholars.png',dpi=150,bbox_inches='tight',facecolor='white')
print("Done!")