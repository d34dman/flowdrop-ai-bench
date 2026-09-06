<?php

declare(strict_types=1);

namespace Drupal\flowdrop_ai_bench\EventSubscriber;

use Drupal\ai\Event\PreGenerateResponseEvent;
use Drupal\flowdrop_ai_bench\BenchRunContext;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;

/**
 * Stamps every AI call made during a benchmark run with that run's id.
 *
 * ai_metering reads an 'aim_context:<uuid>' tag into its context_id column,
 * which turns "which tokens belong to this run" into an exact query. The
 * alternative — bracketing a run with before/after usage-table id snapshots —
 * silently attributes another process's tokens to whichever run happens to be
 * open, and gives no error when it does.
 */
class AiContextTagSubscriber implements EventSubscriberInterface {

  public function __construct(
    private readonly BenchRunContext $runContext,
  ) {}

  /**
   * {@inheritdoc}
   */
  public static function getSubscribedEvents(): array {
    return [PreGenerateResponseEvent::EVENT_NAME => 'onPreGenerate'];
  }

  /**
   * Appends the run tag to the outgoing AI request.
   */
  public function onPreGenerate(PreGenerateResponseEvent $event): void {
    $uuid = $this->runContext->get();
    if ($uuid === NULL) {
      return;
    }
    $tags = $event->getTags();
    // ai_metering scans tag *values*, so this must be appended as a plain
    // string rather than set as a key.
    $tags[] = 'aim_context:' . $uuid;
    $event->setTags($tags);
  }

}
