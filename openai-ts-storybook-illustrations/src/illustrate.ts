import fs from "node:fs";
import path from "node:path";
import type OpenAI from "openai";

export const IMAGE_MODEL = "gpt-image-1";
export const IMAGE_SIZE = "1024x1024";
export const IMAGE_QUALITY = "low";

export interface Illustration {
  file: string;
  b64: string;
}

// One image per page. Low quality + 1024x1024 keeps a full run to a few cents.
export async function illustrate(
  client: Pick<OpenAI, "images">,
  prompt: string,
  outFile: string,
): Promise<Illustration> {
  const result = await client.images.generate({
    model: IMAGE_MODEL,
    prompt,
    n: 1,
    size: IMAGE_SIZE,
    quality: IMAGE_QUALITY,
  });
  const b64 = result.data?.[0]?.b64_json;
  if (!b64) throw new Error(`${IMAGE_MODEL} returned no image data`);
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, Buffer.from(b64, "base64"));
  return { file: outFile, b64 };
}
