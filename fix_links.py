import os

base_dir = r"c:\Anish\App\copyyyyyyyy"
files = ["index.html", "quiz.html", "video-analysis.html", "game.html"]

for file in files:
    path = os.path.join(base_dir, file)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Fix the navbar links
    content = content.replace('href="/"', 'href="index.html"')
    content = content.replace('href="/#about"', 'href="index.html#about"')
    content = content.replace('href="/quiz"', 'href="quiz.html"')
    content = content.replace('href="/video-analysis"', 'href="video-analysis.html"')
    content = content.replace('href="/game"', 'href="game.html"')
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("Links fixed.")
