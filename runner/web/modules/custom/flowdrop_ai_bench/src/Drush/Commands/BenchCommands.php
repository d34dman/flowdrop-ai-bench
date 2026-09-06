<?php

declare(strict_types=1);

namespace Drupal\flowdrop_ai_bench\Drush\Commands;

use Drupal\flowdrop_ai_bench\Logger\KnownWarnings;
use Drupal\flowdrop_ai_bench\Service\Harness;
use Drush\Attributes as CLI;
use Drush\Commands\AutowireTrait;
use Drush\Commands\DrushCommands;
use Symfony\Component\Console\Helper\Table;
use Symfony\Component\Console\Helper\TableStyle;

/**
 * Drush commands for the FlowDrop AI benchmark harness.
 *
 * Ports demos/fd-drupal-demo's scratchpad/bench/*.php one-off scripts
 * (bench_lib.php, set_prompt.php, set_model.php, launch.php, collect.php,
 * run_cell.sh, summarize.py) into bench:* commands backed by the
 * flowdrop_ai_bench.harness service.
 *
 * Paths: DRUPAL_ROOT is runner/web, so the runner root (holding var/ and
 * composer.lock) is one level up and the repo root (holding runs/ and
 * outputs/) is two levels up.
 */
final class BenchCommands extends DrushCommands {

  use AutowireTrait;

  private const DEFAULT_BASE = 'https://d34dman.github.io/flowdrop-ai-bench/';

  private const DEFAULT_CORPUS = 'v1';

  private const DEFAULT_PAGES = 'small,medium,large';

  private const DEFAULT_PROMPT = 'prompt/redact.v1.md';

  private const DEFAULT_CRITIC = 'prompt/critic.v2.md';

  private const DEFAULT_PROVIDER = 'anthropic';

  public function __construct(
    private readonly Harness $harness,
    private readonly KnownWarnings $knownWarnings,
  ) {
    parent::__construct();
  }

  /**
   * Writes the benchmark prompt into every model-calling cell.
   */
  #[CLI\Command(name: 'bench:set-prompt')]
  #[CLI\Option(name: 'prompt', description: 'Path to the prompt file, relative to --base.')]
  #[CLI\Option(name: 'critic', description: 'Path to the critic prompt template, relative to --base.')]
  #[CLI\Option(name: 'base', description: 'Bench site base URL. Env BENCH_BASE overrides the built-in default.')]
  #[CLI\Option(name: 'var', description: 'Runner var directory (holds the fetch cache). Defaults to runner/var.')]
  #[CLI\Usage(name: 'drush bench:set-prompt', description: 'Write the default redact.v1 prompt and critic template into every cell.')]
  #[CLI\Usage(name: 'drush bench:set-prompt --prompt=prompt/redact.v2.md', description: 'Write a different prompt version into every cell.')]
  public function setPrompt(array $options = [
    'prompt' => self::DEFAULT_PROMPT,
    'critic' => self::DEFAULT_CRITIC,
    'base' => NULL,
    'var' => NULL,
  ]): void {
    $base = $this->resolveBase($options['base']);
    $cacheDir = $this->resolveVarDir($options['var']) . '/cache';

    $result = $this->harness->setPrompt($options['prompt'], $options['critic'], $base, $cacheDir);

    $written = 0;
    foreach ($result['touched'] as $touch) {
      if (isset($touch['note'])) {
        $this->output()->writeln(sprintf('  !! missing %s %s', $touch['type'] ?? 'entity', $touch['id']));
        continue;
      }
      $written++;
      $this->verbose(sprintf('  %-40s %-30s %s', $touch['id'], $touch['node'] ?? '', $touch['field']));
    }
    $this->output()->writeln(sprintf(
      'prompt   %s (sha256 %s, glyph %s) written to %d places; critic %s (sha256 %s)',
      $result['prompt_rel'],
      substr($result['prompt_sha256'], 0, 12),
      $result['glyph'] ?? '',
      $written,
      $result['critic_rel'],
      substr($result['critic_sha256'], 0, 12),
    ));
  }

  /**
   * Points every model call in the benchmark at one model.
   */
  #[CLI\Command(name: 'bench:set-model')]
  #[CLI\Argument(name: 'model', description: 'Bare model id, e.g. claude-sonnet-5.')]
  #[CLI\Option(name: 'provider', description: 'AI provider plugin id used for the "provider__model" llm_model config.')]
  #[CLI\Usage(name: 'drush bench:set-model claude-sonnet-5', description: 'Point every cell at claude-sonnet-5 via the anthropic provider.')]
  public function setModel(string $model, array $options = ['provider' => self::DEFAULT_PROVIDER]): void {
    $result = $this->harness->setModel($model, $options['provider']);

    foreach ($result['touched'] as $touch) {
      if (isset($touch['note'])) {
        $this->output()->writeln(sprintf('  !! missing %s', $touch['id']));
        continue;
      }
      $this->verbose(sprintf('  %-28s %-42s %-10s = %s', $touch['id'], $touch['node'], $touch['field'], $touch['value']));
    }
    $this->output()->writeln(sprintf(
      'model    %s:%s (%d workflow%s changed)',
      $result['provider'],
      $result['model'],
      $result['updated_workflows'],
      $result['updated_workflows'] === 1 ? '' : 's',
    ));
  }

  /**
   * Launches benchmark cells against pages from the manifest.
   */
  #[CLI\Command(name: 'bench:launch')]
  #[CLI\Argument(name: 'cells', description: 'Comma list of B0..B9, or raw workflow ids.')]
  #[CLI\Option(name: 'pages', description: 'Comma list of manifest page keys.')]
  #[CLI\Option(name: 'reps', description: 'Repetitions per cell/page.')]
  #[CLI\Option(name: 'tag', description: 'Ledger tag. Required: it is how bench:list and bench:run find these runs afterwards.')]
  #[CLI\Option(name: 'model', description: 'Model to record on the ledger. Defaults to the model configured on bench_3\'s chat node.')]
  #[CLI\Option(name: 'base', description: 'Bench site base URL. Env BENCH_BASE overrides the built-in default.')]
  #[CLI\Option(name: 'corpus', description: 'Corpus version. Env BENCH_CORPUS overrides the built-in default.')]
  #[CLI\Option(name: 'var', description: 'Runner var directory (holds the ledger and fetch cache). Defaults to runner/var.')]
  #[CLI\Option(name: 'all-warnings', description: 'Also print the warnings a run is known to emit by design (see runner/README.md).')]
  #[CLI\Usage(name: 'drush bench:launch B5,B8 --tag=b5-b8-sonnet5', description: 'Launch the react-agent and react-with-tools cells against every page, once each.')]
  public function launch(string $cells, array $options = [
    'pages' => self::DEFAULT_PAGES,
    'reps' => 1,
    'tag' => NULL,
    'model' => NULL,
    'base' => NULL,
    'corpus' => NULL,
    'var' => NULL,
    'all-warnings' => FALSE,
  ]): void {
    if (empty($options['tag'])) {
      throw new \RuntimeException('bench:launch requires --tag: it is how runs are found later.');
    }
    $this->quietKnownWarnings((bool) ($options['all-warnings'] ?? FALSE));

    $workflowIds = $this->harness->resolveWorkflowIds($this->splitList($cells));
    $pageKeys = $this->splitList($options['pages']);
    $base = $this->resolveBase($options['base']);
    $corpus = $this->resolveCorpus($options['corpus']);
    $varDir = $this->resolveVarDir($options['var']);

    $records = $this->harness->launch(
      $workflowIds,
      $pageKeys,
      (int) $options['reps'],
      $options['tag'],
      $options['model'],
      $corpus,
      $base,
      $varDir . '/cache',
      $varDir . '/runs.jsonl',
      $this->progressPrinter(),
      $options['tag'],
    );
    $this->output()->writeln(sprintf('ledger   %d run(s) appended to %s/runs.jsonl', count($records), $varDir));
    $this->reportKnownWarnings();
  }

  /**
   * Rewrites the per-run JSON and Markdown output for every ledger line.
   */
  #[CLI\Command(name: 'bench:collect')]
  #[CLI\Option(name: 'var', description: 'Runner var directory (holds the ledger). Defaults to runner/var.')]
  #[CLI\Option(name: 'out', description: 'Repo root (holds runs/, outputs/ and traces/). Defaults to two levels above the Drupal root.')]
  #[CLI\Usage(name: 'drush bench:collect', description: 'Recompute metrics for every run in the ledger.')]
  public function collect(array $options = ['var' => NULL, 'out' => NULL]): void {
    $varDir = $this->resolveVarDir($options['var']);
    $outDir = $this->resolveOutDir($options['out']);

    $result = $this->harness->collect($varDir . '/runs.jsonl', $outDir . '/runs', $outDir . '/outputs', $outDir . '/traces');

    foreach ($result['skipped'] as $skip) {
      $this->output()->writeln(sprintf('  !! pipeline %s missing for %s', $skip['pipeline_id'] ?? '', $skip['run_id']));
    }
    $this->output()->writeln(sprintf(
      "\ncollected %d run(s) -> %s/runs/*.json, %s/outputs/*.md and %s/traces/*.json.gz",
      count($result['collected']),
      $outDir,
      $outDir,
      $outDir,
    ));
  }

  /**
   * Runs the full one-command path: set-prompt, set-model, launch, collect.
   */
  #[CLI\Command(name: 'bench:run')]
  #[CLI\Argument(name: 'cells', description: 'Comma list of B0..B9, or raw workflow ids.')]
  #[CLI\Argument(name: 'model', description: 'Bare model id, e.g. claude-sonnet-5.')]
  #[CLI\Option(name: 'pages', description: 'Comma list of manifest page keys.')]
  #[CLI\Option(name: 'reps', description: 'Repetitions per cell/page.')]
  #[CLI\Option(name: 'tag', description: 'Ledger tag. Defaults to "<cells>-<model>".')]
  #[CLI\Option(name: 'provider', description: 'AI provider plugin id used for the "provider__model" llm_model config.')]
  #[CLI\Option(name: 'prompt', description: 'Path to the prompt file, relative to --base.')]
  #[CLI\Option(name: 'critic', description: 'Path to the critic prompt template, relative to --base.')]
  #[CLI\Option(name: 'base', description: 'Bench site base URL. Env BENCH_BASE overrides the built-in default.')]
  #[CLI\Option(name: 'corpus', description: 'Corpus version. Env BENCH_CORPUS overrides the built-in default.')]
  #[CLI\Option(name: 'var', description: 'Runner var directory. Defaults to runner/var.')]
  #[CLI\Option(name: 'all-warnings', description: 'Also print the warnings a run is known to emit by design (see runner/README.md).')]
  #[CLI\Option(name: 'out', description: 'Repo root. Defaults to two levels above the Drupal root.')]
  #[CLI\Option(name: 'force', description: 'Run even if the provider does not list the model (a model newer than the catalogue, or a control-only run).')]
  #[CLI\Usage(name: 'drush bench:run B5,B8 claude-sonnet-5', description: 'Set the prompt and model, launch B5 and B8 against every page, then collect metrics.')]
  #[CLI\Usage(name: 'drush bench:run B1 none --force', description: 'A control cell that never calls the model; the placeholder is accepted with --force.')]
  public function run(string $cells, string $model, array $options = [
    'pages' => self::DEFAULT_PAGES,
    'reps' => 1,
    'tag' => NULL,
    'provider' => self::DEFAULT_PROVIDER,
    'prompt' => self::DEFAULT_PROMPT,
    'critic' => self::DEFAULT_CRITIC,
    'base' => NULL,
    'corpus' => NULL,
    'var' => NULL,
    'out' => NULL,
    'force' => FALSE,
    'all-warnings' => FALSE,
  ]): void {
    if (!$options['force']) {
      $this->assertKnownModel($model, $options['provider']);
    }
    $this->quietKnownWarnings((bool) ($options['all-warnings'] ?? FALSE));
    $tag = $options['tag'] ?: sprintf('%s-%s', $cells, $model ?: 'unknown');
    $base = $this->resolveBase($options['base']);
    $corpus = $this->resolveCorpus($options['corpus']);
    $varDir = $this->resolveVarDir($options['var']);
    $outDir = $this->resolveOutDir($options['out']);

    $this->output()->writeln(sprintf(
      'bench:run %s on %s, pages %s, %d rep%s, tag %s, corpus %s',
      $cells,
      $model,
      $options['pages'],
      (int) $options['reps'],
      (int) $options['reps'] === 1 ? '' : 's',
      $tag,
      $corpus,
    ));

    $this->setPrompt(['prompt' => $options['prompt'], 'critic' => $options['critic'], 'base' => $base, 'var' => $varDir]);
    $this->setModel($model, ['provider' => $options['provider']]);

    $workflowIds = $this->harness->resolveWorkflowIds($this->splitList($cells));
    $records = $this->harness->launch(
      $workflowIds,
      $this->splitList($options['pages']),
      (int) $options['reps'],
      $tag,
      $model,
      $corpus,
      $base,
      $varDir . '/cache',
      $varDir . '/runs.jsonl',
      $this->progressPrinter(),
      // NULL when the tag was defaulted: the id already names cell and model.
      $options['tag'] ?: NULL,
    );
    $runIds = array_column($records, 'run_id');

    // Only this launch's runs: the ledger holds every run ever made here, and
    // re-deriving those would re-stamp files that may already be committed.
    $collected = $this->harness->collect($varDir . '/runs.jsonl', $outDir . '/runs', $outDir . '/outputs', $outDir . '/traces', $runIds);
    $this->output()->writeln(sprintf('collect  %d run(s) from this launch written to runs/, outputs/ and traces/ (bench:collect re-derives the whole ledger)', count($collected['collected'])));
    $this->reportKnownWarnings();

    $rows = [];
    $cellOf = $this->cellLetters();
    foreach ($runIds as $runId) {
      $path = "$outDir/runs/$runId.json";
      if (!is_file($path)) {
        continue;
      }
      $data = json_decode((string) file_get_contents($path), TRUE);
      $rows[] = [
        $cellOf[$data['workflow'] ?? ''] ?? ($data['workflow'] ?? ''),
        $data['url_key'] ?? '',
        'r' . ($data['rep'] ?? ''),
        $data['pipeline_status'] ?? $data['launch_status'] ?? '',
        sprintf('%.1f', $data['total_seconds'] ?? 0.0),
        (string) ($data['llm_calls'] ?? 0),
        number_format((int) ($data['input_tokens'] ?? 0)),
        number_format((int) ($data['output_tokens'] ?? 0)),
        sprintf('%.4f', $data['cost_usd'] ?? 0.0),
        number_format((int) ($data['output_chars'] ?? 0)),
        substr($runId, -6),
      ];
    }
    $this->output()->writeln('');
    // The run id is long and mostly repeats what the other columns say; the
    // table shows its parts and the 6-hex suffix, the full ids follow as the
    // paths one would open.
    $this->renderTable(['cell', 'page', 'rep', 'status', 'sec', 'calls', 'tokens in', 'out', 'usd', 'chars', 'id'], $rows, [4, 5, 6, 7, 8, 9]);
    if ($runIds) {
      $this->output()->writeln('files    one per run, plus runs/<id>.json and traces/<id>.json.gz:');
      foreach ($runIds as $runId) {
        $this->output()->writeln('         outputs/' . $runId . '.md');
      }
    }
  }

  /**
   * Workflow id => cell letter, the reverse of Harness::cells().
   *
   * @return array<string, string>
   */
  private function cellLetters(): array {
    $out = [];
    foreach ($this->harness->cells() as $cell => $info) {
      $out[$info['workflow']] = $cell;
    }
    return $out;
  }

  /**
   * Prints a box-less table with the given columns right-aligned.
   *
   * @param string[] $headers
   * @param array<int, array<int, string>> $rows
   * @param int[] $numeric
   *   Zero-based indexes of the columns to right-align.
   */
  private function renderTable(array $headers, array $rows, array $numeric): void {
    $table = new Table($this->output());
    $table->setStyle('symfony-style-guide');
    $table->setHeaders($headers)->setRows($rows);
    $right = (new TableStyle())->setPadType(STR_PAD_LEFT);
    foreach ($numeric as $i) {
      $table->setColumnStyle($i, $right);
    }
    $table->render();
  }

  /**
   * Lists collected runs from runs/*.json, newest last.
   */
  #[CLI\Command(name: 'bench:list')]
  #[CLI\Argument(name: 'cell', description: 'Cell letter (B0..B9), raw workflow id, or empty for all.')]
  #[CLI\Argument(name: 'page', description: 'Manifest page key, or empty for all.')]
  #[CLI\Argument(name: 'model', description: 'Model substring filter, or empty for all.')]
  #[CLI\Option(name: 'out', description: 'Repo root (holds runs/). Defaults to two levels above the Drupal root.')]
  #[CLI\Usage(name: 'drush bench:list B5 small', description: 'List every collected run of B5 against the small page.')]
  #[CLI\Usage(name: 'drush bench:list', description: 'List every collected run.')]
  public function list(
    ?string $cell = NULL,
    ?string $page = NULL,
    ?string $model = NULL,
    array $options = ['out' => NULL],
  ): void {
    $outDir = $this->resolveOutDir($options['out']);
    $workflowId = $cell !== NULL ? ($this->harness->resolveWorkflowIds([$cell])[0] ?? NULL) : NULL;

    $files = glob($outDir . '/runs/*.json') ?: [];
    $rows = [];
    foreach ($files as $file) {
      $data = json_decode((string) file_get_contents($file), TRUE);
      if (!is_array($data)) {
        continue;
      }
      if ($workflowId !== NULL && ($data['workflow'] ?? NULL) !== $workflowId) {
        continue;
      }
      if ($page !== NULL && ($data['url_key'] ?? NULL) !== $page) {
        continue;
      }
      $modelLabel = implode(',', $data['models'] ?? []);
      if ($model !== NULL && $model !== '' && !str_contains($modelLabel, $model)) {
        continue;
      }
      $rows[] = [
        'ts' => $data['ts'] ?? '',
        'run' => substr((string) ($data['run_id'] ?? ''), -10),
        'tag' => (string) ($data['tag'] ?? ''),
        'status' => (string) ($data['pipeline_status'] ?? ''),
        'model' => $modelLabel,
        'sec' => (float) ($data['total_seconds'] ?? 0.0),
        'calls' => (int) ($data['llm_calls'] ?? 0),
        'in' => (int) ($data['input_tokens'] ?? 0),
        'out' => (int) ($data['output_tokens'] ?? 0),
        'cached' => (int) ($data['cached_tokens'] ?? 0),
        'usd' => (float) ($data['cost_usd'] ?? 0.0),
        'chars' => (int) ($data['output_chars'] ?? 0),
      ];
    }
    usort($rows, static fn (array $a, array $b): int => $a['ts'] <=> $b['ts']);

    $this->output()->writeln(sprintf(
      '%10s %-28s %-9s %-26s %7s %5s %7s %6s %6s %8s %6s',
      'run',
      'tag',
      'status',
      'model',
      'sec',
      'calls',
      'in',
      'out',
      'cached',
      'usd',
      'chars',
    ));
    foreach ($rows as $row) {
      $this->output()->writeln(sprintf(
        '%10s %-28s %-9s %-26s %7.1f %5d %7d %6d %6d %8.4f %6d',
        $row['run'],
        substr($row['tag'], 0, 28),
        $row['status'],
        substr($row['model'], 0, 26),
        $row['sec'],
        $row['calls'],
        $row['in'],
        $row['out'],
        $row['cached'],
        $row['usd'],
        $row['chars'],
      ));
    }
  }

  /**
   * Splits a comma list option/argument into a trimmed, non-empty array.
   *
   * @return string[]
   */
  /**
   * Prints a line only at -v or above.
   */
  /**
   * Lists the chat models the provider offers, i.e. what bench:run accepts.
   */
  #[CLI\Command(name: 'bench:models')]
  #[CLI\Option(name: 'provider', description: 'AI provider plugin id. Defaults to anthropic.')]
  #[CLI\Option(name: 'all', description: 'Every usable provider, keyed provider__model.')]
  #[CLI\Option(name: 'cells', description: 'List the benchmark cells instead of models.')]
  #[CLI\Usage(name: 'drush bench:models', description: 'Model ids the anthropic provider offers right now.')]
  #[CLI\Usage(name: 'drush bench:models --cells', description: 'The cells B0..B9 with one line each.')]
  public function models(array $options = ['provider' => self::DEFAULT_PROVIDER, 'all' => FALSE, 'cells' => FALSE]): void {
    if ($options['cells']) {
      foreach ($this->harness->cells() as $cell => $info) {
        $this->output()->writeln(sprintf('%-3s %-42s %s', $cell, $info['workflow'], $info['label']));
      }
      return;
    }
    $models = $options['all'] ? $this->harness->listAllModels() : $this->harness->listModels($options['provider']);
    foreach ($models as $id => $name) {
      $this->output()->writeln($name !== $id ? sprintf('%-40s %s', $id, $name) : $id);
    }
    if (!$options['all']) {
      $this->output()->writeln(sprintf("\n%d model(s) from provider %s. Run one with:  drush bench:run B3 <model> --pages=small --tag=<who-why>", count($models), $options['provider']));
    }
  }

  /**
   * Interactive front door: pick a model, cells, pages, reps and tag, then run.
   */
  #[CLI\Command(name: 'bench:wizard')]
  #[CLI\Option(name: 'provider', description: 'AI provider plugin id. Defaults to anthropic.')]
  #[CLI\Option(name: 'var', description: 'Runner var directory. Defaults to runner/var.')]
  #[CLI\Option(name: 'out', description: 'Repo root. Defaults to two levels above the Drupal root.')]
  #[CLI\Option(name: 'all-warnings', description: 'Also print the warnings a run is known to emit by design (see runner/README.md).')]
  #[CLI\Usage(name: 'drush bench:wizard', description: 'Answer a few questions, see the equivalent bench:run command, confirm, run.')]
  public function wizard(array $options = ['provider' => self::DEFAULT_PROVIDER, 'var' => NULL, 'out' => NULL, 'all-warnings' => FALSE]): void {
    $io = $this->io();
    $provider = $options['provider'];

    // --- model ---------------------------------------------------------
    $models = [];
    try {
      $models = $this->harness->listModels($provider);
    }
    catch (\RuntimeException $e) {
      $io->warning($e->getMessage());
    }
    $other = '(type another id)';
    $choices = $models ? array_combine(array_keys($models), array_map(
      static fn (string $id, string $name): string => $name !== $id ? "$id  ($name)" : $id,
      array_keys($models), array_values($models))) : [];
    $choices[$other] = $other;
    // Prefer a dated id: an undated alias can be repointed to a newer snapshot by the
    // provider, and the ledger records only the id requested. The scorer groups both
    // forms under one model family anyway.
    $dated = array_filter(array_keys($models), static fn (string $id): bool => (bool) preg_match('/-\d{8}$/', $id));
    $haiku = array_values(array_filter($dated, static fn (string $id): bool => str_contains($id, 'haiku')));
    $default = $haiku[0] ?? ($dated ? reset($dated) : array_key_first($choices));
    $model = (string) $io->choice(sprintf('Model (provider %s)', $provider), $choices, $default);
    if ($model === $other) {
      $model = (string) $io->ask('Model id', NULL, NULL, 'claude-sonnet-5', TRUE);
    }

    // --- cells ---------------------------------------------------------
    $cellChoices = [];
    foreach ($this->harness->cells() as $cell => $info) {
      $cellChoices[$cell] = sprintf('%s  %s', $cell, $info['label']);
    }
    $cells = (array) $io->choice('Cells (space to toggle, enter to accept)', $cellChoices, ['B3'], TRUE);
    if (!$cells) {
      throw new \RuntimeException('no cells selected');
    }

    // --- pages, reps, tag ------------------------------------------------
    $pages = (array) $io->choice('Pages', ['small' => 'small (2.6 k)', 'medium' => 'medium (7.3 k)', 'large' => 'large (13 k)'], ['small'], TRUE);
    if (!$pages) {
      throw new \RuntimeException('no pages selected');
    }
    $reps = (int) $io->ask('Repetitions per cell and page', '1', NULL, '1', TRUE, static function ($v): ?string {
      return ctype_digit((string) $v) && (int) $v >= 1 ? NULL : 'a whole number of 1 or more';
    });
    $who = trim((string) (getenv('BENCH_USER') ?: getenv('USER') ?: 'someone'));
    $tag = (string) $io->ask('Tag: who ran this and why (goes into the run id and the published table)', sprintf('%s-%s', $who, date('Ymd')), NULL, '', FALSE);

    // --- summary and confirm ------------------------------------------
    $cellList = implode(',', $cells);
    $pageList = implode(',', $pages);
    $command = sprintf('drush bench:run %s %s --pages=%s --reps=%d%s', $cellList, $model, $pageList, $reps, $tag !== '' ? ' --tag=' . escapeshellarg($tag) : '');
    $modelCells = count(array_filter($cells, static fn (string $c): bool => !in_array($c, ['B0', 'B1'], TRUE)));
    $io->writeln('');
    $io->writeln(sprintf('%d run(s): %d cell(s) x %d page(s) x %d rep(s); %d of the cells call %s.',
      count($cells) * count($pages) * $reps, count($cells), count($pages), $reps, $modelCells * count($pages) * $reps, $model));
    $io->writeln('Equivalent command:  ' . $command);
    if (!$io->confirm('Run it now?', TRUE)) {
      $io->writeln('Not run. The command above can be run later as is.');
      return;
    }
    $this->run($cellList, $model, [
      'pages' => $pageList,
      'reps' => $reps,
      'tag' => $tag !== '' ? $tag : NULL,
      'provider' => $provider,
      'prompt' => self::DEFAULT_PROMPT,
      'critic' => self::DEFAULT_CRITIC,
      'base' => NULL,
      'corpus' => NULL,
      'var' => $options['var'],
      'out' => $options['out'],
      // The wizard offered the provider's own list; a typed id is the user's call.
      'force' => TRUE,
      'all-warnings' => (bool) ($options['all-warnings'] ?? FALSE),
    ]);
  }

  /**
   * Refuses a model id the provider does not list, naming what it does.
   *
   * When the list itself cannot be fetched the run proceeds with a warning:
   * a catalogue outage must not block a benchmark.
   */
  private function assertKnownModel(string $model, string $provider): void {
    try {
      $models = $this->harness->listModels($provider);
    }
    catch (\RuntimeException $e) {
      $this->io()->warning('model list unavailable, not validating: ' . $e->getMessage());
      return;
    }
    if (isset($models[$model])) {
      return;
    }
    $known = implode("\n  ", array_keys($models));
    throw new \RuntimeException(sprintf(
      "provider %s does not list a model \"%s\". It offers:\n  %s\nPass --force to run anyway (a model newer than the catalogue, or a control-only run).",
      $provider, $model, $known,
    ));
  }

  private function verbose(string $line): void {
    if ($this->output()->isVerbose()) {
      $this->output()->writeln($line);
    }
  }

  /**
   * Returns the launch progress callback: one line per run, opened when the
   * run starts and closed when it ends, so a long agent cell shows it is alive.
   */
  private function progressPrinter(): callable {
    return function (string $event, array $info): void {
      if ($event === 'start') {
        $cell = $this->cellLetters()[$info['workflow']] ?? $info['workflow'];
        $this->output()->write(sprintf('run      %-4s %-7s r%-2d ... ', $cell, $info['url_key'], $info['rep']));
        return;
      }
      $status = $info['launch_status'];
      $ok = in_array($status, ['completed', 'success'], TRUE);
      $this->output()->writeln(sprintf(
        '%s %.1fs%s',
        $ok ? 'completed' : strtoupper((string) $status),
        $info['wall_seconds'] ?? 0.0,
        !empty($info['launch_error']) ? '  ' . $info['launch_error'] : '',
      ));
    };
  }

  private function splitList(string $value): array {
    return array_values(array_filter(array_map('trim', explode(',', $value))));
  }

  /**
   * Resolves the bench site base URL: option, then env, then built-in default.
   */
  private function resolveBase(?string $base): string {
    if (!empty($base)) {
      return $base;
    }
    $env = getenv('BENCH_BASE');
    return $env !== FALSE && $env !== '' ? $env : self::DEFAULT_BASE;
  }

  /**
   * Resolves the corpus version: option, then env, then built-in default.
   */
  private function resolveCorpus(?string $corpus): string {
    if (!empty($corpus)) {
      return $corpus;
    }
    $env = getenv('BENCH_CORPUS');
    return $env !== FALSE && $env !== '' ? $env : self::DEFAULT_CORPUS;
  }

  /**
   * Resolves the runner var directory: option, else runner/var.
   */
  private function resolveVarDir(?string $var): string {
    return $var ?: dirname(DRUPAL_ROOT) . '/var';
  }

  /**
   * Resolves the repo root: option, else two levels above the Drupal root.
   */
  private function resolveOutDir(?string $out): string {
    return $out ?: dirname(DRUPAL_ROOT, 2);
  }


  /**
   * Starts dropping the warnings a run is known to print, unless asked not to.
   *
   * The list, and why each entry is benign, is KnownWarnings and the
   * "Warnings a run prints" table in runner/README.md. Everything not on the
   * list still prints, so a real warning stands out instead of scrolling past
   * between a dozen expected ones.
   */
  private function quietKnownWarnings(bool $showAll): void {
    if ($showAll) {
      $this->knownWarnings->deactivate();
      return;
    }
    $this->knownWarnings->activate();
  }

  /**
   * Prints one line saying what was dropped, so nothing disappears silently.
   */
  private function reportKnownWarnings(): void {
    $summary = $this->knownWarnings->summary();
    if ($summary !== NULL) {
      $this->output()->writeln($summary);
    }
    $this->knownWarnings->deactivate();
  }

}
