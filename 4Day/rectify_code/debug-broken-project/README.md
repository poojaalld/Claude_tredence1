# Debug Broken Authorization Project

This lab adds a real-time debugging sandbox to the Module 03 labs. Learners fix a broken authorization stack (React + Express) inside the incorrect/ folder, then compare their solution against the working copy in correct/ to confirm the bug was fully resolved.

## Lab layout

- correct/backend/ and correct/frontend/ contain a working authorization app that accepts a user ID and password, calls POST /login, and shows a "Sign in successful" prompt when the credentials match the hard-coded store.
- incorrect/backend/ and incorrect/frontend/ contain the same stack with intentional issues (missing middleware, a typo in the login route, inconsistent fetch handling, etc.) so you can practice debugging the real service.

## Getting started

1. Open two terminals for each stack (correct and incorrect).
2. In each backend folder, run  
`npm install`, then  
`npm run dev` (the servers listen on http://localhost:5000).
3. In each frontend folder, run  
`npm run dev` (the UI runs on http://localhost:5173). The correct frontend now serves a simple static bundle via a lightweight Node script, so no bundler is required; it talks directly to http://localhost:5000/login.
4. Sign in as learner / pass123 (or demo / claude) to confirm the working stack and reproduce the broken behavior.

## Exercise steps

1. Inspect the logs or DevTools network tab for the incorrect stack to find the error (missing JSON middleware, incorrect route, or failing fetch call).
2. Use Claude to propose and apply fixes inside incorrect/ so the login flow behaves like the working stack.
3. Once the incorrect stack succeeds, compare both folders (e.g., git diff -r) to verify your fix matches the working implementation.
4. Optional: extend the lab by adding another user or introducing a new front-end validation bug for extra debugging practice.
