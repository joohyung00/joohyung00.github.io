# Joohyung Yun - Personal Website

Personal academic website for Joohyung Yun, built with Jekyll and Beautiful Jekyll theme.

## Website Structure

```
joohyung00.github.io/
├── _layouts/
│   ├── base.html              # Homepage (About Me, Publications list, Research Focus)
│   ├── custom_cv.html         # CV page (Education, Publications, Experience, Awards, Patents, Skills)
│   ├── custom_publications.html # Detailed publications with expandable cards
│   └── custom_experiences.html  # Experience page with expandable cards
├── assets/
│   ├── cv/
│   │   └── cv.pdf             # PDF version of CV (linked from CV page)
│   ├── img/
│   │   ├── publications/      # Publication thumbnails and figures
│   │   └── experiences/       # Experience thumbnails (company logos)
│   └── slides/                # Presentation slides (pptx, pdf)
└── index.html, cv.html, publications.html, experiences.html  # Page entry points
```

---

## 1. Updating Summary / About Me

**File:** `_layouts/base.html`

The About Me section is in the `<section id="about">` block. Update the following:

```html
<section id="about" class="home-section">
  <h2 class="section-title">About Me</h2>
  <p>
    I am a <strong>4th year integrated M.S./Ph.D. student (2nd year Ph.D.)</strong> ...
  </p>
  <!-- Research Focus subsection -->
  <h3>Research Focus</h3>
  <ul>
    <li><strong>Agentic RAG</strong>: ...</li>
    <li><strong>Enterprise RAG</strong>: ...</li>
  </ul>
</section>
```

**Key points:**
- Update year/status as needed (e.g., "4th year" → "5th year")
- Add/modify research focus areas in the `<ul>` list
- Keep formatting consistent with existing style

---

## 2. Adding a New Publication

Publications appear in **three locations**. Update all three for consistency:

### 2.1 Homepage Publications List (`_layouts/base.html`)

Find the `<section id="publications">` and add a new entry:

```html
<li>
  <span class="pub-emoji" aria-hidden="true">🔄</span>
  <strong>Paper Title</strong><br>
  <span class="pub-authors"><strong>Yun, J.</strong>, Coauthor, A., Coauthor, B.</span><br>
  <span class="pub-venue"><em>Venue Name</em>, Year.</span>
</li>
```

### 2.2 CV Publications (`_layouts/custom_cv.html`)

Find the `<section id="publications">` and add inside `<div class="cv-body">`:

```html
<div class="pub-entry">
    <p class="pub-title"><span class="pub-emoji" aria-hidden="true">🔄</span>Paper Title</p>
    <div class="pub-meta"><strong>Yun, J.</strong>, Coauthor, A. — Venue Year, Location.</div>
</div>
```

### 2.3 Publications Page with Details (`_layouts/custom_publications.html`)

Add a new `<details class="pub-card">` block:

```html
<details class="pub-card">
  <summary>
    <div class="pub-thumb">
      <img src="{{ '/assets/img/publications/paper_thumb.jpg' | relative_url }}" alt="Paper preview">
    </div>
    <div class="pub-meta">
      <span class="badge badge-primary pub-badge">Conference</span>  <!-- or badge-secondary for Under Review, badge-info for Workshop -->
      <h3 class="pub-title"><span class="pub-emoji" aria-hidden="true">🔄</span>Paper Title</h3>
      <small><strong>Yun, J.</strong>, Coauthor, A., Coauthor, B.</small>
      <small><em>Venue</em>, Year.</small>
    </div>
    <div class="pub-toggle" aria-hidden="true">▾</div>
  </summary>
  <div class="pub-extra">
    <img class="pub-hero" src="{{ '/assets/img/publications/paper_figure.png' | relative_url }}" alt="Paper figure">
    <div class="pub-links">
        <a class="pub-link" href="https://link-to-paper.pdf" target="_blank" rel="noopener" title="Paper (PDF)">
          <i class="fa-solid fa-file-pdf" aria-hidden="true"></i><span>Paper</span>
        </a>
        <a class="pub-link" href="{{ '/assets/slides/paper.pptx' | relative_url }}" target="_blank" rel="noopener" title="Slides">
          <i class="fa-solid fa-file-powerpoint" aria-hidden="true"></i><span>Slides</span>
        </a>
        <a class="pub-link" href="https://github.com/repo" target="_blank" rel="noopener" title="GitHub Repo">
          <i class="fa-brands fa-github" aria-hidden="true"></i><span>Code</span>
        </a>
    </div>
    <p><strong>Problem:</strong> Description of the problem...</p>
    <p><strong>Existing Research Issues:</strong> What's wrong with current approaches...</p>
    <p><strong>Our Research:</strong> What we propose and achieve...</p>
  </div>
</details>
```

### Required Assets for Publications

1. **Thumbnail image** (`assets/img/publications/paper_thumb.jpg`): 4:3 aspect ratio, ~160px wide
2. **Hero/Overview image** (`assets/img/publications/paper_figure.png`): Main figure, max 820px wide
3. **Slides** (optional, `assets/slides/paper.pptx` or `.pdf`)

### Badge Types
- `badge-primary`: Published conference/journal paper
- `badge-secondary`: Under review
- `badge-info`: Workshop paper

---

## 3. Updating CV Content

**File:** `_layouts/custom_cv.html`

### Sections available:
- `#education` - Education history
- `#publications` - Publications list
- `#work` - Work experience
- `#awards` - Honors & Awards
- `#patents` - Patents
- `#teaching` - Teaching experience
- `#skills` - Languages and coding skills

### Adding a new CV item (e.g., Award):

```html
<div class="cv-item">
  <div class="cv-when">2026</div>
  <div>
    <h3 class="cv-role">Award Title</h3>
    <p class="cv-sub">Description or granting organization</p>
  </div>
</div>
```

### Adding a new Patent:

```html
<div class="cv-item">
  <div class="cv-when">Month Year</div>
  <div>
    <h3 class="cv-role">Patent Title</h3>
    <p class="cv-sub">Patent Type — No. XXXX-XXXXXXX</p>
    <ul class="cv-list">
      <li>Inventor1, and <strong>Yun, J.</strong></li>
    </ul>
  </div>
</div>
```

### PDF CV
The PDF version is stored at `assets/cv/cv.pdf`. The download button in the CV page links to this file.

---

## 4. Adding/Updating Experiences

**File:** `_layouts/custom_experiences.html`

Each experience is a `<details class="exp-card">` block. Order from top (most recent) to bottom (oldest).

```html
<details class="exp-card" open>
  <summary>
    <div class="exp-thumb">
      <img src="{{ '/assets/img/experiences/company_logo.png' | relative_url }}" alt="Company">
    </div>
    <div class="exp-meta">
      <span class="badge badge-primary exp-badge">Research</span>
      <h3 class="exp-title">Position Title</h3>
      <small>Organization Name</small>
      <small><em>Location</em> · Month–Month Year</small>
    </div>
    <div class="exp-toggle" aria-hidden="true">▾</div>
  </summary>
  <div class="exp-extra">
    <ul>
      <li>Description of work...</li>
      <li>Another point...</li>
    </ul>
    <div class="exp-links">
      <a class="exp-link" href="https://official-url.com" target="_blank" rel="noopener">
        <i class="fa-solid fa-arrow-up-right-from-square"></i><span>Official Site</span>
      </a>
    </div>
  </div>
</details>
```

**Experience thumbnails** go in `assets/img/experiences/`.

---

## 5. Syncing with LaTeX CV (cv2 repository)

The LaTeX CV is in a separate repository (`cv2`). Keep content synchronized:

| Website File | LaTeX File |
|--------------|------------|
| `_layouts/custom_cv.html` | `cv2/cv/` (publications.tex, experience.tex, honors.tex, patents.tex) |
| `_layouts/custom_experiences.html` | `cv2/cv/experience.tex` |

When updating experience in LaTeX, you can add URLs:
```latex
\cventry
  {Position}
  {Organization}
  {Location}
  {Date}
  {
    \begin{cvitems}
      \item {Description}
      \item {\url{https://official-url.com}}
    \end{cvitems}
  }
```

---

## 6. Common Tasks Reference

### Changing academic year
Search and replace across files:
- "3rd year" → "4th year"
- "1st year Ph.D." → "2nd year Ph.D."

Files to check: `base.html`, `custom_cv.html`

### Updating arXiv/submission year
If a paper's submission year changes, update in:
- `base.html` (homepage publications)
- `custom_cv.html` (CV publications)
- `custom_publications.html` (publications page)

### Git push with large files
If git push fails with HTTP 400 error for large files:
```bash
git config http.postBuffer 524288000
git push
```

---

## 7. Local Development

### Prerequisites (one-time setup)

rbenv와 Ruby 3.2.2가 설치되어 있어야 합니다:

```bash
# Install rbenv (if not installed)
brew install rbenv ruby-build

# Install Ruby 3.2.2
rbenv install 3.2.2
rbenv global 3.2.2

# Install dependencies (in the project directory)
cd /Users/joohyung/MyFiles/GithubRepositories/joohyung00.github.io
eval "$(rbenv init -)"
bundle install
```

### Running the local server

```bash
cd /Users/joohyung/MyFiles/GithubRepositories/joohyung00.github.io
eval "$(rbenv init -)"
bundle exec jekyll serve
```

Then open **http://127.0.0.1:4000** in your browser.

Press `Ctrl+C` to stop the server.

### Quick one-liner

```bash
cd /Users/joohyung/MyFiles/GithubRepositories/joohyung00.github.io && eval "$(rbenv init -)" && bundle exec jekyll serve
```

---

## Changelog (Recent Updates)

- **2026-04**: Added FiF publication (Failure is Feedback) to all pages
- **2026-04**: Updated summary to 4th year Ph.D., added Agentic RAG and Enterprise RAG research focus
- **2026-04**: Added NYU visiting researcher experience
- **2026-04**: Added KJMD 2025 and VLDB 2024 experiences
- **2026-04**: Moved cv.pdf to `/assets/cv/cv.pdf` subdirectory
- **2026-04**: Added 3 patents to CV (LILaC, HELIOS, DIP)
- **2026-04**: Added new honors (2025-2026): Overseas Dispatch Program, Research Excellence Award, Outstanding Paper Award, BK Fellowship
