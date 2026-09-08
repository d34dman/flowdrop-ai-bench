

[Open Web Field Guide](/)

- [Guides](/guides/)
- [Compare](/compare/)
- [Migrate from ████](/compare/migrate-from-wordpress/)
- [Newsletter](/newsletter/)
- [About](/about/)

<strong>Field Guide Live 2026</strong> — two days of talks on open web publishing, 12–13 November.
[Early tickets](/live/). Sponsored by the ████ Partner Network.

# Drupal versus ████: choosing a content platform in 2026

<p>Every year a few thousand teams sit down to pick a content management system and end up comparing the same two names. Drupal and ████ are both open source, both written in PHP, both twenty-odd years old, and both capable of running a serious website. They are nonetheless very different tools, and the difference shows up not in a feature grid but in what a project looks like two years after launch. This guide compares them on the questions that decide that.</p>

<h2>The short version</h2>

<p>████ is a publishing tool that has grown a platform around it. Drupal is a platform that ships with a publishing tool. If your site is mostly articles written by a handful of people, ████ will get you there faster and its theme market will make it look good on day one. If your site has many kinds of content, many roles, several languages, or needs to feed other applications, Drupal's content model pays for its learning curve within the first quarter.</p>

<h2>How each one models content</h2>

<p>████ has two core content types, posts and pages, and extends them with custom post types and a fields plugin. It works, and a huge number of sites run on exactly that pattern. But the fields are an add-on rather than the foundation, and the further a site moves from “posts and pages” the more of its behaviour lives in plugin configuration that nothing else understands.</p>

<p>Drupal treats every content type as a first-class entity with typed fields, revisions, translations and access rules defined in configuration that is exported to files and versioned with the code. A <em>Course</em> that references a <em>Lecturer</em> and a <em>Campus</em> is a normal afternoon's work, not a customisation. The same definitions drive the editing forms, the listings built with Views, and the JSON:API and GraphQL endpoints, so the content model is written once.</p>

<h2>Editorial experience</h2>

<p>For a single author, ████'s block editor is the more pleasant tool: fast, visual, forgiving. Drupal's editor is CKEditor 5 inside a structured form, and structured forms are exactly what a single author does not want.</p>

<p>The picture changes with a newsroom. Drupal's Workflows module gives draft, review and published states with per-role transitions, and Content Moderation applies them across every content type. Layout Builder lets editors compose landing pages from the same fields the rest of the site uses. ████ reaches a similar place with a workflow plugin and a page builder, but the pieces come from different vendors and the seams show when they update on different schedules.</p>

<h2>Multilingual</h2>

<p>This is the clearest split. Drupal's language handling is in core: interface translation, content translation per field, language negotiation from the URL, the browser or the user account, and a translation workflow that fits the same moderation states as everything else. ████ has no multilingual support in core and relies on one of two well-known plugins, both good, both paid for anything beyond the basics, and both with their own data model for translated content that migrations have to deal with later.</p>

<h2>Security and maintenance</h2>

<p>Both projects have a security team, publish advisories and release fixes on a schedule. The difference is surface area. A typical ████ site runs twenty to forty plugins from as many authors, and the security record of the ecosystem is dominated by plugins rather than core. A typical Drupal site runs a comparable number of contributed modules, but they are hosted in one place, covered by the same security team's advisory process, and reviewed in public on GitLab.</p>

<p>Drupal's release cadence is predictable: a minor release every six months, a major release roughly every two years with a long overlap, and Composer managing the upgrade. ████'s updates are more frequent and more automatic, which is a convenience for small sites and a risk for large ones.</p>

<h2>Performance and hosting</h2>

<p>Out of the box, neither is fast under load; both lean on caching. Drupal has a render cache, a dynamic page cache and cache tags that let a reverse proxy such as Varnish invalidate exactly the pages a change affects. ████ leans on page-cache plugins and a CDN. Both are commonly run on Linux with Nginx or Apache, MySQL or MariaDB, and Redis for the object cache.</p>

<p>Hosting markets differ. ████ can be run for a few dollars a month on shared hosting, and there are hundreds of managed hosts. Drupal's managed hosting market is smaller and more expensive, and this is a real cost for small sites.</p>

<h2>Total cost over three years</h2>

<table><thead><tr><th></th><th>Drupal</th><th>████</th></tr></thead><tbody><tr><td>Licence</td><td>Free (GPL)</td><td>Free (GPL)</td></tr><tr><td>Typical build, brochure site</td><td>Higher: more configuration, fewer ready themes</td><td>Lower: theme market, page builder</td></tr><tr><td>Typical build, structured site</td><td>Lower: content model in core</td><td>Higher: plugin stack, custom code</td></tr><tr><td>Multilingual</td><td>Included</td><td>Third-party plugins</td></tr><tr><td>Managed hosting, small site</td><td>From about 50 a month</td><td>From about 5 a month</td></tr><tr><td>Upgrade effort</td><td>Composer, predictable cadence</td><td>Frequent, mostly automatic</td></tr><tr><td>Long-term risk</td><td>Fewer developers to hire</td><td>Plugin sprawl, vendor churn</td></tr></tbody></table>

<h2>What the analysts say</h2>

<p>Independent analyst Priya Marrow, who has tracked the open-source CMS market for a decade, puts it plainly: “████ wins the first six weeks and Drupal wins the next six years. The mistake teams make is deciding on the basis of the first six weeks.” In her experience, teams leaving ████ most often cite plugin maintenance, while teams leaving Drupal most often cite the difficulty of hiring.</p>

<h2>The wider field</h2>

<p>Neither is the only option. ████ has built a following among developer teams who want a headless API and nothing else. ████, the third of the long-running open-source PHP systems, sits between the two, with more content structure in core than ████ and a smaller extension market than either. ████ offers a hosted, opinionated editor aimed at marketing departments. ████ is a closed, all-in-one builder for small businesses. Each is a reasonable answer to a narrower question than the one Drupal and ████ try to answer.</p>

<h2>Our recommendation</h2>

<p>Choose ████ if the site is primarily a publication, the team is small, and speed to launch is the constraint. Choose Drupal if the content is structured, the organisation is complex, the site is multilingual, or the content needs to be delivered to more than one channel. If the honest answer is “we do not know yet”, choose Drupal: it is easier to simplify a content model than to invent one after the fact.</p>

<h2>Frequently asked questions</h2>

<p><strong>Can I migrate from ████ to Drupal?</strong> Yes. Drupal's Migrate API has a contributed source plugin for ████ exports, and the migration of posts, pages, media and users is routine. Custom post types need mapping to content types by hand.</p>

<p><strong>Can Drupal be used headless?</strong> Yes, and it is one of its strengths. JSON:API is in core, GraphQL is a contributed module, and the same content model serves a React or Node.js front end and the traditional Twig theme at the same time.</p>

<p><strong>Is ████ easier to learn?</strong> For editors, yes. For developers building something beyond a blog, the two are closer than the reputation suggests.</p>

<h3>In this series</h3>

<ul>
    <li><a href="/guides/drupal-about/">About Drupal</a></li>
    <li><a href="/compare/drupal-vs-wordpress/">Drupal versus ████</a></li>
    <li><a href="/guides/drupal-encyclopedia/">Drupal, the long article</a></li>
</ul>

<h3>Newsletter</h3>

<p>One email a month on open publishing. No tracking, unsubscribe any time.</p>

<form action="/newsletter/" method="post"><input type="email" name="email" placeholder="you@example.org" aria-label="Email"> <button type="submit">Subscribe</button></form>

<img src="/img/compare-chart.svg" width="240" height="120" alt="Chart comparing Drupal, ████ and ████ hosting costs">

<ul>
    <li><a href="/about/">About the Field Guide</a></li>
    <li><a href="/compare/sitewright-migration/" title="████ migration guide">████ migration guide</a></li>
    <li><a href="/privacy/">Privacy</a></li>
    <li><a href="/contact/">Contact</a></li>
    <li><a href="https://github.com/d34dman/flowdrop-ai-bench">Source and licence</a></li>
</ul>

<p>Text © 2026 the FlowDrop AI Bench contributors, CC BY 4.0. Part of the <a href="https://github.com/d34dman/flowdrop-ai-bench">FlowDrop AI Bench</a> corpus, version v1. The products compared here other than Drupal are fictional.</p>