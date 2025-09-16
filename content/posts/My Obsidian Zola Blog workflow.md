+++
title = "My Obsidian -> Zola Blog workflow"
description = "A complete overview of my personal blog workflow. This post details how a Python script, GitHub Actions, and Caddy come together to sync content from Obsidian and deploy it automatically to a live Zola site."
date = "2025-09-11"
updated = "2025-09-11"
draft = false

[taxonomies]
categories = ["sysadmin"]
tags = ["obsidian", "zola", "workflow", "automation", "github-actions", "python", "caddy", "docker", "ci-cd", "self-hosting"]

[extra]
lang = "en"
toc = true
copy = true
featured = true
comment = false
reaction = false
math = false
mermaid = false
outdate_alert = false
outdate_alert_days = 120
+++

## Abstract

It's been quite a long time since I wanted to have such a straightforward and easy-to-use way of writing blog posts and synchronizing them directly into my [website](https://biscoito.eu) in a way that favors flexibility and convenience.

Just recently I decided to finally get this to work and I will show how everything works alongside with everything that's needed to make it work (it's all open-source anyway).

To be more specific and technical, I can basically have Obsidian (synced across all my devices with Obsidian Sync), to sync with my website GitHub repository through a simple commit and push, and to have my website automatically updated with a GitHub workflow that triggers on push, a simple building process for Zola and rsyncing with my VPS running a simple Caddy web-server with docker-compose.

## Why Zola Over the Competition

Let's start with the first decision: why did I choose Zola over Hugo, Jekyll, or even 11ty?

Zola is a simple static site generator that leverages Rust's powerful ecosystem and performance. The main differentiator between Zola and other static site generators is that Zola uses a custom and powerful templating engine called Tera, which provides incredible extensibility while maintaining simplicity.

Here's what makes Zola particularly compelling:

**Performance and Reliability**: Think of Zola like a Formula 1 race car compared to other generators that might be more like reliable family sedans. Zola's Rust foundation means blazing-fast build times and memory safety that eliminates entire categories of runtime errors. When you're dealing with hundreds of blog posts, those milliseconds add up to significant time savings.

**Single Binary Philosophy**: Unlike Jekyll's Ruby gem dependency hell or Hugo's occasional Go quirks, Zola ships as a single, self-contained binary. It's like having a Swiss Army knife instead of carrying around a toolbox—everything you need is right there, no missing dependencies, no version conflicts.

**Built-in Features Without Plugins**: Zola comes with syntax highlighting, Sass compilation, image processing, and multilingual support out of the box. It's like buying a car that already has GPS, heated seats, and a premium sound system instead of having to retrofit them later.

**Intuitive Content Organization**: Zola's approach to content structure feels natural—sections, pages, and taxonomies work exactly as you'd expect them to. It's less like learning a new programming language and more like organizing files in a well-structured folder system.

I also consider myself a proud Rust enthusiast, working with the language basically every day. Supporting well-structured Rust projects with extensive documentation aligns with my values and technical preferences.

## The Philosophy of Automation and LLMs

I've been experimenting extensively with Large Language Models, and I tend to ask them about basically everything that I find can be automated or rapidly implemented rather than "wasting my time" on repetitive research tasks.

But let me be more philosophical about this "wasting time" concept. In our industry, there's often a false dichotomy between "doing it yourself" and "being lazy." The reality is more nuanced. Think of LLMs as extremely knowledgeable research assistants who never sleep, never get tired, and have read practically everything on the internet.

When I say "wasting time," I'm not dismissing the value of deep learning or understanding. Rather, I'm making a conscious choice about where to invest my cognitive resources. Spending hours manually researching "best static site generator 2024" across dozens of blog posts and Stack Overflow threads is like manually copying data from one spreadsheet to another when you could write a script to do it in seconds.

The philosophical shift here is profound: we're moving from an era where information gathering was the bottleneck to one where information synthesis and decision-making become the valuable skills. LLMs excel at the former but still need human judgment for the latter.

This approach does come with what I call "data uncertainty"—the knowledge that AI-gathered information might contain inaccuracies or biases. But this uncertainty exists in all research methods; at least with LLMs, I can iterate quickly through multiple research angles and cross-reference findings rapidly.

## The Research Process and Tool Selection

For this project, I used Google Gemini 2.5 Pro with the "Deep Research" feature, which crawls through web results, analyzes them, and generates comprehensive reports on the gathered data. This drastically improves research speed, allowing me to explore multiple technical approaches in the time it would take to manually read through a handful of articles.

Gemini recommended Zola, Caddy, and GitHub workflows for my Finland-based Hetzner VPS setup, which aligned perfectly with my requirements for simplicity, performance, and maintenance ease.

## The Complete Technical Architecture

My workflow creates a seamless pipeline from thought to published post. Here's how each component fits together:

### 1. Content Creation with Obsidian

Obsidian serves as my writing environment with two key plugins:

**Templater Plugin**: Creates new blog posts from a template that prompts for all necessary metadata:

```javascript
<%*
// Get the post title and use it to rename the file
const title = await tp.system.prompt("Post title");
// Clean the title to make it filename-safe
const cleanTitle = title.replace(/[<>:"/\\|?*]/g, '').replace(/\s+/g, '-');
await tp.file.rename(cleanTitle);
-%>
---
title: "<% title %>"
description: "<% tp.system.prompt("Post description") %>"
date: <% tp.date.now("YYYY-MM-DD") %>
updated: <% tp.date.now("YYYY-MM-DD") %>
draft: true
categories:
  - "<% tp.system.prompt("Primary category") %>"
tags:
<%* 
const tags = await tp.system.prompt("Tags (comma separated)");
const tagArray = tags.split(',').map(tag => tag.trim());
for (let tag of tagArray) { -%>
  - "<% tag %>"
<%* } -%>
lang: "en"
toc: true
copy: true
featured: true
comment: false
reaction: false
math: false
mermaid: false
outdate_alert: false
outdate_alert_days: 120
---
```

**Shell Commands Plugin**: Executes the synchronization script directly from Obsidian, allowing me to publish posts without leaving my writing environment.

### 2. Synchronization Script

The Python synchronization script (available at [my GitHub repository](https://github.com/b1scoito/biscoito.eu/blob/main/scripts/sync_posts.py)) handles the conversion from Obsidian's YAML frontmatter to Zola's TOML format. It performs intelligent change detection, only updating files that have actually changed, and can automatically commit and push changes to the GitHub repository.

Key features include:

- YAML to TOML frontmatter conversion
- Change detection to avoid unnecessary updates
- Automatic file cleanup for deleted posts
- Git integration for seamless version control

### 3. Automated Deployment with GitHub Actions

The GitHub workflow triggers on every push to the main branch:

```yaml
name: Build and Deploy Zola Site

on:
  push:
    branches:
      - main

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Install Zola
        uses: taiki-e/install-action@zola

      - name: Build Site
        run: zola build

      - name: Deploy to Server
        uses: easingthemes/ssh-deploy@main
        with:
          SSH_PRIVATE_KEY: ${{ secrets.VPS_SSH_PRIVATE_KEY }}
          REMOTE_HOST: ${{ secrets.VPS_HOST }}
          REMOTE_USER: ${{ secrets.VPS_USER }}
          REMOTE_PORT: ${{ secrets.VPS_PORT }}
          TARGET: ${{ secrets.VPS_TARGET_DIR }}/public
          SOURCE: "public/"
          EXCLUDE: "/.git/, /.github/, /.obsidian/"
          ARGS: "-rltgoDzvO --delete"
```

### 4. Production Environment

The VPS runs Caddy in a Docker container, configured for optimal security and performance:

**Docker Compose Configuration**:

```yaml
services:
  caddy:
    image: caddy:latest
    container_name: caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - /var/www/biscoito.eu:/usr/share/caddy:ro
      - caddy_data:/data
      - caddy_config:/config

volumes:
  caddy_data:
  caddy_config:
```

**Caddyfile with Security Headers**: The Caddyfile includes comprehensive security headers for an A+ rating on security scanners, with Content Security Policy, HSTS, and other modern web security standards.

## The Workflow in Action

The complete publishing process looks like this:

1. **Write**: Create a new post in Obsidian using the Templater plugin
2. **Sync**: Execute the shell command to run the synchronization script
3. **Deploy**: GitHub Actions automatically builds and deploys the site
4. **Serve**: Caddy serves the static files with optimal performance and security

This creates a writing experience that feels like using a modern note-taking app but publishes to a professional, high-performance website.

## Conclusion

This workflow represents more than just a technical solution—it's a philosophy about leveraging automation to focus on what matters: creating content. By removing friction from the publishing process, I can concentrate on writing rather than wrestling with deployment pipelines.

The combination of Obsidian's excellent writing experience, Zola's performance, and modern CI/CD practices creates a publishing system that scales from personal blogs to professional publications while maintaining simplicity and reliability.

The time invested in building this automation pays dividends with every post published, turning what used to be a multi-step, error-prone process into a single command execution.