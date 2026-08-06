const defaults = {
  host: "api.example.com",
  retries: 3,
  timeout: 5000
};

const consolidated = { ...defaults, ...overrides };
console.log("Merged configuration:", consolidated);
