/* Pragmatic lint config for the Vite + React + TypeScript app.
   Kept lenient on rules that would flag the existing codebase's patterns
   (explicit any, etc.) so it's adoptable now and can be tightened later. */
module.exports = {
  root: true,
  env: { browser: true, es2021: true },
  parser: '@typescript-eslint/parser',
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module', ecmaFeatures: { jsx: true } },
  plugins: ['@typescript-eslint', 'react-hooks'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  settings: { react: { version: 'detect' } },
  ignorePatterns: ['dist', 'node_modules', 'public', '*.config.js', '*.config.ts'],
  rules: {
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    '@typescript-eslint/no-empty-function': 'off',
    'no-empty': ['warn', { allowEmptyCatch: true }],
  },
};
