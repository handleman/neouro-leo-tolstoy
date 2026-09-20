/**
 * Phase 0 stub: prints the API base URL from env and exits.
 * Real REPL (chat loop, --lang, citations) lands in Phase 3 (0009).
 */

const apiUrl = process.env["TOLSTOY_API_URL"] ?? "http://127.0.0.1:8000";
const lang = process.env["TOLSTOY_DEFAULT_LANG"] ?? "ru";

console.log(`tolstoy-chat (stub) -> API: ${apiUrl} [lang=${lang}]`);
