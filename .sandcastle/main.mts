import { run, claudeCode } from "@ai-hero/sandcastle";
import { docker } from "@ai-hero/sandcastle/sandboxes/docker";

const FORGEJO_URL = process.env.FORGEJO_URL ?? "http://100.108.73.68:3002";
const FORGEJO_OWNER = process.env.FORGEJO_OWNER ?? "Holly";
const FORGEJO_REPO = process.env.FORGEJO_REPO ?? "bomber-memorial-site";

const LIST_TASKS = [
  `curl -sf -H "Authorization: token $FORGEJO_TOKEN"`,
  `"${FORGEJO_URL}/api/v1/repos/${FORGEJO_OWNER}/${FORGEJO_REPO}/issues?state=open&type=issues&labels=ralph&limit=50"`,
  `| jq '[.[] | {number, title, body, labels: [.labels[].name], state}]'`,
].join(" ");

const VIEW_TASK = [
  `curl -sf -H "Authorization: token $FORGEJO_TOKEN"`,
  `"${FORGEJO_URL}/api/v1/repos/${FORGEJO_OWNER}/${FORGEJO_REPO}/issues/<TASK_ID>"`,
  `| jq '{number, title, body, labels: [.labels[].name], comments_count: .comments}'`,
].join(" ");

await run({
  name: "ralph",

  sandbox: docker({
    imageName: "sandcastle:bomber-memorial-site",
    network: "host",
    containerUid: 1000,
    containerGid: 1000,
    env: {
      FORGEJO_TOKEN: process.env.FORGEJO_TOKEN ?? "",
    },
  }),

  agent: claudeCode("claude-sonnet-4-6"),
  promptFile: "./.sandcastle/prompt.md",
  maxIterations: 1,
  branchStrategy: { type: "merge-to-head" },

  hooks: {
    sandbox: {
      onSandboxReady: [{ command: "npm install --no-audit --no-fund --prefer-offline" }],
    },
  },

  promptArgs: {
    LIST_TASKS_COMMAND: LIST_TASKS,
    VIEW_TASK_COMMAND: VIEW_TASK,
    FORGEJO_URL,
    FORGEJO_OWNER,
    FORGEJO_REPO,
  },
});
