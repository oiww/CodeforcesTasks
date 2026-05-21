#!/usr/bin/env python3
import json
import os
import re

TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}

CARD_COLORS = ['#5b9aff', '#b040d0', '#2db539', '#ff8c00', '#ff4444', '#03bdb6']


def slugify(text):
    result = []
    for char in text.lower():
        if char in TRANSLIT:
            result.append(TRANSLIT[char])
        elif char.isalnum():
            result.append(char)
        elif char in (' ', '_', '-'):
            result.append('-')
    slug = ''.join(result)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def get_rating_class(rating):
    if rating < 1200: return 'rating-newbie'
    if rating < 1400: return 'rating-pupil'
    if rating < 1600: return 'rating-specialist'
    if rating < 1900: return 'rating-expert'
    if rating < 2100: return 'rating-cm'
    if rating < 2400: return 'rating-master'
    return 'rating-gm'


def pluralize(n, forms):
    if n % 10 == 1 and n % 100 != 11:
        return f'{n} {forms[0]}'
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return f'{n} {forms[1]}'
    else:
        return f'{n} {forms[2]}'


TASK_FORMS = ('задача', 'задачи', 'задач')
SUBTAG_FORMS = ('подтема', 'подтемы', 'подтем')



def generate_theme_page(tag_name, subtags, theme_template):
    total_tasks = sum(len(s['tasks']) for s in subtags.values())
    stats_text = f'{pluralize(len(subtags), SUBTAG_FORMS)} · {pluralize(total_tasks, TASK_FORMS)}'

    nav_items = []
    for st_name, st_data in subtags.items():
        st_slug = slugify(st_name)
        count = len(st_data['tasks'])
        if count > 0:
            nav_items.append(
                f'                <a href="#{st_slug}" class="subtag-nav-item">'
                f'{st_name} <span class="subtag-nav-count">{count}</span></a>'
            )

    sections = []
    for st_name, st_data in subtags.items():
        st_slug = slugify(st_name)
        tasks = sorted(st_data['tasks'], key=lambda t: t.get('rating', 0))
        if len(tasks) == 0:
            continue

        rows = []
        for i, task in enumerate(tasks, 1):
            if not task.get('name') or not task.get('url'):
                continue

            rc = get_rating_class(task['rating'])
            rows.append(
                f'                        <tr data-url="{task["url"]}">\n'
                f'                            <td class="task-num">{i}</td>\n'
                f'                            <td class="task-name">'
                f'<a href="{task["url"]}" target="_blank">{task["name"]}</a></td>\n'
                f'                            <td class="task-rating">'
                f'<span class="{rc}">{task["rating"]}</span></td>\n'
                f'                        </tr>'
            )

        section = (
                f'            <div class="subtag-section" id="{st_slug}">\n'
                f'                <div class="subtag-header">\n'
                f'                    <h2 class="subtag-title">{st_name}</h2>\n'
                f'                    <span class="subtag-count">{pluralize(len(tasks), TASK_FORMS)}</span>\n'
                f'                </div>\n'
                f'                <table class="tasks-table">\n'
                f'                    <thead>\n'
                f'                        <tr>\n'
                f'                            <th class="th-num">#</th>\n'
                f'                            <th class="th-name">Задача</th>\n'
                f'                            <th class="th-rating">Рейтинг</th>\n'
                f'                        </tr>\n'
                f'                    </thead>\n'
                f'                    <tbody>\n'
                + '\n'.join(rows) + '\n'
                                    f'                    </tbody>\n'
                                    f'                </table>\n'
                                    f'            </div>'
        )
        sections.append(section)

    html = theme_template
    html = html.replace('%%TITLE%%', tag_name)
    html = html.replace('%%STATS_TEXT%%', stats_text)
    html = html.replace('%%NAV%%', '\n'.join(nav_items))
    html = html.replace('%%SECTIONS%%', '\n\n'.join(sections))

    return html



def main():
    print('🔧 CFTasks Generator\n')

    with open('tasks.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open('theme_card_template.html', 'r', encoding='utf-8') as f:
        card_template = f.read()

    with open('theme_page_template.html', 'r', encoding='utf-8') as f:
        theme_template = f.read()

    with open('index.html', 'r', encoding='utf-8') as f:
        index_html = f.read()

    os.makedirs('themes', exist_ok=True)

    tags = data['tags']

    themes_info = []
    total_tasks = 0
    total_subtags = 0

    for tag_name, tag_data in tags.items():
        subtags = tag_data['subtags']
        slug = slugify(tag_name)

        all_tasks = []
        for st_data in subtags.values():
            for task in st_data.get('tasks', []):
                if task.get('name') and task.get('url') and task.get('rating'):
                    all_tasks.append(task)

        task_count = len(all_tasks)
        subtag_count = sum(1 for st in subtags.values() if len(st.get('tasks', [])) > 0)
        total_tasks += task_count
        total_subtags += subtag_count

        if all_tasks:
            ratings = [t['rating'] for t in all_tasks]
            min_r, max_r = min(ratings), max(ratings)
            avg_r = sum(ratings) // len(ratings)
        else:
            min_r = max_r = avg_r = 0

        themes_info.append({
            'name': tag_name,
            'data': tag_data,
            'avg_rating': avg_r,
            'task_count': task_count,
            'subtag_count': subtag_count,
            'min_r': min_r,
            'max_r': max_r
        })

    themes_info.sort(key=lambda x: x['avg_rating'])

    cards_html = []

    for idx, theme in enumerate(themes_info):
        tag_name = theme['name']
        tag_data = theme['data']
        subtags = tag_data['subtags']
        slug = slugify(tag_name)
        color = CARD_COLORS[idx % len(CARD_COLORS)]

        all_tasks = []
        for st_data in subtags.values():
            for task in st_data.get('tasks', []):
                if task.get('name') and task.get('url') and task.get('rating'):
                    all_tasks.append(task)

        task_count = theme['task_count']
        subtag_count = theme['subtag_count']
        avg_r = theme['avg_rating']
        min_r = theme['min_r']
        max_r = theme['max_r']

        avg_rating_class = get_rating_class(avg_r) if avg_r > 0 else 'rating-newbie'


        active_subtags = [name for name, st in subtags.items() if len(st.get('tasks', [])) > 0]

        urls_json = json.dumps([t['url'] for t in all_tasks], ensure_ascii=False)

        card = card_template
        card = card.replace('{{theme_name}}', tag_name)
        card = card.replace('{{theme_slug}}', slug)
        card = card.replace('{{task_count_text}}', pluralize(task_count, TASK_FORMS))
        card = card.replace('{{subtag_count_text}}', pluralize(subtag_count, SUBTAG_FORMS))
        card = card.replace('{{subtag_list}}',
                            ', '.join(active_subtags[:3]) + ('...' if len(active_subtags) > 3 else ''))
        card = card.replace('{{min_rating}}', str(min_r) if all_tasks else '—')
        card = card.replace('{{max_rating}}', str(max_r) if all_tasks else '—')
        card = card.replace('{{avg_rating}}', str(avg_r) if all_tasks else '—')
        card = card.replace('{{avg_rating_class}}', avg_rating_class)
        card = card.replace('{{accent_color}}', color)
        card = card.replace('{{urls_json}}', urls_json)

        cards_html.append(card)
        print(f'  📁 {tag_name} → themes/{slug}.html  ({task_count} задач, {subtag_count} подтем)')

        # Генерация страницы темы
        theme_html = generate_theme_page(tag_name, subtags, theme_template)
        theme_path = os.path.join('themes', f'{slug}.html')
        with open(theme_path, 'w', encoding='utf-8') as f:
            f.write(theme_html)


    cards_content = '\n'.join(cards_html)
    index_html = re.sub(
        r'(<!-- THEMES_START -->).*?(<!-- THEMES_END -->)',
        lambda m: m.group(1) + '\n' + cards_content + '\n                    ' + m.group(2),
        index_html,
        flags=re.DOTALL
    )

    index_html = re.sub(
        r'<div class="stat-item">\s*<span class="stat-number" id="stat-themes">[^<]*</span>\s*<span class="stat-label">Тем</span>\s*</div>',
        '',
        index_html,
        flags=re.DOTALL
    )
    index_html = re.sub(
        r'<div class="stat-divider"></div>\s*<div class="stat-item">\s*<span class="stat-number" id="stat-subtags">[^<]*</span>\s*<span class="stat-label">Подтем</span>\s*</div>',
        '',
        index_html,
        flags=re.DOTALL
    )

    index_html = re.sub(
        r'(<span class="stat-number" id="stat-tasks">)[^<]*(</span>)',
        lambda m: m.group(1) + str(total_tasks) + m.group(2),
        index_html
    )

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)

    print(f'\n✅ Генерация завершена!')
    print(f'   Тем: {len(tags)} (отсортированы по сложности)')
    print(f'   Подтем: {total_subtags}')
    print(f'   Задач: {total_tasks}')


if __name__ == '__main__':
    main()