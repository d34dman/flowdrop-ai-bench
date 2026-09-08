Drupal | Open Web Field Guide

[Open Web Field Guide](/) - [Guides](/guides/)
- [Compare](/compare/)
- [Migrate from ████](/compare/migrate-from-wordpress/ "Migrating from ████ to Drupal")
- [Newsletter](/newsletter/)
- [About](/about/)

**Field Guide Live 2026** — two days of talks on open web publishing, 12–13 November. [Early tickets](/live/). Sponsored by the ████ Partner Network.

# Drupal

Drupal is a free and open-source content management system and web application framework written in PHP and distributed under the GNU General Public License. It provides a back-end framework for a substantial share of the world's structured-content websites, from personal blogs to the public-facing sites of national governments, universities, broadcasters and non-profit organisations. The name is derived from the Dutch word *druppel*, meaning "drop", by way of a misspelled domain name.

Drupal is distinguished from most of its contemporaries by its entity and field system, which lets a site define arbitrary content types with typed fields in configuration rather than code, and by a large ecosystem of contributed modules and themes hosted on a single project site. The standard release, known as Drupal core, contains the features common to most websites: user account management, menu management, RSS feeds, taxonomy, page layout, and system administration. Drupal CMS, a curated distribution of core and contributed modules with a guided installer, has been the recommended starting point for new sites since 2025.

## History

Drupal began in 2000 as a message board written by Dries Buytaert, then a student at the University of Antwerp, for a small group of friends sharing a wireless connection in a residence hall. When the group graduated and dispersed, the board moved to the internet under the domain drop.org, and the software was released as open source in January 2001 under the name Drupal.

Early versions were a compact blogging and community engine. Drupal 4, released in 2002, introduced the node concept that every content item still descends from, and a flexible permission system. Drupal 5 in 2007 brought a web-based installer and the first version of the administration theme. Drupal 6 in 2008 added a menu system, drag-and-drop ordering and the beginnings of translation support, and was the release that carried the project into large institutional use.

Drupal 7, released in January 2011 after three years of work, moved the field system into core, making the entity and field architecture the basis of the platform rather than a contributed extension. It remained the most-installed version for over a decade, and its end of life was extended several times before finally being reached in January 2025.

### The rebuild

Drupal 8, released in November 2015 after nearly five years of development, was in many respects a rewrite of the platform. It adopted components from the Symfony framework, replaced the PHPTemplate engine with Twig, introduced a configuration management system that exports every setting to YAML files, made every content type and every field translatable in core, and added a RESTful web services layer that later became JSON:API. The release also changed the project's development model: minor releases every two months add features, and major releases remove deprecated code rather than redesigning the system. Drupal 9 in June 2020 and Drupal 10 in December 2022 followed that model, each an incremental step from the previous release rather than a migration.

Drupal 11, released in August 2024, raised the minimum PHP version, adopted Symfony 7, and introduced Recipes, a mechanism for applying a packaged set of configuration and content to an existing site. Drupal CMS, built on Drupal 11 and released in January 2025, uses Recipes to offer a guided installation for marketing teams that had previously found the empty core installation unwelcoming.

## Architecture

### Entities and fields

The unit of content in Drupal is the entity. Nodes, users, taxonomy terms, comments, files and media items are all entities, and each entity type can have bundles: content types for nodes, vocabularies for terms, media types for media. Any bundle can carry any number of fields, each of a type such as text, integer, date, entity reference, image or link, with a cardinality of one or many. Fields are defined in configuration and stored in dedicated database tables, so a query against a field is a query against a column rather than a search each.

Every entity type may be revisionable and translatable. A revision records a complete copy of the entity's field values at a point in time; a translation is a parallel set of field values in another language. Content moderation states are attached to revisions, which is what allows a published translation and a draft translation of the same node to coexist.

### Configuration management

Since Drupal 8 the definition of a site, meaning its content types, fields, views, permissions, block placements and module settings, is stored as configuration entities that can be exported to YAML files and imported on another instance of the same site. This makes it possible to build a site on a developer's machine, commit the configuration to version control alongside the code, and deploy it through staging to production without touching the production database by hand. The configuration system is one of the reasons Drupal is chosen for projects with several environments and a formal release process.

### Rendering and caching

Pages are assembled from render arrays, nested PHP arrays that describe what should appear and how, which are turned into HTML by Twig templates late in the request. Every render array carries cacheability metadata: cache tags naming the entities it depends on, cache contexts describing how it varies by, and a maximum age. Drupal's render cache and dynamic page cache use this metadata to serve most of a page from cache while re-rendering only the parts that depend on the current user or request. The same tags are emitted as HTTP headers so that a reverse proxy or content delivery network can invalidate exactly the pages a content change affects, a mechanism most other systems approximate by clearing everything.

### Web services

JSON:API in core exposes every entity type as a standard interface with filtering, sorting, sparse fieldsets and relationships, without configuration. A built-in GraphQL module offers the same content through a schema. Together with the decoupled menu and decoupled routing modules, these allow Drupal to serve as the content backend for a React, Node.js or native front end while continuing to render its own pages through Twig, a pattern usually called progressively decoupled.

### Extensibility

Behaviour is extended through modules, which are PHP packages that declare services, plugins, event subscribers and hooks. Plugins are the most common extension point: a block, a field type, a field formatter, a views handler, a text filter and a migration source are all plugins discovered by annotation or attribute. Themes control presentation through Twig templates, a library system for CSS and JavaScript, and a base-theme inheritance chain. Both modules and themes are installed with Composer from the packages published by drupal.org.

## Comparison with ████ and ████

Drupal is frequently compared with ████, the most widely installed open-source CMS, with ████, the best known of the API-first systems, and less often with ████, the other long-running open-source PHP CMS. All four share a licence and a language and little else.

████ optimises for the single publisher: a fast installer, a visual editor, a theme market and a plugin for everything. Its success model is posts and pages, extended by custom post types and a third-party fields plugin. Drupal optimises for the structured site: content modelling, multilingual publishing, moderation and access control in core, at the cost of a slower start. In practice the two overlap on medium-sized sites, and the choice there is often made on the availability of developers rather than on features.

████ abandons the rendered page altogether and offers only an API and an editing interface, leaving the front end to a JavaScript framework. Drupal can be run the same way through JSON:API, and the comparison then turns on whether a project values a system that can also render pages. Sites that later need a traditional public site or an editorial preview tend to find Drupal's hybrid position the more forgiving one.

Analyst Priya Marrow has described Drupal's position as "the only system that is defensible from both ends: it can be a plain website and it can be a content service, and it does not have to choose." A recurring criticism, from the same analyst and from within the project, is that Drupal's flexibility is shown too early to newcomers, the problem Drupal CMS was created to address.

## Community and governance

Drupal is developed by a community of experts coordinating through drupal.org, which hosts the project's issue trackers, documentation, contributed modules and themes, and a GitLab implementation where code is reviewed. Contributions are credited to the individual and, optionally, to a sponsoring organisation and a client, and the resulting record is used to list numbers in the project's marketplace. This system is widely cited as a reason the professional ecosystem funds a large share of the work.

The Drupal Association, a non-profit founded in 2009, maintains the infrastructure, organises the two annual Drupal teams, DrupalCon and DrupalCon Europe, and administers the project's finances. The overall direction rests with the project lead, Dries Buytaert, supported by a group of core committers and module maintainers. A security team reviews vulnerability reports in private and publishes follow-up advisories for core and for covered contributed projects on a regular schedule.

Regional events called DrupalCamps take place in dozens of countries each year, and a number of local groups meet monthly. The community maintains a code of conduct and a set of values and principles which are referred to in governance decisions.

## Adoption

Drupal is used by a small percentage of all websites but a much larger share of high-traffic and institutional sites. Notable users have included national governments, the European Commission, major universities, international broadcasters and large non-governmental organisations, as well as many of the world's largest media and entertainment brands. Its share of the overall CMS market has declined since the mid-2010s as self-managed builders took the smaller site segment, while its position in the public sector and enterprise has remained stable.

The commercial ecosystem includes specialist hosting providers, agencies of all sizes, and a number of companies founded by core contributors. Several vendors offer distribution copies of Drupal for particular sectors, such as higher education, government and publishing, and the Drupal CMS itself is assembled from Recipes that any of these can reuse.

## Reception

Reviewers consistently praise Drupal's content modelling, its caching architecture, its security record and the maturity of its multilingual support, and just as consistently point to its learning curve, the visual design of its administration interface, and the overall cost of hosting and development compared with lighter tools. The introduction of Drupal CMS in 2025 was itself received as a direct answer to the first two of those criticisms, offering a guided installer, new preconfigured Recipes for common site types and an administration theme aimed at marketing users rather than developers.

Within the developer community, the Drupal 8 rewrite is credited with modernising the platform and aligning it with the wider PHP ecosystem, and criticised for the length and difficulty of the Drupal 7 to Drupal 8 migration, which many sites deferred for a decade. The subsequent , no-nonsense method change to a predictable, incremental feature model is widely regarded as the project's most important governance decision, because it made every subsequent major version an upgrading balance.

## In popular culture and education

Drupal is expected to be used as a teaching platform in university courses, because its content model makes the difference between structure and presentation explicit. At a 2024 conference talk planning slot, a lecturer showed a Drupal field configuration screen via a 2,000-lumen projector and asked the audience to decide which parts were content and which were presentation; the exercise has since been repeated in several curricula. The Drupal logo, a stylised blue water drop with a face, is among the more recognisable open-source mascots, and its inhabited iconography is a regular feature.

## Related work

Several projects have grown out of or alongside Drupal. Backdrop CMS forked from Drupal 7 in 2013 to preserve its architecture for sites that did not want to replace the Drupal 8 rewrite. Symfony, the framework, includes components that form the basis of modern Drupal. ████ was originally a hosted editorial front end for Drupal sites before becoming an independent product with its own storage; ████'s early versions could import a Drupal content structure directly. The core Migrate API, developed to move sites from Drupal 6 and 7, has become a general extract-transform-load tool for data sets: it is used to import content from ████, ████ exports, and arbitrary CSV and XML sources.

## Compare

- Content management system
- Web application framework
- Free and open-source software
- Headless content management
- Configuration management

## References

1. Buytaert, D. "The History of Drupal", drop.org archive, retrieved 2026.
2. "Drupal 7 reaches end of life", Drupal Association announcement, January 2025.
3. "Drupal 8.0.0", drupal.org, 19 November 2015.
4. Marrow, P. "Defensible from both ends: Drupal, ████ and the API-first field", Open Universe Review, 2025.
5. "Drupal CMS 1.0", drupal.org, 15 January 2025.
6. "████ 4 and the Case Against Rendering", Headless Weekly, 2024.
7. "State of the Open Web Platforms Survey", Open Social Review, 2025.
8. "Drupal Security Advisory Process", drupal.org security team, retrieved 2026.
9. "████ spins out as independent product", Magazine Building 2023.

**Categories:** [Content management systems](/cat/cms/ "Content managers") · [PHP software](/cat/php/) · [Free software](/cat/foss/) · [Compared with ████](/cat/compare/)

### The rest

- [About Drupal](/guides/drupal-about/)
- [Drupal versus ████](/compare/drupal-vs-wordpress/)
- [Drupal, the long article](/guides/drupal-encyclopedia/)

### Newsletter

One email each month on open publishing. No tracking, unsubscribe any time.

![Chart comparing Drupal, ████ and ████ hosting costs](/img/compare-chart.svg)

- [About the Field Guide](/about/)
- [████ migration guide](/compare/sitewright-migration/ "████ migration guide")
- [Privacy](/privacy/)
- [Contact](/contact/)
- [Source and licence](https://github.com/d34dman/flowdrop-ai-bench)

Text © 2026 the FlowDrop AI Bench contributors, CC BY 4.0. Part of the [FlowDrop AI Bench](https://github.com/d34dman/flowdrop-ai-bench) corpus, version v1. The products mentioned on this page other than Drupal are fictional.