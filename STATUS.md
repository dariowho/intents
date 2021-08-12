# Project Status

Here we report how individual features are currently supported in
*Intents* across different Connectors.

colors: 🟢 complete, 🟡 partial, 🔴 missing, ⚪ not planned


## Agent Definition

| Feature                          | Dialogflow ES | Alexa  | Snips  |
|----------------------------------|---------------|--------|--------|
| Entity declaration               | 🟢            | 🟢     | 🟢     |
| Intent declaration               | 🟢            | 🟢     | 🟢     |
| Examples Utterances              | 🟢            | 🟢     | 🟢     |
| Example Utterances with Entities | 🟢            | 🟢     | 🟢     |
| Parameters with System Entities  | 🟢            | 🟢     | 🟡     |
| Parameters with Custom Entities  | 🟢            | 🟢     | 🟢     |
| List Parameters                  | 🟢            | 🟢     | 🟢     |
| Required Parameters with prompts | 🟢            | 🔴     | 🔴     |
| Default Text Responses           | 🟢            | 🟢     | 🟢     |
| Platform Text/Rich Responses     | 🟢            | 🔴     | 🟢     |
| Custom Payload Responses         | 🟢            | ⚪     | 🟢     |
| Agent Webhook Settings           | 🟢            | 🔴     | ⚪     |
| Multi-Language Agents            | 🟢            | 🟢     | 🟢     |
| "Follow" Intent Relation         | 🟢            | 🔴     | 🔴     |

Some service-specific features (such as Actions, Contexts, Session Entities,
Extended System Entities and such) are not supported.


## Connector Capabilities

| Feature                                | Dialogflow ES | Alexa | Snips |
|----------------------------------------|---------------|-------|-------|
| Export Agent to ZIP                    | 🟢            | 🟢    | 🟢    |
| Upload Agent to existing Cloud project | 🟢            | 🔴    | 🟢*   |
| Predict Intent                         | 🟢            | ⚪    | 🟢    |
| Trigger Intent                         | 🟢            | ⚪    | 🟢    |
| Webhook Fulfillment interface          | 🟢            | 🔴    | 🟢    |
| Contexts Persistence                   | 🔴            | 🔴    | 🔴    |

(*) Snips runs locally; `SnipsConnector.upload()` trains the local model