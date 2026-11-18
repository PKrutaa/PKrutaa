import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


PALETTES = {
    'dark': {'text': '#f0f6fc', 'muted': '#9198a1', 'empty': '#161b22', 'snake': '#b9f6ca', 'eye': '#0d1117', 'dots': ['#183d2b', '#276343', '#3f9161', '#7bd99c']},
    'light': {'text': '#1f2328', 'muted': '#656d76', 'empty': '#ebedf0', 'snake': '#238636', 'eye': '#ffffff', 'dots': ['#d3efda', '#9dd8ae', '#58ac71', '#287c42']},
}


def activity(counts):
    active = best = streak = 0
    for count in counts:
        active += count > 0
        streak = streak + 1 if count else 0
        best = max(best, streak)
    return active, best


def simulate(width, food):
    cycle = [(0, 0)]
    for y in range(8):
        columns = range(1, width) if y % 2 == 0 else range(width - 1, 0, -1)
        cycle.extend((x, y) for x in columns)
    cycle.extend((0, y) for y in range(7, 0, -1))
    start = cycle.index((min(3, width - 1), 7))
    cycle = cycle[start:] + cycle[:start]
    initial = min(4, width)
    body = list(reversed(cycle[:initial]))
    frames = [body[:]]
    remaining = set(food)
    for head in cycle[initial:]:
        body = [head] + (body if head in remaining else body[:-1])
        remaining.discard(head)
        frames.append(body[:])
    return frames


def svg_start(width, height, label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{label}</title>'


def stats_svg(metrics, theme):
    palette = PALETTES[theme]
    parts = [svg_start(960, 234, 'GitHub statistics for kruta')]
    for index, (value, label, scope) in enumerate(metrics):
        x, y = (index % 3) * 320, 34 + (index // 3) * 118
        parts.append(f'<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"><text x="{x}" y="{y}" font-size="32" font-weight="500" fill="{palette["text"]}">{value}</text><text x="{x}" y="{y+31}" font-size="15" fill="{palette["muted"]}">{label}</text><text x="{x}" y="{y+53}" font-size="11" fill="{palette["muted"]}">{scope}</text></g>')
    return ''.join(parts) + '</svg>'


def snake_svg(weeks, theme):
    palette = PALETTES[theme]
    food = {(x, y) for x, week in enumerate(weeks) for y, day in enumerate(week['contributionDays']) if day['contributionCount']}
    frames = simulate(len(weeks), food)
    moving = len(frames) - 1
    hold = 22
    frames += [frames[-1]] * hold
    duration = (len(frames) - 1) * 0.085
    total = len(frames) - 1
    eaten = {body[0]: i for i, body in enumerate(frames[:moving + 1]) if i and body[0] in food}
    parts = [svg_start(len(weeks) * 18 + 8, 192, 'Snake grows as it eats contribution cells, without hitting walls or itself')]
    parts.append(f'<style>@media(prefers-reduced-motion:reduce){{.motion{{display:none}}}}.blink{{animation:blink .65s steps(2,end) infinite}}@keyframes blink{{50%{{opacity:0}}}}</style>')

    def animate(attribute, values, discrete=False):
        mode = 'discrete' if discrete else 'linear'
        return f'<animate attributeName="{attribute}" values="{";".join(str(v) for v in values)}" dur="{duration:.3f}s" repeatCount="indefinite" calcMode="{mode}"/>'

    for x, week in enumerate(weeks):
        for y, day in enumerate(week['contributionDays']):
            count = day['contributionCount']
            level = 0 if count < 4 else 1 if count < 9 else 2 if count < 16 else 3
            color = palette['dots'][level] if count else palette['empty']
            parts.append(f'<rect x="{x*18+4}" y="{y*18+14}" width="13" height="13" rx="3" fill="{color}">')
            if (x, y) in eaten:
                t = eaten[x, y] / total
                parts.append(f'<animate attributeName="fill" values="{color};{palette["empty"]};{palette["empty"]}" keyTimes="0;{t:.6f};1" calcMode="discrete" dur="{duration:.3f}s" repeatCount="indefinite"/>')
            parts.append('</rect>')
    previous = 0
    for cell, tick in sorted(eaten.items(), key=lambda item: item[1]):
        x, y = cell
        begin, end = previous / total, tick / total
        parts.append(f'<circle class="motion" cx="{x*18+10.5}" cy="{y*18+20.5}" r="5" fill="{palette["snake"]}" opacity="0"><animate attributeName="opacity" values="0;1;0;0" keyTimes="0;{begin:.6f};{end:.6f};1" calcMode="discrete" dur="{duration:.3f}s" repeatCount="indefinite"/><animate attributeName="r" values="3.5;6;3.5" dur=".6s" repeatCount="indefinite"/></circle>')
        previous = tick
    parts.append('<g class="motion">')
    for segment in reversed(range(len(frames[-1]))):
        points = [body[segment] if segment < len(body) else body[-1] for body in frames]
        opacity = [1 if segment < len(body) else 0 for body in frames]
        parts.append(f'<rect width="15" height="15" rx="5" fill="{palette["snake"]}" opacity="{opacity[0]}">')
        parts.append(animate('x', [x*18+3 for x, y in points]))
        parts.append(animate('y', [y*18+13 for x, y in points]))
        if not opacity[0]:
            birth = opacity.index(1) / total
            parts.append(f'<animate attributeName="opacity" values="0;1;1" keyTimes="0;{birth:.6f};1" calcMode="discrete" dur="{duration:.3f}s" repeatCount="indefinite"/>')
        parts.append('</rect>')
    directions = []
    for i, body in enumerate(frames):
        before = frames[max(0, i-1)][0] if i else body[1]
        dx, dy = body[0][0]-before[0], body[0][1]-before[1]
        directions.append((dx, dy) if dx or dy else directions[-1])
    for side in (-1, 1):
        parts.append(f'<circle r="1.65" fill="{palette["eye"]}">')
        parts.append(animate('cx', [body[0][0]*18+10.5+dx*3-dy*side*3 for body, (dx, dy) in zip(frames, directions)]))
        parts.append(animate('cy', [body[0][1]*18+20.5+dy*3+dx*side*3 for body, (dx, dy) in zip(frames, directions)]))
        parts.append('</circle>')
    parts.append('<line class="blink" stroke="#f28b9b" stroke-width="1.5" stroke-linecap="round">')
    for attr, axis, distance in [('x1', 0, 7), ('y1', 1, 7), ('x2', 0, 12), ('y2', 1, 12)]:
        offset = 10.5 if axis == 0 else 20.5
        parts.append(animate(attr, [body[0][axis]*18+offset+direction[axis]*distance for body, direction in zip(frames, directions)]))
    parts.append('</line></g>')
    parts.append(f'<text x="4" y="182" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="10" fill="{palette["muted"]}">Past 12 months · GitHub contribution calendar</text></svg>')
    return ''.join(parts)


def github(path, query=None):
    data = json.dumps({'query': query}).encode() if query else None
    request = Request('https://api.github.com/' + path, data=data, headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'], 'Accept': 'application/vnd.github+json', 'User-Agent': 'PKrutaa-profile'})
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if isinstance(result, dict) and result.get('errors'):
        raise RuntimeError('GitHub rejected the contribution query')
    return result


def generate(calendar, user, repos, output):
    output.mkdir(parents=True, exist_ok=True)
    counts = [day['contributionCount'] for week in calendar['weeks'] for day in week['contributionDays']]
    active, longest = activity(counts)
    if sum(counts) != calendar['totalContributions']:
        raise ValueError('Contribution calendar total does not match daily counts')
    metrics = [(f'{sum(counts):,}', 'Contributions', 'Past 12 months'), (str(active), 'Active days', 'Past 12 months'), (f'{longest} days', 'Longest streak', 'Past 12 months'), (str(user['public_repos']), 'Public repositories', 'Current total'), (str(user['followers']), 'Followers', 'Current total'), (str(sum(repo['stargazers_count'] for repo in repos if not repo['fork'])), 'Public stars', 'Owned, non-fork repos')]
    for theme in PALETTES:
        suffix = '-dark' if theme == 'dark' else ''
        (output / f'stats{suffix}.svg').write_text(stats_svg(metrics, theme))
        (output / f'github-contribution-grid-snake{suffix}.svg').write_text(snake_svg(calendar['weeks'], theme))


def main():
    query = '{user(login:"PKrutaa"){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'
    calendar = github('graphql', query)['data']['user']['contributionsCollection']['contributionCalendar']
    user = github('users/PKrutaa')
    repos = []
    page = 1
    while True:
        batch = github(f'users/PKrutaa/repos?per_page=100&page={page}')
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    generate(calendar, user, repos, Path('dist'))


if __name__ == '__main__':
    main()
