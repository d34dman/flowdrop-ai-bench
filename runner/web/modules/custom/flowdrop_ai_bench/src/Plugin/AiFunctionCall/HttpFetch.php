<?php

declare(strict_types=1);

namespace Drupal\flowdrop_ai_bench\Plugin\AiFunctionCall;

use Drupal\ai\Attribute\FunctionCall;
use Drupal\ai\Base\FunctionCallBase;
use Drupal\ai\Service\FunctionCalling\FunctionCallInterface;
use Drupal\ai\Service\FunctionCalling\ExecutableFunctionCallInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use GuzzleHttp\ClientInterface;
use GuzzleHttp\Exception\GuzzleException;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Lets an AI agent retrieve a URL itself.
 *
 * The benchmark compares a FlowDrop graph that fetches a page before handing
 * it to a model against a Drupal AI Agent doing the same job. Without a fetch
 * tool the agent cannot reach the page on its own, so the comparison is
 * between an agent that is handed its input and one that goes and gets it —
 * two different tasks. This closes that gap.
 *
 * The plugin id and function name are kept exactly as they were in the
 * previous fd_bench module: existing agent configuration references
 * `ai_agent:http_fetch` and would silently stop calling this tool if either
 * changed.
 */
#[FunctionCall(
  id: 'ai_agent:http_fetch',
  function_name: 'ai_agent_http_fetch',
  name: 'HTTP Fetch',
  description: 'Retrieves the content at a URL over HTTP GET and returns the response body. Use this to read a web page before working with its content.',
  group: 'information_tools',
  context_definitions: [
    'url' => new ContextDefinition(
      data_type: 'string',
      label: new TranslatableMarkup("URL"),
      description: new TranslatableMarkup("The absolute http:// or https:// URL to retrieve."),
      required: TRUE,
    ),
  ],
)]
class HttpFetch extends FunctionCallBase implements ExecutableFunctionCallInterface {

  /**
   * Caps a single response so one large page cannot exhaust the context window.
   */
  private const MAX_BYTES = 2097152;

  /**
   * The HTTP client.
   */
  protected ClientInterface $httpClient;

  /**
   * {@inheritdoc}
   */
  public static function create(ContainerInterface $container, array $configuration, $plugin_id, $plugin_definition): FunctionCallInterface|static {
    $instance = parent::create($container, $configuration, $plugin_id, $plugin_definition);
    $instance->httpClient = $container->get('http_client');
    return $instance;
  }

  /**
   * {@inheritdoc}
   */
  public function execute() {
    $url = trim((string) $this->getContextValue('url'));

    // The model chooses this value, so it is untrusted input. Restricting it
    // to absolute http(s) URLs keeps the tool from being talked into reading
    // file:// paths or other local schemes.
    if (!filter_var($url, FILTER_VALIDATE_URL) || !preg_match('#^https?://#i', $url)) {
      $this->setOutput('Error: "' . $url . '" is not an absolute http:// or https:// URL.');
      return;
    }

    try {
      $response = $this->httpClient->request('GET', $url, [
        'timeout' => 30,
        'allow_redirects' => TRUE,
        'headers' => ['Accept' => 'text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8'],
      ]);
    }
    catch (GuzzleException $e) {
      // Returned as text rather than thrown: the agent can react to a failed
      // fetch (retry, try another URL, report it), which it cannot do with an
      // exception that aborts its loop.
      $this->setOutput('Error fetching ' . $url . ': ' . $e->getMessage());
      return;
    }

    $body = (string) $response->getBody();
    if (strlen($body) > self::MAX_BYTES) {
      $body = substr($body, 0, self::MAX_BYTES)
        . "\n\n[truncated after " . self::MAX_BYTES . " bytes]";
    }

    $this->setOutput($body);
  }

}
