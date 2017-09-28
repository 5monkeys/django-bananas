/* eslint-env node */

/*
This script adds fallbacks for custom properties.

Input:

    :root {
      --theme-color: red;
    }

    a {
      color: var(--theme-color);
    }

Output:

    :root {
      --theme-color: red;
    }

    a {
      color: red /* fallback * /;
      color: var(--theme-color);
    }

This script should work with:

- Node.js 4 or later.
- npm 5 or later (npm 3 might work too).
*/

const fs = require("fs");
const path = require("path");
const postcss = require("postcss");
const customProperties = require("postcss-custom-properties");

const CSS_FILE = path.join(__dirname, "../bananas/static/admin/css/bananas.css");
// const CSS_FILE = path.join(__dirname, "test.css");

const FALLBACK_COMMENT = "/* fallback */";

const input = fs.readFileSync(CSS_FILE, "utf8");

const output = postcss()
  .use(removeOldFallbacks)
  .use(customProperties({ preserve: true }))
  .use(markFallbacksWithComment)
  .process(input).css;

fs.writeFileSync(CSS_FILE, output);

function removeOldFallbacks(root) {
  root.walkDecls(decl => {
    if (decl.toString().endsWith(FALLBACK_COMMENT)) {
      decl.remove();
    }
  });
}

function markFallbacksWithComment(root) {
  root.walkDecls(decl => {
    if (decl.value.includes("var(")) {
      const prev = decl.prev();
      if (prev) {
        prev.value += ` ${FALLBACK_COMMENT}`;
      }
    }
  });
}
