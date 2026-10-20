import { PromptType, type Prompt } from "opik";
import { BRIEF_V1, BRIEF_V2, PROMPT_NAME, V1_CHANGE, V2_CHANGE } from "./prompts.js";

// The slice of the Opik client this module uses; tests pass a stub.
export interface PromptLibrary {
  getPrompt(opts: { name: string; version?: string; projectName?: string }): Promise<Prompt | null>;
  api: {
    prompts: {
      createPromptVersion(req: {
        name: string;
        projectName?: string;
        version: { template: string; type: PromptType; changeDescription: string; tags: string[] };
      }): unknown;
    };
  };
}

export interface BriefVersions {
  v1: Prompt;
  v2: Prompt;
  created: number;
}

const TAGS = ["image-generation", "children-book"];

// Find-or-create: look each version up first and only create what is missing, so
// re-runs never add versions. The library ends with exactly two however often this runs.
export async function ensureBriefVersions(
  library: PromptLibrary,
  projectName: string,
): Promise<BriefVersions> {
  let created = 0;
  const create = async (template: string, changeDescription: string) => {
    created += 1;
    // createPromptVersion posts a new version of the prompt to the Opik prompt library
    // together with its change description (shown in the version history). The SDK's
    // higher-level createPrompt never sends changeDescription, so we call the API client.
    await library.api.prompts.createPromptVersion({
      name: PROMPT_NAME,
      projectName,
      version: { template, type: PromptType.MUSTACHE, changeDescription, tags: TAGS },
    });
  };

  let v1 = await library.getPrompt({ name: PROMPT_NAME, version: "v1", projectName });
  if (!v1) {
    await create(BRIEF_V1, V1_CHANGE);
    v1 = await library.getPrompt({ name: PROMPT_NAME, version: "v1", projectName });
  }
  let v2 = await library.getPrompt({ name: PROMPT_NAME, version: "v2", projectName });
  if (!v2) {
    await create(BRIEF_V2, V2_CHANGE);
    v2 = await library.getPrompt({ name: PROMPT_NAME, version: "v2", projectName });
  }
  if (!v1 || !v2) throw new Error(`Prompt "${PROMPT_NAME}" is missing v1 or v2 after setup`);
  return { v1, v2, created };
}
