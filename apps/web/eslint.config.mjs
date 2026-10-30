import nextConfig from "eslint-config-next";

// The package is CJS; handle both interop shapes for the flat config array.
const next = Array.isArray(nextConfig) ? nextConfig : (nextConfig.default ?? []);

const config = [
  ...next,
  {
    ignores: [".next/**", "node_modules/**"],
  },
];

export default config;
