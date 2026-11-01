#!/usr/bin/env node
/**
 * Blender MCP Server for Claude Code
 * Connects to the running Blender GUI via the MCP for Blender socket on port 9876.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import * as net from "net";

const server = new McpServer({
  name: "blender-live-mcp",
  version: "1.0.0",
});

const BLENDER_HOST = "127.0.0.1";
const BLENDER_PORT = 9876;

function sendToBlender(commandType, params = {}, timeoutMs = 60000) {
  return new Promise((resolve, reject) => {
    const client = net.createConnection(BLENDER_PORT, BLENDER_HOST);
    let buffer = "";
    let completed = false;

    const timer = setTimeout(() => {
      if (!completed) {
        completed = true;
        client.destroy();
        reject(new Error("Timeout waiting for response from Blender GUI. Is Blender running with MCP for Blender enabled?"));
      }
    }, timeoutMs);

    client.on("connect", () => {
      const payload = { type: commandType, params };
      client.write(JSON.stringify(payload) + "\n");
    });

    client.on("data", (chunk) => {
      buffer += chunk.toString("utf8");
      try {
        const parsed = JSON.parse(buffer);
        if (!completed) {
          completed = true;
          clearTimeout(timer);
          client.end();
          resolve(parsed);
        }
      } catch (e) {
        // Buffer until complete JSON
      }
    });

    client.on("error", (err) => {
      if (!completed) {
        completed = true;
        clearTimeout(timer);
        reject(new Error(`Blender connection error: ${err.message}`));
      }
    });

    client.on("close", () => {
      if (!completed) {
        completed = true;
        clearTimeout(timer);
        if (buffer) {
          try {
            resolve(JSON.parse(buffer));
          } catch (e) {
            reject(new Error(`Connection closed with partial data: ${buffer}`));
          }
        } else {
          reject(new Error("Connection closed with empty response."));
        }
      }
    });
  });
}

// Tool 1: execute_blender_code
server.tool(
  "execute_blender_code",
  "Executes Python bpy code in the running Blender GUI in real time. Redraws viewport automatically.",
  {
    code: z.string().describe("Python bpy code to execute live in Blender"),
  },
  async ({ code }) => {
    try {
      const response = await sendToBlender("execute_code", { code });
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(response, null, 2),
          },
        ],
      };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: "text", text: `Error: ${err.message}` }],
      };
    }
  }
);

// Tool 2: get_scene_objects
server.tool(
  "get_scene_objects",
  "Fetches the list of all objects, dimensions, locations, and materials in the active Blender scene.",
  {},
  async () => {
    try {
      const response = await sendToBlender("get_scene_info", {});
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(response, null, 2),
          },
        ],
      };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: "text", text: `Error: ${err.message}` }],
      };
    }
  }
);

// Tool 3: save_blender_project
server.tool(
  "save_blender_project",
  "Saves the active Blender project to disk (.blend file).",
  {
    filepath: z.string().optional().describe("Optional target path to save the .blend file"),
  },
  async ({ filepath }) => {
    const savePath = filepath || "C:\\Users\\Win11 Pro\\Desktop\\chemlab\\chemlab.blend";
    const code = `import bpy\nbpy.ops.wm.save_mainfile(filepath=r"${savePath}")\nprint("Saved to ${savePath}")`;
    try {
      const response = await sendToBlender("execute_code", { code });
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(response, null, 2),
          },
        ],
      };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: "text", text: `Error: ${err.message}` }],
      };
    }
  }
);

async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

run().catch((err) => {
  console.error("Blender MCP server fatal error:", err);
  process.exit(1);
});
