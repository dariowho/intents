# v0.3.0

Add:

* (#19) Add basic SnipsNLU Connector
* (#19) Add builtin entities module and `service_connector.PatchEntityMapping`
    * Add `Color`, `Language`, `MusicGenre` and `FirstName` builtin entities
* (#19) Add `EntityMapping.supported_languages` property
* (#17) Add Fulfillment interface with support for Dialogflow, Alexa and Snips
  * (#17) Add dataclass model for Dialogflow Responses, Webhook requests and
    Webhook responses
  * (#17) Add dataclass model for Alexa Fulfillment requests and responses
  * (#17) Implement recursive local fulfillment for Snips and Alexa
* (#17) Implement development fulfillment server
* (#16) Add configurable intent lifespan
* (#16) Add `new_lifespan` property to `follow` relation

Change:

* (#11) Breaking change: remove deprecated `Context` interface, `Intent.events`
  and `Intent.parameter_schema()` (`Intent.parameter_schema` is the way to
  access that information)
* (#16) Breaking change: replace `relations.related_intents()` with
  `relations.intent_relations()` (without deprecation)
* (#19) Change ServiceConnector to accept `LanguageCode` values as language
  codes, in addition to ISO strings
* (#17) Change (with deprecation) `Prediction.fulfillment_messages()` to be a
  property of type `IntentResponseDict`. Remove
  `Prediction.fulfillment_response_dict` (with deprecation)
* (#17) Move `service_connector` to `connectors.interface` (with deprecation)
* (#17) (internal) Refactor `ServiceEntityMappings` handling of Custom Entities 
* (#17) (internal) Refactor Dialogflow prediction modules:
    * `connectors.dialogflow_es.response_format` renamed to `prediction_format`
    * `DialogflowIntentResponse` classes moved from `prediction_format` to
      `prediction` 
    * Replace protobuf parameters with dataclass equivalents
* Change Dialogflow context/event names generation to use CamelCase ->
  snake_case conversion (e.g. context for `AskCoffee` will be `c_ask_coffee`
  instead of `c_askcoffee`). This requires re-uploading old agents.

Fix:

* (#19) Enforce name constraints on Entities
* (#17) Fix Entity export in Dialogflow (canonical value needed to be in
  synonyms as well)
* (#17) Patch entity entries with invalid characters in Alexa
* Fix Webhook status and Image Response in Dialogflow `DetectIntent` payload parsing

# v0.2.0

This release contains breaking changes (see [semantic versioning FAQ](https://semver.org/#doesnt-this-discourage-rapid-development-and-fast-iteration)), they are reported below.

* (#4) Add experimental Alexa connector
* (#7) Add `follow` intent relation
* (#7) Deprecate manual Contexts
* (#7) Breaking change: predict() and trigger() now return Prediction objects
* (#5) Change documentation to render pages separately
* (#9) Change Intent and Agent model to enforce stricter naming rules
* (#10) Change `Intent.parameter_schema()` to `Intent.parameter_schema` (with deprecation)
* (#10) Fix double dataclass decorator bug
* (#13) Fix Entities de-serialization during predictions

# v0.1.0

First release, includes

* **Model** for basic Agent Definition
    * Intents with parameters, default parameters and List parameters
    * System Entities
    * Custom Entities
    * Input/Output contexts
* **Language** Resources implementation
    * Example Utterances with parameter references
    * Slot filling prompts
    * Text responses
    * Rich responses (Quick Replies, Image, Card and Custom Payloads)
    * Multi-language support 
* **Dialogflow ES** connector
    * Export Agent as ZIP
    * Upload Agent to Cloud project
    * Make *predict* requests
    * Make *trigger* requests
    