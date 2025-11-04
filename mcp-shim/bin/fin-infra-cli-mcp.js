#!/usr/bin/env node
const { spawn } = require("child_process");

const UVX  = process.env.UVX_PATH || "uvx";
const REPO = process.env.FIN_INFRA_REPO || "https://github.com/aliikhatami94/fin-infra.git";
const REF  = process.env.FIN_INFRA_REF  || "main";
const SPEC = `git+${REPO}@${REF}`;

const args = [
    "--quiet",
    ...(process.env.UVX_REFRESH ? ["--refresh"] : []),
    "--from", SPEC,          // primary package: fin-infra
    "python", "-m", "fin_infra.mcp.fin_infra_mcp",
    "--transport", "stdio",
    ...process.argv.slice(2)
];

console.error("[fin-infra-cli-mcp] using", { SPEC, UVX, refresh: !!process.env.UVX_REFRESH });
const child = spawn(UVX, args, { stdio: "inherit", shell: process.platform === "win32" });
child.on("exit", code => process.exit(code));
