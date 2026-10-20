<script lang="ts">
  import { Chat } from "@ai-sdk/svelte";

  const chat = new Chat({});
  let input = $state("");
  const busy = $derived(chat.status === "submitted" || chat.status === "streaming");

  function submit(e: SubmitEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    chat.sendMessage({ text });
    input = "";
  }
</script>

<main>
  <h1>Sprout</h1>
  <p class="sub">Ask about watering, pests, pruning or compost. Replies stream in as they are written.</p>

  <div class="log">
    {#each chat.messages as message (message.id)}
      <div class="row {message.role}">
        <div class="bubble">
          {#each message.parts as part}
            {#if part.type === "text"}{part.text}{/if}
          {/each}
        </div>
      </div>
    {/each}
  </div>

  <form onsubmit={submit}>
    <input bind:value={input} placeholder="Why are my basil leaves turning black?" disabled={busy} />
    <button disabled={busy || !input.trim()}>Send</button>
  </form>
</main>

<style>
  :global(body) { font-family: system-ui, sans-serif; background: #f4f7f2; margin: 0; color: #1d2a1f; }
  main { max-width: 640px; margin: 0 auto; padding: 2rem 1rem; min-height: 100vh; box-sizing: border-box; display: flex; flex-direction: column; }
  h1 { font-size: 1.3rem; margin: 0 0 .25rem; }
  .sub { color: #5f6f62; margin: 0 0 1rem; font-size: .9rem; }
  .log { flex: 1; }
  .row { display: flex; margin: .6rem 0; }
  .row.user { justify-content: flex-end; }
  .bubble { max-width: 85%; padding: .6rem .9rem; border-radius: 12px; white-space: pre-wrap; line-height: 1.45; background: #fff; border: 1px solid #dde6da; }
  .user .bubble { background: #2f7d4f; color: #fff; border: none; }
  form { display: flex; gap: .5rem; margin-top: 1rem; }
  input { flex: 1; padding: .65rem .8rem; border: 1px solid #c9d6c6; border-radius: 8px; font-size: 1rem; }
  button { padding: .65rem 1.1rem; border: none; border-radius: 8px; background: #2f7d4f; color: #fff; font-size: 1rem; cursor: pointer; }
  button:disabled { opacity: .5; cursor: default; }
</style>
