---
layout: page
title: My Posts
---

<div class="posts-list">
  {% for post in site.posts %}
  <article class="post-preview">
    <a href="{{ post.url | relative_url }}">
      
      <!-- Post Thumbnail -->
      {% capture thumbnail %}
        {% if post.thumbnail %}
          {{ post.thumbnail }}
        {% elsif post.cover-img %}
          {% if post.cover-img.first %}
            {{ post.cover-img[0].first.first }}
          {% else %}
            {{ post.cover-img }}
          {% endif %}
        {% else %}
          /assets/img/default-thumbnail.jpg  <!-- placeholder if no thumbnail -->
        {% endif %}
      {% endcapture %}

      {% assign thumbnail=thumbnail | strip %}
      {% if thumbnail != "" %}
      <div class="post-thumbnail">
        <img src="{{ thumbnail | relative_url }}" alt="Thumbnail for {{ post.title }}">
      </div>
      {% endif %}

      <!-- Post Title and Excerpt -->
      <h2 class="post-title">{{ post.title }}</h2>
      {% if post.subtitle %}
        <h3 class="post-subtitle">{{ post.subtitle }}</h3>
      {% endif %}

    </a>

    <p class="post-meta">
      Posted on {{ post.date | date: "%B %d, %Y" }}
      {% if post.author %}
        by {{ post.author }}
      {% endif %}
    </p>

    <div class="post-entry-container">
      <div class="post-entry">
        {{ post.excerpt | strip_html | xml_escape | truncatewords: 50 }}
        {% assign excerpt_word_count = post.excerpt | number_of_words %}
        {% if post.content != post.excerpt or excerpt_word_count > 50 %}
          <a href="{{ post.url | relative_url }}" class="post-read-more">[Read&nbsp;More]</a>
        {% endif %}
      </div>
    </div>

    {% if post.tags.size > 0 %}
    <div class="blog-tags">
      Tags:
      {% for tag in post.tags %}
      <a href="{{ '/tags' | relative_url }}#{{- tag -}}">{{- tag -}}</a>
      {% endfor %}
    </div>
    {% endif %}

  </article>
  {% endfor %}
</div>
