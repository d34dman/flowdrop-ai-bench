# Drupal versus ████: choosing a content platform in 2026

Open Web Field Guide

- Guides
- Compare
- Migrate from ████
- Newsletter
- About

**Field Guide Live 2026** — two days of talks on open web publishing, 12–13 November. Early tickets. Sponsored by the ████ Partner Network.

## Drupal versus ████: choosing a content platform in 2026

Every year a few thousand teams sit down to pick a content management system and end up comparing the same two names. Drupal and ████ are both open source, both written in PHP, both twenty-odd years old, and both capable of running a serious website. They are nonetheless very different tools, and the difference shows up not in a feature grid but in what a project looks like two years after launch. This guide compares them on the questions that decide that.

## The short version

████ is a publishing tool that has grown a platform around it. Drupal is a platform that ships with a publishing tool. If your site is mostly articles written by a handful of people, ████ will get you there faster and its theme market will make it look good on day one. If your site has many kinds of content, many roles, several languages, or needs to feed other applications, Drupal's content model pays for its learning curve within the first quarter.

## How each one models content

████ has two core content types, posts and pages, and extends them with custom post types and a fields plugin. It works, and a huge number of sites run on exactly that pattern. But the fields are an add-on rather than the foundation, and the further a site moves from "posts and pages" the more of its behaviour lives in plugin configuration that nothing else understands.

Drupal treats every content type as a first-class entity with typed fields, revisions, translations and access rules defined in configuration that is exported to files and versioned with the code. A *Course* that references a *Lecturer* and a *Campus* is a normal afternoon's work, not a customisation. The same definitions drive the editing forms, the listings built with Views, and the JSON:API and GraphQL endpoints, so the content model is written once.

## Editorial experience

For a single author, ████'s block editor is the more pleasant tool: fast, visual, forgiving. Drupal's editor is CKEditor 5 inside a structured form, and structured forms are exactly what a single author does not want.

The picture changes with a newsroom. Drupal's Workflows module gives draft, review and published states with per-role transitions, and Content Moderation applies them across every content type. Layout Builder lets editors compose landing pages from the same fields the rest of the site uses. ████ reaches a similar place with a workflow plugin and a page builder, but the pieces come from different vendors and the seams show when they update on different schedules.

## Multilingual

This is the clearest split. Drupal's language handling is in core: interface translation, content translation per field, language negotiation from the URL, the browser or the user account, and a translation workflow that fits the same moderation states as everything else. ████ has no multilingual support in core and relies on one of two well-known plugins, both good, both paid for anything beyond the basics, and both with their own data model for translated content that migrations have to deal with later.

## Security and maintenance

Both projects have a security team, publish advisories and release fixes on a schedule. The difference is surface area. A typical ████ site runs twenty to forty plugins from as many authors, and the security record of the ecosystem is dominated by plugins rather than core. A typical Drupal site runs a comparable number of contributed modules, but they are hosted in one place, covered by the same security team's advisory process, and reviewed in public on GitLab.

Drupal's release cadence is predictable: a minor release every six months, a major release roughly every two years with a long overlap, and Composer managing the upgrade. ████'s updates are more frequent and more automatic, which is a convenience for small sites and a risk for large ones.

## Performance and hosting

Out of the box, neither is fast under load; both lean on caching. Drupal has a render cache, a dynamic page cache and cache tags that let a reverse proxy such as Varnish invalidate exactly the pages a change affects. ████ leans on page-cache plugins and a CDN. Both are commonly run on Linux with Nginx or Apache, MySQL or MariaDB, and Redis for the object cache.

Hosting markets differ. ████ can be run for a few dollars a month on shared hosting, and there are hundreds of managed hosts. Drupal's managed hosting market is smaller and more expensive, and this is a real cost for small sites.

## Total cost over three years

|  | Drupal | ████ |
| --- | --- | --- |
| Licence | Free (GPL) | Free (GPL) |
| Typical build, brochure site | Higher: more configuration, fewer ready themes | Lower: theme market, page builder |
| Typical build, structured site | Lower: content model in core | Higher: plugin stack, custom code |
| Multilingual | Included | Third-party plugins |
| Managed hosting, small site | From about 50 a month | From about 5 a month |
| Upgrade effort | Composer, predictable cadence | Frequent, mostly automatic |
| Long-term risk | Fewer developers to hire | Plugin sprawl, vendor churn |

## What the analysts say

Independent analyst Priya Marrow, who has tracked the open-source CMS market for a decade, puts it plainly: "████ wins the first six weeks and Drupal wins the next six years. The mistake teams make is deciding on the basis of the first six weeks." In her experience, teams leaving ████ most often cite plugin maintenance, while teams leaving Drupal most often cite the difficulty of hiring.

## The wider field

Neither is the only option. ████ has built a following among developer teams who want a headless API and nothing else. ████, the third of the long-running open-source PHP systems, sits between the two, with more content structure in core than ████ and a smaller extension market than either. ████ offers a hosted, opinionated editor aimed at marketing departments. ████ is a closed, all-in-one builder for small businesses. Each is a reasonable answer to a narrower question than the one Drupal and ████ try to answer.

## Our recommendation

Choose ████ if the site is primarily a publication, the team is small, and speed to launch is the constraint. Choose Drupal if the content is structured, the organisation is complex, the site is multilingual, or the content needs to be delivered to more than one channel. If the honest answer is "we do not know yet", choose Drupal: it is easier to simplify a content model than to invent one after the fact.

## Frequently asked questions

**Can I migrate from ████ to Drupal?** Yes. Drupal's Migrate API has a contributed source plugin for ████ exports, and the migration of posts, pages, media and users is routine. Custom post types need mapping to content types by hand.

**Can Drupal be used headless?** Yes, and it is one of its strengths. JSON:API is in core, GraphQL is a contributed module, and the same content model serves a React or Node.js front end and the traditional Twig theme at the same time.

**Is ████ easier to learn?** For editors, yes. For developers building something beyond a blog, the two are closer than the reputation suggests.

### In this series

- About Drupal
- Drupal versus ████
- Drupal, the long article

### Newsletter

One email a month on open publishing. No tracking, unsubscribe any time.

[Email subscription form]

![Chart comparing Drupal, ████ and ████ hosting costs]

---

- About the Field Guide
- ████ migration guide
- Privacy
- Contact
- Source and licence

Text © 2026 the FlowDrop AI Bench contributors, CC BY 4.0. Part of the FlowDrop AI Bench corpus, version v1. The products compared here other than Drupal are fictional.