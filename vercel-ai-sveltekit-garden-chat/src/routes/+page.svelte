<script lang="ts">
  import { Chat } from "@ai-sdk/svelte";
  import { DefaultChatTransport } from "ai";

  // @ai-sdk/svelte exposes a Chat class (there is no useChat hook). Its id is sent with every
  // request; the server uses it as the Opik thread id, so one browser chat = one thread.
  const chat = new Chat({ transport: new DefaultChatTransport({ api: "/api/chat" }) });
  let input = $state("");

  function send(e: SubmitEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    chat.sendMessage({ text: input });
    input = "";
  }
</script>

<main>
  <h1>Sprout, the Hollowbrook garden assistant</h1>
  {#each chat.messages as message (message.id)}
    <p class={message.role}>
      <strong>{message.role === "user" ? "You" : "Sprout"}:</strong>
      {#each message.parts as part}{#if part.type === "text"}{part.text}{/if}{/each}
    </p>
  {/each}
  <form onsubmit={send}>
    <input bind:value={input} placeholder="When do I plant tomatoes?" disabled={chat.status !== "ready"} />
    <button disabled={chat.status !== "ready"}>Send</button>
  </form>
</main>

<style>
  main { max-width: 40rem; margin: 2rem auto; font-family: system-ui, sans-serif; }
  .user { color: #1d4ed8; }
  form { display: flex; gap: 0.5rem; margin-top: 1rem; }
  input { flex: 1; padding: 0.5rem; }
</style>
