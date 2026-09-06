<?php

declare(strict_types=1);

namespace Drupal\flowdrop_ai_bench;

use Drupal\Core\DependencyInjection\ContainerBuilder;
use Drupal\Core\DependencyInjection\ServiceModifierInterface;
use Drupal\flowdrop_ai_bench\Logger\FilteringDrushLog;
use Drush\Log\DrushLog;
use Symfony\Component\DependencyInjection\Reference;

/**
 * Swaps Drush's Drupal-to-console log bridge for the filtering one.
 *
 * Only when Drush registered the bridge (a Drush request); a web request has
 * no `logger.drupaltodrush` service and is left alone.
 */
final class FlowdropAiBenchServiceProvider implements ServiceModifierInterface {

  /**
   * {@inheritdoc}
   */
  public function alter(ContainerBuilder $container): void {
    if (!$container->hasDefinition('logger.drupaltodrush') || !class_exists(DrushLog::class)) {
      return;
    }
    $container->getDefinition('logger.drupaltodrush')
      ->setClass(FilteringDrushLog::class)
      ->addArgument(new Reference('flowdrop_ai_bench.known_warnings'));
  }

}
