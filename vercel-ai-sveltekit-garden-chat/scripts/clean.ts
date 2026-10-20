import { deleteAllTraces } from "./opik-rest";

console.log(`Deleted ${await deleteAllTraces()} traces (the online rule is untouched).`);
