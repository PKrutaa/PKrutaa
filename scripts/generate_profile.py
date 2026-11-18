import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


PALETTES = {
    'dark': {'text': '#f0f6fc', 'muted': '#9198a1'},
    'light': {'text': '#1f2328', 'muted': '#656d76'},
}


def activity(counts):
    active = best = streak = 0
    for count in counts:
        active += count > 0
        streak = streak + 1 if count else 0
        best = max(best, streak)
    return active, best


def svg_start(width, height, label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{label}</title>'


def stats_svg(metrics, theme):
    palette = PALETTES[theme]
    parts = [svg_start(960, 234, 'GitHub statistics for kruta')]
    for index, (value, label, scope) in enumerate(metrics):
        x, y = (index % 3) * 320, 34 + (index // 3) * 118
        parts.append(f'<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"><text x="{x}" y="{y}" font-size="32" font-weight="500" fill="{palette["text"]}">{value}</text><text x="{x}" y="{y+31}" font-size="15" fill="{palette["muted"]}">{label}</text><text x="{x}" y="{y+53}" font-size="11" fill="{palette["muted"]}">{scope}</text></g>')
    return ''.join(parts) + '</svg>'


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
