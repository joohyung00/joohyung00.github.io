# legacy/ — previous versions of joohyung00.github.io

Every redesign keeps the outgoing site **alive here as a static snapshot**, so it can be
revisited any time and compared with the current one when deciding the next change.

| version | dates live | what it was | open |
|---|---|---|---|
| v1-beautiful-jekyll | 2025 – 2026-10 | Beautiful Jekyll fork: yellow theme, 6 tabs (About/Publications/Experiences/Teaching/CV/Posts), photo carousel home | [/legacy/v1-beautiful-jekyll/](v1-beautiful-jekyll/) |

## How a snapshot is made (do this *before* switching the live site)

```bash
# 1. mirror the live site as rendered (works for Jekyll sites, no Ruby needed)
mkdir -p /tmp/snap && cd /tmp/snap
wget --mirror --convert-links --adjust-extension --page-requisites --no-parent \
     --no-host-directories --directory-prefix=site -e robots=off \
     --reject-regex 'mypages/.*\.html$' https://joohyung00.github.io/
# 2. drop the query-string copies of the my-page listing assets and point the Posts page at the live ones
rm -f site/mypages/listing.*
sed -i 's#mypages/listing\.css[^"]*#/mypages/listing.css#; s#mypages/listing\.js[^"]*#/mypages/listing.js#' site/pages/posts_home.html
# 3. move it in and add a row to index.html + this table
mv site legacy/v<N>-<name>
```

Links inside a snapshot are relative (`--convert-links`), so it works under any sub-path.
The Posts tab of a snapshot reads `/mypages/index.json` (absolute), i.e. the live post list.

## Source

The Jekyll sources of v1 are kept in git: tag `legacy-bj`, branch `archive/beautiful-jekyll`.
To bring v1 back as the live site without touching files: GitHub → Settings → Pages →
source branch `archive/beautiful-jekyll`. To restore permanently: `git reset --hard legacy-bj`.
