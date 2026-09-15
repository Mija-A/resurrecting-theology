import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Exact birth/death from the document
scholars = [
    # Christianity
    ('Thomas Aquinas',           'Christianity', 1225, 1274),
    ('Martin Luther',            'Christianity', 1483, 1546),
    ('John Wesley',              'Christianity', 1703, 1791),
    ('Hannah Arendt',            'Christianity', 1906, 1975),
    ('Rosemary Radford Ruether', 'Christianity', 1936, 2022),

    # Judaism
    ('Moses Maimonides',         'Judaism',      1138, 1204),
    ('Baruch Spinoza',           'Judaism',      1632, 1677),
    ('Martin Buber',             'Judaism',      1878, 1965),
    ('Hannah Arendt',            'Judaism',      1906, 1975),  # Jewish identity

    # Islam
    ('Al-Ghazali',               'Islam',        1058, 1111),
    ('Ibn Taymiyya',             'Islam',        1263, 1328),
    ('Ali Shariati',             'Islam',        1933, 1977),
    ('Fatema Mernissi',          'Islam',        1940, 2015),

    # Buddhism
    ('Dogen',                    'Buddhism',     1200, 1253),
    ('Tsongkhapa',               'Buddhism',     1357, 1419),
    ('Hakuin Ekaku',             'Buddhism',     1686, 1769),
    ('Ledi Sayadaw',             'Buddhism',     1846, 1923),
    ('Yin Shun',                 'Buddhism',     1906, 2005),
    ('14th Dalai Lama',          'Buddhism',     1935, 2025),

    # Hinduism
    ('Adi Shankara',             'Hinduism',      700,  750),
    ('Ramanuja',                 'Hinduism',     1017, 1137),
    ('Swami Vivekananda',        'Hinduism',     1863, 1902),
    ('Sri Aurobindo',            'Hinduism',     1872, 1950),
    ('Nisargadatta Maharaj',     'Hinduism',     1897, 1981),
]

# Remove duplicate Arendt — she's Christianity in this study
scholars = [s for s in scholars if not (s[0] == 'Hannah Arendt' and s[1] == 'Judaism')]

COLORS = {
    'Christianity': '#C0392B',
    'Judaism':      '#2471A3',
    'Islam':        '#1E8449',
    'Buddhism':     '#6E2F1A',
    'Hinduism':     '#D4860A',
}

order = ['Christianity', 'Judaism', 'Islam', 'Buddhism', 'Hinduism']

# Build rows with section headers
rows = []
for rel in order:
    group = [s for s in scholars if s[1] == rel]
    rows.append(('header', rel))
    for s in group:
        rows.append(('scholar', s))

n = len(rows)
fig, ax = plt.subplots(figsize=(15, n * 0.38 + 1.2))

X_MIN, X_MAX = 650, 2060
ax.set_xlim(X_MIN, X_MAX)
ax.set_ylim(-0.5, n - 0.5)
ax.invert_yaxis()

# Style
ax.set_facecolor('#FAFAFA')
fig.patch.set_facecolor('white')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#cccccc')
ax.tick_params(left=False, bottom=True)
ax.set_yticks([])

# Vertical grid
xticks = list(range(700, 2100, 100))
ax.set_xticks(xticks)
ax.set_xticklabels([str(x) for x in xticks], fontsize=7.5, color='#555555')
ax.xaxis.grid(True, color='#e0e0e0', linewidth=0.6, zorder=0)
ax.set_axisbelow(True)
ax.set_xlabel('Year', fontsize=10, color='#333333', labelpad=6)
ax.set_title('Timeline of Scholars Across World Traditions',
             fontsize=13, fontweight='bold', pad=14, color='#111111')

NAME_X = X_MIN - 15  # right-align names here

for i, row in enumerate(rows):
    if row[0] == 'header':
        rel = row[1]
        # Light band for religion section
        ax.axhspan(i - 0.48, i + 0.48, color=COLORS[rel], alpha=0.06, zorder=0)
        ax.text(NAME_X, i, rel, ha='right', va='center',
                fontsize=9, fontweight='bold', color=COLORS[rel],
                style='italic')
    else:
        _, (name, rel, birth, death) = row
        color = COLORS[rel]
        duration = death - birth

        # Alternating row bg
        if i % 2 == 0:
            ax.axhspan(i - 0.48, i + 0.48, color='#f0f0f0', alpha=0.4, zorder=0)

        # Bar
        ax.barh(i, duration, left=birth, height=0.52,
                color=color, alpha=0.82, zorder=3,
                linewidth=0, capstyle='round')

        # Age label
        age_label = f'{duration}' if death < 2025 else f'{duration}+'
        bar_frac = duration / (X_MAX - X_MIN)
        if bar_frac > 0.04:
            ax.text(birth + duration / 2, i, age_label,
                    ha='center', va='center', fontsize=7,
                    color='white', fontweight='bold', zorder=5)
        else:
            ax.text(death + 5, i, age_label,
                    ha='left', va='center', fontsize=7,
                    color=color, fontweight='bold', zorder=5)

        # Name left of chart
        ax.text(NAME_X, i, name, ha='right', va='center',
                fontsize=8, color='#222222')

        # Birth year small tick
        ax.plot(birth, i, '|', color=color, ms=6, mew=1.2, zorder=4)

# Horizontal dividers between religion groups
prev = None
for i, row in enumerate(rows):
    rel = row[1] if row[0] == 'header' else row[1][1]
    if prev and rel != prev:
        ax.axhline(i - 0.5, color='#bbbbbb', linewidth=0.8)
    prev = rel

# Legend — top right, outside bars
legend_patches = [
    mpatches.Patch(color=COLORS[r], alpha=0.85, label=r) for r in order
]
ax.legend(handles=legend_patches, loc='upper right',
          fontsize=8, framealpha=0.95, edgecolor='#cccccc',
          title='Religion', title_fontsize=8.5,
          bbox_to_anchor=(1.0, 1.0))

plt.tight_layout(rect=[0.17, 0, 1, 1])
plt.savefig('/mnt/user-data/outputs/timeline_scholars.pdf',
            dpi=200, bbox_inches='tight', facecolor='white')
plt.savefig('/mnt/user-data/outputs/timeline_scholars.png',
            dpi=150, bbox_inches='tight', facecolor='white')
print("Done!")