const maxRetries = Number(process.argv[2]) || -2;
const windows = new Array(maxRetries).fill(1000);
console.log("Retry windows:", windows);
