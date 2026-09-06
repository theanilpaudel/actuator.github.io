#!/usr/bin/env python3
"""
Actuator - Local Preview Generator
Compiles the Jekyll source files into static HTML in the `_site` directory
so you can view the site locally in Google Chrome with zero gem installations.
"""

import os
import re
import shutil
import json
import subprocess

def load_yaml(filepath):
    # Use ruby to reliably parse YAML since ruby is preinstalled on macOS
    result = subprocess.run(
        ["ruby", "-ryaml", "-rjson", "-e", f'puts JSON.generate(YAML.load_file("{filepath}"))'],
        capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)

def simple_markdown_to_html(md):
    lines = md.split('\n')
    html_lines = []
    in_list = False
    in_ol = False
    in_blockquote = False

    for line in lines:
        stripped = line.strip()

        # Horizontal rule
        if stripped in ('---', '***', '___'):
            if in_list: html_lines.append('</ul>'); in_list = False
            if in_ol: html_lines.append('</ol>'); in_ol = False
            if in_blockquote: html_lines.append('</blockquote>'); in_blockquote = False
            html_lines.append('<hr>')
            continue

        # Headings
        m = re.match(r'^(#{1,6})\s+(.*)', stripped)
        if m:
            if in_list: html_lines.append('</ul>'); in_list = False
            if in_ol: html_lines.append('</ol>'); in_ol = False
            if in_blockquote: html_lines.append('</blockquote>'); in_blockquote = False
            level = len(m.group(1))
            heading_text = format_inlines(m.group(2))
            html_lines.append(f'<h{level}>{heading_text}</h{level}>')
            continue

        # Blockquotes
        if stripped.startswith('> '):
            if not in_blockquote:
                html_lines.append('<blockquote>')
                in_blockquote = True
            html_lines.append(f'<p>{format_inlines(stripped[2:])}</p>')
            continue
        elif in_blockquote and not stripped.startswith('> '):
            html_lines.append('</blockquote>')
            in_blockquote = False

        # Unordered list
        if stripped.startswith('* ') or stripped.startswith('- '):
            if in_ol: html_lines.append('</ol>'); in_ol = False
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{format_inlines(stripped[2:])}</li>')
            continue

        # Ordered list
        m_ol = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if m_ol:
            if in_list: html_lines.append('</ul>'); in_list = False
            if not in_ol:
                html_lines.append('<ol>')
                in_ol = True
            html_lines.append(f'<li>{format_inlines(m_ol.group(2))}</li>')
            continue

        # Blank line
        if not stripped:
            if in_list: html_lines.append('</ul>'); in_list = False
            if in_ol: html_lines.append('</ol>'); in_ol = False
            if in_blockquote: html_lines.append('</blockquote>'); in_blockquote = False
            continue

        # Paragraph
        if not in_list and not in_ol and not in_blockquote:
            html_lines.append(f'<p>{format_inlines(stripped)}</p>')

    if in_list: html_lines.append('</ul>')
    if in_ol: html_lines.append('</ol>')
    if in_blockquote: html_lines.append('</blockquote>')

    return '\n'.join(html_lines)

def format_inlines(text):
    # Bold italic
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    # Markdown links
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
    return text

def parse_frontmatter(content):
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            fm = {}
            for line in fm_text.splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    fm[k.strip()] = v.strip().strip('"\'')
            return fm, body
    return {}, content

def render_includes(html, site_config, includes_dir):
    def replace_include(match):
        inc_file = match.group(1).strip()
        inc_args = match.group(2) if match.group(2) else ""
        class_match = re.search(r'class="([^"]+)"', inc_args)
        inc_class = class_match.group(1) if class_match else ""
        inc_path = os.path.join(includes_dir, inc_file)
        if os.path.exists(inc_path):
            with open(inc_path, 'r', encoding='utf-8') as f:
                inc_content = f.read()
            inc_content = inc_content.replace('{{ include.class }}', inc_class)
            return inc_content
        return ""

    pattern = r'\{%\s*include\s+([a-zA-Z0-9_\-\.]+)(?:\s+([^%]+))?\s*%\}'
    prev = ""
    while prev != html:
        prev = html
        html = re.sub(pattern, replace_include, html)
    return html

def render_liquid_vars(html, site_config, page_data):
    # page.title, page.url, page.last_updated
    html = re.sub(r'\{\{\s*page\.title\s*\}\}', page_data.get('title', ''), html)
    html = re.sub(r'\{\{\s*page\.url\s*\}\}', page_data.get('url', ''), html)
    html = re.sub(r'\{\{\s*page\.last_updated\s*\}\}', page_data.get('last_updated', ''), html)

    # site.title, site.tagline, site.description, etc.
    for k, v in site_config.items():
        if isinstance(v, str):
            html = re.sub(r'\{\{\s*site\.' + k + r'\s*\}\}', v, html)
            html = re.sub(r'\{\{\s*site\.' + k + r'\s*\|\s*upcase\s*\}\}', v.upper(), html)

    # Filters like {{ 'now' | date: "%Y" }}
    html = re.sub(r'\{\{\s*[\'"]now[\'"]\s*\|\s*date:\s*[\'"]%Y[\'"]\s*\}\}', "2026", html)

    # Relative URLs {{ '/path' | relative_url }} or {{ site.app_icon | relative_url }}
    def rel_url(match):
        raw = match.group(1).strip().strip('\'"')
        if raw.startswith('site.'):
            prop = raw[5:]
            raw = str(site_config.get(prop, ''))
        elif raw.startswith('page.'):
            prop = raw[5:]
            raw = str(page_data.get(prop, ''))
        baseurl = site_config.get('baseurl', '')
        if not raw:
            return ''
        if raw == '/':
            return baseurl + '/' if baseurl else '/'
        return (baseurl + ('/' + raw.lstrip('/'))).replace('//', '/')
    html = re.sub(r'\{\{\s*([^\}]+?)\s*\|\s*relative_url\s*\}\}', rel_url, html)
    html = re.sub(r'\{\{\s*([^\}]+?)\s*\|\s*absolute_url\s*\}\}', rel_url, html)

    # Clean up head title conditionals
    title = page_data.get('title') or site_config.get('title')
    html = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', html, count=1, flags=re.DOTALL)
    html = re.sub(r'\{\{\s*page\.body_class\s*\|\s*default:\s*[\'"][^\'"]+[\'"]\s*\}\}', 'page-default', html)

    return html

def render_liquid_tags(html, site_config, data_features, data_faq, data_screenshots):
    # Replace feature loop
    if '{% for feature in site.data.features %}' in html:
        parts = html.split('{% for feature in site.data.features %}')
        before = parts[0]
        rest = parts[1]
        loop_body, after = rest.split('{% endfor %}', 1)

        rendered_features = []
        for feat in data_features:
            item_html = loop_body
            item_html = item_html.replace('{{ feature.title }}', feat.get('title', ''))
            item_html = item_html.replace('{{ feature.description }}', feat.get('description', ''))
            item_html = item_html.replace('{{ feature.badge }}', feat.get('badge', ''))

            # Icon conditions
            for icon_type in ['zap', 'shield', 'cloud', 'cpu', 'wifi-off']:
                if feat.get('icon') == icon_type:
                    pattern = r'\{%\s*if feature\.icon == "' + icon_type + r'"\s*%\}(.*?)\{%\s*(?:elsif|else|endif)'
                    # Simple replacement based on icon
            # Instead of complex regex for each elsif, evaluate the icon block
            icon_block_match = re.search(r'(\s*\{%\s*if feature\.icon == "zap"\s*%\}.*?\{%\s*endif\s*\}\s*)', item_html, re.DOTALL)
            if icon_block_match:
                icon_tag = feat.get('icon', 'zap')
                icon_svgs = {
                    'zap': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
                    'shield': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>',
                    'cloud': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>',
                    'cpu': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>',
                    'wifi-off': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="1" y1="1" x2="23" y2="23"></line><path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"></path><path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"></path><path d="M10.71 5.05A16 16 0 0 1 22.58 9"></path><path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>'
                }
                svg = icon_svgs.get(icon_tag, icon_svgs['zap'])
                item_html = item_html[:icon_block_match.start()] + svg + item_html[icon_block_match.end():]
            rendered_features.append(item_html)
        html = before + "".join(rendered_features) + after

    # Replace screenshots loop
    if '{% for shot in site.data.screenshots %}' in html:
        parts = html.split('{% for shot in site.data.screenshots %}')
        before = parts[0]
        rest = parts[1]
        loop_body, after = rest.split('{% endfor %}', 1)

        rendered_shots = []
        for shot in data_screenshots:
            shot_html = loop_body
            shot_html = shot_html.replace('{{ shot.accent }}', shot.get('accent', ''))
            shot_html = shot_html.replace('{{ shot.title }}', shot.get('title', ''))
            shot_html = shot_html.replace('{{ shot.caption }}', shot.get('caption', ''))

            image_val = shot.get('image', '')
            if image_val:
                shot_html = re.sub(r'\{%\s*if shot\.image.*?%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}', r'\1', shot_html, flags=re.DOTALL)
                shot_html = shot_html.replace('{{ shot.image | relative_url }}', image_val)
            else:
                shot_html = re.sub(r'\{%\s*if shot\.image.*?%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}', r'\2', shot_html, flags=re.DOTALL)

            emoji_block_match = re.search(r'(\s*\{%\s*if shot\.id == \'dashboard\'.*?\{%\s*endif\s*\}\s*)', shot_html, re.DOTALL)
            if emoji_block_match:
                emojis = {'dashboard': '📊', 'tasks': '🚀', 'sync': '🔄', 'security': '🛡️'}
                shot_html = shot_html[:emoji_block_match.start()] + emojis.get(shot.get('id', ''), '📱') + shot_html[emoji_block_match.end():]
            rendered_shots.append(shot_html)
        html = before + "".join(rendered_shots) + after

    # Replace hero_screenshot conditional
    hero_screen = site_config.get('hero_screenshot', '')
    if hero_screen:
        html = re.sub(r'\{%\s*if site\.hero_screenshot.*?%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}', r'\1', html, flags=re.DOTALL)
        html = html.replace('{{ site.hero_screenshot | relative_url }}', hero_screen)
    else:
        html = re.sub(r'\{%\s*if site\.hero_screenshot.*?%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}', r'\2', html, flags=re.DOTALL)

    # Replace app_icon conditional
    app_icon = site_config.get('app_icon', '')
    if app_icon:
        html = re.sub(r'\{%\s*if site\.app_icon\s*%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}', r'\1', html, flags=re.DOTALL)
        html = re.sub(r'\{%\s*if site\.app_icon\s*%\}(.*?)\{%\s*endif\s*%\}', r'\1', html, flags=re.DOTALL)
    else:
        html = re.sub(r'\{%\s*if site\.app_icon\s*%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}', r'\2', html, flags=re.DOTALL)
        html = re.sub(r'\{%\s*if site\.app_icon\s*%\}(.*?)\{%\s*endif\s*%\}', '', html, flags=re.DOTALL)

    # Replace FAQ loop
    if '{% for item in site.data.faq %}' in html:
        parts = html.split('{% for item in site.data.faq %}')
        before = parts[0]
        rest = parts[1]
        loop_body, after = rest.split('{% endfor %}', 1)

        rendered_faqs = []
        for idx, item in enumerate(data_faq):
            faq_html = loop_body
            faq_html = faq_html.replace('{{ item.question }}', item.get('question', ''))
            faq_html = faq_html.replace('{{ item.answer }}', item.get('answer', ''))
            if idx == 0:
                faq_html = re.sub(r'\{%\s*if forloop\.first\s*%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}', r'\1', faq_html)
                faq_html = re.sub(r'\{%\s*if forloop\.first\s*%\}(.*?)\{%\s*endif\s*%\}', r'\1', faq_html)
            else:
                faq_html = re.sub(r'\{%\s*if forloop\.first\s*%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}', r'\2', faq_html)
                faq_html = re.sub(r'\{%\s*if forloop\.first\s*%\}(.*?)\{%\s*endif\s*%\}', '', faq_html)
            rendered_faqs.append(faq_html)
        html = before + "".join(rendered_faqs) + after

    # Replace navigation loop in header
    if '{% for item in site.navigation %}' in html:
        parts = html.split('{% for item in site.navigation %}')
        before = parts[0]
        rest = parts[1]
        loop_body, after = rest.split('{% endfor %}', 1)

        rendered_nav = []
        for item in site_config.get('navigation', []):
            url = item.get('url', '')
            title = item.get('title', '')
            rendered_nav.append(f'<li><a href="{url}" class="nav-link">{title}</a></li>')
        html = before + "\n".join(rendered_nav) + after

    # Rating stars loop: {% for i in (1..5) %}
    if '{% for i in (1..5) %}' in html:
        parts = html.split('{% for i in (1..5) %}')
        before = parts[0]
        loop_body, after = parts[1].split('{% endfor %}', 1)
        stars = loop_body * 5
        html = before + stars + after

    return html

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    site_dir = os.path.join(root, '_site')
    if os.path.exists(site_dir):
        shutil.rmtree(site_dir)
    os.makedirs(site_dir, exist_ok=True)

    site_config = load_yaml(os.path.join(root, '_config.yml'))
    features = load_yaml(os.path.join(root, '_data', 'features.yml'))
    faq = load_yaml(os.path.join(root, '_data', 'faq.yml'))
    screenshots = load_yaml(os.path.join(root, '_data', 'screenshots.yml'))

    # Copy assets
    if os.path.exists(os.path.join(root, 'assets')):
        shutil.copytree(os.path.join(root, 'assets'), os.path.join(site_dir, 'assets'))

    # Load layouts and includes
    with open(os.path.join(root, '_layouts', 'default.html')) as f:
        _, default_layout = parse_frontmatter(f.read())
    with open(os.path.join(root, '_layouts', 'page.html')) as f:
        _, page_layout = parse_frontmatter(f.read())

    pages = [
        ('index.html', '', 'default'),
        ('privacy.md', 'privacy', 'page'),
        ('terms.md', 'terms', 'page'),
        ('support.md', 'support', 'page'),
    ]

    for filename, out_subdir, layout_name in pages:
        filepath = os.path.join(root, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        fm, body = parse_frontmatter(raw_content)

        if filename.endswith('.md'):
            content_html = simple_markdown_to_html(body)
        else:
            content_html = body

        if layout_name == 'page':
            intermediate = page_layout.replace('{{ content }}', content_html)
            full_html = default_layout.replace('{{ content }}', intermediate)
        else:
            full_html = default_layout.replace('{{ content }}', content_html)

        # Render includes
        full_html = render_includes(full_html, site_config, os.path.join(root, '_includes'))

        # Render loops & tags
        full_html = render_liquid_tags(full_html, site_config, features, faq, screenshots)

        # Render vars
        page_data = {
            'title': fm.get('title', site_config.get('title')),
            'url': '/' + out_subdir + '/' if out_subdir else '/',
            'last_updated': fm.get('last_updated', '')
        }
        full_html = render_liquid_vars(full_html, site_config, page_data)

        # Clean remaining template comments or unmatched tags
        full_html = re.sub(r'\{%.*?%\}', '', full_html)

        if out_subdir:
            dest_dir = os.path.join(site_dir, out_subdir)
            os.makedirs(dest_dir, exist_ok=True)
            dest_file = os.path.join(dest_dir, 'index.html')
        else:
            dest_file = os.path.join(site_dir, 'index.html')

        with open(dest_file, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"Generated: {dest_file}")

    print("\nStatic site compiled into _site/ successfully!")

if __name__ == '__main__':
    main()
