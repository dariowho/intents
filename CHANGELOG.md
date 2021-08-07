# v0.3.0 (in development)

* (#19) Add basic SnipsNLU Connector
* (#19) Add builtin entities module and `service_connector.PatchEntityMapping`
    * Add `Color`, `Language`, `MusicGenre` and `FirstName` builtin entities
* (#19) Add `EntityMapping.supported_languages` property
* (#17) Add dataclass model for Dialogflow Responses and Webhook requests
* (#17) Breaking changes (internal):
    * `connectors.dialogflow_es.response_format` renamed to `prediction_format`
    * `DialogflowIntentResponse` classes moved from `prediction_format` to
      `prediction` 
    * Replaced protobuf parameters with dataclass equivalents
* (#19) Fix name constraints not enforced on Entities

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
    