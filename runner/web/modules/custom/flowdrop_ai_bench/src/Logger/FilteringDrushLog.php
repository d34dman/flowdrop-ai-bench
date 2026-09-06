<?php

declare(strict_types=1);

namespace Drupal\flowdrop_ai_bench\Logger;

use Drupal\Core\Logger\LogMessageParserInterface;
use Drush\Log\DrushLog;

/**
 * Drush's Drupal-to-console log bridge, minus the warnings a bench run expects.
 *
 * Replaces the class of Drush's `logger.drupaltodrush` service (see
 * FlowdropAiBenchServiceProvider). Every Drupal log record still reaches
 * Drush's console logger exactly as before, except a warning that
 * KnownWarnings recognises while a bench:* command has activated it.
 */
final class FilteringDrushLog extends DrushLog {

  public function __construct(
    LogMessageParserInterface $parser,
    private readonly KnownWarnings $known,
  ) {
    parent::__construct($parser);
  }

  /**
   * {@inheritdoc}
   */
  public function log($level, $message, array $context = []): void {
    if ($this->known->drops($level, $message)) {
      return;
    }
    parent::log($level, $message, $context);
  }

}
