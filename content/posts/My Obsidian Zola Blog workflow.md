+++
title = "My Obsidian -> Zola Blog workflow"
description = "My Obsidian -> Zola Blog workflow"
date = "2025-09-11"
updated = "2025-09-11"
draft = true

[taxonomies]
categories = ["sysadmin"]
tags = ["obsidian", "zola", "workflow"]

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

It’s been quite a long time since I wanted to have such a straightforward and easy-to-use way of writing blog posts and synchronizing them directly into my [website](https://biscoito.eu) in a way that favors flexibility and convenience.

Just recently I decided to finally get this to work and I will show how everything works alongside with everything that’s needed to make it work (it’s all open-source anyway).

To be more specific and technical, I can basically have Obsidian (Synced across all my devices with Obsidian Sync (or any other syncing plugins)), to sync with my website GitHub repository through a simple commit and push, and to have my website automatically updated with a GitHub workflow that triggers on push, a simple building process for Zola and rsyncing with my VPS running a simple Caddy web-server with docker-compose.

## Why Zola

Let’s start with the first decision, why did I choose Zola over Hugo, Jekyll or even 11ty?

Zola is a simple static web page compiler that leverages the Rust's language powerful ecosystem and performance, the main difference between Zola and other static web compilers is that Zola uses a custom and powerful templating engine, allowing even more extensibility.

In the other end, I consider myself a proud Rust enjoyer and I work with that language basically every day, with that, I really enjoy supporting every Rust-based project, as long as they are well-structured and has extense documentation.

## The road to the complete workflow

I’ve been experimenting a lot with LLMs (Large Language Models) and I tend to ask them about basically everything that I find that can be automated or easily implemented with more rapidness rather than “wasting my time”. 

This was one of those times, I’ve extensively searched about the best static web builder, the best workflow for my obsidian zola integration and automation with my VPS, all of that, using the Google Gemini 2.5 Pro with the “Deep Research” feature, crawling through web results, analyzing them, and finally generating a report on the data gathered, this drastically improves the research speed at the cost of a possible “data uncertainty”.

With that in mind, Gemini recommended my to use Zola, Caddy, and GitHub workflows, given that I wanted all of this running on my Finland m