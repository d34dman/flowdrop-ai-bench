<?php

declare(strict_types=1);

namespace Drupal\flowdrop_ai_bench\Drush\Commands;

use Drupal\flowdrop_ai_bench\Service\Harness;
use Drush\Attributes as CLI;
use Drush\Commands\AutowireTrait;
use Drush\Commands\DrushCommands;

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

  private const DEFAULT_CRITIC = 'prompt/critic.v1.md';

  private const DEFAULT_PROVIDER = 'anthropic';

  public function __construct(
    private readonly Harness $harness,
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
  #[CLI\Usage(name: 'drush bench:launch B5,B8 --tag=b5-b8-sonnet5', description: 'Launch the react-agent and react-with-tools cells against every page, once each.')]
  public function launch(string $cells, array $options = [
    'pages' => self::DEFAULT_PAGES,
    'reps' => 1,
    'tag' => NULL,
    'model' => NULL,
    'base' => NULL,
    'corpus' => NULL,
    'var' => NULL,
  ]): void {
    if (empty($options['tag'])) {
      throw new \RuntimeException('bench:launch requires --tag: it is how runs are found later.');
    }

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
  }

  /**
   * Rewrites the per-run JSON and Markdown output for every ledger line.
   */
  #[CLI\Command(name: 'bench:collect')]
  #[CLI\Option(name: 'var', description: 'Runner var directory (holds the ledger). Defaults to runner/var.')]
  #[CLI\Option(name: 'out', description: 'Repo root (holds runs/ and outputs/). Defaults to two levels above the Drupal root.')]
  #[CLI\Usage(name: 'drush bench:collect', description: 'Recompute metrics for every run in the ledger.')]
  public function collect(array $options = ['var' => NULL, 'out' => NULL]): void {
    $varDir = $this->resolveVarDir($options['var']);
    $outDir = $this->resolveOutDir($options['out']);

    $result = $this->harness->collect($varDir . '/runs.jsonl', $outDir . '/runs', $outDir . '/outputs');

    foreach ($result['skipped'] as $skip) {
      $this->output()->writeln(sprintf('  !! pipeline %s missing for %s', $skip['pipeline_id'] ?? '', $skip['run_id']));
    }
    $this->output()->writeln(sprintf(
      "\ncollected %d run(s) -> %s/runs/*.json and %s/outputs/*.md",
      count($result['collected']),
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
  #[CLI\Option(name: 'out', description: 'Repo root. Defaults to two levels above the Drupal root.')]
  #[CLI\Usage(name: 'drush bench:run B5,B8 claude-sonnet-5', description: 'Set the prompt and model, launch B5 and B8 against every page, then collect metrics.')]
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
  ]): void {
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

    $collected = $this->harness->collect($varDir . '/runs.jsonl', $outDir . '/runs', $outDir . '/outputs');
    $this->output()->writeln(sprintf('collect  %d run(s) in the ledger re-derived into runs/ and outputs/', count($collected['collected'])));

    $this->output()->writeln(sprintf(
      "\n%-52s %-10s %7s %6s %8s %8s %10s %7s",
      'run_id',
      'status',
      'sec',
      'calls',
      'in',
      'out',
      'cost_usd',
      'chars',
    ));
    foreach ($runIds as $runId) {
      $path = "$outDir/runs/$runId.json";
      if (!is_file($path)) {
        continue;
      }
      $data = json_decode((string) file_get_contents($path), TRUE);
      $this->output()->writeln(sprintf(
        "%-52s %-10s %7.1f %6d %8d %8d %10.4f %7d",
        $runId,
        $data['pipeline_status'] ?? $data['launch_status'] ?? '',
        $data['total_seconds'] ?? 0.0,
        $data['llm_calls'] ?? 0,
        $data['input_tokens'] ?? 0,
        $data['output_tokens'] ?? 0,
        $data['cost_usd'] ?? 0.0,
        $data['output_chars'] ?? 0,
      ));
    }
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
        $this->output()->write(sprintf('run      %-40s %-7s r%-2d ... ', $info['workflow'], $info['url_key'], $info['rep']));
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

}
