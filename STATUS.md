# Project Status

Here we report how individual features are currently supported in
*Intents* across different Connectors.

colors: 🟢 complete, 🟡 partial, 🔴 missing, ⚪ not planned


## Basic Agent Definition

| Feature                          | Dialogflow ES | Alexa  |
|----------------------------------|---------------|--------|
| Entity declaration               | 🟢            | 🟢     |
| Intent declaration               | 🟢            | 🟢     |
| Examples Utterances              | 🟢            | 🟢     |
| Example Utterances with Entities | 🟢            | 🟢     |
| Parameters with System Entities  | 🟢            | 🟢     |
| Parameters with Custom Entities  | 🟢            | 🟢     |
| List Parameters                  | 🟢            | 🟢     |
| Required Parameters with prompts | 🟢            | 🔴     |
| Default Text Responses           | 🟢            | 🔴     |
| Platform Text/Rich Responses     | 🟢            | 🔴     |
| Custom Payload Responses         | 🟢            | 🔴     |
| Agent Webhook Settings           | 🟢            | 🔴     |
| Multi-Language Agents            | 🟢            | 🟢     |
| "Follow" Intent Relation         | 🟢            | 🔴     |

Some service-specific features (such as Actions, Contexts, Session Entities,
Extended System Entities and such) are not supported.

## Cloud Sync

| Feature                                | Dialogflow ES | Alexa |
|----------------------------------------|---------------|-------|
| Export Agent to ZIP                    | 🟢            | 🟢    |
| Upload Agent to existing Cloud project | 🟢            | 🔴    |
| Sync Language changes from Cloud       | 🔴            | 🔴    |
| Upload agent to a new Cloud project    | 🔴            | 🔴    |

## Prediction Client

| Feature                       | Dialogflow ES | Alexa |
|-------------------------------|---------------|-------|
| Predict Intent                | 🟢            | ⚪    |
| Trigger Intent                | 🟢            | ⚪    |
| Webhook Fulfillment interface | 🔴            | 🔴    |
| Contexts Persistence          | 🔴            | 🔴    |
| Offline Intent Triggers       | 🔴            | 🔴    |
| Offline Intent Predictions    | 🔴            | 🔴    |
