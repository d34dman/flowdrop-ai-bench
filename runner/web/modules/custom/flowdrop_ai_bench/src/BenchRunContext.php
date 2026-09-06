<?php

declare(strict_types=1);

namespace Drupal\flowdrop_ai_bench;

/**
 * Carries the identifier of the benchmark run currently executing.
 *
 * The harness sets this immediately before launching a workflow and clears it
 * afterwards, so every AI call the run makes can be stamped with it.
 */
class BenchRunContext {

  /**
   * The current run's UUID, or NULL outside a benchmark run.
   */
  private ?string $runUuid = NULL;

  public function set(?string $uuid): void {
    $this->runUuid = $uuid;
  }

  public function get(): ?string {
    return $this->runUuid;
  }

}
