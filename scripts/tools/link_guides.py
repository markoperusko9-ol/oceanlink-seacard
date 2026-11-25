"""Adds a 'Free calculator' card to the guides that a tool works out, and a Tools link on the guides index.
Safe to run again: pages that already carry the link are left alone.  python3 scripts/tools/link_guides.py"""
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
LINKS = {
    'navigation/azimuth-and-amplitude-observations': ('sun-compass-error-calculator', 'Compass error by the Sun calculator', 'Get the true azimuth, amplitude and your compass error without an almanac.'),
    'navigation/compass-error-deviation-and-variation': ('sun-compass-error-calculator', 'Compass error by the Sun calculator', 'Find gyro error, compass error and deviation from a bearing of the Sun.'),
    'navigation/gyro-error-and-how-to-find-it': ('sun-compass-error-calculator', 'Compass error by the Sun calculator', 'Find your gyro error from a bearing of the Sun, without an almanac.'),
    'navigation/great-circle-vs-rhumb-line-sailing': ('great-circle-rhumb-line-calculator', 'Great circle and rhumb line calculator', 'Distances, courses, vertex and the saving for your own two positions.'),
    'navigation/tidal-streams-and-set-and-drift': ('set-and-drift-course-to-steer-calculator', 'Set and drift and course to steer calculator', 'Solve the current triangle with your own figures.'),
    'navigation/dead-reckoning-and-estimated-position': ('set-and-drift-course-to-steer-calculator', 'Set and drift and course to steer calculator', 'Course to steer, set and drift, and course made good.'),
    'meteorology/beaufort-scale-and-sea-state': ('true-wind-calculator', 'True wind calculator', 'Turn the anemometer reading into true wind and Beaufort force.'),
    'navigation/cpa-and-tcpa-explained': ('cpa-tcpa-calculator', 'CPA and TCPA calculator', 'Enter two timed plots and see the CPA, TCPA and the plot drawn.'),
    'navigation/radar-plotting-and-relative-motion': ('cpa-tcpa-calculator', 'CPA and TCPA calculator', 'Check your manual plot: CPA, TCPA, target course, speed and aspect.'),
    'operations/squat-and-shallow-water-effect': ('squat-ukc-calculator', 'Squat and UKC calculator', 'Barrass squat and the clearance left under the keel at your speed.'),
    'navigation/under-keel-clearance-ukc-calculation': ('squat-ukc-calculator', 'Squat and UKC calculator', 'Work the UKC for your own depth, tide, draught and speed.'),
    'stability-cargo/load-lines-and-freeboard-marks': ('fwa-dwa-calculator', 'FWA and DWA calculator', 'See how far you may submerge the load line at your berth.'),
    'stability-cargo/gm-and-metacentric-height-explained': ('list-and-gm-calculator', 'List and GM calculator', 'Fluid GM and the list from a weight shifted across.'),
    'stability-cargo/free-surface-effect': ('list-and-gm-calculator', 'List and GM calculator', 'See what your free surface moments do to GM.'),
    'stability-cargo/angle-of-loll-vs-list': ('list-and-gm-calculator', 'List and GM calculator', 'Work out the list from a weight shifted across.'),
    'operations/ship-stability-basics-gm-free-surface-effect': ('list-and-gm-calculator', 'List and GM calculator', 'Fluid GM and the list from a weight shifted across.'),
    'operations/passage-planning-appraisal-planning-execution-monitoring': ('eta-speed-distance-time-calculator', 'ETA, speed, distance and time calculator', 'ETA across time zones and the speed needed to arrive on time.'),
    'stability-cargo/draft-survey-basics': ('draft-survey-calculator', 'Draft survey calculator', 'Mean of means, trim and density corrections with your own figures.'),
    'stability-cargo/trim-and-trim-calculations': ('draft-survey-calculator', 'Draft survey calculator', 'Corrected draughts, true trim and the trim corrections to displacement.'),
    'stability-cargo/hogging-and-sagging': ('draft-survey-calculator', 'Draft survey calculator', 'See the hog or sag from six draughts and the mean of means.'),
    'operations/bunkering-operations': ('bunker-quantity-calculator', 'Bunker quantity calculator', 'Sounded volume to tonnes with the Table 54B correction.'),
    'engineering/bunker-sampling-and-marpol-samples': ('bunker-quantity-calculator', 'Bunker quantity calculator', 'Check the delivered quantity: volume, temperature and density to tonnes.'),
    'stability-cargo/tanker-cargo-calculations-astm-tables-vcf': ('bunker-quantity-calculator', 'Bunker and Table 54B calculator', 'Get the VCF from Table 54B and the weight in air.'),
    'stability-cargo/gas-tanker-cargo-calculations-basics': ('lng-conversion-boil-off-calculator', 'LNG converter and boil-off calculator', 'Cubic metres of LNG to tonnes, MMBtu and gas volume, and the boil-off rate.'),
    'navigation/celestial-navigation-basics-noon-sight': ('sunrise-sunset-twilight-calculator', 'Sunrise, sunset and twilight calculator', 'Twilight times for star sights and the time of meridian passage.'),
    'operations/parallel-indexing': ('rate-of-turn-calculator', 'Rate of turn calculator', 'Rate of turn for a planned radius and the wheel-over distance.'),
    'navigation/pilotage-master-pilot-information-exchange': ('rate-of-turn-calculator', 'Rate of turn calculator', 'Rate of turn, turn radius and time for a planned alteration.'),
    'navigation/chartwork-basics-position-fixing-methods': ('distance-to-horizon-calculator', 'Horizon and light range calculator', 'Dipping range of a light for your height of eye.'),
    'meteorology/swell-wind-waves-and-parametric-rolling': ('rolling-period-gm-calculator', 'Rolling period and GM calculator', 'Compare the wave encounter period with your rolling period.'),
    'operations/heavy-weather-precautions': ('rolling-period-gm-calculator', 'Rolling period and GM calculator', 'Rolling period from GM and the wave encounter period.'),
    'meteorology/fog-types-and-when-they-form': ('dew-point-calculator', 'Dew point calculator', 'Dew point and relative humidity from wet and dry bulb readings.'),
}
n = 0
for g, (slug, name, line) in LINKS.items():
    p = os.path.join(ROOT, 'guides', g, 'index.html')
    s = open(p, encoding='utf-8').read()
    if 'data-tool="' in s:
        continue
    card = ('<div class="card" data-tool="%s"><div class="label">Free calculator</div><p style="margin:6px 0 0"><a href="/tools/%s/">%s</a>. %s</p></div>' % (slug, slug, name, line))
    assert s.count('<div class="card toc">') == 1, g
    open(p, 'w', encoding='utf-8').write(s.replace('<div class="card toc">', card + '<div class="card toc">'))
    n += 1
print('guides linked:', n)

# Tools link on the guides index
p = os.path.join(ROOT, 'guides', 'index.html')
s = open(p, encoding='utf-8').read()
if 'data-tool="' not in s:
    intro = 'written and fact-checked for officers, ratings and cadets.</p>'
    assert s.count(intro) == 1
    card = ('<div class="card" data-tool="hub"><div class="label">Free calculators</div><p style="margin:6px 0 0"><a href="/tools/">Seafarer tools</a>. '
            'Compass error by the Sun, true wind, CPA and TCPA, squat and UKC, ETA, great circle and more.</p></div>')
    open(p, 'w', encoding='utf-8').write(s.replace(intro, intro + card))
    print('guides index linked')

# sitemap line in robots.txt
p = os.path.join(ROOT, 'robots.txt')
s = open(p, encoding='utf-8').read()
line = 'Sitemap: https://card.oceanlinkai.com/tools/sitemap.xml'
if line not in s:
    open(p, 'w', encoding='utf-8').write(s.rstrip('\n') + '\n\n' + line + '\n')
    print('robots.txt updated')
