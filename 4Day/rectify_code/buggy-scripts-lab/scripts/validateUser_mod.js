const userPayload = process.argv[2];
const user = userPayload ? JSON.parse(userPayload) : undefined;

function describeAccess(u) {
  return u.roles.map((role) => role.toUpperCase()).join(", ");
}

if (!user) {
  console.error("Usage: node validateUser_mod.js '<user JSON with roles array>'");
  process.exit(1);
}

console.log("User access:", describeAccess(user));
