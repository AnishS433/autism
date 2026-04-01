import os
import re

base_dir = r"c:\Anish\App\copyyyyyyyy"
index_path = os.path.join(base_dir, "index.html")

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Replace nav links in the HTML
html = html.replace('href="#home"', 'href="/"')
html = html.replace('href="#about"', 'href="/#about"')
html = html.replace('href="#quiz"', 'href="/quiz"')
html = html.replace('href="#video-analysis"', 'href="/video-analysis"')
html = html.replace('href="#game"', 'href="/game"')

# The hero section a tag
html = html.replace('href="#quiz" class="btn btn-primary"', 'href="/quiz" class="btn btn-primary"')

# Extract sections
# We'll use regex to extract the sections
def extract_section(section_id):
    pattern = re.compile(rf'(<section id="{section_id}".*?</section>)', re.DOTALL | re.IGNORECASE)
    match = pattern.search(html)
    if match:
        return match.group(1)
    return ""

quiz_section = extract_section('quiz')
video_section = extract_section('video-analysis')
game_section = extract_section('game')
results_section = extract_section('results')

# We need to remove these from index.html
new_index_html = html.replace(quiz_section, "")
new_index_html = new_index_html.replace(video_section, "")
new_index_html = new_index_html.replace(game_section, "")
new_index_html = new_index_html.replace(results_section, "")

# Remove any empty lines left by replacements
new_index_html = re.sub(r'\n\s*\n', '\n\n', new_index_html)

with open(index_path, "w", encoding="utf-8") as f:
    f.write(new_index_html)

# Create template engine for other pages
header_pattern = re.compile(r'(.*?)(<section id="home" class="hero">)', re.DOTALL | re.IGNORECASE)
footer_pattern = re.compile(r'(<footer class="footer">.*)', re.DOTALL | re.IGNORECASE)

header_match = header_pattern.search(new_index_html)
footer_match = footer_pattern.search(new_index_html)

header = header_match.group(1) if header_match else ""
footer = footer_match.group(1) if footer_match else ""

# Write Quiz Page
quiz_page = header + quiz_section + "\n\n" + results_section + "\n\n" + footer
with open(os.path.join(base_dir, "quiz.html"), "w", encoding="utf-8") as f:
    f.write(quiz_page)

# Write Video Page
video_page = header + video_section + "\n\n" + footer
with open(os.path.join(base_dir, "video-analysis.html"), "w", encoding="utf-8") as f:
    f.write(video_page)

# Write Game Page
game_page = header + game_section + "\n\n" + footer
with open(os.path.join(base_dir, "game.html"), "w", encoding="utf-8") as f:
    f.write(game_page)

print("Split successful!")
