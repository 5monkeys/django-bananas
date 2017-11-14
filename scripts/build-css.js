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

const mainCssFile = path.join(
  __dirname,
  "../bananas/static/admin/bananas/css/bananas.css"
);

const variables = extractVariables(mainCssFile);

const CSS_FILES = [
  mainCssFile,
  path.join(__dirname, "../bananas/static/admin/bananas/css/banansive.css")
];

const FALLBACK_COMMENT = "/* fallback */";

CSS_FILES.forEach(cssFile => {
  const input = fs.readFileSync(cssFile, "utf8");

  const output = postcss()
    .use(removeOldFallbacks)
    .use(customProperties({ preserve: true, variables }))
    .use(markFallbacksWithComment)
    .process(input).css;

  fs.writeFileSync(cssFile, output);
});

function extractVariables(file) {
  const input = fs.readFileSync(file, "utf8");
  const root = postcss.parse(input);

  const variables = {};

  root.walkRules(":root", rule => {
    rule.each(decl => {
      if (decl.prop && decl.prop.startsWith("--")) {
        variables[decl.prop.slice(2)] = decl.value;
      }
    });
  });

  return variables;
}

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
