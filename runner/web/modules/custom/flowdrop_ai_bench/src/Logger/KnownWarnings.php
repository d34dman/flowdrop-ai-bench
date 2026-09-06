<?php

declare(strict_types=1);

namespace Drupal\flowdrop_ai_bench\Logger;

use Drupal\Core\Logger\RfcLogLevel;

/**
 * The warnings a benchmark run is known to print and that mean nothing is wrong.
 *
 * FlowDrop logs each of these at warning level because, in a workflow somebody
 * is still building, they may point at a mistake. In the benchmark cells they
 * are the documented, intended shape of the workflow (see "Warnings a run
 * prints" in runner/README.md), and at several per loop iteration they bury
 * the one line an operator would need to see. While a bench:* command runs,
 * FilteringDrushLog drops a warning whose message matches one of these and
 * counts it; the command prints the counts once at the end. Anything else,
 * including these same texts at error level, passes through untouched.
 *
 * Patterns match the message *template*, before placeholders are filled in,
 * so they pin the exact log call in FlowDrop and cannot match a coincidentally
 * similar message from elsewhere.
 */
final class KnownWarnings {

  /**
   * Regex on the message template => short label used in the summary.
   *
   * @var array<string, string>
   */
  private const KNOWN = [
    // flowdrop_pipeline JobGenerationService: the BR-6 observability floor. A
    // loop consumer read a producer's value from an earlier iteration; the
    // value is delivered regardless. Expected for the conversation buffers
    // feeding message assembly in B5, B7, B8, B9.
    '/^Cross-iteration data read on pipeline @pipeline:/' => 'cross-iteration read (BR-6, observability only)',
    // flowdrop_runtime ToolGraphFlattener: in the "tools in the parent" cells
    // (B8, B9) the engine's own ToolBox is empty by design; the tools arrive
    // from the parent workflow as an execution argument.
    '/^ToolBox @node has no tools wired into it\.$/' => 'empty ToolBox (tools arrive from the parent)',
    // flowdrop_stategraph StateGraphOrchestrator only ("on node"): the
    // Reflexion engine (B9) has two legitimate re-entry paths into the actor
    // loop wired to one trigger port; last executor wins by definition. The
    // sync/async orchestrators' "on job" variant is not listed: without a loop
    // it is more likely a wiring mistake and stays visible.
    "/^Multiple sources target port '@port' on node '@node'; keeping value /" => "loop_back fan-in (last executor wins)",
  ];

  private bool $active = FALSE;

  /**
   * @var array<string, int>
   */
  private array $dropped = [];

  public function activate(): void {
    $this->active = TRUE;
    $this->dropped = [];
  }

  public function deactivate(): void {
    $this->active = FALSE;
  }

  /**
   * Whether this record is a known-benign warning to drop (and count).
   */
  public function drops(mixed $level, string|\Stringable $message): bool {
    if (!$this->active || (int) $level !== RfcLogLevel::WARNING) {
      return FALSE;
    }
    $text = (string) $message;
    foreach (self::KNOWN as $pattern => $label) {
      if (preg_match($pattern, $text) === 1) {
        $this->dropped[$label] = ($this->dropped[$label] ?? 0) + 1;
        return TRUE;
      }
    }
    return FALSE;
  }

  /**
   * Label => count of warnings dropped since activate(); empty when none.
   *
   * @return array<string, int>
   */
  public function dropped(): array {
    return $this->dropped;
  }

  /**
   * One console line summarising what was dropped, or NULL when nothing was.
   */
  public function summary(): ?string {
    if ($this->dropped === []) {
      return NULL;
    }
    $parts = [];
    foreach ($this->dropped as $label => $n) {
      $parts[] = sprintf('%d× %s', $n, $label);
    }
    return sprintf(
      'quiet    %d known-benign warning(s) not shown: %s. Documented in runner/README.md; pass --all-warnings to see them.',
      array_sum($this->dropped),
      implode(', ', $parts),
    );
  }

}
