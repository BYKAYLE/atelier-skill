#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF' > /private/tmp/sisyphus_claude_fixture_node/src/message.txt
hello from node fixture
EOF

cat <<'EOF' > /private/tmp/sisyphus_claude_fixture_node/test/message.test.js
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("message file contains fixture marker", () => {
  const content = readFileSync(new URL("../src/message.txt", import.meta.url), "utf8");
  assert.match(content, /fixture/);
});
EOF

cat <<'EOF' > /private/tmp/sisyphus_claude_fixture_python/app/message.txt
hello from python fixture
EOF

cat <<'EOF' > /private/tmp/sisyphus_claude_fixture_python/tests/test_message.py
import unittest

from app.message import read_message


class MessageTests(unittest.TestCase):
    def test_message_contains_fixture_marker(self) -> None:
        self.assertIn("fixture", read_message())


if __name__ == "__main__":
    unittest.main()
EOF

cat <<'EOF' > /private/tmp/sisyphus_claude_fixture_service/apps/web/message.txt
web fixture marker
EOF

cat <<'EOF' > /private/tmp/sisyphus_claude_fixture_service/apps/web/check.js
import { readFileSync } from "node:fs";

const content = readFileSync(new URL("./message.txt", import.meta.url), "utf8").trim();

if (!content.includes("fixture")) {
  console.error("web message must contain fixture");
  process.exit(1);
}

console.log(`web message: ${content}`);
EOF

cat <<'EOF' > /private/tmp/sisyphus_claude_fixture_service/apps/api/config.json
{
  "statusMessage": "api fixture marker",
  "retryCount": 2
}
EOF

cat <<'EOF' > /private/tmp/sisyphus_claude_fixture_service/apps/api/check.js
import { readFileSync } from "node:fs";

const config = JSON.parse(readFileSync(new URL("./config.json", import.meta.url), "utf8"));

if (!String(config.statusMessage || "").includes("fixture")) {
  console.error("api statusMessage must contain fixture");
  process.exit(1);
}

if (config.retryCount !== 2) {
  console.error("api retryCount must stay at 2");
  process.exit(1);
}

console.log(`api status: ${config.statusMessage}`);
EOF

cat <<'EOF' > /private/tmp/sisyphus_claude_fixture_service/tests/service.test.js
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("web message still contains fixture marker", () => {
  const content = readFileSync(new URL("../apps/web/message.txt", import.meta.url), "utf8");
  assert.match(content, /fixture/);
});

test("api config still contains fixture marker", () => {
  const config = JSON.parse(readFileSync(new URL("../apps/api/config.json", import.meta.url), "utf8"));
  assert.match(config.statusMessage, /fixture/);
  assert.equal(config.retryCount, 2);
});
EOF

echo "Fixture reset complete"
