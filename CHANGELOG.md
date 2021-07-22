# v0.2.0 (in development)

This release, like probably many others in 0.x (see [semantic versioning FAQ](https://semver.org/#doesnt-this-discourage-rapid-development-and-fast-iteration)), contains breaking changes. They are reported below.

* Add experimental Alexa connector
* Add `follow` intent relation
* Breaking change: predict() and trigger() now return Prediction objects
* Change `Intent.parameter_schema()` to `Intent.parameter_schema` (with deprecation)
* Fix double dataclass decorator bug

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
    