const userPayload = process.argv[2];
const user = userPayload ? JSON.parse(userPayload) : undefined;

function describeAccess(u) {
  return u.roles.map((role) => role.toUpperCase()).join(", ");
}

console.log("User access:", describeAccess(user));
