import re
from pathlib import Path


def decorate(source, eye_color):
    def segment(match):
        index = match.group(1)
        body = '<rect x="0.5" y="0.5" width="15" height="15" rx="5"/>'
        face = ''
        if index == '0':
            face = f'<circle cx="11" cy="4.5" r="1.5" fill="{eye_color}"/><circle cx="11" cy="11.5" r="1.5" fill="{eye_color}"/><path class="snake-tongue" d="M15 8h4m0 0 2-2m-2 2 2 2" fill="none" stroke="#f28b9b" stroke-width="1.2" stroke-linecap="round"/>'
        return f'<g class="s s{index}">{body}{face}</g>'

    result, count = re.subn(r'<rect class="s s(\d+)"[^>]*/>', segment, source)
    if not count or 'class="s s0"' not in result:
        raise ValueError('Expected the original snake segments in the generated SVG')
    css = '.snake-tongue{animation:tongue .65s steps(2,end) infinite}@keyframes tongue{50%{opacity:0}}@media(prefers-reduced-motion:reduce){.s{display:none}.c,.u{animation:none!important}}'
    return result.replace('</style>', css + '</style>', 1)


if __name__ == '__main__':
    for file in Path('dist').glob('github-contribution-grid-snake*.svg'):
        eye_color = '#0d1117' if '-dark' in file.stem else '#ffffff'
        file.write_text(decorate(file.read_text(), eye_color))
