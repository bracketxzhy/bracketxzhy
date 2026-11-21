"""Render a 31-day graph from GitHub's public contribution calendar."""
from argparse import ArgumentParser
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from math import ceil
from pathlib import Path
import re
from urllib.request import Request, urlopen


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.dates, self.labels, self.current = {}, {}, None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'td' and 'data-date' in attrs:
            self.dates[attrs['id']] = attrs['data-date']
        if tag == 'tool-tip' and 'for' in attrs:
            self.current = attrs['for']

    def handle_data(self, data):
        if self.current:
            self.labels[self.current] = self.labels.get(self.current, '') + data

    def handle_endtag(self, tag):
        if tag == 'tool-tip':
            self.current = None


def render(raw, output):
    parser = CalendarParser()
    parser.feed(raw)
    values = {}
    for key, day in parser.dates.items():
        label = parser.labels.get(key, '').strip()
        match = re.match(r'^(\d+) contributions? on ', label)
        if match:
            values[date.fromisoformat(day)] = int(match[1])
        elif label.startswith('No contributions on '):
            values[date.fromisoformat(day)] = 0
        else:
            raise ValueError(f'Unrecognized contribution label for {day}')
    if not values:
        raise ValueError('No public calendar data received')
    end = max(values)
    days = [end - timedelta(days=i) for i in range(30, -1, -1)]
    counts = [values[day] for day in days]  # Missing dates fail, rather than become zero.
    maximum = max(4, ceil(max(counts) / 4) * 4)
    left, right, top, bottom = 64, 986, 68, 240
    points = [(left + i * (right-left)/30, bottom - n * (bottom-top)/maximum) for i, n in enumerate(counts)]
    polyline = ' '.join(f'{x:.2f},{y:.2f}' for x, y in points)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1016" height="300" viewBox="0 0 1016 300" role="img" aria-labelledby="title desc" data-start-date="{days[0]}" data-end-date="{end}">',
           '<title id="title">bracketxzhy\'s Contribution Graph</title>',
           f'<desc id="desc">Public GitHub contributions from {days[0]} through {end}; {sum(counts)} contributions in this period.</desc>',
           '<rect width="1016" height="300" rx="12" fill="#0d1117"/>',
           '<g font-family="Arial, Helvetica, sans-serif">',
           '<text x="508" y="34" text-anchor="middle" fill="#39d353" font-size="21" font-weight="600">bracketxzhy\'s Contribution Graph</text>']
    for i in range(5):
        y = bottom - i * (bottom-top)/4
        svg += [f'<path d="M{left} {y}H{right}" stroke="#24302a" stroke-width="1"/>',
                f'<text x="50" y="{y+4}" text-anchor="end" fill="#8b949e" font-size="11">{maximum*i//4}</text>']
    for i in range(0, 31, 5):
        x = points[i][0]
        svg += [f'<text x="{x:.2f}" y="261" text-anchor="middle" fill="#8b949e" font-size="11">{escape(days[i].strftime("%b %d"))}</text>']
    svg += [f'<polygon points="{left},{bottom} {polyline} {right},{bottom}" fill="#26a641" opacity="0.14"/>',
            f'<polyline points="{polyline}" fill="none" stroke="#39d353" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>']
    for (x, y), day, n in zip(points, days, counts):
        svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="#39d353"><title>{day}: {n} contributions</title></circle>')
    svg += ['<text x="508" y="286" text-anchor="middle" fill="#8b949e" font-size="12">Date</text>',
            '<text x="18" y="154" transform="rotate(-90 18 154)" text-anchor="middle" fill="#8b949e" font-size="12">Contributions</text>',
            '</g></svg>']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(svg) + '\n', encoding='utf-8')
    print(f'Rendered {len(days)} verified dates: {days[0]} to {end}')


if __name__ == '__main__':
    cli = ArgumentParser()
    cli.add_argument('--html', type=Path, help='Use a previously fetched public calendar')
    args = cli.parse_args()
    if args.html:
        html = args.html.read_text(encoding='utf-8')
    else:
        request = Request('https://github.com/users/bracketxzhy/contributions', headers={'User-Agent': 'GitHub-Profile-Graph', 'Accept-Language': 'en-US,en;q=0.8'})
        with urlopen(request, timeout=45) as response:
            html = response.read().decode('utf-8')
    render(html, Path(__file__).resolve().parents[1] / 'assets' / 'contribution-graph.svg')
