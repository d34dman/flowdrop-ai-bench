<?php

declare(strict_types=1);

namespace Drupal\flowdrop_ai_bench\Service;

use Drupal\Component\Uuid\UuidInterface;
use Drupal\Core\Database\Connection;
use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Session\AccountSwitcherInterface;
use Drupal\flowdrop_ai_bench\BenchRunContext;
use Drupal\flowdrop_workflow_executor\DTO\LaunchOptions;
use GuzzleHttp\ClientInterface;
use Symfony\Component\DependencyInjection\Attribute\Autowire;

/**
 * Shared logic for the bench:* Drush commands.
 *
 * Ports demos/fd-drupal-demo's scratchpad/bench/*.php harness scripts (drush
 * php:script one-offs) into a reusable, testable service. The benchmark
 * corpus and prompt are fetched over HTTP from the flowdrop-ai-bench GitHub
 * Pages site (or a local override), so a run is reproducible from a base URL
 * and corpus version alone, and the ledger records exactly which corpus
 * version and prompt hash it used.
 */
class Harness {

  /**
   * Bumped whenever the ledger record shape changes.
   */
  public const HARNESS_VERSION = '3.1.0';

  /**
   * Cell letter to workflow id, per the retired run_cell.sh table.
   *
   * B5a (bench_5a_react_agent_naive) is retired and deliberately absent: one
   * prompt now covers every ReAct variant, so the "naive prompt" cell no
   * longer exists.
   */
  private const CELL_WORKFLOWS = [
    'B0' => 'bench_0_floor',
    'B1' => 'bench_1_reference',
    'B2' => 'bench_2_raw_html_llm',
    'B3' => 'bench_3_markdown_llm',
    'B4' => 'bench_4_ai_agent_tool',
    'B5' => 'bench_5_react_agent',
    'B6' => 'bench_6_agent_autonomous',
    'B7' => 'bench_7_react_optimized',
    'B8' => 'bench_8_react_with_tools_in_parent',
    'B9' => 'bench_9_reflexion_with_tools_in_parent',
  ];

  /**
   * Workflows whose nodes carry the benchmark's model-facing system prompt.
   */
  private const PROMPT_WORKFLOWS = [
    'bench_2_raw_html_llm', 'bench_3_markdown_llm', 'bench_5_react_agent',
    'bench_7_react_optimized', 'bench_8_react_with_tools_in_parent',
    'bench_9_reflexion_with_tools_in_parent',
    // Sub-workflows whose reason node carries its own systemPrompt.
    'react_agent_with_tools', 'react_agent_with_optimized_tools', 'react_agent_with_optimized_tools_v2',
  ];

  /**
   * ai_agent entities whose system_prompt mirrors the same benchmark prompt.
   */
  private const PROMPT_AGENTS = ['agent_w81pomww', 'agent_bench_autonomous'];

  /**
   * Workflows whose nodes carry the model id under test.
   */
  private const MODEL_WORKFLOWS = [
    'bench_2_raw_html_llm', 'bench_3_markdown_llm', 'bench_4_ai_agent_tool',
    'bench_5_react_agent', 'bench_6_agent_autonomous',
    'react_agent_with_tools', 'react_agent_with_optimized_tools', 'bench_7_react_optimized',
    'react_agent_engine', 'reflexion_agent_engine', 'react_agent_with_optimized_tools_v2',
    'bench_8_react_with_tools_in_parent', 'bench_9_reflexion_with_tools_in_parent',
  ];

  public function __construct(
    private readonly ClientInterface $httpClient,
    private readonly EntityTypeManagerInterface $entityTypeManager,
    private readonly Connection $database,
    private readonly UuidInterface $uuid,
    private readonly AccountSwitcherInterface $accountSwitcher,
    private readonly BenchRunContext $runContext,
    #[Autowire(service: 'flowdrop_workflow_executor.launcher')]
    private readonly object $launcher,
  ) {}

  /**
   * Resolves a list of cell letters (or raw workflow ids) to workflow ids.
   *
   * @param string[] $cells
   *   Cell letters such as "B5", or workflow ids passed through unchanged.
   *
   * @return string[]
   *   Workflow ids in the same order, one per input cell.
   */
  public function resolveWorkflowIds(array $cells): array {
    return array_map(
      static fn (string $cell): string => self::CELL_WORKFLOWS[$cell] ?? $cell,
      $cells,
    );
  }

  /**
   * Fetches a path relative to the bench base URL, caching the raw response.
   */
  public function fetch(string $relativePath, string $base, string $cacheDir): string {
    $url = rtrim($base, '/') . '/' . ltrim($relativePath, '/');
    $body = (string) $this->httpClient->request('GET', $url, ['timeout' => 30])->getBody()->getContents();
    if ($body === '') {
      throw new \RuntimeException("empty response from $url");
    }
    if (!is_dir($cacheDir) && !mkdir($cacheDir, 0777, TRUE) && !is_dir($cacheDir)) {
      throw new \RuntimeException("cannot create cache directory: $cacheDir");
    }
    file_put_contents($cacheDir . '/' . str_replace('/', '__', $relativePath), $body);
    return $body;
  }

  /**
   * Fetches and decodes one corpus version's manifest.
   */
  public function manifest(string $corpusVersion, string $base, string $cacheDir): array {
    $manifest = json_decode($this->fetch("corpus/$corpusVersion/manifest.json", $base, $cacheDir), TRUE);
    if (!isset($manifest['pages'])) {
      throw new \RuntimeException('manifest has no pages');
    }
    return $manifest;
  }

  /**
   * Fetches a prompt file and splits it into [front-matter, body, sha256].
   *
   * @return array{0: array<string, mixed>, 1: string, 2: string}
   */
  public function promptFile(string $relativePath, string $base, string $cacheDir): array {
    $text = $this->fetch($relativePath, $base, $cacheDir);
    $meta = [];
    $body = $text;
    if (preg_match('/\A---\n(.*?)\n---\n(.*)\z/s', $text, $matches)) {
      foreach (explode("\n", $matches[1]) as $line) {
        if (!str_contains($line, ':')) {
          continue;
        }
        [$key, $value] = explode(':', $line, 2);
        $value = trim($value);
        if (str_starts_with($value, '[')) {
          $value = array_map('trim', explode(',', trim($value, '[]')));
        }
        else {
          $value = trim($value, '"');
        }
        $meta[trim($key)] = $value;
      }
      $body = $matches[2];
    }
    return [$meta, rtrim($body, "\n"), hash('sha256', $text)];
  }

  /**
   * Reads the installed flowdrop version and commit from a composer.lock.
   */
  public function flowdropVersion(string $composerLockPath): string {
    $lock = json_decode((string) file_get_contents($composerLockPath), TRUE);
    foreach ($lock['packages'] ?? [] as $package) {
      if ($package['name'] === 'drupal/flowdrop') {
        return $package['version'] . '@' . substr($package['source']['reference'] ?? '', 0, 12);
      }
    }
    return 'unknown';
  }

  /**
   * Writes the benchmark prompt into every model-calling cell.
   *
   * The prompt lives in three unrelated config shapes, and a cell that keeps
   * an old prompt silently turns a workflow comparison into a prompt
   * comparison:
   *   - flowdrop_ai_provider_chat / flowdrop_node_processor_reason nodes ->
   *     config.systemPrompt (and the systemPrompt input port must be
   *     un-exposed: an exposed, unconnected port resolves to '' and shadows
   *     the configured value).
   *   - react / reflexion engine nodes -> config.system_prompt (reflexion
   *     also has config.critic_prompt, rendered from the critic template).
   *   - ai_agent entities -> system_prompt.
   *
   * @return array{
   *   prompt_rel: string, critic_rel: string, prompt_chars: int,
   *   prompt_sha256: string, critic_sha256: string, glyph: string|null,
   *   touched: array<int, array<string, mixed>>,
   * }
   */
  public function setPrompt(string $promptRel, string $criticRel, string $base, string $cacheDir): array {
    [$meta, $prompt, $promptSha] = $this->promptFile($promptRel, $base, $cacheDir);
    [, $criticTemplate, $criticSha] = $this->promptFile($criticRel, $base, $cacheDir);

    $competitors = $meta['competitors'] ?? [];
    $competitorList = $competitors
      ? implode(', ', array_slice($competitors, 0, -1)) . ' and ' . end($competitors)
      : '';
    $critic = str_replace(
      ['{{competitors}}', '{{glyph}}'],
      [$competitorList, $meta['glyph'] ?? ''],
      $criticTemplate,
    );

    $touched = [];
    $workflowStorage = $this->entityTypeManager->getStorage('flowdrop_workflow');
    foreach (self::PROMPT_WORKFLOWS as $workflowId) {
      $workflow = $workflowStorage->load($workflowId);
      if (!$workflow) {
        $touched[] = ['type' => 'workflow', 'id' => $workflowId, 'field' => NULL, 'note' => 'missing'];
        continue;
      }
      $nodes = $workflow->get('nodes');
      $changed = FALSE;
      foreach ($nodes as &$node) {
        $nodeType = $node['data']['metadata']['node_type_id'] ?? '';
        $config = &$node['data']['config'];
        if (preg_match('/ai_provider_chat|processor_reason/', $nodeType)) {
          $config['systemPrompt'] = $prompt;
          foreach ($config['ports']['inputs'] ?? [] as &$port) {
            if (($port['id'] ?? '') === 'systemPrompt') {
              $port['exposed'] = FALSE;
            }
          }
          unset($port);
          $changed = TRUE;
          $touched[] = ['type' => 'workflow', 'id' => $workflowId, 'node' => $node['id'], 'field' => 'systemPrompt'];
        }
        if (preg_match('/react_agent|reflexion_agent/', $nodeType) && array_key_exists('system_prompt', $config)) {
          $config['system_prompt'] = $prompt;
          $changed = TRUE;
          $touched[] = ['type' => 'workflow', 'id' => $workflowId, 'node' => $node['id'], 'field' => 'system_prompt'];
          if (array_key_exists('critic_prompt', $config)) {
            $config['critic_prompt'] = $critic;
            $touched[] = ['type' => 'workflow', 'id' => $workflowId, 'node' => $node['id'], 'field' => 'critic_prompt'];
          }
        }
        unset($config);
      }
      unset($node);
      if ($changed) {
        $workflow->set('nodes', $nodes)->save();
      }
    }

    $agentStorage = $this->entityTypeManager->getStorage('ai_agent');
    foreach (self::PROMPT_AGENTS as $agentId) {
      $agent = $agentStorage->load($agentId);
      if (!$agent) {
        $touched[] = ['type' => 'ai_agent', 'id' => $agentId, 'field' => NULL, 'note' => 'missing'];
        continue;
      }
      $agent->set('system_prompt', $prompt)->save();
      $touched[] = ['type' => 'ai_agent', 'id' => $agentId, 'field' => 'system_prompt'];
    }

    return [
      'prompt_rel' => $promptRel,
      'critic_rel' => $criticRel,
      'prompt_chars' => strlen($prompt),
      'prompt_sha256' => $promptSha,
      'critic_sha256' => $criticSha,
      'glyph' => $meta['glyph'] ?? NULL,
      'touched' => $touched,
    ];
  }

  /**
   * Points every model call in the benchmark at one model.
   *
   * The model is configured in two unrelated shapes, and missing either
   * produces a matrix that silently mixes models:
   *   - flowdrop_ai_provider_chat / flowdrop_node_processor_reason nodes ->
   *     config.model (bare model id).
   *   - ai_agents_executor nodes -> config.llm_model ("provider__model").
   *
   * @return array{
   *   model: string, provider: string, updated_workflows: int,
   *   touched: array<int, array<string, mixed>>,
   * }
   */
  public function setModel(string $model, string $provider): array {
    $storage = $this->entityTypeManager->getStorage('flowdrop_workflow');
    $touched = [];
    $updated = 0;
    foreach (self::MODEL_WORKFLOWS as $workflowId) {
      $workflow = $storage->load($workflowId);
      if (!$workflow) {
        $touched[] = ['id' => $workflowId, 'field' => NULL, 'note' => 'missing'];
        continue;
      }
      $nodes = $workflow->get('nodes');
      $changed = FALSE;
      foreach ($nodes as &$node) {
        $nodeType = $node['data']['metadata']['node_type_id'] ?? '';
        if (preg_match('/ai_provider_chat|processor_reason/', $nodeType)) {
          if (($node['data']['config']['model'] ?? NULL) !== $model) {
            $node['data']['config']['model'] = $model;
            $changed = TRUE;
            $touched[] = ['id' => $workflowId, 'node' => $node['id'], 'field' => 'model', 'value' => $model];
          }
        }
        if (str_contains($nodeType, 'ai_agents_executor')) {
          $simple = $provider . '__' . $model;
          if (($node['data']['config']['llm_model'] ?? NULL) !== $simple) {
            $node['data']['config']['llm_model'] = $simple;
            $changed = TRUE;
            $touched[] = ['id' => $workflowId, 'node' => $node['id'], 'field' => 'llm_model', 'value' => $simple];
          }
        }
      }
      unset($node);
      if ($changed) {
        $workflow->set('nodes', $nodes)->save();
        $updated++;
      }
    }
    return [
      'model' => $model,
      'provider' => $provider,
      'updated_workflows' => $updated,
      'touched' => $touched,
    ];
  }

  /**
   * Reads the model configured on the bench_3 markdown-LLM chat node.
   *
   * Used as the fallback for bench:launch when no --model is given.
   */
  public function detectModel(): ?string {
    $workflow = $this->entityTypeManager->getStorage('flowdrop_workflow')->load('bench_3_markdown_llm');
    if (!$workflow) {
      return NULL;
    }
    foreach ($workflow->get('nodes') as $node) {
      $nodeType = $node['data']['metadata']['node_type_id'] ?? '';
      if (preg_match('/ai_provider_chat|processor_reason/', $nodeType)) {
        return $node['data']['config']['model'] ?? NULL;
      }
    }
    return NULL;
  }

  /**
   * Launches cells against pages from the manifest, appending to the ledger.
   *
   * The ledger is deliberately thin: run identity, the pipeline it produced
   * and the context uuid its model calls carried. Everything else is derived
   * later by collect() from stored state, so a run never has to be watched.
   *
   * wall_seconds is the one thing that cannot be derived — the stored job
   * stamps are second-resolution, and orchestrator overhead is a sub-second
   * quantity — so the launch is timed here and carried through.
   *
   * @param string[] $workflowIds
   *   Workflow ids to launch, already resolved from cell letters.
   * @param string[] $pageKeys
   *   Manifest page keys (e.g. small, medium, large).
   *
   * @return array<int, array<string, mixed>>
   *   One ledger record per run, in launch order.
   */
  /**
   * Returns the tag segment of a run id: "__<tag>" or "" when there is none.
   *
   * Lower-cased, anything but [a-z0-9] collapsed to "-", at most 24 characters.
   * Callers pass NULL for a defaulted tag so the id is not padded with the cell
   * and model it already names.
   */
  public static function runIdTag(?string $tag): string {
    if ($tag === NULL || $tag === '') {
      return '';
    }
    $clean = trim(preg_replace('/[^a-z0-9]+/', '-', strtolower($tag)) ?? '', '-');
    $clean = rtrim(substr($clean, 0, 24), '-');
    return $clean === '' ? '' : '__' . $clean;
  }

  public function launch(
    array $workflowIds,
    array $pageKeys,
    int $reps,
    string $tag,
    ?string $model,
    string $corpusVersion,
    string $base,
    string $cacheDir,
    string $ledgerPath,
    ?callable $progress = NULL,
    ?string $idTag = NULL,
  ): array {
    $manifest = $this->manifest($corpusVersion, $base, $cacheDir);
    $idTagPart = self::runIdTag($idTag);
    $urls = array_map(static fn (array $page): string => $page['url'], $manifest['pages']);
    [$promptMeta, , $promptSha] = $this->promptFile($manifest['prompt'] ?? 'prompt/redact.v1.md', $base, $cacheDir);
    $flowdropVersion = $this->flowdropVersion(dirname(DRUPAL_ROOT) . '/composer.lock');
    $model ??= $this->detectModel() ?? 'unknown';

    $ledgerDir = dirname($ledgerPath);
    if (!is_dir($ledgerDir) && !mkdir($ledgerDir, 0777, TRUE) && !is_dir($ledgerDir)) {
      throw new \RuntimeException("cannot create ledger directory: $ledgerDir");
    }

    $userStorage = $this->entityTypeManager->getStorage('user');
    $workflowStorage = $this->entityTypeManager->getStorage('flowdrop_workflow');

    // drush commands execute as anonymous by default, whose quota is a small
    // shared ceiling meant for public traffic; a benchmark exhausts it
    // mid-matrix.
    $this->accountSwitcher->switchTo($userStorage->load(1));

    $records = [];
    try {
      $handle = fopen($ledgerPath, 'a');
      if ($handle === FALSE) {
        throw new \RuntimeException("cannot append to $ledgerPath");
      }
      try {
        foreach (range(1, $reps) as $rep) {
          foreach ($pageKeys as $urlKey) {
            $url = $urls[$urlKey] ?? $urlKey;
            foreach ($workflowIds as $workflowId) {
              $workflow = $workflowStorage->load($workflowId);
              if (!$workflow) {
                $records[] = [
                  'workflow' => $workflowId,
                  'url_key' => $urlKey,
                  'rep' => $rep,
                  'launch_status' => 'error',
                  'launch_error' => 'missing workflow',
                  'tag' => $tag,
                ];
                continue;
              }

              // The id must never collide across contributors, who add runs to the
              // same dataset by pull request: a random suffix guarantees that, the
              // tag (when the user gave one) is only there for a human reading the
              // directory. See runIdTag().
              $runId = sprintf('%s__%s__r%d__%d%s__%s', $workflowId, $urlKey, $rep, time(), $idTagPart, bin2hex(random_bytes(3)));
              if ($progress) {
                $progress('start', ['run_id' => $runId, 'workflow' => $workflowId, 'url_key' => $urlKey, 'rep' => $rep]);
              }
              $runUuid = $this->uuid->generate();
              $this->runContext->set($runUuid);

              $start = microtime(TRUE);
              $pipelineId = NULL;
              $status = 'error';
              $error = NULL;
              try {
                $result = $this->launcher->launch(
                  $workflow,
                  ['url' => $url],
                  new LaunchOptions(wait: TRUE),
                );
                $pipelineId = $result->pipelineId;
                $status = $result->status;
              }
              catch (\Throwable $e) {
                $error = $e->getMessage();
              }
              $wallSeconds = microtime(TRUE) - $start;
              $this->runContext->set(NULL);

              $record = [
                'run_id' => $runId,
                'workflow' => $workflowId,
                'url_key' => $urlKey,
                'url' => $url,
                'corpus_version' => $manifest['version'],
                'page_sha256' => $manifest['pages'][$urlKey]['sha256'] ?? NULL,
                'prompt_sha256' => $promptSha,
                'glyph' => $promptMeta['glyph'] ?? NULL,
                'flowdrop_version' => $flowdropVersion,
                'harness_version' => self::HARNESS_VERSION,
                'model' => $model,
                'rep' => $rep,
                'pipeline_id' => (string) $pipelineId,
                'context_uuid' => $runUuid,
                'wall_seconds' => round($wallSeconds, 4),
                'launch_status' => $status,
                'launch_error' => $error,
                'tag' => $tag,
                'ts' => gmdate('c'),
              ];
              fwrite($handle, json_encode($record, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . "\n");
              fflush($handle);
              $records[] = $record;
              if ($progress) {
                $progress('done', $record);
              }
            }
          }
        }
      }
      finally {
        fclose($handle);
      }
    }
    finally {
      $this->accountSwitcher->switchBack();
    }

    return $records;
  }

  /**
   * Derives every benchmark metric from what FlowDrop and ai_metering stored.
   *
   * Nothing here observes a run as it happens, so runs may be launched in any
   * order, in parallel, or days earlier, and re-collected as often as wanted
   * without spending anything. Timing comes from each job's
   * execution_time_us (microseconds) rather than the second-resolution
   * started/completed stamps.
   *
   * A ledger line whose pipeline is missing is skipped with a warning: it
   * never overwrites a previously collected run/output file for that id.
   *
   * @return array{
   *   collected: array<int, array<string, mixed>>,
   *   skipped: array<int, array{run_id: string|null, pipeline_id: mixed}>,
   * }
   */
  public function collect(string $ledgerPath, string $runsDir, string $outputsDir): array {
    $collected = [];
    $skipped = [];
    if (!is_file($ledgerPath)) {
      return ['collected' => $collected, 'skipped' => $skipped];
    }
    foreach ([$runsDir, $outputsDir] as $dir) {
      if (!is_dir($dir) && !mkdir($dir, 0777, TRUE) && !is_dir($dir)) {
        throw new \RuntimeException("cannot create output directory: $dir");
      }
    }

    // Hand-written notes about individual runs, keyed by run id. They record
    // what the stored state cannot: chiefly that a failed run's work was
    // retrievable from job output even though the engine delivered nothing.
    // Kept out of the derived record so re-collection never erases them.
    $annotations = [];
    $annotationsPath = dirname($ledgerPath) . '/annotations.jsonl';
    if (is_file($annotationsPath)) {
      foreach (file($annotationsPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $annotation = json_decode($line, TRUE);
        if (isset($annotation['run_id'])) {
          $annotations[$annotation['run_id']][] = $annotation;
        }
      }
    }

    $pipelineStorage = $this->entityTypeManager->getStorage('flowdrop_pipeline');
    // Node types whose time is model time; everything else is the graph's
    // own work.
    $isAiNode = static fn (string $nodeType): bool => (bool) preg_match(
      '/ai_provider_chat|processor_reason|ai_agents_executor|react_agent/',
      $nodeType,
    );

    foreach (file($ledgerPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
      $run = json_decode($line, TRUE);
      if (!is_array($run) || empty($run['run_id'])) {
        continue;
      }
      $pipeline = !empty($run['pipeline_id']) ? $pipelineStorage->load($run['pipeline_id']) : NULL;
      if (!$pipeline) {
        $skipped[] = ['run_id' => $run['run_id'], 'pipeline_id' => $run['pipeline_id'] ?? NULL];
        continue;
      }

      // --- timing and per-node trail, from stored job metadata -----------
      $nodes = [];
      $aiUs = $deterministicUs = 0;
      $retries = 0;
      // Bytes FlowDrop had to serialise and store for this run. Orchestrator
      // overhead tracks this far more closely than it tracks node count.
      $payloadBytes = 0;
      $output = NULL;
      $failed = [];
      foreach ($pipeline->get('job_id') as $reference) {
        $job = $reference->entity;
        if (!$job) {
          continue;
        }
        $nodeType = (string) ($job->get('node_type_id')->target_id ?? '?');
        $metadata = $job->getMetadata();
        $microseconds = isset($metadata['execution_time_us']) ? (int) $metadata['execution_time_us'] : NULL;
        $status = (string) $job->get('status')->value;
        $retries += (int) $job->get('retry_count')->value;
        $payloadBytes += strlen((string) $job->get('input_data')->value)
          + strlen((string) $job->get('output_data')->value);

        if ($microseconds !== NULL) {
          if ($isAiNode($nodeType)) {
            $aiUs += $microseconds;
          }
          else {
            $deterministicUs += $microseconds;
          }
        }
        if ($status !== 'completed') {
          $failed[] = $nodeType . ':' . $status;
        }
        $nodes[] = [
          'node_type' => $nodeType,
          'status' => $status,
          'seconds' => $microseconds !== NULL ? round($microseconds / 1e6, 3) : NULL,
          'is_ai' => $isAiNode($nodeType),
          'error' => $job->get('error_message')->value ?: NULL,
        ];
        if (str_contains($nodeType, 'output')) {
          $data = json_decode((string) $job->get('output_data')->value, TRUE);
          // A workflow may end in more than one output node (B8 has
          // chat_output and a text_output capped at 1000 chars). Keep the
          // longest, not the last.
          foreach (['message', 'text'] as $key) {
            if (!empty($data[$key]) && strlen($data[$key]) > strlen((string) $output)) {
              $output = $data[$key];
            }
          }
        }
      }

      // --- tokens and cost, by the tag each call carried ------------------
      $rows = $this->database->query(
        'SELECT model_id, input_tokens, output_tokens, cached_tokens,
          estimated_cost_usd, status FROM {ai_metering_usage} WHERE context_id = :c ORDER BY id',
        [':c' => $run['context_uuid'] ?? NULL],
      )->fetchAll();
      $inputTokens = $outputTokens = $cachedTokens = 0;
      $cost = 0.0;
      $models = [];
      foreach ($rows as $row) {
        $inputTokens += (int) $row->input_tokens;
        $outputTokens += (int) $row->output_tokens;
        $cachedTokens += (int) $row->cached_tokens;
        $cost += (float) $row->estimated_cost_usd;
        $models[$row->model_id] = TRUE;
      }

      if ($output !== NULL) {
        file_put_contents("$outputsDir/{$run['run_id']}.md", $output);
      }

      $record = $run + [
        'pipeline_status' => $pipeline->getStatus(),
        'failed_nodes' => $failed,
        'job_count' => count($nodes),
        'payload_bytes' => $payloadBytes,
        'total_seconds' => round(($aiUs + $deterministicUs) / 1e6, 3),
        'ai_seconds' => round($aiUs / 1e6, 3),
        'deterministic_seconds' => round($deterministicUs / 1e6, 3),
        'llm_calls' => count($rows),
        'models' => array_keys($models),
        'input_tokens' => $inputTokens,
        'output_tokens' => $outputTokens,
        'cached_tokens' => $cachedTokens,
        'cost_usd' => round($cost, 6),
        'retries' => $retries,
        'output_chars' => $output !== NULL ? strlen($output) : NULL,
        'nodes' => $nodes,
        // The status stays whatever the engine reported; an annotation never
        // upgrades a failed run into a successful one.
        'annotations' => $annotations[$run['run_id']] ?? [],
      ];

      // One file per run is the unit of contribution to flowdrop-ai-bench:
      // two contributors never touch the same line, and a run is reviewable
      // on its own.
      file_put_contents(
        "$runsDir/{$run['run_id']}.json",
        json_encode($record, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n",
      );
      $collected[] = $record;
    }

    return ['collected' => $collected, 'skipped' => $skipped];
  }

}
