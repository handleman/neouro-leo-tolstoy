/**
 * Chat REPL (0009 step 4): readline loop over POST /chat.
 * Commands: /ru, /en (switch answer language), /chain <name>, /quit.
 * Transport errors (422/404/503, refused) render as one human line.
 */

import * as readline from "node:readline";

interface ChatSource {
  chunk_id: string;
  volume: number | null;
  work: string;
  chapter: string;
  score: number;
}

interface ChatResponse {
  answer: string;
  answer_lang: string;
  chain: string;
  sources: ChatSource[];
}

function parseArgs(argv: string[]): { api: string; lang: string; chain: string } {
  let api = process.env["TOLSTOY_API_URL"] ?? "http://127.0.0.1:8000";
  let lang = process.env["TOLSTOY_DEFAULT_LANG"] ?? "ru";
  let chain = "naive";
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--api" && argv[i + 1]) api = argv[++i] as string;
    else if (argv[i] === "--lang" && argv[i + 1]) lang = argv[++i] as string;
    else if (argv[i] === "--chain" && argv[i + 1]) chain = argv[++i] as string;
  }
  if (lang !== "ru" && lang !== "en") lang = "ru";
  return { api, lang, chain };
}

function renderSources(sources: ChatSource[]): void {
  if (sources.length === 0) {
    console.log("(no sources)");
    return;
  }
  sources.forEach((s, i) => {
    const vol = s.volume === null ? "vol?" : `vol${String(s.volume).padStart(2, "0")}`;
    console.log(`[${i + 1}] ${vol} | ${s.work} | ${s.chapter} | ${s.chunk_id} | ${s.score.toFixed(4)}`);
  });
}

async function ask(api: string, question: string, lang: string, chain: string): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${api.replace(/\/$/, "")}/chat`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question, lang, chain }),
    });
  } catch {
    console.log("error: cannot reach API (is uvicorn running?)");
    return;
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* keep status text */
    }
    console.log(`error ${res.status}: ${detail}`);
    return;
  }
  const body = (await res.json()) as ChatResponse;
  if (body.answer_lang === "en") console.log("[translated from RU sources]");
  console.log(body.answer);
  renderSources(body.sources);
}

async function main(): Promise<void> {
  const opts = parseArgs(process.argv.slice(2));
  let { lang, chain } = opts;
  const api = opts.api;
  console.log(`cyber-tolstoy chat -> ${api} [lang=${lang} chain=${chain}]`);
  console.log("Commands: /ru /en /chain <name> /quit");

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  let inputClosed = false;
  rl.on("close", () => {
    inputClosed = true;
  });
  const prompt = (): void => {
    if (!inputClosed) rl.prompt();
  };
  prompt();

  for await (const raw of rl) {
    const line = raw.trim();
    if (!line) {
      prompt();
      continue;
    }
    if (line === "/quit" || line === "/exit") break;
    if (line === "/ru" || line === "/en") {
      lang = line.slice(1);
      console.log(`lang=${lang}`);
      prompt();
      continue;
    }
    if (line.startsWith("/chain")) {
      const name = line.split(/\s+/)[1];
      if (!name) {
        console.log("usage: /chain <name>");
      } else {
        chain = name;
        console.log(`chain=${chain}`);
      }
      prompt();
      continue;
    }
    await ask(api, line, lang, chain);
    prompt();
  }
  rl.close();
}

void main();
