# Project Status

Here we report how individual Dialogflow features are currently supported in
*Intents*.

colors: 🟢 complete, 🟡 partial, 🔴 missing, ⚪ not planned


## Basic Agent Definition

| Feature                          | Status | Note               |
|----------------------------------|--------|--------------------|
| Entity declaration               | 🟢     |                    |
| Intent declaration               | 🟢     |                    |
| Input/Output Context             | 🟢     |                    |
| Custom Events                    | 🟢     |                    |
| Examples Utterances              | 🟢     |                    |
| Example Utterances with Entities | 🟢     |                    |
| Action                           | ⚪     |                    |
| Parameters with System Entities  | 🟢     | Only some entities |
| Parameters with Custom Entities  | 🟢     |                    |
| Extended System Entities         | ⚪     |                    |
| Session Entities                 | ⚪     |                    |
| List Parameters                  | 🟢     |                    |
| Required Parameters with prompts | 🟢     |                    |
| Default Text Responses           | 🟢     |                    |
| Platform Text/Rich Responses     | 🟢     |                    |
| Custom Payload Responses         | 🟢     |                    |
| Agent Webhook Settings           | 🟢     |                    |
| Multi-Language Agents            | 🟢     |                    |

## Rich Agent definition

| Feature                          | Status | Note |
|----------------------------------|--------|------|
| Follow-up Intent Shortcut        | 🔴     |      |
| Intent Flow Graphs               | 🔴     |      |
| Context Required Parameters      | 🔴     |      |
| Advanced Slot Filling Framework  | 🔴     |      |

## Cloud Sync

| Feature                                | Status | Note |
|----------------------------------------|--------|------|
| Export Agent to ZIP                    | 🟢     |      |
| Upload Agent to existing Cloud project | 🟢     |      |
| Sync Language changes from Cloud       | 🔴     |      |
| Upload agent to a new Cloud project    | 🔴     |      |

## Prediction Client

| Feature                       | Status | Note |
|-------------------------------|--------|------|
| Predict Intent                | 🟢     |      |
| Trigger Intent                | 🟢     |      |
| Webhook Fulfillment interface | 🔴     |      |
| Contexts Persistence          | 🔴     |      |
| Offline Intent Triggers       | 🔴     |      |
| Offline Intent Predictions    | 🔴     |      |
