# Worked-example explainer posts

Generators for the step-through posts published at `/mypages/` (same shell as the Failure-is-Feedback post):

    python build/explainers/lilac.py  out.html     # LILaC — Worked Example
    python build/explainers/recg.py   out.html     # ReCG — Worked Example

`gen.py` holds the shared shell (`shell.html`, extracted from the FiF post), the stage stylesheet
(`stage_base.css`) and SVG helpers. Each frame is a 1920x850 stage rendered in a srcdoc iframe.
Publish the output with the my-page skill (`my_page.py preview --raw --file out.html --id <slug>` → review → `publish`).
Similarity values, MDL costs and other per-example numbers in the frames are illustrative; the statistics
in the last frame of each post come from the papers.
